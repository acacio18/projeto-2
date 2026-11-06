"""Usuário do SUAP V2: login pelo e-mail institucional e um perfil (ID 1 e ID 15)."""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.contas.validadores import validar_email_institucional


class Perfil(models.TextChoices):
    PROFESSOR = "PROFESSOR", "Professor"
    COORDENADOR = "COORDENADOR", "Coordenador"
    ADMIN = "ADMIN", "Administrador"


class GerenciadorUsuarios(BaseUserManager):
    use_in_migrations = True

    def _criar(self, email, nome, password, **campos):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        usuario = self.model(email=self.normalize_email(email).lower(), nome=nome, **campos)
        usuario.set_password(password)  # None gera senha inutilizável (até definir pelo convite)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, nome, password=None, **campos):
        campos.setdefault("perfil", Perfil.PROFESSOR)
        campos["is_staff"] = False
        campos["is_superuser"] = False
        return self._criar(email, nome, password, **campos)

    def create_superuser(self, email, nome, password=None, **campos):
        """Usado pelo "manage.py createsuperuser": cria o primeiro administrador."""
        campos.update(perfil=Perfil.ADMIN, is_staff=True, is_superuser=True)
        return self._criar(email, nome, password, **campos)

    def get_by_natural_key(self, username):
        return self.get(email__iexact=username)


class Usuario(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        "e-mail institucional",
        max_length=254,
        unique=True,
        validators=[validar_email_institucional],
        error_messages={"unique": "Já existe um usuário com este e-mail."},
    )
    nome = models.CharField("nome completo", max_length=150)
    perfil = models.CharField("perfil", max_length=20, choices=Perfil.choices, default=Perfil.PROFESSOR)
    is_active = models.BooleanField(
        "ativo", default=True, help_text="Usuários desativados não conseguem entrar. Nunca são apagados."
    )
    is_staff = models.BooleanField(
        "acesso ao admin do Django", default=False, help_text="Só para manutenção técnica."
    )
    criado_em = models.DateTimeField("criado em", default=timezone.now, editable=False)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    objects = GerenciadorUsuarios()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["nome"]

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} <{self.email}>"

    def clean(self):
        super().clean()
        self.email = self.email.strip().lower()

    def save(self, *args, **kwargs):
        # E-mail sempre em minúsculas: a unicidade e o login não dependem de maiúsculas.
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def get_full_name(self):
        return self.nome

    def get_short_name(self):
        return self.nome.split()[0] if self.nome else self.email

    @property
    def convite_pendente(self) -> bool:
        """Ainda não definiu a senha pelo link do convite."""
        return not self.has_usable_password()

    @property
    def eh_admin(self) -> bool:
        return self.perfil == Perfil.ADMIN

    @property
    def eh_coordenador(self) -> bool:
        return self.perfil == Perfil.COORDENADOR

    @property
    def eh_professor(self) -> bool:
        return self.perfil == Perfil.PROFESSOR
