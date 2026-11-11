"""Telas de importação: enviar boletins, acompanhar a leitura e ver o envio em lote."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.contas import escopo
from apps.importacao import envio
from apps.importacao.formularios import FormularioEnvio
from apps.importacao.models import LoteImportacao, StatusImportacao

EM_ANDAMENTO = {StatusImportacao.RECEBIDA, StatusImportacao.PROCESSANDO}
PRONTA = {StatusImportacao.AGUARDANDO_CONFIRMACAO, StatusImportacao.CONFIRMADA}


def _importacao(request, pk):
    return escopo.obter_visivel(
        escopo.importacoes_visiveis(request.user).select_related("diario", "lote"), pk
    )


def _lote(request, pk):
    lote = get_object_or_404(LoteImportacao, pk=pk)
    if lote.enviado_por_id != request.user.pk and not escopo.pode_gerenciar_usuarios(request.user):
        raise Http404  # fora do escopo: não revela que o envio existe
    return lote


def _destino(importacao) -> str:
    """Onde ver o resultado: a conferência no diário (pronta) ou a própria página da importação."""
    if importacao.status in PRONTA and importacao.diario_id:
        return f"{reverse('diarios:detalhe', args=[importacao.diario_id])}?importacao={importacao.pk}"
    return reverse("importacoes:detalhe", args=[importacao.pk])


def _situacao(importacao) -> dict:
    return {
        "id": importacao.pk,
        "status": importacao.status,
        "rotulo": importacao.get_status_display(),
        "terminal": importacao.status not in EM_ANDAMENTO,
        "destino": _destino(importacao),
    }


@login_required
def lista(request):
    importacoes = escopo.importacoes_visiveis(request.user).select_related(
        "diario__disciplina", "enviada_por"
    )
    pagina = Paginator(importacoes.order_by("-criada_em"), 25).get_page(request.GET.get("pagina"))
    return render(request, "importacao/lista.html", {"pagina": pagina, "parametros": ""})


@login_required
@require_http_methods(["GET", "POST"])
def enviar(request):
    form = FormularioEnvio(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            lote = envio.receber_envio(
                por=request.user,
                arquivos_enviados=form.cleaned_data["arquivos"],
                bimestre_corte=form.cleaned_data["bimestre_corte"],
                request=request,
            )
        except ValidationError as erro:
            form.add_error("arquivos", " ".join(erro.messages))
        else:
            recebidas = lote.importacoes.count()
            messages.success(
                request,
                f"{recebidas} boletim recebido. A leitura começou."
                if recebidas == 1
                else f"{recebidas} boletins recebidos. A leitura começou.",
            )
            if recebidas == 1 and not lote.ignorados:
                return redirect("importacoes:detalhe", pk=lote.importacoes.get().pk)
            return redirect("importacoes:lote", pk=lote.pk)
    return render(request, "importacao/enviar.html", {"form": form})


@login_required
def detalhe(request, pk):
    importacao = _importacao(request, pk)
    if importacao.status in PRONTA:
        return redirect(_destino(importacao))
    contexto = {
        "importacao": importacao,
        "relatorio": importacao.relatorio_validacao,
        "em_andamento": importacao.status in EM_ANDAMENTO,
    }
    return render(request, "importacao/detalhe.html", contexto)


@login_required
@require_GET
def situacao(request, pk):
    return JsonResponse(_situacao(_importacao(request, pk)))


@login_required
@require_POST
def ler_de_novo(request, pk):
    importacao = _importacao(request, pk)
    try:
        envio.reprocessar(por=request.user, importacao=importacao, request=request)
    except (ValidationError, PermissionDenied) as erro:
        messages.error(
            request, " ".join(getattr(erro, "messages", [])) or "Sem permissão para esta importação."
        )
    else:
        messages.success(request, "O boletim voltou para a fila de leitura.")
    return redirect("importacoes:detalhe", pk=pk)


@login_required
def lote(request, pk):
    lote_ = _lote(request, pk)
    importacoes = lote_.importacoes.select_related("diario__disciplina").order_by("pk")
    em_andamento = any(i.status in EM_ANDAMENTO for i in importacoes)
    contexto = {"lote": lote_, "importacoes": importacoes, "em_andamento": em_andamento}
    return render(request, "importacao/lote.html", contexto)


@login_required
@require_GET
def lote_situacao(request, pk):
    lote_ = _lote(request, pk)
    itens = [_situacao(i) for i in lote_.importacoes.order_by("pk")]
    return JsonResponse({"terminal": all(i["terminal"] for i in itens), "itens": itens})
