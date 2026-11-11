"""Leitura do boletim do SUAP em PDF (IDs 4 e 5).

Fluxo: verificar o arquivo → extrair a tabela pelo texto do PDF (pdfplumber) → se não houver texto
utilizável, extrair por OCR (pypdfium2 + Tesseract) → interpretar com o perfil de layout do SUAP →
entregar os dados no formato do gabarito ("esquema": 1), que o serviço de versões grava.
"""

from apps.importacao.leitura.leitor import VERSAO_LEITOR, Leitura, ler_boletim
from apps.importacao.leitura.modelo import ErroDeLeitura

__all__ = ["VERSAO_LEITOR", "ErroDeLeitura", "Leitura", "ler_boletim"]
