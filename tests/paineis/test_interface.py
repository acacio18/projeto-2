"""Peças da interface: ícones, acessibilidade dos formulários e páginas de erro."""

import pytest
from django import forms
from django.template import Context, Template
from django.template.loader import render_to_string

from apps.paineis.formularios import FormularioAcessivel
from apps.paineis.templatetags.interface import icone
from tests.apoio.fabricas import ProfessorFactory


def test_icone_e_decorativo_e_sem_comentario_de_licenca():
    svg = icone("log-in", "extra")
    assert svg.startswith('<svg class="icone extra" aria-hidden="true" focusable="false" ')
    assert "<!--" not in svg
    assert "lucide" not in svg
    assert 'stroke="currentColor"' in svg


def test_icone_pela_template_tag_escapa_a_classe():
    html = Template('{% load interface %}{% icone "x" classe %}').render(Context({"classe": '"><script>'}))
    assert "<script>" not in html
    assert "&quot;&gt;&lt;script&gt;" in html


@pytest.mark.parametrize(("nome", "erro"), [("../segredo", ValueError), ("nao-existe", FileNotFoundError)])
def test_icone_recusa_nome_invalido_ou_inexistente(nome, erro):
    with pytest.raises(erro):
        icone(nome)


class _Formulario(FormularioAcessivel, forms.Form):
    nome = forms.CharField(help_text="Como aparece nos relatórios.")
    email = forms.EmailField()


def test_formulario_liga_ajuda_e_erro_aos_campos():
    form = _Formulario(data={"nome": "", "email": "invalido"})
    assert form.fields["nome"].widget.attrs["aria-describedby"] == "id_nome_ajuda"
    assert not form.is_valid()
    assert form.fields["nome"].widget.attrs["aria-describedby"] == "id_nome_ajuda id_nome_erro"
    assert form.fields["email"].widget.attrs["aria-describedby"] == "id_email_erro"
    assert form.fields["email"].widget.attrs["aria-invalid"] == "true"


def test_erro_geral_do_formulario_nao_quebra_a_ligacao():
    form = _Formulario(data={"nome": "x", "email": "a@ifpb.edu.br"})
    form.is_valid()
    form.add_error(None, "Erro geral")
    form.full_clean()
    assert "aria-invalid" not in form.fields["nome"].widget.attrs


@pytest.mark.django_db
def test_pagina_404_propria(client):
    resposta = client.get("/endereco-que-nao-existe/")
    assert resposta.status_code == 404
    assert "Página não encontrada" in resposta.content.decode()


@pytest.mark.django_db
def test_pagina_403_propria(client):
    client.force_login(ProfessorFactory())
    resposta = client.get("/usuarios/")
    assert resposta.status_code == 403
    assert "Acesso não permitido" in resposta.content.decode()


def test_pagina_500_renderiza_sem_contexto():
    html = render_to_string("500.html")
    assert "Erro inesperado" in html
    assert "Traceback" not in html
