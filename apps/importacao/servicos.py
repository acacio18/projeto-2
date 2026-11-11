"""Versões das notas de um diário (IDs 6 e 19): registrar, confirmar, trocar a vigente e descartar.

`registrar_versao` recebe os dados no mesmo formato do gabarito do boletim de exemplo
(tests/fixtures/boletins/exemplo_boletins.gabarito.json, "esquema": 1). Na E3, o leitor de PDF
produzirá exatamente esse formato. Curso, disciplina, diário e estudantes são encontrados pelos códigos
do SUAP (deduplicação) ou criados.

Quem pode registrar e confirmar uma versão (PRC-12): o professor responsável pelo diário (um diário
novo fica com quem importou) e quem gerencia o curso (Coordenador do curso ou Administrador).
"""

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.academico.models import Curso, Diario, Disciplina, Estudante, MatriculaDiario
from apps.auditoria.models import TipoEvento
from apps.auditoria.registro import registrar
from apps.contas import escopo
from apps.contas.models import Perfil
from apps.importacao.models import Importacao, MetodoExtracao, StatusImportacao
from apps.notas.models import RegistroBimestral, ResultadoAluno

ESQUEMA_SUPORTADO = 1


def _decimal(valor):
    return None if valor is None else Decimal(str(valor))


def pode_cuidar_do_diario(usuario, diario) -> bool:
    """Registrar, confirmar e escolher a versão vigente: professor responsável ou quem gerencia o curso."""
    if not escopo.esta_ativo(usuario):
        return False
    return diario.professor_id == usuario.pk or escopo.pode_gerenciar_curso(usuario, diario.curso)


def _diario_para(por, dados) -> Diario:
    curso_dados, diario_dados = dados["curso"], dados["diario"]
    periodo = dados["periodo_letivo"]
    curso, _ = Curso.objects.get_or_create(
        codigo=curso_dados["codigo"], defaults={"nome": curso_dados["nome"]}
    )
    disciplina, _ = Disciplina.objects.get_or_create(
        curso=curso,
        codigo=diario_dados["disciplina_codigo"],
        defaults={
            "nome": diario_dados["disciplina_nome"],
            "carga_horaria_horas": diario_dados["carga_horaria_horas"],
        },
    )
    diario = (
        Diario.objects.select_for_update()
        .filter(codigo=diario_dados["codigo"], ano_letivo=periodo["ano"], periodo_letivo=periodo["periodo"])
        .first()
    )
    if diario is None:
        da_aula = por.perfil in (Perfil.PROFESSOR, Perfil.COORDENADOR)
        diario = Diario(
            codigo=diario_dados["codigo"],
            curso=curso,
            disciplina=disciplina,
            professor=por if da_aula else None,
            ano_letivo=periodo["ano"],
            periodo_letivo=periodo["periodo"],
            aulas_previstas=diario_dados["aulas_previstas"],
            carga_horaria_horas=diario_dados["carga_horaria_horas"],
        )
        diario.full_clean()
        diario.save()
        registrar(TipoEvento.CADASTRO_CRIADO, usuario=por, objeto=diario, origem="boletim")
        return diario
    if diario.professor_id is None and por.perfil in (Perfil.PROFESSOR, Perfil.COORDENADOR):
        diario.professor = por  # diário sem responsável fica com quem importou (PRC-12)
        diario.save(update_fields=["professor", "atualizado_em"])
    if not pode_cuidar_do_diario(por, diario):
        raise PermissionDenied(
            "Este diário está vinculado a outro professor. Fale com a coordenação do curso."
        )
    return diario


@transaction.atomic
def preencher_versao(
    *,
    importacao: Importacao,
    dados: dict,
    metodo=MetodoExtracao.TEXTO,
    versao_extrator: str = "",
    relatorio: dict | None = None,
    request=None,
) -> Importacao:
    """Grava as notas lidas numa importação já criada; ela passa a aguardar a confirmação do professor.

    Na importação de PDF (E3), a importação nasce no envio do arquivo e é preenchida pela tarefa da fila.
    Curso, disciplina, diário e estudantes são encontrados pelos códigos do SUAP ou criados.
    """
    por = importacao.enviada_por
    if not escopo.esta_ativo(por):
        raise PermissionDenied
    if dados.get("esquema") != ESQUEMA_SUPORTADO:
        raise ValidationError(
            f"Formato de dados não suportado (esquema {dados.get('esquema')!r}).", code="esquema"
        )
    diario = _diario_para(por, dados)
    repetida = (
        diario.importacoes.filter(sha256=importacao.sha256)
        .exclude(pk=importacao.pk)
        .exclude(status__in=[StatusImportacao.DESCARTADA, StatusImportacao.FALHOU])
        .first()
    )
    if repetida:
        raise ValidationError(
            f"Este boletim já foi enviado para este diário ({repetida}). Nada foi duplicado.",
            code="duplicado",
        )
    importacao.diario = diario
    importacao.status = StatusImportacao.AGUARDANDO_CONFIRMACAO
    importacao.metodo_extracao = metodo
    importacao.versao_extrator = versao_extrator
    importacao.aulas_ministradas = dados["aulas_ministradas"]["ministradas"]
    importacao.cabecalho = {
        "curso": dados["curso"]["texto"],
        "diario": dados["diario"]["texto"],
        "periodo_letivo": dados["periodo_letivo"]["texto"],
        "aulas_ministradas": dados["aulas_ministradas"]["texto"],
        "professor_principal": dados.get("professor_principal", ""),
        "emissao": dados.get("emissao", {}),
    }
    importacao.relatorio_validacao = relatorio or {}
    importacao.full_clean()
    importacao.save()
    for aluno in dados["alunos"]:
        _registrar_aluno(importacao, diario, aluno)
    registrar(
        TipoEvento.VERSAO_REGISTRADA,
        request=request,
        usuario=por,
        objeto=importacao,
        diario=diario.codigo,
        alunos=len(dados["alunos"]),
    )
    return importacao


@transaction.atomic
def registrar_versao(
    *,
    por,
    dados: dict,
    bimestre_corte: int,
    sha256: str,
    metodo=MetodoExtracao.TEXTO,
    versao_extrator: str = "",
    nome_arquivo: str = "",
    tamanho_bytes: int = 0,
    arquivo=None,
    relatorio: dict | None = None,
    request=None,
) -> Importacao:
    """Cria a importação e grava as notas de uma vez (dados já lidos; usado também na demonstração)."""
    if not escopo.esta_ativo(por):
        raise PermissionDenied
    importacao = Importacao(
        status=StatusImportacao.PROCESSANDO,
        bimestre_corte=bimestre_corte,
        sha256=sha256,
        nome_arquivo_original=nome_arquivo,
        tamanho_bytes=tamanho_bytes,
        enviada_por=por,
    )
    if arquivo is not None:
        importacao.arquivo = arquivo
    importacao.save()
    return preencher_versao(
        importacao=importacao,
        dados=dados,
        metodo=metodo,
        versao_extrator=versao_extrator,
        relatorio=relatorio,
        request=request,
    )


def _registrar_aluno(importacao, diario, aluno) -> None:
    estudante = Estudante.objects.filter(matricula=aluno["matricula"]).first()
    if estudante is None:
        estudante = Estudante(matricula=aluno["matricula"], nome=aluno["nome"])
        estudante.full_clean()
        estudante.save()
    matricula, _ = MatriculaDiario.objects.get_or_create(estudante=estudante, diario=diario)
    final = aluno["avaliacao_final"]
    media_final = aluno["media_final"]
    resultado = ResultadoAluno(
        importacao=importacao,
        matricula=matricula,
        ordem=aluno["ordem"],
        nome_no_boletim=aluno["nome"],
        situacao=aluno["situacao"],
        total_faltas=aluno["total_faltas"],
        frequencia_percentual=_decimal(aluno["frequencia_percentual"]),
        media_disciplina=_decimal(aluno["media_disciplina"]),
        nota_avaliacao_final=_decimal(final["nota"]),
        faltas_avaliacao_final=final["faltas"],
        media_final=_decimal(media_final) if not isinstance(media_final, str) else None,
        conceito=media_final if isinstance(media_final, str) else "",
    )
    resultado.full_clean()
    resultado.save()
    registros = [
        RegistroBimestral(
            resultado=resultado, bimestre=e["etapa"], nota=_decimal(e["nota"]), faltas=e["faltas"]
        )
        for e in aluno["etapas"]
    ]
    for registro in registros:
        registro.full_clean()
    RegistroBimestral.objects.bulk_create(registros)


def _exigir_cuidado(por, importacao) -> Diario:
    diario = Diario.objects.select_for_update().get(pk=importacao.diario_id)
    if not pode_cuidar_do_diario(por, diario):
        raise PermissionDenied
    return diario


def _trocar_vigente(diario, nova: Importacao) -> Importacao | None:
    anterior = diario.importacoes.filter(vigente=True).exclude(pk=nova.pk).first()
    if anterior:
        anterior.vigente = False
        anterior.save(update_fields=["vigente"])
    nova.vigente = True
    nova.save(update_fields=["vigente"])
    return anterior


@transaction.atomic
def confirmar_versao(*, por, importacao, request=None) -> Importacao:
    """O professor conferiu as notas: vira a próxima versão e passa a ser a vigente."""
    diario = _exigir_cuidado(por, importacao)
    importacao = Importacao.objects.select_for_update().get(pk=importacao.pk)
    if importacao.status != StatusImportacao.AGUARDANDO_CONFIRMACAO:
        raise ValidationError(
            "Só uma importação aguardando confirmação pode ser confirmada.", code="situacao"
        )
    ultima = diario.importacoes.aggregate(maior=Max("numero_versao"))["maior"] or 0
    importacao.numero_versao = ultima + 1
    importacao.status = StatusImportacao.CONFIRMADA
    importacao.confirmada_por = por
    importacao.confirmada_em = timezone.now()
    importacao.save()
    anterior = _trocar_vigente(diario, importacao)
    for resultado in importacao.resultados.select_related("matricula__estudante"):
        estudante = resultado.matricula.estudante
        if estudante.nome != resultado.nome_no_boletim:  # nome corrigido no SUAP: vale o mais recente
            estudante.nome = resultado.nome_no_boletim
            estudante.save(update_fields=["nome", "atualizado_em"])
    registrar(
        TipoEvento.VERSAO_CONFIRMADA,
        request=request,
        usuario=por,
        objeto=importacao,
        diario=diario.codigo,
        versao=importacao.numero_versao,
        vigente_anterior=anterior.numero_versao if anterior else None,
    )
    return importacao


@transaction.atomic
def definir_versao_vigente(*, por, importacao, request=None) -> Importacao:
    """Volta (ou avança) a versão vigente para outra versão já confirmada do mesmo diário."""
    diario = _exigir_cuidado(por, importacao)
    importacao = Importacao.objects.get(pk=importacao.pk)
    if importacao.status != StatusImportacao.CONFIRMADA:
        raise ValidationError("Só uma versão confirmada pode ser a vigente.", code="situacao")
    if importacao.vigente:
        return importacao
    anterior = _trocar_vigente(diario, importacao)
    registrar(
        TipoEvento.VERSAO_VIGENTE_ALTERADA,
        request=request,
        usuario=por,
        objeto=importacao,
        diario=diario.codigo,
        de=anterior.numero_versao if anterior else None,
        para=importacao.numero_versao,
    )
    return importacao


@transaction.atomic
def descartar_versao(*, por, importacao, request=None) -> Importacao:
    """Descarta uma importação ainda não confirmada (as notas dela nunca valeram)."""
    _exigir_cuidado(por, importacao)
    importacao = Importacao.objects.select_for_update().get(pk=importacao.pk)
    if importacao.status == StatusImportacao.CONFIRMADA:
        raise ValidationError("Uma versão confirmada não pode ser descartada.", code="situacao")
    if importacao.status != StatusImportacao.DESCARTADA:
        importacao.status = StatusImportacao.DESCARTADA
        importacao.save(update_fields=["status"])
        registrar(TipoEvento.VERSAO_DESCARTADA, request=request, usuario=por, objeto=importacao)
    return importacao
