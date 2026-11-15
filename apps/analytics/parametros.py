"""Monta o ``dominio.regras.parametros.Parametros`` a partir de ``notas.ParametroRegra``."""

import hashlib
import json
from dataclasses import asdict

from apps.notas.models import ParametroRegra
from dominio.regras.parametros import CHAVES, Parametros


def carregar(em=None) -> Parametros:
    """Os limiares vigentes na data ``em``. Uma chave sem linha no banco fica com o valor da norma."""
    valores, pendentes = {}, set()
    for campo, chave in CHAVES.items():
        try:
            parametro = ParametroRegra.vigente(chave, em=em)
        except ParametroRegra.DoesNotExist:
            continue
        valor = parametro.valor_convertido
        if campo == "faixas_desempenho":
            valor = tuple(int(limite) for limite in valor.split(";"))
        valores[campo] = valor
        if not parametro.confirmada:
            pendentes.add(chave)
    return Parametros(**valores, pendentes=frozenset(pendentes))


def assinatura(parametros: Parametros) -> str:
    """Identifica o conjunto de limiares: muda quando um valor ou uma confirmação muda."""
    dados = asdict(parametros) | {"pendentes": sorted(parametros.pendentes)}
    return hashlib.sha256(json.dumps(dados, sort_keys=True, default=str).encode()).hexdigest()[:16]
