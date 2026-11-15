"""Parâmetros das regras (ParametroRegra): valores iniciais do Regimento e das PRC, e vigência por data."""

import datetime
from decimal import Decimal

import pytest

from apps.notas.models import ParametroRegra, TipoParametro

pytestmark = pytest.mark.django_db

INTERPRETACOES = {
    "MEDIA_MINIMA_AVALIACAO_FINAL",
    "RENDIMENTO_SATISFATORIO_MINIMO",
    "ARREDONDAMENTO_MEDIA",
    "MATRICULA_PADRAO",
    "FAIXAS_DESEMPENHO",
}


def test_valores_iniciais_do_regimento():
    valores = {
        chave: ParametroRegra.vigente(chave).valor_convertido
        for chave in [
            "MEDIA_APROVACAO",
            "MEDIA_FINAL_APROVACAO",
            "FREQUENCIA_MINIMA_PERCENTUAL",
            "ALERTA_CONSELHO_PERCENTUAL",
        ]
    }
    assert valores == {
        "MEDIA_APROVACAO": 70,
        "MEDIA_FINAL_APROVACAO": 50,
        "FREQUENCIA_MINIMA_PERCENTUAL": 75,
        "ALERTA_CONSELHO_PERCENTUAL": 30,
    }
    assert ParametroRegra.objects.count() == 19
    assert all(p.fundamento for p in ParametroRegra.objects.all())


def test_interpretacoes_foram_confirmadas_pelo_usuario():
    """notas/0004: decisões de 14/11/2026 (leitura mais favorável do Regimento, sem esperar validação)."""
    assert not ParametroRegra.objects.filter(confirmada=False).exists()
    for chave in INTERPRETACOES:
        assert "confirmada pelo usuário" in ParametroRegra.vigente(chave).fundamento


def test_valem_tambem_para_anos_anteriores():
    assert ParametroRegra.vigente("MEDIA_APROVACAO", em=datetime.date(2023, 3, 1)).valor == "70"


def test_mudar_um_valor_e_uma_nova_linha_com_vigencia():
    ParametroRegra.objects.create(
        chave="MEDIA_APROVACAO",
        valor="60",
        tipo=TipoParametro.INTEIRO,
        descricao="Valor hipotético de teste.",
        fundamento="Teste",
        confirmada=True,
        vigente_desde=datetime.date(2030, 1, 1),
    )
    assert ParametroRegra.vigente("MEDIA_APROVACAO", em=datetime.date(2029, 12, 31)).valor == "70"
    assert ParametroRegra.vigente("MEDIA_APROVACAO", em=datetime.date(2030, 1, 1)).valor == "60"
    assert ParametroRegra.objects.filter(chave="MEDIA_APROVACAO").count() == 2


@pytest.mark.parametrize(
    ("tipo", "valor", "esperado"),
    [
        (TipoParametro.INTEIRO, "7", 7),
        (TipoParametro.DECIMAL, "7.5", Decimal("7.5")),
        (TipoParametro.TEXTO, "x", "x"),
    ],
)
def test_valor_convertido(tipo, valor, esperado):
    parametro = ParametroRegra(chave="X", valor=valor, tipo=tipo)
    assert parametro.valor_convertido == esperado
    assert str(parametro) == f"X = {valor}"
