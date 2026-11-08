"""Gatilhos no PostgreSQL: uma versão confirmada e as notas dela não mudam nem somem.

Segunda camada de proteção (a primeira está nos modelos). Vale também para acesso direto ao banco.
- importacao_importacao: depois de CONFIRMADA, só o campo "vigente" pode mudar; não pode ser apagada.
- notas_resultadoaluno e notas_registrobimestral: nunca são alteradas (correção = nova versão) e só
  podem ser apagadas enquanto a versão não foi confirmada (descarte de rascunho).
TRUNCATE continua permitido (o Django o usa para limpar o banco entre testes).
"""

from django.db import migrations

CRIAR = """
CREATE FUNCTION importacao_versao_congelada() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        IF OLD.status = 'CONFIRMADA' THEN
            RAISE EXCEPTION 'importacao_importacao: versao confirmada nao pode ser apagada'
                USING ERRCODE = 'insufficient_privilege';
        END IF;
        RETURN OLD;
    END IF;
    IF OLD.status = 'CONFIRMADA' AND (
        NEW.diario_id IS DISTINCT FROM OLD.diario_id
        OR NEW.numero_versao IS DISTINCT FROM OLD.numero_versao
        OR NEW.status IS DISTINCT FROM OLD.status
        OR NEW.bimestre_corte IS DISTINCT FROM OLD.bimestre_corte
        OR NEW.sha256 IS DISTINCT FROM OLD.sha256
        OR NEW.arquivo IS DISTINCT FROM OLD.arquivo
        OR NEW.aulas_ministradas IS DISTINCT FROM OLD.aulas_ministradas
        OR NEW.cabecalho IS DISTINCT FROM OLD.cabecalho
        OR NEW.relatorio_validacao IS DISTINCT FROM OLD.relatorio_validacao
        OR NEW.confirmada_por_id IS DISTINCT FROM OLD.confirmada_por_id
        OR NEW.confirmada_em IS DISTINCT FROM OLD.confirmada_em
    ) THEN
        RAISE EXCEPTION 'importacao_importacao: versao confirmada nao pode ser alterada (so o campo vigente)'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER importacao_versao_congelada
    BEFORE UPDATE OR DELETE ON importacao_importacao
    FOR EACH ROW EXECUTE FUNCTION importacao_versao_congelada();

CREATE FUNCTION notas_linha_imutavel() RETURNS trigger AS $$
DECLARE
    situacao text;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        RAISE EXCEPTION '%: notas de uma versao nao sao alteradas (importe uma nova versao)', TG_TABLE_NAME
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    IF TG_TABLE_NAME = 'notas_resultadoaluno' THEN
        SELECT i.status INTO situacao FROM importacao_importacao i WHERE i.id = OLD.importacao_id;
    ELSE
        SELECT i.status INTO situacao
          FROM notas_resultadoaluno r JOIN importacao_importacao i ON i.id = r.importacao_id
         WHERE r.id = OLD.resultado_id;
    END IF;
    IF situacao = 'CONFIRMADA' THEN
        RAISE EXCEPTION '%: notas de versao confirmada nao podem ser apagadas', TG_TABLE_NAME
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER notas_resultado_imutavel
    BEFORE UPDATE OR DELETE ON notas_resultadoaluno
    FOR EACH ROW EXECUTE FUNCTION notas_linha_imutavel();

CREATE TRIGGER notas_registro_imutavel
    BEFORE UPDATE OR DELETE ON notas_registrobimestral
    FOR EACH ROW EXECUTE FUNCTION notas_linha_imutavel();
"""

DESFAZER = """
DROP TRIGGER IF EXISTS notas_registro_imutavel ON notas_registrobimestral;
DROP TRIGGER IF EXISTS notas_resultado_imutavel ON notas_resultadoaluno;
DROP FUNCTION IF EXISTS notas_linha_imutavel();
DROP TRIGGER IF EXISTS importacao_versao_congelada ON importacao_importacao;
DROP FUNCTION IF EXISTS importacao_versao_congelada();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("notas", "0001_initial"),
        ("importacao", "0001_initial"),
    ]

    operations = [migrations.RunSQL(CRIAR, reverse_sql=DESFAZER)]
