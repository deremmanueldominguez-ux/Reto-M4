"""Pruebas del campo de clave de la página web."""

import re
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "app" / "static" / "index.html"


def test_page_keeps_the_key_in_a_password_field_for_the_session_only():
    html = PAGE.read_text(encoding="utf-8")
    key_input = re.search(r'<input[^>]*data-testid="api-key"[^>]*>', html)

    assert key_input is not None
    assert 'type="password"' in key_input.group(0)
    assert "sessionStorage" in html
    assert "localStorage" not in html
    assert "X-API-Key" in html
    assert "Clave inválida" in html
    assert "Demasiadas preguntas; espera" in html
