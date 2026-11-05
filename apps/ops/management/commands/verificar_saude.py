"""Comando ``python manage.py verificar_saude``: mesmas verificações do /healthz, no terminal."""

from django.core.management.base import BaseCommand, CommandError

from apps.ops import saude

DESCRICOES = {
    "banco": "Banco de dados (DATABASE_URL do .env)",
    "tesseract_por": "Tesseract OCR com o idioma português (TESSERACT_CMD)",
}


class Command(BaseCommand):
    help = "Verifica se o banco de dados e o Tesseract com português estão disponíveis."

    def handle(self, *args, **options):
        verificacoes = saude.verificar()
        for nome, passou in verificacoes.items():
            marca = self.style.SUCCESS("OK   ") if passou else self.style.ERROR("FALHA")
            self.stdout.write(f"{marca} {DESCRICOES.get(nome, nome)}")
        if not all(verificacoes.values()):
            raise CommandError("Há verificações de saúde com falha.")
