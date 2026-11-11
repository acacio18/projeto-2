"""Envio de e-mail de verdade: senha do SMTP lida de arquivo e endereço público nos links."""

import re

import pytest
from django.core import mail
from django.urls import reverse

from config.settings import base
from tests.apoio.fabricas import AdminFactory, ProfessorFactory

pytestmark = pytest.mark.django_db


def _link(mensagem) -> str:
    return re.search(r"https?://\S+", mensagem.body).group(0)


def test_senha_do_smtp_vem_de_arquivo_fora_do_repositorio(tmp_path, monkeypatch):
    arquivo = tmp_path / "smtp_senha_de_app.txt"
    arquivo.write_text("abcd efgh ijkl mnop\n", encoding="utf-8")  # como o Google mostra
    monkeypatch.setenv("DJANGO_EMAIL_SENHA_ARQUIVO", str(arquivo))
    assert base.ler_segredo("DJANGO_EMAIL_SENHA_ARQUIVO") == "abcdefghijklmnop"
    monkeypatch.setenv("DJANGO_EMAIL_SENHA_ARQUIVO", str(tmp_path / "ainda-nao-criado.txt"))
    assert base.ler_segredo("DJANGO_EMAIL_SENHA_ARQUIVO") == ""
    monkeypatch.delenv("DJANGO_EMAIL_SENHA_ARQUIVO")
    assert base.ler_segredo("DJANGO_EMAIL_SENHA_ARQUIVO") == ""


def test_convite_usa_o_endereco_publico(client, settings):
    settings.ENDERECO_PUBLICO = "http://192.168.0.10:8000"
    convidado = ProfessorFactory()
    convidado.set_unusable_password()
    convidado.save()
    client.force_login(AdminFactory())
    client.post(reverse("usuarios:reenviar_convite", args=[convidado.pk]))
    assert _link(mail.outbox[0]).startswith("http://192.168.0.10:8000/senha/definir/")


@pytest.mark.parametrize(
    ("endereco", "inicio"),
    [("http://192.168.0.10:8000", "http://192.168.0.10:8000/"), ("", "http://testserver/")],
)
def test_redefinicao_usa_o_endereco_publico_quando_configurado(client, settings, endereco, inicio):
    settings.ENDERECO_PUBLICO = endereco
    professor = ProfessorFactory()
    client.post(reverse("contas:esqueci_senha"), {"email": professor.email})
    assert _link(mail.outbox[0]).startswith(inicio + "senha/definir/")
