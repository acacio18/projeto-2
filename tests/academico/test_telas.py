"""Telas da E2: diários (com versões das notas), cadastros de cursos, turmas e disciplinas, permissões."""

import pytest
from django.core.management import CommandError, call_command
from django.urls import reverse

from apps.academico.models import CoordenacaoCurso, Curso, Diario, Disciplina, Turma
from apps.auditoria.models import EventoAuditoria, TipoEvento
from apps.importacao import servicos as versoes
from apps.importacao.models import Importacao, StatusImportacao
from tests.apoio.fabricas import (
    AdminFactory,
    CoordenadorFactory,
    CursoFactory,
    DiarioFactory,
    DisciplinaFactory,
    ProfessorFactory,
    TurmaFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def cenario():
    curso = CursoFactory(nome="Informática")
    coordenador = CoordenadorFactory()
    CoordenacaoCurso.objects.create(curso=curso, usuario=coordenador)
    professor = ProfessorFactory()
    diario = DiarioFactory(disciplina=DisciplinaFactory(curso=curso), professor=professor)
    turma = TurmaFactory(curso=curso, ano_letivo=diario.ano_letivo)
    return {
        "curso": curso,
        "coordenador": coordenador,
        "professor": professor,
        "diario": diario,
        "turma": turma,
    }


def _entrar(client, usuario):
    client.force_login(usuario)
    return client


def _rotas_de_consulta(c):
    return [
        reverse("diarios:lista"),
        reverse("diarios:detalhe", args=[c["diario"].pk]),
        reverse("cadastros:inicio"),
        reverse("cadastros:cursos"),
        reverse("cadastros:curso", args=[c["curso"].pk]),
        reverse("cadastros:turmas"),
        reverse("cadastros:disciplinas"),
    ]


def _rotas_de_alteracao(c):
    return [
        reverse("diarios:novo"),
        reverse("diarios:editar", args=[c["diario"].pk]),
        reverse("diarios:excluir", args=[c["diario"].pk]),
        reverse("cadastros:turma_nova"),
        reverse("cadastros:turma_editar", args=[c["turma"].pk]),
        reverse("cadastros:turma_excluir", args=[c["turma"].pk]),
        reverse("cadastros:disciplina_nova"),
        reverse("cadastros:disciplina_editar", args=[c["diario"].disciplina_id]),
    ]


def _rotas_de_admin(c):
    return [
        reverse("cadastros:curso_novo"),
        reverse("cadastros:curso_editar", args=[c["curso"].pk]),
        reverse("cadastros:curso_excluir", args=[c["curso"].pk]),
    ]


def test_anonimo_vai_para_o_login(client, cenario):
    for url in _rotas_de_consulta(cenario) + _rotas_de_alteracao(cenario) + _rotas_de_admin(cenario):
        resposta = client.get(url)
        assert resposta.status_code == 302, url
        assert resposta.url.startswith(reverse("contas:entrar")), url


def test_matriz_de_permissoes(client, cenario):
    outro_coordenador = CoordenadorFactory()
    CoordenacaoCurso.objects.create(curso=CursoFactory(), usuario=outro_coordenador)
    casos = {
        "admin": (AdminFactory(), 200, 200, 200),
        "coordenador": (cenario["coordenador"], 200, 200, 403),
        "professor": (cenario["professor"], 200, 403, 403),  # alteração: 403 ou 404
    }
    for nome, (usuario, consulta, alteracao, admin) in casos.items():
        _entrar(client, usuario)
        for url in _rotas_de_consulta(cenario):
            assert client.get(url).status_code == consulta, (nome, url)
        for url in _rotas_de_alteracao(cenario):
            # 403 se o registro está no escopo (só não pode alterar); 404 se nem é visível
            esperado = {200} if alteracao == 200 else {403, 404}
            assert client.get(url).status_code in esperado, (nome, url)
        for url in _rotas_de_admin(cenario):
            assert client.get(url).status_code == admin, (nome, url)
    # O professor vê a disciplina do próprio diário, mas não pode alterá-la: 403.
    _entrar(client, cenario["professor"])
    assert (
        client.get(reverse("cadastros:disciplina_editar", args=[cenario["diario"].disciplina_id])).status_code
        == 403
    )
    assert client.get(reverse("diarios:editar", args=[cenario["diario"].pk])).status_code == 403
    # Coordenador de outro curso: nem vê os registros (404) e não altera nada lá.
    _entrar(client, outro_coordenador)
    assert client.get(reverse("diarios:detalhe", args=[cenario["diario"].pk])).status_code == 404
    assert client.get(reverse("cadastros:curso", args=[cenario["curso"].pk])).status_code == 404
    assert client.get(reverse("cadastros:turma_editar", args=[cenario["turma"].pk])).status_code == 404
    assert client.get(reverse("diarios:novo")).status_code == 200  # pode criar no próprio curso


def test_professor_nao_ve_diario_alheio(client, cenario):
    alheio = DiarioFactory()
    _entrar(client, cenario["professor"])
    html = client.get(reverse("diarios:lista")).content.decode()
    assert cenario["diario"].disciplina.nome in html
    assert alheio.disciplina.nome not in html
    assert client.get(reverse("diarios:detalhe", args=[alheio.pk])).status_code == 404


def test_filtros_da_lista_de_diarios(client, cenario):
    _entrar(client, AdminFactory())
    DiarioFactory(ano_letivo=2025, codigo="99999")
    url = reverse("diarios:lista")

    def codigos(**filtros):
        return sorted(d.codigo for d in client.get(url, filtros).context["pagina"])

    assert codigos(q="99999") == ["99999"]
    assert codigos(ano=2025) == ["99999"]
    assert codigos(situacao="sem_turma") == sorted([cenario["diario"].codigo, "99999"])
    assert codigos(situacao="com_notas") == []
    assert codigos(situacao="sem_notas") == sorted([cenario["diario"].codigo, "99999"])
    assert codigos(situacao="aguardando") == []


def test_versoes_na_tela_do_diario(client, gabarito_exemplo):
    professor = ProfessorFactory()
    importacao = versoes.registrar_versao(
        por=professor, dados=gabarito_exemplo, bimestre_corte=4, sha256="a" * 64
    )
    diario = importacao.diario
    _entrar(client, professor)
    url = reverse("diarios:detalhe", args=[diario.pk])

    html = client.get(url).content.decode()
    assert "Boletim aguardando confirmação" in html
    assert "Aline Santana Ramos de Jesus" in html
    assert "201927621032" in html
    assert (
        client.get(reverse("diarios:lista"), {"situacao": "aguardando"}).context["pagina"].paginator.count
        == 1
    )

    resposta = client.post(reverse("diarios:confirmar", args=[diario.pk, importacao.pk]), follow=True)
    assert "Notas confirmadas como versão 1, agora vigente." in resposta.content.decode()

    corrigido = dict(gabarito_exemplo, alunos=gabarito_exemplo["alunos"][:5])
    v2 = versoes.registrar_versao(por=professor, dados=corrigido, bimestre_corte=4, sha256="b" * 64)
    client.post(reverse("diarios:confirmar", args=[diario.pk, v2.pk]))
    assert Importacao.objects.get(pk=v2.pk).vigente

    v1_html = client.get(url, {"importacao": importacao.pk}).content.decode()
    assert "Notas da versão 1" in v1_html
    assert "Tornar esta versão a vigente" in v1_html
    assert "Zuleika Bandeira Rocha" in v1_html  # a v1 tem os 32 alunos
    assert "Zuleika Bandeira Rocha" not in client.get(url).content.decode()  # a vigente (v2) tem 5

    resposta = client.post(reverse("diarios:tornar_vigente", args=[diario.pk, importacao.pk]), follow=True)
    assert "A versão 1 passou a ser a vigente." in resposta.content.decode()
    assert Importacao.objects.get(pk=importacao.pk).vigente
    assert client.get(url, {"importacao": 999_999}).status_code == 404


def test_descartar_e_erros_de_versao_na_tela(client, gabarito_exemplo):
    professor = ProfessorFactory()
    importacao = versoes.registrar_versao(
        por=professor, dados=gabarito_exemplo, bimestre_corte=4, sha256="a" * 64
    )
    diario = importacao.diario
    _entrar(client, professor)
    resposta = client.post(reverse("diarios:descartar", args=[diario.pk, importacao.pk]), follow=True)
    assert "Importação descartada." in resposta.content.decode()
    assert Importacao.objects.get(pk=importacao.pk).status == StatusImportacao.DESCARTADA
    resposta = client.post(reverse("diarios:confirmar", args=[diario.pk, importacao.pk]), follow=True)
    assert "Só uma importação aguardando confirmação" in resposta.content.decode()
    assert client.get(reverse("diarios:confirmar", args=[diario.pk, importacao.pk])).status_code == 405


def test_outro_professor_nao_confirma_pela_url(client, gabarito_exemplo):
    importacao = versoes.registrar_versao(
        por=ProfessorFactory(), dados=gabarito_exemplo, bimestre_corte=4, sha256="a" * 64
    )
    _entrar(client, ProfessorFactory())
    url = reverse("diarios:confirmar", args=[importacao.diario_id, importacao.pk])
    assert client.post(url).status_code == 404
    assert Importacao.objects.get(pk=importacao.pk).status == StatusImportacao.AGUARDANDO_CONFIRMACAO


def test_coordenador_vincula_turma_e_professor_ao_diario(client, cenario):
    _entrar(client, cenario["coordenador"])
    novo_professor = ProfessorFactory()
    diario = cenario["diario"]
    dados = {
        "codigo": diario.codigo,
        "curso": cenario["curso"].pk,
        "disciplina": diario.disciplina_id,
        "ano_letivo": diario.ano_letivo,
        "periodo_letivo": 1,
        "turma": cenario["turma"].pk,
        "professor": novo_professor.pk,
        "aulas_previstas": 80,
        "carga_horaria_horas": "",
    }
    resposta = client.post(reverse("diarios:editar", args=[diario.pk]), dados, follow=True)
    assert "Alterações salvas." in resposta.content.decode()
    diario.refresh_from_db()
    assert (diario.turma, diario.professor) == (cenario["turma"], novo_professor)
    invalido = client.post(
        reverse("diarios:editar", args=[diario.pk]), {**dados, "disciplina": DisciplinaFactory().pk}
    )
    assert 'aria-invalid="true"' in invalido.content.decode()


def test_coordenador_cadastra_diario_no_proprio_curso(client, cenario):
    _entrar(client, cenario["coordenador"])
    dados = {
        "codigo": "12345",
        "curso": cenario["curso"].pk,
        "disciplina": cenario["diario"].disciplina_id,
        "ano_letivo": 2026,
        "periodo_letivo": 1,
        "turma": "",
        "professor": "",
        "aulas_previstas": "",
        "carga_horaria_horas": "",
    }
    resposta = client.post(reverse("diarios:novo"), dados, follow=True)
    assert "Diário 12345 cadastrado." in resposta.content.decode()
    repetido = client.post(reverse("diarios:novo"), dados)
    assert "já existe" in repetido.content.decode()
    outro_curso = client.post(
        reverse("diarios:novo"), {**dados, "codigo": "54321", "curso": CursoFactory().pk}
    )
    assert 'aria-invalid="true"' in outro_curso.content.decode()  # curso fora do escopo nem é opção


def test_excluir_diario_sem_e_com_notas(client, cenario, gabarito_exemplo):
    _entrar(client, cenario["coordenador"])
    diario = cenario["diario"]
    assert "Excluir o diário" in client.get(reverse("diarios:excluir", args=[diario.pk])).content.decode()
    resposta = client.post(reverse("diarios:excluir", args=[diario.pk]), follow=True)
    assert "excluído" in resposta.content.decode()
    assert not Diario.objects.filter(pk=diario.pk).exists()

    importacao = versoes.registrar_versao(
        por=cenario["coordenador"], dados=gabarito_exemplo, bimestre_corte=4, sha256="a" * 64
    )
    com_notas = importacao.diario
    com_notas.curso.coordenacoes.create(usuario=cenario["coordenador"])
    resposta = client.post(reverse("diarios:excluir", args=[com_notas.pk]), follow=True)
    assert "as versões nunca são apagadas" in resposta.content.decode()
    assert Diario.objects.filter(pk=com_notas.pk).exists()


def test_admin_cadastra_curso_e_vincula_coordenador(client):
    admin = AdminFactory()
    coordenador = CoordenadorFactory(nome="Cora Coralina")
    _entrar(client, admin)
    resposta = client.post(
        reverse("cadastros:curso_novo"), {"codigo": "700", "nome": "Edificações"}, follow=True
    )
    curso = Curso.objects.get(codigo="700")
    assert "Curso Edificações cadastrado." in resposta.content.decode()
    resposta = client.post(
        reverse("cadastros:coordenador_vincular", args=[curso.pk]), {"usuario": coordenador.pk}, follow=True
    )
    assert "Cora Coralina agora coordena Edificações." in resposta.content.decode()
    resposta = client.post(
        reverse("cadastros:coordenador_vincular", args=[curso.pk]), {"usuario": ""}, follow=True
    )
    assert "Escolha um coordenador válido." in resposta.content.decode()
    client.post(
        reverse("cadastros:curso_editar", args=[curso.pk]), {"codigo": "700", "nome": "Edificações Integrado"}
    )
    curso.refresh_from_db()
    assert curso.nome == "Edificações Integrado"
    resposta = client.post(reverse("cadastros:curso_excluir", args=[curso.pk]), follow=True)
    assert (
        "O curso tem turmas, disciplinas, diários ou coordenadores vinculados." in resposta.content.decode()
    )
    resposta = client.post(
        reverse("cadastros:coordenador_desvincular", args=[curso.pk, coordenador.pk]), follow=True
    )
    assert "não coordena mais" in resposta.content.decode()
    assert (
        "Excluir o curso" in client.get(reverse("cadastros:curso_excluir", args=[curso.pk])).content.decode()
    )
    client.post(reverse("cadastros:curso_excluir", args=[curso.pk]))
    assert not Curso.objects.filter(pk=curso.pk).exists()


def test_curso_mostra_coordenacao_e_professores_a_quem_gerencia(client, cenario):
    _entrar(client, cenario["coordenador"])
    html = client.get(reverse("cadastros:curso", args=[cenario["curso"].pk])).content.decode()
    assert "Professores do curso" in html
    assert cenario["professor"].nome in html
    _entrar(client, cenario["professor"])
    html = client.get(reverse("cadastros:curso", args=[cenario["curso"].pk])).content.decode()
    assert "Professores do curso" not in html


def test_coordenador_cadastra_altera_e_exclui_turma_e_disciplina(client, cenario):
    _entrar(client, cenario["coordenador"])
    curso = cenario["curso"]
    resposta = client.post(
        reverse("cadastros:turma_nova"),
        {"curso": curso.pk, "ano_letivo": 2026, "serie": 3, "identificador": "3º B"},
        follow=True,
    )
    assert "Turma 3º B (2026) cadastrada." in resposta.content.decode()
    turma = Turma.objects.get(identificador="3º B")
    client.post(
        reverse("cadastros:turma_editar", args=[turma.pk]),
        {"curso": curso.pk, "ano_letivo": 2026, "serie": 3, "identificador": "3º B Noite"},
    )
    turma.refresh_from_db()
    assert turma.identificador == "3º B Noite"
    assert (
        "Excluir a turma" in client.get(reverse("cadastros:turma_excluir", args=[turma.pk])).content.decode()
    )
    client.post(reverse("cadastros:turma_excluir", args=[turma.pk]))
    assert not Turma.objects.filter(pk=turma.pk).exists()

    resposta = client.post(
        reverse("cadastros:disciplina_nova"),
        {
            "curso": curso.pk,
            "codigo": "TIN.0099",
            "nome": "Redes",
            "carga_horaria_horas": 80,
            "optativa": "on",
        },
        follow=True,
    )
    assert "Disciplina TIN.0099 - Redes cadastrada." in resposta.content.decode()
    assert Disciplina.objects.get(codigo="TIN.0099").optativa
    duplicada = client.post(
        reverse("cadastros:disciplina_nova"), {"curso": curso.pk, "codigo": "TIN.0099", "nome": "Outra"}
    )
    assert "já existe" in duplicada.content.decode()
    em_uso = cenario["diario"].disciplina
    resposta = client.post(reverse("cadastros:disciplina_excluir", args=[em_uso.pk]), follow=True)
    assert "A disciplina tem diários vinculados." in resposta.content.decode()
    assert EventoAuditoria.objects.filter(tipo=TipoEvento.CADASTRO_CRIADO).count() == 2


def test_listas_de_cadastro_com_filtro_e_edicao_so_no_que_gerencia(client, cenario):
    alheia = TurmaFactory(identificador="Turma de Outro Curso")
    _entrar(client, AdminFactory())
    assert alheia.identificador in client.get(reverse("cadastros:turmas")).content.decode()
    _entrar(client, cenario["coordenador"])
    url = reverse("cadastros:turmas")
    html = client.get(url).content.decode()
    assert cenario["turma"].identificador in html
    assert alheia.identificador not in html
    assert client.get(url, {"q": "nada-disso"}).context["pagina"].paginator.count == 0
    assert client.get(url, {"curso": cenario["curso"].pk}).context["pagina"].paginator.count == 1
    disciplinas = client.get(reverse("cadastros:disciplinas"), {"q": cenario["diario"].disciplina.codigo})
    assert disciplinas.context["pagina"].paginator.count == 1
    _entrar(client, cenario["professor"])
    html = client.get(reverse("cadastros:disciplinas")).content.decode()
    assert "Somente consulta." in html
    assert reverse("cadastros:disciplina_editar", args=[cenario["diario"].disciplina_id]) not in html


def test_painel_resume_os_diarios(client, cenario, gabarito_exemplo):
    _entrar(client, cenario["professor"])
    resumo = client.get(reverse("painel")).context["resumo_diarios"]
    assert resumo == {"total": 1, "com_notas": 0, "aguardando": 0, "sem_turma": 1}


def test_comando_de_demonstracao_carrega_duas_versoes(capsys):
    professor = ProfessorFactory(email="demo@ifpb.edu.br")
    call_command("carregar_exemplo", email="DEMO@ifpb.edu.br")
    assert "carregado com 2 versões" in capsys.readouterr().out
    diario = Diario.objects.get(codigo="70764")
    assert diario.professor == professor
    v1, v2 = diario.importacoes.order_by("numero_versao")
    assert (v1.bimestre_corte, v2.bimestre_corte, v2.vigente) == (2, 4, True)
    assert not v1.resultados.filter(media_disciplina__isnull=False).exists()  # até o 2º bimestre
    with pytest.raises(CommandError, match="já foi enviado"):
        call_command("carregar_exemplo", email="demo@ifpb.edu.br")
    with pytest.raises(CommandError, match="não encontrado"):
        call_command("carregar_exemplo", email="ninguem@ifpb.edu.br")


@pytest.mark.parametrize(
    ("funcao", "rota", "com_pk", "dados"),
    [
        ("salvar_curso", "cadastros:curso_novo", False, {"codigo": "1", "nome": "X"}),
        ("salvar_curso", "cadastros:curso_editar", "curso", {"codigo": "1", "nome": "X"}),
        ("salvar_turma", "cadastros:turma_nova", False, {"ano_letivo": 2026, "identificador": "Z"}),
        ("salvar_turma", "cadastros:turma_editar", "turma", {"ano_letivo": 2026, "identificador": "Z"}),
        ("salvar_diario", "diarios:novo", False, {"codigo": "777", "ano_letivo": 2026, "periodo_letivo": 1}),
        (
            "salvar_diario",
            "diarios:editar",
            "diario",
            {"codigo": "777", "ano_letivo": 2026, "periodo_letivo": 1},
        ),
    ],
)
def test_recusa_do_servico_aparece_no_formulario(client, cenario, monkeypatch, funcao, rota, com_pk, dados):
    """Ex.: outra pessoa gravou o mesmo registro entre a validação do formulário e a gravação."""
    from django.core.exceptions import ValidationError

    from apps.academico import servicos

    def recusar(**kwargs):
        raise ValidationError("Conflito simulado ao gravar.")

    monkeypatch.setattr(servicos, funcao, recusar)
    _entrar(client, AdminFactory())
    curso = cenario["curso"]
    completos = {"curso": curso.pk, "disciplina": cenario["diario"].disciplina_id, **dados}
    args = [cenario[com_pk].pk] if com_pk else []
    resposta = client.post(reverse(rota, args=args), completos)
    assert resposta.status_code == 200
    assert "Conflito simulado ao gravar." in resposta.content.decode()


def test_versao_parcial_de_demonstracao_e_coerente(gabarito_exemplo):
    from apps.importacao.management.commands.carregar_exemplo import ate_o_bimestre

    parcial = ate_o_bimestre(gabarito_exemplo, 2)
    assert parcial["aulas_ministradas"]["ministradas"] == 40
    aline = parcial["alunos"][0]  # 4 faltas no 1º bimestre: (40 - 4) / 40 = 90%
    assert (aline["situacao"], aline["total_faltas"], aline["frequencia_percentual"]) == ("Cursando", 4, 90)
    assert [e["nota"] for e in aline["etapas"]] == [50, 85, None, None]
    assert parcial["alunos"][23]["situacao"] == "Cancelado"
