"""Fluxo de importação (IDs 3, 4 e 18): envio → fila → leitura → validação → conferência ou falha."""

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.auditoria.models import EventoAuditoria, TipoEvento
from apps.importacao import envio, tarefas
from apps.importacao.models import Importacao, StatusImportacao
from apps.notas.models import ResultadoAluno
from tests.apoio.boletim_sintetico import gerar
from tests.apoio.boletins import carregar_gabarito
from tests.apoio.fabricas import AdminFactory, ProfessorFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def midia(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path / "midia")


@pytest.fixture
def pdf_exemplo(boletim_exemplo):
    return boletim_exemplo.read_bytes()


def _enviar(por, *arquivos, corte=4, capturar=None):
    enviados = [SimpleUploadedFile(nome, conteudo) for nome, conteudo in arquivos]
    with capturar(execute=True):
        return envio.receber_envio(por=por, arquivos_enviados=enviados, bimestre_corte=corte)


def test_envio_le_valida_e_deixa_aguardando_confirmacao(pdf_exemplo, django_capture_on_commit_callbacks):
    professor = ProfessorFactory()
    lote = _enviar(professor, ("Boletim APS.pdf", pdf_exemplo), capturar=django_capture_on_commit_callbacks)
    importacao = lote.importacoes.get()
    assert importacao.status == StatusImportacao.AGUARDANDO_CONFIRMACAO
    assert importacao.diario.codigo == "70764"
    assert importacao.diario.professor == professor
    assert importacao.nome_arquivo_original == "Boletim APS.pdf"
    assert "Fulano" not in importacao.arquivo.name
    assert importacao.arquivo.name.startswith("boletins/")
    assert importacao.metodo_extracao == "TEXTO"
    relatorio = importacao.relatorio_validacao
    assert (relatorio["metodo"], relatorio["alunos"], relatorio["problemas"]) == ("TEXTO", 32, [])
    assert ResultadoAluno.objects.filter(importacao=importacao).count() == 32
    tipos = set(EventoAuditoria.objects.values_list("tipo", flat=True))
    assert {TipoEvento.IMPORTACAO_RECEBIDA, TipoEvento.VERSAO_REGISTRADA} <= tipos
    assert not importacao.vigente  # nada vale antes da confirmação


def test_boletim_com_problema_falha_com_explicacao(django_capture_on_commit_callbacks, tmp_path):
    dados = carregar_gabarito()
    dados["alunos"][0]["matricula"] = "123"
    lote = _enviar(
        ProfessorFactory(), ("ruim.pdf", gerar(dados)), capturar=django_capture_on_commit_callbacks
    )
    importacao = lote.importacoes.get()
    assert importacao.status == StatusImportacao.FALHOU
    assert "problemas que impedem" in importacao.relatorio_validacao["mensagem"]
    assert any("Matrícula “123”" in p["mensagem"] for p in importacao.relatorio_validacao["problemas"])
    assert importacao.diario is None
    assert not ResultadoAluno.objects.exists()
    assert EventoAuditoria.objects.filter(tipo=TipoEvento.IMPORTACAO_FALHOU).exists()


@pytest.mark.parametrize(
    ("conteudo", "trecho"),
    [
        (b"%PDF-1.4 corrompido", "corrompido"),
        ("protegido", "protegido por senha"),
        ("sem_alunos", "Não encontrei a tabela de alunos"),
    ],
)
def test_pdfs_problematicos_falham_com_mensagem_clara(
    django_capture_on_commit_callbacks, monkeypatch, conteudo, trecho
):
    if conteudo == "protegido":
        conteudo = gerar(carregar_gabarito(), senha="x")
    elif conteudo == "sem_alunos":
        dados = carregar_gabarito()
        dados["alunos"] = []
        conteudo = gerar(dados)
        monkeypatch.setattr(
            "apps.importacao.leitura.leitor.ocr.extrair",
            lambda *a, **k: __import__("apps.importacao.leitura.modelo", fromlist=["Documento"]).Documento(
                metodo="OCR"
            ),
        )
    lote = _enviar(ProfessorFactory(), ("x.pdf", conteudo), capturar=django_capture_on_commit_callbacks)
    importacao = lote.importacoes.get()
    assert importacao.status == StatusImportacao.FALHOU
    assert trecho in importacao.relatorio_validacao["mensagem"]


def test_diario_de_outro_professor_falha(pdf_exemplo, django_capture_on_commit_callbacks):
    _enviar(ProfessorFactory(), ("a.pdf", pdf_exemplo), capturar=django_capture_on_commit_callbacks)
    dados = carregar_gabarito()
    dados["alunos"][0]["nome"] = "Outra versão"
    lote = _enviar(ProfessorFactory(), ("b.pdf", gerar(dados)), capturar=django_capture_on_commit_callbacks)
    importacao = lote.importacoes.get()
    assert importacao.status == StatusImportacao.FALHOU
    assert "outro professor" in importacao.relatorio_validacao["mensagem"]


def test_mesmo_arquivo_nao_e_enviado_duas_vezes(pdf_exemplo, django_capture_on_commit_callbacks):
    professor = ProfessorFactory()
    _enviar(professor, ("a.pdf", pdf_exemplo), capturar=django_capture_on_commit_callbacks)
    with pytest.raises(ValidationError, match="já foi enviado"):
        _enviar(professor, ("de novo.pdf", pdf_exemplo), capturar=django_capture_on_commit_callbacks)
    assert Importacao.objects.count() == 1


def test_lote_com_um_arquivo_ruim_nao_afeta_os_outros(pdf_exemplo, django_capture_on_commit_callbacks):
    outro = carregar_gabarito()
    outro["diario"]["codigo"] = "70765"
    outro["diario"]["texto"] = outro["diario"]["texto"].replace("70764", "70765")
    lote = _enviar(
        ProfessorFactory(),
        ("bom.pdf", pdf_exemplo),
        ("outro.pdf", gerar(outro)),
        ("quebrado.pdf", b"%PDF-1.4 lixo"),
        ("foto.jpg", b"\xff\xd8\xff"),
        capturar=django_capture_on_commit_callbacks,
    )
    situacoes = dict(lote.importacoes.values_list("nome_arquivo_original", "status"))
    assert situacoes == {
        "bom.pdf": StatusImportacao.AGUARDANDO_CONFIRMACAO,
        "outro.pdf": StatusImportacao.AGUARDANDO_CONFIRMACAO,
        "quebrado.pdf": StatusImportacao.FALHOU,
    }
    assert [i["nome"] for i in lote.ignorados] == ["foto.jpg"]


def test_envio_vazio_ou_de_usuario_inativo(django_capture_on_commit_callbacks):
    with pytest.raises(ValidationError, match="Nenhum boletim"):
        _enviar(ProfessorFactory(), ("foto.jpg", b"\xff"), capturar=django_capture_on_commit_callbacks)
    with pytest.raises(PermissionDenied):
        _enviar(
            ProfessorFactory(is_active=False),
            ("a.pdf", b"%PDF-1"),
            capturar=django_capture_on_commit_callbacks,
        )


def test_tarefa_repetida_nao_faz_nada(pdf_exemplo, django_capture_on_commit_callbacks):
    lote = _enviar(ProfessorFactory(), ("a.pdf", pdf_exemplo), capturar=django_capture_on_commit_callbacks)
    assert tarefas.processar_importacao(lote.importacoes.get().pk) == "ignorada"


def test_erro_inesperado_vira_falha_generica(pdf_exemplo, django_capture_on_commit_callbacks, monkeypatch):
    def quebrar(caminho):
        raise RuntimeError("bug")

    monkeypatch.setattr(tarefas, "ler_boletim", quebrar)
    lote = _enviar(ProfessorFactory(), ("a.pdf", pdf_exemplo), capturar=django_capture_on_commit_callbacks)
    assert lote.importacoes.get().relatorio_validacao["mensagem"] == tarefas.ERRO_INESPERADO


def test_validation_error_do_servico_vira_falha(pdf_exemplo, django_capture_on_commit_callbacks, monkeypatch):
    def recusar(**kwargs):
        raise ValidationError("Recusado pelo serviço.")

    monkeypatch.setattr(tarefas.servicos, "preencher_versao", recusar)
    lote = _enviar(ProfessorFactory(), ("a.pdf", pdf_exemplo), capturar=django_capture_on_commit_callbacks)
    assert lote.importacoes.get().relatorio_validacao["mensagem"] == "Recusado pelo serviço."


def test_gancho_marca_falha_quando_a_tarefa_morre(
    pdf_exemplo, django_capture_on_commit_callbacks, monkeypatch
):
    monkeypatch.setattr(envio, "enfileirar", lambda pk: None)  # simula a fila parada
    lote = _enviar(ProfessorFactory(), ("a.pdf", pdf_exemplo), capturar=django_capture_on_commit_callbacks)
    importacao = lote.importacoes.get()
    assert importacao.status == StatusImportacao.RECEBIDA

    class Tarefa:
        success = True
        args = (importacao.pk,)

    tarefas.ao_terminar(Tarefa())
    importacao.refresh_from_db()
    assert importacao.status == StatusImportacao.RECEBIDA
    Tarefa.success = False
    tarefas.ao_terminar(Tarefa())
    importacao.refresh_from_db()
    assert importacao.status == StatusImportacao.FALHOU
    assert "demorou demais" in importacao.relatorio_validacao["mensagem"]


def test_ler_de_novo_uma_importacao_que_falhou(pdf_exemplo, django_capture_on_commit_callbacks, monkeypatch):
    professor = ProfessorFactory()
    monkeypatch.setattr(tarefas, "ler_boletim", lambda caminho: (_ for _ in ()).throw(RuntimeError("fora")))
    lote = _enviar(professor, ("a.pdf", pdf_exemplo), capturar=django_capture_on_commit_callbacks)
    importacao = lote.importacoes.get()
    assert importacao.status == StatusImportacao.FALHOU
    monkeypatch.undo()
    with django_capture_on_commit_callbacks(execute=True):
        envio.reprocessar(por=professor, importacao=importacao)
    importacao.refresh_from_db()
    assert importacao.status == StatusImportacao.AGUARDANDO_CONFIRMACAO
    with pytest.raises(ValidationError):
        envio.reprocessar(por=professor, importacao=importacao)
    with pytest.raises(PermissionDenied):
        envio.reprocessar(por=ProfessorFactory(), importacao=importacao)
    envio.reprocessar(
        por=AdminFactory(), importacao=Importacao(pk=importacao.pk, status=StatusImportacao.FALHOU)
    )


def test_usuario_desativado_depois_do_envio(pdf_exemplo, django_capture_on_commit_callbacks, monkeypatch):
    from apps.importacao import servicos

    professor = ProfessorFactory()
    monkeypatch.setattr(envio, "enfileirar", lambda pk: None)
    lote = _enviar(professor, ("a.pdf", pdf_exemplo), capturar=django_capture_on_commit_callbacks)
    professor.is_active = False
    professor.save()
    importacao = lote.importacoes.get()
    with pytest.raises(PermissionDenied):
        servicos.preencher_versao(importacao=importacao, dados=carregar_gabarito())
    tarefas.processar_importacao(importacao.pk)
    importacao.refresh_from_db()
    assert importacao.status == StatusImportacao.FALHOU
    assert "permissão" in importacao.relatorio_validacao["mensagem"]


def test_gancho_nao_mexe_em_importacao_ja_terminada(pdf_exemplo, django_capture_on_commit_callbacks):
    lote = _enviar(ProfessorFactory(), ("a.pdf", pdf_exemplo), capturar=django_capture_on_commit_callbacks)
    importacao = lote.importacoes.get()

    class Tarefa:
        success = False
        args = (importacao.pk,)

    tarefas.ao_terminar(Tarefa())
    importacao.refresh_from_db()
    assert importacao.status == StatusImportacao.AGUARDANDO_CONFIRMACAO
