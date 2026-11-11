"""Telas de importação: enviar, acompanhar, ver o lote, ler de novo e permissões."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.importacao import tarefas
from apps.importacao.models import Importacao, StatusImportacao
from tests.apoio.fabricas import AdminFactory, ProfessorFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def midia(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path / "midia")


@pytest.fixture
def professor(client):
    usuario = ProfessorFactory()
    client.force_login(usuario)
    return usuario


def _enviar(client, capturar, *arquivos, corte=4):
    enviados = [
        SimpleUploadedFile(nome, conteudo, content_type="application/pdf") for nome, conteudo in arquivos
    ]
    with capturar(execute=True):
        return client.post(reverse("importacoes:enviar"), {"arquivos": enviados, "bimestre_corte": corte})


def test_tela_de_envio(client, professor):
    html = client.get(reverse("importacoes:enviar")).content.decode()
    assert 'enctype="multipart/form-data"' in html
    assert "multiple" in html
    assert 'accept=".pdf,.zip,application/pdf"' in html
    assert "Até qual bimestre" in html


def test_enviar_um_pdf_leva_a_conferencia_no_diario(
    client, professor, boletim_exemplo, django_capture_on_commit_callbacks
):
    resposta = _enviar(
        client, django_capture_on_commit_callbacks, ("boletim.pdf", boletim_exemplo.read_bytes())
    )
    importacao = Importacao.objects.get()
    assert resposta.url == reverse("importacoes:detalhe", args=[importacao.pk])
    destino = client.get(resposta.url)
    assert (
        destino.url == f"{reverse('diarios:detalhe', args=[importacao.diario_id])}?importacao={importacao.pk}"
    )
    html = client.get(destino.url).content.decode()
    assert "Boletim aguardando confirmação" in html
    assert "Lido pelo texto do PDF." in html
    assert "Confirmar notas" in html
    situacao = client.get(reverse("importacoes:situacao", args=[importacao.pk])).json()
    assert (situacao["status"], situacao["terminal"]) == (StatusImportacao.AGUARDANDO_CONFIRMACAO, True)


def test_varios_arquivos_viram_um_lote(
    client, professor, boletim_exemplo, django_capture_on_commit_callbacks
):
    resposta = _enviar(
        client,
        django_capture_on_commit_callbacks,
        ("bom.pdf", boletim_exemplo.read_bytes()),
        ("quebrado.pdf", b"%PDF-1.4 lixo"),
        ("foto.png", b"\x89PNG"),
    )
    lote_url = resposta.url
    assert "/importacoes/lotes/" in lote_url
    html = client.get(lote_url).content.decode()
    assert "bom.pdf" in html
    assert "quebrado.pdf" in html
    assert "Arquivos não recebidos" in html
    assert "foto.png" in html
    assert "Conferir e confirmar" in html
    assert "Falhou" in html
    pk = int(lote_url.rstrip("/").split("/")[-1])
    situacao = client.get(reverse("importacoes:lote_situacao", args=[pk])).json()
    assert situacao["terminal"] is True
    assert len(situacao["itens"]) == 2
    lista = client.get(reverse("importacoes:lista")).content.decode()
    assert "2 envios" in lista


def test_envio_sem_nada_aproveitavel_mostra_o_motivo(client, professor, django_capture_on_commit_callbacks):
    resposta = _enviar(client, django_capture_on_commit_callbacks, ("foto.png", b"\x89PNG"))
    assert resposta.status_code == 200
    assert "Nenhum boletim pôde ser recebido" in resposta.content.decode()
    assert not Importacao.objects.exists()


def test_falha_mostra_explicacao_e_permite_ler_de_novo(
    client, professor, boletim_exemplo, django_capture_on_commit_callbacks, monkeypatch
):
    monkeypatch.setattr(tarefas, "ler_boletim", lambda caminho: (_ for _ in ()).throw(RuntimeError("x")))
    resposta = _enviar(client, django_capture_on_commit_callbacks, ("a.pdf", boletim_exemplo.read_bytes()))
    html = client.get(resposta.url).content.decode()
    assert "Não foi possível importar este boletim." in html
    assert tarefas.ERRO_INESPERADO in html
    monkeypatch.undo()
    importacao = Importacao.objects.get()
    with django_capture_on_commit_callbacks(execute=True):
        resposta = client.post(reverse("importacoes:ler_de_novo", args=[importacao.pk]), follow=True)
    assert "voltou para a fila" in resposta.content.decode()
    importacao.refresh_from_db()
    assert importacao.status == StatusImportacao.AGUARDANDO_CONFIRMACAO
    resposta = client.post(reverse("importacoes:ler_de_novo", args=[importacao.pk]), follow=True)
    assert "Só uma importação que falhou" in resposta.content.decode()


def test_em_andamento_mostra_acompanhamento(
    client, professor, boletim_exemplo, django_capture_on_commit_callbacks, monkeypatch
):
    monkeypatch.setattr("apps.importacao.envio.enfileirar", lambda pk: None)  # fila parada
    resposta = _enviar(client, django_capture_on_commit_callbacks, ("a.pdf", boletim_exemplo.read_bytes()))
    html = client.get(resposta.url).content.decode()
    assert "data-acompanhar=" in html
    assert "js/acompanhar.js" in html
    assert "Recebida" in html
    importacao = Importacao.objects.get()
    assert client.get(reverse("importacoes:situacao", args=[importacao.pk])).json()["terminal"] is False


def test_descartada_mostra_aviso(client, professor, boletim_exemplo, django_capture_on_commit_callbacks):
    _enviar(client, django_capture_on_commit_callbacks, ("a.pdf", boletim_exemplo.read_bytes()))
    importacao = Importacao.objects.get()
    client.post(reverse("diarios:descartar", args=[importacao.diario_id, importacao.pk]))
    html = client.get(reverse("importacoes:detalhe", args=[importacao.pk])).content.decode()
    assert "Nada foi alterado nas notas" in html


def test_ninguem_ve_o_envio_alheio(client, boletim_exemplo, django_capture_on_commit_callbacks):
    dono = ProfessorFactory()
    client.force_login(dono)
    resposta = _enviar(
        client, django_capture_on_commit_callbacks, ("a.pdf", boletim_exemplo.read_bytes()), ("b.png", b"x")
    )
    lote_pk = int(resposta.url.rstrip("/").split("/")[-1])
    importacao = Importacao.objects.get()
    client.force_login(ProfessorFactory())
    for url in [
        reverse("importacoes:detalhe", args=[importacao.pk]),
        reverse("importacoes:situacao", args=[importacao.pk]),
        reverse("importacoes:lote", args=[lote_pk]),
        reverse("importacoes:lote_situacao", args=[lote_pk]),
    ]:
        assert client.get(url).status_code == 404, url
    assert client.post(reverse("importacoes:ler_de_novo", args=[importacao.pk])).status_code == 404
    client.force_login(AdminFactory())
    assert client.get(reverse("importacoes:lote", args=[lote_pk])).status_code == 200


def test_anonimo_vai_para_o_login(client):
    for url in [reverse("importacoes:lista"), reverse("importacoes:enviar")]:
        assert client.get(url).url.startswith(reverse("contas:entrar"))


def test_ler_de_novo_de_outra_pessoa_e_recusado(
    client, boletim_exemplo, django_capture_on_commit_callbacks, monkeypatch
):
    """O coordenador vê a importação do diário do curso, mas só quem enviou (ou o admin) pede nova leitura."""
    from apps.academico.models import CoordenacaoCurso
    from tests.apoio.fabricas import CoordenadorFactory

    dono = ProfessorFactory()
    client.force_login(dono)
    _enviar(client, django_capture_on_commit_callbacks, ("a.pdf", boletim_exemplo.read_bytes()))
    importacao = Importacao.objects.get()
    Importacao.objects.filter(pk=importacao.pk).update(status=StatusImportacao.FALHOU)
    coordenador = CoordenadorFactory()
    CoordenacaoCurso.objects.create(curso=importacao.diario.curso, usuario=coordenador)
    client.force_login(coordenador)
    resposta = client.post(reverse("importacoes:ler_de_novo", args=[importacao.pk]), follow=True)
    assert "Sem permissão" in resposta.content.decode()


def test_campo_de_varios_arquivos_aceita_um_so():
    from apps.importacao.formularios import CampoDeVariosArquivos

    arquivo = SimpleUploadedFile("a.pdf", b"%PDF-1")
    assert CampoDeVariosArquivos().clean(arquivo) == [arquivo]
