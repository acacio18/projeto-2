"""Ponto único para gravar eventos de auditoria."""

from apps.auditoria.models import EventoAuditoria
from apps.contas.rede import agente_do_cliente, ip_do_cliente


def registrar(tipo, *, request=None, usuario=None, objeto=None, email_informado="", **detalhes):
    """Grava um evento. `objeto` é o registro afetado (ex.: o usuário criado), se houver."""
    if usuario is not None and not getattr(usuario, "is_authenticated", False):
        usuario = None
    return EventoAuditoria.objects.create(
        tipo=tipo,
        usuario=usuario,
        email_informado=(email_informado or "")[:254],
        objeto_tipo=objeto._meta.label if objeto is not None else "",
        objeto_id=str(objeto.pk) if objeto is not None else "",
        ip=ip_do_cliente(request) if request is not None else None,
        agente=agente_do_cliente(request) if request is not None else "",
        detalhes=detalhes,
    )
