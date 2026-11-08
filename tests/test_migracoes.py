"""Migrações sobem e descem (E2): inclusive os gatilhos e os parâmetros iniciais do Regimento.

Não supõe nada do estado inicial do banco: os testes transacionais rodam por último e limpam o banco
(TRUNCATE) ao terminar, inclusive os dados criados por migração. A restauração automática do
pytest-django (serialized_rollback) não funciona depois dos testes com Playwright, porque a conexão do
Django passa a ser outro objeto. Por isso este teste desce e sobe as migrações e confere o resultado.
"""

import pytest
from django.core.management import call_command
from django.db import connection

from apps.notas.models import ParametroRegra

GATILHOS = {"importacao_versao_congelada", "notas_resultado_imutavel", "notas_registro_imutavel"}


def _gatilhos():
    with connection.cursor() as cursor:
        cursor.execute("SELECT tgname FROM pg_trigger WHERE NOT tgisinternal")
        return {linha[0] for linha in cursor.fetchall()}


@pytest.mark.django_db(transaction=True)
def test_migracoes_da_e2_descem_e_sobem():
    call_command("migrate", "notas", "0001", verbosity=0)
    assert not GATILHOS & _gatilhos()
    assert not ParametroRegra.objects.exists()
    call_command("migrate", "importacao", "zero", verbosity=0)
    call_command("migrate", "academico", "zero", verbosity=0)
    call_command("migrate", verbosity=0)
    assert _gatilhos() >= GATILHOS
    assert ParametroRegra.objects.count() == 19
    call_command("makemigrations", "--check", "--dry-run", verbosity=0)
