"""Gatilho no PostgreSQL que barra UPDATE e DELETE na tabela de auditoria.

É a segunda camada de proteção (a primeira está no modelo): vale também para quem acessa o banco
direto, sem passar pelo Django. TRUNCATE continua permitido porque o Django o usa para limpar o banco
entre testes; a proteção contra adulteração de quem tem acesso total ao banco vem na E9 (eventos
encadeados por hash).
"""

from django.db import migrations

CRIAR = """
CREATE FUNCTION auditoria_barra_alteracao() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'auditoria_eventoauditoria: eventos de auditoria nao podem ser alterados nem apagados'
        USING ERRCODE = 'insufficient_privilege';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auditoria_somente_insercao
    BEFORE UPDATE OR DELETE ON auditoria_eventoauditoria
    FOR EACH ROW EXECUTE FUNCTION auditoria_barra_alteracao();
"""

DESFAZER = """
DROP TRIGGER IF EXISTS auditoria_somente_insercao ON auditoria_eventoauditoria;
DROP FUNCTION IF EXISTS auditoria_barra_alteracao();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("auditoria", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(CRIAR, reverse_sql=DESFAZER),
    ]
