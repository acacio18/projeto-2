r"""Carrega o boletim de exemplo (nomes fictícios) como duas versões confirmadas, para demonstração.

Enquanto a importação de PDF (E3) não existe, permite ver diários, versões e notas nas telas:
- versão 1: o boletim "até o 2º bimestre" (notas do 3º e 4º e médias ainda vazias);
- versão 2: o boletim completo, que fica vigente.

Uso: .venv\Scripts\python manage.py carregar_exemplo --email professor@ifpb.edu.br
"""

import copy
import hashlib
import json
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.importacao import servicos
from apps.importacao.models import MetodoExtracao

GABARITO = Path(settings.BASE_DIR) / "tests" / "fixtures" / "boletins" / "exemplo_boletins.gabarito.json"


def ate_o_bimestre(dados: dict, corte: int) -> dict:
    """Como o boletim estaria no fim do bimestre `corte` (simulação para demonstração).

    Etapas seguintes e médias ficam vazias, os alunos ativos aparecem como "Cursando" e a frequência
    é recalculada sobre as aulas dadas até ali (proporcionais ao corte), com meio para o par (PRC-01).
    """
    parcial = copy.deepcopy(dados)
    previstas = dados["aulas_ministradas"]["previstas"]
    dadas = previstas * corte // 4
    parcial["aulas_ministradas"] = {
        "texto": f"{dadas} de {previstas} Aulas",
        "ministradas": dadas,
        "previstas": previstas,
    }
    for aluno in parcial["alunos"]:
        for etapa in aluno["etapas"]:
            if etapa["etapa"] > corte:
                etapa["nota"], etapa["faltas"] = None, 0
        aluno["total_faltas"] = sum(e["faltas"] for e in aluno["etapas"])
        aluno["media_disciplina"] = aluno["media_final"] = None
        aluno["avaliacao_final"] = {"nota": None, "faltas": 0}
        if aluno["situacao"] != "Cancelado":
            aluno["situacao"] = "Cursando"
            presenca = Decimal(dadas - aluno["total_faltas"]) * 100 / dadas
            aluno["frequencia_percentual"] = int(presenca.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
    return parcial


class Command(BaseCommand):
    help = "Carrega o boletim de exemplo em duas versões (demonstração das telas de diários)."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="E-mail do professor (ou coordenador) responsável")
        parser.add_argument("--arquivo", default=str(GABARITO), help="Arquivo JSON no formato do gabarito")

    def handle(self, *args, email, arquivo, **opcoes):
        professor = get_user_model().objects.filter(email=email.strip().lower()).first()
        if professor is None:
            raise CommandError(f"Usuário {email} não encontrado.")
        conteudo = Path(arquivo).read_bytes()
        dados = json.loads(conteudo)
        hash_base = hashlib.sha256(conteudo).hexdigest()
        try:
            for numero, (versao, corte) in enumerate([(ate_o_bimestre(dados, 2), 2), (dados, 4)], start=1):
                sha = hashlib.sha256(f"{hash_base}:{numero}".encode()).hexdigest()
                importacao = servicos.registrar_versao(
                    por=professor,
                    dados=versao,
                    bimestre_corte=corte,
                    sha256=sha,
                    metodo=MetodoExtracao.DEMONSTRACAO,
                    versao_extrator="exemplo",
                )
                servicos.confirmar_versao(por=professor, importacao=importacao)
        except (ValidationError, PermissionDenied) as erro:
            mensagem = " ".join(getattr(erro, "messages", [])) or str(erro) or "sem permissão neste diário"
            raise CommandError(f"Não foi possível carregar o exemplo: {mensagem}") from erro
        diario = importacao.diario
        self.stdout.write(
            self.style.SUCCESS(f"Diário {diario.codigo} ({diario.disciplina.nome}) carregado com 2 versões.")
        )
