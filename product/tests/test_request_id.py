"""Pruebas de cómo se decide el id de cada petición."""

import uuid

from app.request_id import resolve_request_id


def test_a_valid_client_request_id_is_kept():
    for value in ("demo-123", "trace:1.2_x", "a" * 128):
        assert resolve_request_id(value) == value


def test_a_missing_or_unsafe_request_id_is_replaced_by_a_uuid4():
    for value in (None, "", "a" * 129, "bad\nvalue", "con espacio"):
        generated = resolve_request_id(value)
        assert generated != value
        assert uuid.UUID(generated).version == 4
