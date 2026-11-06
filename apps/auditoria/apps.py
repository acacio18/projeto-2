from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    name = "apps.auditoria"
    verbose_name = "Auditoria"

    def ready(self):
        from apps.auditoria import sinais  # noqa: F401  (conecta os receptores de sinais)
