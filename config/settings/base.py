"""Configurações comuns a todos os ambientes do SUAP V2.

Valores sensíveis ou que mudam por máquina vêm de variáveis de ambiente,
lidas do arquivo .env na raiz do projeto (fora do repositório; modelo em
.env.example).
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.contas",
    "apps.academico",
    "apps.importacao",
    "apps.notas",
    "apps.analytics",
    "apps.paineis",
    "apps.relatorios",
    "apps.api",
    "apps.auditoria",
    "apps.ops",
    "axes",
    "django_q",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Último, como pede o django-axes: transforma o bloqueio por tentativas em resposta 429.
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {"default": env.db("DATABASE_URL")}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Fortaleza"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Contas e autenticação (E1: IDs 1, 2 e 15) -------------------------------------------------
AUTH_USER_MODEL = "contas.Usuario"

# Domínios de e-mail aceitos no cadastro. Pendente de confirmação institucional (o plano cita
# @ifpb.edu.br e @academico.ifpb.edu.br; o segundo é dos estudantes, que não têm perfil).
CONTAS_DOMINIOS_EMAIL = env.list("CONTAS_DOMINIOS_EMAIL", default=["ifpb.edu.br"])

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",  # recusa o login de quem está bloqueado
    "django.contrib.auth.backends.ModelBackend",  # recusa usuários desativados
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "contas:entrar"
LOGIN_REDIRECT_URL = "painel"
LOGOUT_REDIRECT_URL = "contas:entrar"

# Sessão expira após N minutos sem uso (o prazo é renovado a cada requisição) e ao fechar o navegador.
SESSION_COOKIE_AGE = env.int("CONTAS_SESSAO_INATIVIDADE_MINUTOS", default=30) * 60
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

# Convite e redefinição de senha: validade do link enviado por e-mail.
PASSWORD_RESET_TIMEOUT = env.int("CONTAS_LINK_SENHA_VALIDADE_HORAS", default=72) * 3600

# Bloqueio por tentativas (django-axes): N falhas seguidas bloqueiam a CONTA (o e-mail digitado,
# em minúsculas), venha de qualquer IP, até o fim do prazo ou até um administrador desbloquear.
AXES_FAILURE_LIMIT = env.int("CONTAS_LOGIN_FALHAS_PARA_BLOQUEIO", default=5)
AXES_COOLOFF_TIME = timedelta(minutes=env.int("CONTAS_LOGIN_BLOQUEIO_MINUTOS", default=30))
AXES_LOCKOUT_PARAMETERS = ["username"]
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = "contas/bloqueado.html"  # resposta 429 com explicação
AXES_USERNAME_FORM_FIELD = "username"  # nome do campo no formulário de login do Django
AXES_USERNAME_CALLABLE = "apps.contas.autenticacao.email_da_tentativa"
AXES_CLIENT_IP_CALLABLE = "apps.contas.rede.ip_do_cliente"
# O axes recomenda bloquear também por IP (W006). Não fazemos isso: na rede de um campus todos saem
# pelo mesmo IP público, e 5 erros de pessoas diferentes trancariam o campus inteiro. O risco de
# testar uma senha comum em várias contas fica atenuado pelos validadores de senha; uma limitação por
# IP com limite próprio está prevista na revisão de segurança da E9.
SILENCED_SYSTEM_CHECKS = ["axes.W006"]

# E-mail (convites e redefinição de senha). Em desenvolvimento, as mensagens saem no terminal;
# em produção (E10), SMTP institucional configurado pelo .env.
EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DJANGO_DEFAULT_FROM_EMAIL", default="SUAP V2 <nao-responda@localhost>")

# Executável do Tesseract OCR (precisa do idioma "por" instalado).
TESSERACT_CMD = env("TESSERACT_CMD", default=r"C:\Program Files\Tesseract-OCR\tesseract.exe")

# --- Cadastros acadêmicos e importação (E2) ----------------------------------------------------
# Formato da matrícula (PRC-09): 12 dígitos no boletim de exemplo; pendente de confirmação.
ACADEMICO_MATRICULA_REGEX = env("ACADEMICO_MATRICULA_REGEX", default=r"^\d{12}$")

# PDFs enviados ficam numa pasta privada (fora de static/, nunca servida diretamente; fora do Git).
MEDIA_ROOT = env("DJANGO_MEDIA_ROOT", default=str(BASE_DIR / "media"))

# --- Importação de boletins (E3) ---------------------------------------------------------------
# Limites do envio (pendentes de confirmação com a TI; ajustáveis no .env).
IMPORTACAO_TAMANHO_MAXIMO_MB = env.int("IMPORTACAO_TAMANHO_MAXIMO_MB", default=10)
IMPORTACAO_MAXIMO_PAGINAS = env.int("IMPORTACAO_MAXIMO_PAGINAS", default=20)
IMPORTACAO_LOTE_MAXIMO_ARQUIVOS = env.int("IMPORTACAO_LOTE_MAXIMO_ARQUIVOS", default=50)
IMPORTACAO_LOTE_MAXIMO_MB = env.int("IMPORTACAO_LOTE_MAXIMO_MB", default=100)
# Resolução do OCR (PDF escaneado). 300 dpi é o recomendado pelo Tesseract.
IMPORTACAO_OCR_DPI = env.int("IMPORTACAO_OCR_DPI", default=300)

# Fila de tarefas (Django-Q2 com o próprio PostgreSQL como fila; sem Redis). Em desenvolvimento, o
# scripts\dev.ps1 sobe o "qcluster" junto com o servidor. Uma leitura com OCR leva cerca de 20 s.
Q_CLUSTER = {
    "name": "suap_v2",
    "orm": "default",
    "workers": env.int("FILA_PROCESSOS", default=2),
    "timeout": 300,  # uma leitura que passe de 5 min é interrompida e marcada como falha
    "retry": 360,  # precisa ser maior que o timeout
    "max_attempts": 1,  # a leitura não é repetida sozinha: o professor reenvia, se quiser
    "catch_up": False,
    "label": "Fila de tarefas",
}
