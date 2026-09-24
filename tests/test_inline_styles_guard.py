"""P3 AUDITORIA_COMPONENTES - Regresión del guard de estilos inline.

Ejecuta _tools/check_inline_styles.py en modo CI: debe salir con código 0.
Registra la deuda existente en el baseline; solo falla si un template
supera su conteo previo o si un template nuevo trae mas de 25 inline.
"""
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "_tools" / "check_inline_styles.py"


def test_guard_inline_styles_no_regresiones():
    result = subprocess.run(
        [sys.executable, str(TOOL)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr