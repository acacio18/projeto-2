"""Versões das notas de um diário (IDs 6 e 19) com os dados reais do boletim de exemplo.

Aceitação da E2: é possível consultar as notas de qualquer versão histórica, e nenhuma operação apaga
ou altera uma versão já confirmada.
"""

import copy
from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import DatabaseError, connection, transaction

from apps.academico.models import Curso, Diario, Disciplina, Estudante, MatriculaDiario
from apps.auditoria.models import EventoAuditoria, TipoEvento
from apps.importacao import servicos
from apps.importacao.models import Importacao, StatusImportacao, VersaoImutavelError
from apps.notas import consultas
from apps.notas.models import NotaImutavelError, RegistroBimestral, ResultadoAluno
from tests.apoio.fabricas import AdminFactory, CoordenadorFactory, ProfessorFactory

pytestmark = pytest.mark.django_db

SHA_V1 = "a" * 64
SHA_V2 = "b" * 64


def _registrar(por, dados, sha=SHA_V1, corte=4):
    return servicos.registrar_versao(por=por, dados=dados, bimestre_corte=corte, sha256=sha)


def _nota(importacao, matricula, bimestre):
    return RegistroBimestral.objects.get(
        resultado__importacao=importacao,
        resultado__matricula__estudante__matricula=matricula,
        bimestre=bimestre,
    ).nota


@pytest.fixture
def professor():
    return ProfessorFactory(nome="Paulo Henrique")


def test_registrar_cria_cadastros_pelos_codigos_do_suap_e_aguarda_confirmacao(professor, gabarito_exemplo):
    importacao = _registrar(professor, gabarito_exemplo)
    assert importacao.status == StatusImportacao.AGUARDANDO_CONFIRMACAO
    assert importacao.numero_versao is None
    assert not importacao.vigente
    diario = importacao.diario
    assert (diario.codigo, diario.ano_letivo, diario.periodo_letivo) == ("70764", 2023, 1)
    assert (diario.curso.codigo, diario.disciplina.codigo) == ("661", "TIN.0054")
    assert diario.professor == professor  # diário novo fica com quem importou (PRC-12)
    assert diario.turma is None  # o boletim não traz a turma
    assert (diario.aulas_previstas, diario.carga_horaria_horas, importacao.aulas_ministradas) == (80, 67, 80)
    assert Estudante.objects.count() == 32
    assert MatriculaDiario.objects.filter(diario=diario).count() == 32
    assert ResultadoAluno.objects.filter(importacao=importacao).count() == 32
    assert RegistroBimestral.objects.filter(resultado__importacao=importacao).count() == 128
    assert consultas.versao_vigente(diario) is None
    assert list(consultas.pendentes(diario)) == [importacao]
    assert EventoAuditoria.objects.filter(tipo=TipoEvento.VERSAO_REGISTRADA, usuario=professor).exists()


def test_valores_gravados_sao_os_do_boletim(professor, gabarito_exemplo):
    importacao = _registrar(professor, gabarito_exemplo)
    linhas = {r.matricula.estudante.matricula: r for r in consultas.linhas_da_versao(importacao)}
    for aluno in gabarito_exemplo["alunos"]:
        linha = linhas[aluno["matricula"]]
        assert linha.ordem == aluno["ordem"]
        assert linha.situacao == aluno["situacao"]
        assert linha.total_faltas == aluno["total_faltas"]
        esperados = [aluno["frequencia_percentual"], aluno["media_disciplina"], aluno["media_final"]]
        gravados = [linha.frequencia_percentual, linha.media_disciplina, linha.media_final]
        assert gravados == [None if v is None else Decimal(v) for v in esperados]
        assert [(b.bimestre, b.nota, b.faltas) for b in linha.bimestres.all()] == [
            (e["etapa"], None if e["nota"] is None else Decimal(e["nota"]), e["faltas"])
            for e in aluno["etapas"]
        ]
    assert [linha.ordem for linha in consultas.linhas_da_versao(importacao)] == list(range(1, 33))
    assert linhas["202027621030"].cancelado  # "-" vira ausente, não zero
    assert linhas["202027621030"].media_disciplina is None


def test_versoes_historicas_continuam_consultaveis(professor, gabarito_exemplo):
    v1 = servicos.confirmar_versao(por=professor, importacao=_registrar(professor, gabarito_exemplo))
    assert (v1.numero_versao, v1.vigente) == (1, True)

    corrigido = copy.deepcopy(gabarito_exemplo)
    corrigido["alunos"][0]["etapas"][0]["nota"] = 60  # o SUAP corrigiu uma nota
    corrigido["alunos"][0]["nome"] = "Aline Santana Ramos de Jesus Corrigida"
    v2 = servicos.confirmar_versao(por=professor, importacao=_registrar(professor, corrigido, sha=SHA_V2))
    v1.refresh_from_db()
    assert (v2.numero_versao, v2.vigente, v1.vigente) == (2, True, False)

    diario = v2.diario
    assert consultas.versao_vigente(diario) == v2
    assert list(consultas.versoes(diario)) == [v2, v1]
    assert _nota(v1, "201927621032", 1) == Decimal(50)  # a versão antiga continua igual
    assert _nota(v2, "201927621032", 1) == Decimal(60)
    assert Estudante.objects.get(matricula="201927621032").nome.endswith("Corrigida")  # vale o mais recente
    assert Diario.objects.count() == Curso.objects.count() == Disciplina.objects.count() == 1  # sem duplicar
    assert Estudante.objects.count() == 32

    servicos.definir_versao_vigente(por=professor, importacao=v1)  # voltar para a versão 1
    assert consultas.versao_vigente(diario) == v1
    evento = EventoAuditoria.objects.get(tipo=TipoEvento.VERSAO_VIGENTE_ALTERADA)
    assert (evento.detalhes["de"], evento.detalhes["para"]) == (2, 1)
    assert servicos.definir_versao_vigente(por=professor, importacao=v1) == v1  # já vigente: nada muda


def test_mesmo_boletim_nao_e_importado_duas_vezes(professor, gabarito_exemplo):
    _registrar(professor, gabarito_exemplo)
    with pytest.raises(ValidationError) as erro:
        _registrar(professor, gabarito_exemplo)
    assert erro.value.code == "duplicado"
    assert Importacao.objects.count() == 1


def test_descartar_rascunho_e_reenviar(professor, gabarito_exemplo):
    rascunho = _registrar(professor, gabarito_exemplo)
    servicos.descartar_versao(por=professor, importacao=rascunho)
    rascunho.refresh_from_db()
    assert rascunho.status == StatusImportacao.DESCARTADA
    servicos.descartar_versao(por=professor, importacao=rascunho)  # repetir não gera outro evento
    assert EventoAuditoria.objects.filter(tipo=TipoEvento.VERSAO_DESCARTADA).count() == 1
    novo = _registrar(professor, gabarito_exemplo)  # o mesmo arquivo pode ser enviado de novo
    assert servicos.confirmar_versao(por=professor, importacao=novo).numero_versao == 1
    with pytest.raises(ValidationError):
        servicos.confirmar_versao(por=professor, importacao=rascunho)
    with pytest.raises(ValidationError):
        servicos.definir_versao_vigente(por=professor, importacao=rascunho)


def test_versao_confirmada_nao_pode_ser_descartada_nem_confirmada_de_novo(professor, gabarito_exemplo):
    v1 = servicos.confirmar_versao(por=professor, importacao=_registrar(professor, gabarito_exemplo))
    with pytest.raises(ValidationError):
        servicos.descartar_versao(por=professor, importacao=v1)
    with pytest.raises(ValidationError):
        servicos.confirmar_versao(por=professor, importacao=v1)


def test_versao_confirmada_e_imutavel_no_django(professor, gabarito_exemplo):
    v1 = servicos.confirmar_versao(por=professor, importacao=_registrar(professor, gabarito_exemplo))
    v1.bimestre_corte = 2
    with pytest.raises(VersaoImutavelError):
        v1.save()
    with pytest.raises(VersaoImutavelError):
        v1.delete()
    linha = ResultadoAluno.objects.filter(importacao=v1).first()
    linha.total_faltas = 99
    with pytest.raises(NotaImutavelError):
        linha.save()


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE importacao_importacao SET bimestre_corte = 2 WHERE id = %(importacao)s",
        "DELETE FROM importacao_importacao WHERE id = %(importacao)s",
        "UPDATE notas_resultadoaluno SET total_faltas = 99 WHERE id = %(resultado)s",
        "DELETE FROM notas_resultadoaluno WHERE id = %(resultado)s",
        "UPDATE notas_registrobimestral SET nota = 100 WHERE id = %(registro)s",
        "DELETE FROM notas_registrobimestral WHERE id = %(registro)s",
    ],
    ids=[
        "importacao-update",
        "importacao-delete",
        "resultado-update",
        "resultado-delete",
        "registro-update",
        "registro-delete",
    ],
)
def test_gatilhos_do_banco_protegem_a_versao_confirmada(professor, gabarito_exemplo, sql):
    v1 = servicos.confirmar_versao(por=professor, importacao=_registrar(professor, gabarito_exemplo))
    resultado = ResultadoAluno.objects.filter(importacao=v1).first()
    ids = {"importacao": v1.pk, "resultado": resultado.pk, "registro": resultado.bimestres.first().pk}
    with pytest.raises(DatabaseError, match="versao"), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(sql, ids)


def test_gatilho_deixa_trocar_so_a_vigente_e_apagar_rascunho(professor, gabarito_exemplo):
    v1 = servicos.confirmar_versao(por=professor, importacao=_registrar(professor, gabarito_exemplo))
    with connection.cursor() as cursor:
        cursor.execute("UPDATE importacao_importacao SET vigente = FALSE WHERE id = %s", [v1.pk])
    rascunho = _registrar(professor, gabarito_exemplo, sha=SHA_V2)
    resultado = ResultadoAluno.objects.filter(importacao=rascunho).first()
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM notas_registrobimestral WHERE resultado_id = %s", [resultado.pk])
        cursor.execute("DELETE FROM notas_resultadoaluno WHERE id = %s", [resultado.pk])
    assert not ResultadoAluno.objects.filter(pk=resultado.pk).exists()


def test_outro_professor_nao_importa_nem_confirma_no_diario_alheio(professor, gabarito_exemplo):
    importacao = _registrar(professor, gabarito_exemplo)
    intruso = ProfessorFactory()
    with pytest.raises(PermissionDenied):
        _registrar(intruso, gabarito_exemplo, sha=SHA_V2)
    for operacao in (servicos.confirmar_versao, servicos.descartar_versao):
        with pytest.raises(PermissionDenied):
            operacao(por=intruso, importacao=importacao)


def test_coordenador_do_curso_pode_cuidar_e_o_de_outro_curso_nao(professor, gabarito_exemplo):
    importacao = _registrar(professor, gabarito_exemplo)
    coordenador = CoordenadorFactory()
    importacao.diario.curso.coordenacoes.create(usuario=coordenador)
    servicos.confirmar_versao(por=coordenador, importacao=importacao)
    outro = CoordenadorFactory()
    with pytest.raises(PermissionDenied):
        servicos.definir_versao_vigente(por=outro, importacao=importacao)


def test_admin_importa_sem_virar_professor_do_diario(gabarito_exemplo):
    importacao = _registrar(AdminFactory(), gabarito_exemplo)
    assert importacao.diario.professor is None
    professor = ProfessorFactory()
    _registrar(professor, gabarito_exemplo, sha=SHA_V2)  # diário sem responsável fica com quem importou
    importacao.diario.refresh_from_db()
    assert importacao.diario.professor == professor


def test_usuario_inativo_nao_registra(gabarito_exemplo):
    with pytest.raises(PermissionDenied):
        _registrar(ProfessorFactory(is_active=False), gabarito_exemplo)


def test_esquema_desconhecido_e_recusado(professor, gabarito_exemplo):
    gabarito_exemplo["esquema"] = 99
    with pytest.raises(ValidationError) as erro:
        _registrar(professor, gabarito_exemplo)
    assert erro.value.code == "esquema"


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("nota", 101), ("nota", -1), ("matricula", "123"), ("frequencia_percentual", 150)],
)
def test_valores_fora_da_regra_sao_recusados_e_nada_fica_gravado(professor, gabarito_exemplo, campo, valor):
    aluno = gabarito_exemplo["alunos"][5]
    if campo == "nota":
        aluno["etapas"][1]["nota"] = valor
    else:
        aluno[campo] = valor
    with pytest.raises(ValidationError):
        _registrar(professor, gabarito_exemplo)
    assert not Importacao.objects.exists()
    assert not Diario.objects.exists()


def test_conceito_no_lugar_da_media_final(professor, gabarito_exemplo):
    gabarito_exemplo["alunos"][0]["media_final"] = "Apto"
    importacao = _registrar(professor, gabarito_exemplo)
    linha = consultas.linhas_da_versao(importacao).first()
    assert (linha.media_final, linha.conceito) == (None, "Apto")


def test_arquivo_ganha_nome_aleatorio_e_textos(professor, gabarito_exemplo, settings, tmp_path):
    from django.core.files.uploadedfile import SimpleUploadedFile

    from apps.importacao.models import caminho_do_arquivo

    settings.MEDIA_ROOT = str(tmp_path)
    pdf = SimpleUploadedFile(
        "Boletim da Turma A - Fulano.pdf", b"%PDF-1.4 teste", content_type="application/pdf"
    )
    importacao = servicos.registrar_versao(
        por=professor,
        dados=gabarito_exemplo,
        bimestre_corte=4,
        sha256=SHA_V1,
        arquivo=pdf,
        nome_arquivo="Boletim da Turma A - Fulano.pdf",
        tamanho_bytes=14,
    )
    assert importacao.arquivo.name.startswith("boletins/")
    assert "Fulano" not in importacao.arquivo.name  # o nome original fica só no banco
    assert importacao.nome_arquivo_original == "Boletim da Turma A - Fulano.pdf"
    assert caminho_do_arquivo(None, "x.pdf") != caminho_do_arquivo(None, "x.pdf")
    assert str(importacao) == f"Importação {importacao.pk} (Aguardando confirmação)"
    servicos.confirmar_versao(por=professor, importacao=importacao)
    importacao.refresh_from_db()
    assert str(importacao) == "Versão 1 do diário 70764"
    linha = consultas.linhas_da_versao(importacao).first()
    assert str(linha) == "Aline Santana Ramos de Jesus na Versão 1 do diário 70764"
    assert str(linha.bimestres.first()) == "1º bimestre: 50.00"
    ausente = RegistroBimestral(nota=None, bimestre=2)
    assert str(ausente) == "2º bimestre: -"


def test_salvar_versao_confirmada_sem_mudar_nada_e_permitido(professor, gabarito_exemplo):
    v1 = servicos.confirmar_versao(por=professor, importacao=_registrar(professor, gabarito_exemplo))
    v1.save()  # nenhum campo congelado mudou
    assert not servicos.pode_cuidar_do_diario(ProfessorFactory(is_active=False), v1.diario)


def test_importacao_nao_confirmada_sem_notas_pode_ser_apagada(professor):
    importacao = Importacao.objects.create(bimestre_corte=1, sha256=SHA_V1, enviada_por=professor)
    importacao.delete()
    assert not Importacao.objects.exists()
