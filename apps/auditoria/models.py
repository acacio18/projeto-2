"""Trilha de auditoria somente de inclusão (base do ID 13; completada na E9).

Um evento nunca é alterado nem apagado. Isso vale em duas camadas: no Python (save/delete e as
operações em lote do QuerySet recusam) e no PostgreSQL (gatilho criado na migração 0002, que barra
UPDATE e DELETE até para quem acessa o banco direto).
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class EventoImutavelError(Exception):
    """Tentativa de alterar ou apagar um evento de auditoria."""


class TipoEvento(models.TextChoices):
    LOGIN_SUCESSO = "LOGIN_SUCESSO", "Login com sucesso"
    LOGIN_FALHA = "LOGIN_FALHA", "Falha de login"
    LOGOUT = "LOGOUT", "Logout"
    CONTA_BLOQUEADA = "CONTA_BLOQUEADA", "Conta bloqueada por tentativas"
    USUARIO_CRIADO = "USUARIO_CRIADO", "Usuário criado"
    USUARIO_ALTERADO = "USUARIO_ALTERADO", "Usuário alterado"
    USUARIO_DESATIVADO = "USUARIO_DESATIVADO", "Usuário desativado"
    USUARIO_REATIVADO = "USUARIO_REATIVADO", "Usuário reativado"
    CONVITE_ENVIADO = "CONVITE_ENVIADO", "Convite de acesso enviado"
    SENHA_ALTERADA = "SENHA_ALTERADA", "Senha alterada pelo próprio usuário"
    SENHA_REDEFINICAO_PEDIDA = "SENHA_REDEFINICAO_PEDIDA", "Redefinição de senha pedida"
    SENHA_DEFINIDA = "SENHA_DEFINIDA", "Senha definida por link (convite ou redefinição)"


class EventosQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise EventoImutavelError("Eventos de auditoria não podem ser alterados.")

    def delete(self):
        raise EventoImutavelError("Eventos de auditoria não podem ser apagados.")


class EventoAuditoria(models.Model):
    momento = models.DateTimeField("momento", default=timezone.now, db_index=True, editable=False)
    tipo = models.CharField("tipo", max_length=40, choices=TipoEvento.choices, db_index=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="quem fez",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="eventos_auditoria",
    )
    email_informado = models.CharField(
        "e-mail informado", max_length=254, blank=True, help_text="Só em falhas de login e pedidos de senha."
    )
    objeto_tipo = models.CharField("tipo do objeto afetado", max_length=60, blank=True)
    objeto_id = models.CharField("id do objeto afetado", max_length=60, blank=True)
    ip = models.GenericIPAddressField("IP", null=True, blank=True)
    agente = models.CharField("navegador (user agent)", max_length=300, blank=True)
    detalhes = models.JSONField("detalhes", default=dict, blank=True)

    objects = EventosQuerySet.as_manager()

    class Meta:
        verbose_name = "evento de auditoria"
        verbose_name_plural = "eventos de auditoria"
        ordering = ["-momento", "-id"]

    def __str__(self):
        return f"{self.momento:%d/%m/%Y %H:%M:%S} {self.get_tipo_display()}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise EventoImutavelError("Eventos de auditoria não podem ser alterados.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise EventoImutavelError("Eventos de auditoria não podem ser apagados.")
