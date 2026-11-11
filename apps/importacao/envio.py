"""Envio de boletins em PDF (IDs 3 e 18): cria o lote e uma importação por arquivo e põe na fila."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django_q.tasks import async_task

from apps.auditoria.models import TipoEvento
from apps.auditoria.registro import registrar
from apps.contas import escopo
from apps.importacao import arquivos
from apps.importacao.models import Importacao, LoteImportacao, StatusImportacao

EM_ANDAMENTO_OU_VALIDA = [
    StatusImportacao.RECEBIDA,
    StatusImportacao.PROCESSANDO,
    StatusImportacao.AGUARDANDO_CONFIRMACAO,
    StatusImportacao.CONFIRMADA,
]


def enfileirar(importacao_id: int) -> None:
    async_task(
        "apps.importacao.tarefas.processar_importacao",
        importacao_id,
        hook="apps.importacao.tarefas.ao_terminar",
        task_name=f"importacao-{importacao_id}",
    )


def _ja_enviada(por, sha256: str) -> Importacao | None:
    return (
        Importacao.objects.filter(sha256=sha256, status__in=EM_ANDAMENTO_OU_VALIDA)
        .filter(Q(enviada_por=por) | Q(diario__in=escopo.diarios_visiveis(por)))
        .first()
    )


@transaction.atomic
def receber_envio(*, por, arquivos_enviados, bimestre_corte: int, request=None) -> LoteImportacao:
    """Grava os PDFs aceitos, registra o envio e agenda a leitura de cada um (após o commit)."""
    if not escopo.esta_ativo(por):
        raise PermissionDenied
    aceitos, ignorados = arquivos.coletar(arquivos_enviados)
    novos = []
    for arquivo in aceitos:
        if anterior := _ja_enviada(por, arquivo.sha256):
            ignorados.append(
                {
                    "nome": arquivo.nome,
                    "motivo": "este mesmo arquivo já foi enviado",
                    "link": reverse("importacoes:detalhe", args=[anterior.pk]),
                }
            )
        else:
            novos.append(arquivo)
    if not novos:
        motivos = "; ".join(f"{i['nome']}: {i['motivo']}" for i in ignorados) or "nenhum arquivo enviado"
        raise ValidationError(f"Nenhum boletim pôde ser recebido ({motivos}).", code="nada_recebido")
    lote = LoteImportacao.objects.create(enviado_por=por, bimestre_corte=bimestre_corte, ignorados=ignorados)
    for arquivo in novos:
        importacao = Importacao(
            lote=lote,
            status=StatusImportacao.RECEBIDA,
            bimestre_corte=bimestre_corte,
            sha256=arquivo.sha256,
            nome_arquivo_original=arquivo.nome[:255],
            tamanho_bytes=arquivo.tamanho,
            enviada_por=por,
        )
        importacao.arquivo.save("boletim.pdf", ContentFile(arquivo.conteudo), save=False)
        importacao.save()
        registrar(
            TipoEvento.IMPORTACAO_RECEBIDA,
            request=request,
            usuario=por,
            objeto=importacao,
            arquivo=arquivo.nome,
            tamanho=arquivo.tamanho,
            sha256=arquivo.sha256,
        )
        transaction.on_commit(lambda pk=importacao.pk: enfileirar(pk))
    return lote


def reprocessar(*, por, importacao, request=None) -> Importacao:
    """Põe de novo na fila uma importação que falhou (ex.: a fila estava parada)."""
    if importacao.enviada_por_id != por.pk and not escopo.pode_gerenciar_usuarios(por):
        raise PermissionDenied
    if importacao.status != StatusImportacao.FALHOU:
        raise ValidationError("Só uma importação que falhou pode ser lida de novo.", code="situacao")
    Importacao.objects.filter(pk=importacao.pk).update(
        status=StatusImportacao.RECEBIDA, relatorio_validacao={}
    )
    transaction.on_commit(lambda: enfileirar(importacao.pk))
    importacao.refresh_from_db()
    return importacao
