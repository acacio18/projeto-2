"""Apoio à autenticação usado pelo django-axes."""


def email_da_tentativa(request, credentials) -> str | None:
    """E-mail digitado no login, normalizado.

    O bloqueio é por conta: sem normalizar, "Prof@IFPB.edu.br" e "prof@ifpb.edu.br" contariam as
    falhas separadamente e permitiriam o dobro de tentativas.

    As credenciais chegam com a chave "username" (sinal de falha do Django e formulário de login) ou
    "email" (USERNAME_FIELD do modelo, usado por outros caminhos de autenticação). As duas valem: se
    só uma fosse lida, a verificação e o registro das falhas olhariam contas diferentes.
    """
    valor = None
    if credentials:
        valor = credentials.get("username") or credentials.get("email")
    if valor is None and request is not None:
        valor = request.POST.get("username")
    return valor.strip().lower() if isinstance(valor, str) else None
