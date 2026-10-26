"""Configuração dos testes de navegador (Playwright).

A API síncrona do Playwright mantém um loop de eventos ativo na thread do teste. Sem esta
variável, o Django bloqueia o acesso ao banco nessa thread (SynchronousOnlyOperation) quando
o pytest-django limpa o banco usado pelo live_server.
"""

import os

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
