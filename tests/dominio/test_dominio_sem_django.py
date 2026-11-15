"""O domínio é puro: nenhum módulo de dominio/ importa o Django (regra da arquitetura)."""

import subprocess  # nosec B404 - roda o próprio Python do projeto
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def test_dominio_nao_importa_django():
    modulos = [
        ".".join(caminho.relative_to(RAIZ).with_suffix("").parts).removesuffix(".__init__")
        for caminho in sorted((RAIZ / "dominio").rglob("*.py"))
    ]
    linhas = [f"import sys; sys.path.insert(0, {str(RAIZ)!r})", "import importlib"]
    linhas += [f"importlib.import_module({m!r})" for m in modulos]
    linhas.append("assert not [m for m in sys.modules if m.split('.')[0] == 'django'], 'importou django'")
    resultado = subprocess.run(  # nosec B603 - o próprio Python, com código fixo
        [sys.executable, "-I", "-c", "\n".join(linhas)], capture_output=True, text=True, check=False
    )
    assert resultado.returncode == 0, resultado.stderr
    assert len(modulos) >= 8
