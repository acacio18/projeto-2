"""Configurações usadas pela suíte de testes."""

from .base import *  # noqa: F403

DEBUG = False

# Hash rápido: os testes criam muitos usuários e não precisam de hash forte.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
