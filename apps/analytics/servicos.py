"""Indicadores de uma versão: calcula uma vez por assinatura e guarda (SnapshotIndicadores)."""

import datetime
import hashlib

from apps.analytics import indicadores, parametros
from apps.analytics.models import SnapshotIndicadores


def _assinatura(importacao, regras) -> str:
    fora = importacao.resultados.filter(matricula__excluir_das_comparacoes=True).values_list(
        "ordem", flat=True
    )
    exclusoes = hashlib.sha256(",".join(map(str, sorted(fora))).encode()).hexdigest()[:8]
    return f"{indicadores.VERSAO_DO_CALCULO}-{parametros.assinatura(regras)}-{exclusoes}"


def indicadores_da_versao(importacao) -> dict:
    """Os indicadores da versão com as regras vigentes no fim do ano letivo do diário."""
    regras = parametros.carregar(em=datetime.date(importacao.diario.ano_letivo, 12, 31))
    assinatura = _assinatura(importacao, regras)
    guardado = SnapshotIndicadores.objects.filter(importacao=importacao, assinatura=assinatura).first()
    if guardado is not None:
        return guardado.dados
    dados = indicadores.calcular(importacao, regras)
    SnapshotIndicadores.objects.get_or_create(
        importacao=importacao, assinatura=assinatura, defaults={"dados": dados}
    )
    return dados
