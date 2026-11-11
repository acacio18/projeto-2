"""Capturas das telas para a revisão visual (Pre-Delivery Checklist da skill UI/UX Pro Max).

Só roda com a variável SUAP_CAPTURAS apontando para a pasta de saída:
    $env:SUAP_CAPTURAS = "docs\\evidencias\\E1-telas"
    .venv\\Scripts\\python -m pytest tests/e2e/test_capturas_telas.py
"""

import os
from pathlib import Path

import pytest

from apps.contas.models import Perfil
from tests.apoio.fabricas import SENHA_PADRAO, AdminFactory, CoordenadorFactory, ProfessorFactory

PASTA = os.environ.get("SUAP_CAPTURAS")
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(not PASTA, reason="defina SUAP_CAPTURAS para gerar as capturas"),
]


def _foto(page, nome, largura, tema="claro", altura=900):
    page.set_viewport_size({"width": largura, "height": altura})
    # Sem animação: senão a foto pega a transição de 200 ms entre os temas pela metade.
    page.emulate_media(color_scheme="dark" if tema == "escuro" else "light", reduced_motion="reduce")
    page.evaluate("document.documentElement.removeAttribute('data-tema')")
    page.wait_for_timeout(50)
    page.screenshot(path=str(Path(PASTA) / f"{nome}-{largura}-{tema}.png"), full_page=True)


def test_capturas(page, live_server):
    base = live_server.url
    AdminFactory(email="ada.admin@ifpb.edu.br", nome="Ada Lovelace")
    CoordenadorFactory(nome="Carlos Drummond de Andrade", email="carlos.drummond@ifpb.edu.br")
    for numero, nome in enumerate(
        ["Cecília Meireles", "Graciliano Ramos", "Rachel de Queiroz", "José Lins do Rego"]
    ):
        ProfessorFactory(nome=nome, email=f"professor{numero}@ifpb.edu.br")
    convidado = ProfessorFactory(nome="Ariano Suassuna", email="ariano.suassuna@ifpb.edu.br")
    convidado.set_unusable_password()
    convidado.save()
    ProfessorFactory(nome="Augusto dos Anjos", email="augusto.anjos@ifpb.edu.br", is_active=False)

    page.goto(f"{base}/entrar/")
    for largura, tema in [(375, "claro"), (1440, "claro"), (1440, "escuro")]:
        _foto(page, "01-entrar", largura, tema)
    page.get_by_label("E-mail institucional").fill("ada.admin@ifpb.edu.br")
    page.get_by_label("Senha", exact=True).fill("senha-errada")
    page.get_by_role("button", name="Entrar").click()
    _foto(page, "02-entrar-erro", 768)

    page.get_by_label("E-mail institucional").fill("ada.admin@ifpb.edu.br")
    page.get_by_label("Senha", exact=True).fill(SENHA_PADRAO)
    page.get_by_role("button", name="Entrar").click()
    for largura, tema in [(1440, "claro"), (1440, "escuro"), (375, "claro")]:
        _foto(page, "03-painel-admin", largura, tema)
    page.set_viewport_size({"width": 375, "height": 900})
    page.get_by_role("button", name="Abrir menu de navegação").click()
    _foto(page, "04-menu-aberto", 375)

    page.goto(f"{base}/usuarios/")
    for largura, tema in [(1440, "claro"), (1440, "escuro"), (1024, "claro"), (375, "claro")]:
        _foto(page, "05-usuarios", largura, tema)

    page.goto(f"{base}/usuarios/novo/")
    page.get_by_label("E-mail institucional").fill("alguem@gmail.com")
    page.get_by_label("Perfil").select_option(Perfil.PROFESSOR)
    page.get_by_role("button", name="Cadastrar e enviar convite").click()
    for largura, tema in [(768, "claro"), (768, "escuro")]:
        _foto(page, "06-novo-usuario-erros", largura, tema)

    page.goto(f"{base}/usuarios/{convidado.pk}/")
    for largura, tema in [(1440, "claro"), (375, "escuro")]:
        _foto(page, "07-editar-usuario", largura, tema)
    page.goto(f"{base}/usuarios/{convidado.pk}/desativar/")
    _foto(page, "08-confirmar-desativacao", 1024)

    page.goto(f"{base}/senha/alterar/")
    _foto(page, "09-alterar-senha", 1024, "escuro")
    page.goto(f"{base}/usuarios/999999/")
    _foto(page, "10-nao-encontrado", 768)

    # --- E2: diários, versões e cadastros ---
    from apps.academico.models import CoordenacaoCurso
    from apps.importacao import servicos as versoes
    from apps.importacao.management.commands.carregar_exemplo import ate_o_bimestre
    from tests.apoio.boletins import carregar_gabarito
    from tests.apoio.fabricas import DiarioFactory, DisciplinaFactory, TurmaFactory

    professora = ProfessorFactory(nome="Cecília Benevides", email="cecilia.benevides@ifpb.edu.br")
    dados = carregar_gabarito()
    v1 = versoes.registrar_versao(
        por=professora, dados=ate_o_bimestre(dados, 2), bimestre_corte=2, sha256="1" * 64
    )
    versoes.confirmar_versao(por=professora, importacao=v1)
    v2 = versoes.registrar_versao(por=professora, dados=dados, bimestre_corte=4, sha256="2" * 64)
    diario = v2.diario
    coordenadora = CoordenadorFactory(nome="Nísia Floresta", email="nisia.floresta@ifpb.edu.br")
    CoordenacaoCurso.objects.create(curso=diario.curso, usuario=coordenadora)
    turma = TurmaFactory(curso=diario.curso, ano_letivo=2023, serie=3, identificador="3º A")
    DiarioFactory(
        disciplina=DisciplinaFactory(curso=diario.curso, nome="Banco de Dados"), turma=turma, ano_letivo=2023
    )

    page.goto(f"{base}/diarios/")
    for largura, tema in [(1440, "claro"), (375, "claro")]:
        _foto(page, "11-diarios", largura, tema)
    page.goto(f"{base}/diarios/{diario.pk}/")
    for largura, tema in [(1440, "claro"), (1440, "escuro"), (375, "claro")]:
        _foto(page, "12-diario-aguardando-confirmacao", largura, tema)
    versoes.confirmar_versao(por=professora, importacao=v2)
    page.goto(f"{base}/diarios/{diario.pk}/?importacao={v1.pk}")
    _foto(page, "13-diario-versao-antiga", 1440)
    page.goto(f"{base}/cadastros/")
    _foto(page, "14-cadastros", 1024)
    page.goto(f"{base}/cadastros/cursos/{diario.curso_id}/")
    for largura, tema in [(1440, "escuro"), (375, "claro")]:
        _foto(page, "15-curso", largura, tema)
    page.goto(f"{base}/cadastros/turmas/")
    _foto(page, "16-turmas", 768)
    page.goto(f"{base}/diarios/{diario.pk}/editar/")
    _foto(page, "17-editar-diario", 1024)

    # --- E3: envio, lote, falha, conferência com o relatório da leitura ---
    import tempfile

    from apps.importacao.models import Importacao, StatusImportacao
    from tests.apoio import digitalizacao
    from tests.apoio.boletins import BOLETIM_EXEMPLO

    escaneado = digitalizacao.gerar(
        BOLETIM_EXEMPLO,
        Path(tempfile.mkdtemp()) / "boletim-escaneado.pdf",
        digitalizacao.VARIANTES["300dpi_inclinado"],
    )
    page.context.clear_cookies()
    page.goto(f"{base}/entrar/")
    page.get_by_label("E-mail institucional").fill("cecilia.benevides@ifpb.edu.br")
    page.get_by_label("Senha", exact=True).fill(SENHA_PADRAO)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{base}/importacoes/enviar/")
    for largura, tema in [(1440, "claro"), (1440, "escuro"), (375, "claro")]:
        _foto(page, "18-enviar", largura, tema)

    page.set_viewport_size({"width": 1440, "height": 900})
    page.get_by_label("Boletins do SUAP (PDF)").set_input_files(
        [
            {"name": c.name, "mimeType": "application/pdf", "buffer": c.read_bytes()}
            for c in (BOLETIM_EXEMPLO, escaneado)
        ]
        + [
            {"name": "boletim-corrompido.pdf", "mimeType": "application/pdf", "buffer": b"%PDF-1.4 lixo"},
            {"name": "foto-do-boletim.jpg", "mimeType": "image/jpeg", "buffer": b"\xff\xd8\xff"},
        ]
    )
    page.get_by_label("Até qual bimestre as notas estão fechadas?").select_option("4")
    page.set_default_timeout(180_000)  # a fila roda na hora: o OCR do escaneado leva uns 20 s
    page.get_by_role("button", name="Enviar e ler").click()
    page.get_by_text("Arquivos não recebidos").wait_for()
    page.set_default_timeout(30_000)
    for largura, tema in [(1440, "claro"), (1440, "escuro"), (375, "claro")]:
        _foto(page, "19-lote", largura, tema)

    falhou = Importacao.objects.get(status=StatusImportacao.FALHOU)
    page.goto(f"{base}/importacoes/{falhou.pk}/")
    for largura, tema in [(1024, "claro"), (375, "escuro")]:
        _foto(page, "20-importacao-falhou", largura, tema)

    por_ocr = Importacao.objects.get(nome_arquivo_original="boletim-escaneado.pdf")
    page.goto(f"{base}/importacoes/{por_ocr.pk}/")  # leva à conferência no diário
    for largura, tema in [(1440, "claro"), (1440, "escuro"), (375, "claro")]:
        _foto(page, "21-conferencia-ocr", largura, tema)
    por_texto = Importacao.objects.get(nome_arquivo_original=BOLETIM_EXEMPLO.name)
    page.goto(f"{base}/importacoes/{por_texto.pk}/")
    _foto(page, "22-conferencia-texto", 1024)

    page.goto(f"{base}/importacoes/")
    for largura, tema in [(1440, "claro"), (375, "claro")]:
        _foto(page, "23-importacoes", largura, tema)

    lendo = Importacao.objects.create(
        enviada_por=Importacao.objects.first().enviada_por,
        nome_arquivo_original="boletim-3A-matematica.pdf",
        bimestre_corte=2,
        sha256="3" * 64,
    )
    page.goto(f"{base}/importacoes/{lendo.pk}/")
    _foto(page, "24-lendo", 768)
