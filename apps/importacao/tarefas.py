"""Tarefas da fila (Django-Q2): leitura e validação de um boletim enviado.

RECEBIDA → PROCESSANDO → AGUARDANDO_CONFIRMACAO (o professor confere e confirma) ou FALHOU (com a
explicação). Nada vira versão vigente sem a confirmação do professor.
"""

import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError

from apps.auditoria.models import TipoEvento
from apps.auditoria.registro import registrar
from apps.importacao import servicos
from apps.importacao.leitura import ErroDeLeitura, ler_boletim
from apps.importacao.models import Importacao, StatusImportacao
from apps.importacao.validacao import tem_erro, validar

registro = logging.getLogger(__name__)

ERRO_INESPERADO = (
    "Erro inesperado ao ler o boletim. Tente de novo; se continuar, avise a administração do sistema."
)


def falhar(importacao: Importacao, mensagem: str, relatorio: dict | None = None) -> None:
    importacao.status = StatusImportacao.FALHOU
    importacao.relatorio_validacao = {**(relatorio or {}), "mensagem": mensagem}
    importacao.save(update_fields=["status", "relatorio_validacao"])
    registrar(
        TipoEvento.IMPORTACAO_FALHOU, usuario=importacao.enviada_por, objeto=importacao, motivo=mensagem
    )


def processar_importacao(importacao_id: int) -> str:
    atualizadas = Importacao.objects.filter(pk=importacao_id, status=StatusImportacao.RECEBIDA).update(
        status=StatusImportacao.PROCESSANDO
    )
    if not atualizadas:
        return "ignorada"  # já processada (ou descartada): a tarefa pode ser repetida sem efeito
    importacao = Importacao.objects.get(pk=importacao_id)
    relatorio: dict = {}
    try:
        leitura = ler_boletim(importacao.arquivo.path)
        problemas = validar(
            leitura.dados,
            bimestre_corte=importacao.bimestre_corte,
            padrao_matricula=settings.ACADEMICO_MATRICULA_REGEX,
            ilegiveis=leitura.ilegiveis,
        )
        relatorio = {
            "metodo": leitura.metodo,
            "confianca": leitura.confianca,
            "paginas": leitura.paginas,
            "perfil": leitura.perfil,
            "versao_leitor": leitura.versao,
            "alunos": len(leitura.dados["alunos"]),
            "avisos_leitura": leitura.avisos,
            "problemas": [p.como_dict() for p in problemas],
            "diario": leitura.dados["diario"]["texto"],
        }
        if tem_erro(problemas):
            falhar(importacao, "O boletim tem problemas que impedem a importação (veja a lista).", relatorio)
            return "falhou"
        servicos.preencher_versao(
            importacao=importacao,
            dados=leitura.dados,
            metodo=leitura.metodo,
            versao_extrator=leitura.versao,
            relatorio=relatorio,
        )
    except ErroDeLeitura as erro:
        falhar(importacao, str(erro), relatorio)
        return "falhou"
    except PermissionDenied as erro:
        falhar(importacao, str(erro) or "Você não tem permissão para importar este diário.", relatorio)
        return "falhou"
    except ValidationError as erro:
        falhar(importacao, " ".join(erro.messages), relatorio)
        return "falhou"
    except Exception:
        registro.exception("Falha inesperada ao processar a importação %s", importacao_id)
        falhar(importacao, ERRO_INESPERADO, relatorio)
        return "falhou"
    return "aguardando confirmação"


def ao_terminar(tarefa) -> None:
    """Gancho do Django-Q2: se a tarefa morreu (tempo esgotado, worker parado), marca a falha."""
    if tarefa.success:
        return
    importacao = Importacao.objects.filter(
        pk=tarefa.args[0], status__in=[StatusImportacao.RECEBIDA, StatusImportacao.PROCESSANDO]
    ).first()
    if importacao:
        falhar(
            importacao, "A leitura demorou demais ou foi interrompida. Use “Ler de novo” ou envie outra vez."
        )
