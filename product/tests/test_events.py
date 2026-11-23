"""Pruebas del reloj del sistema y del log JSON de una línea por evento."""

import io
import json
import re
from datetime import timedelta

from app.clock import SystemClock
from app.events import EventLogger

# Hora fija del ``FakeClock`` de ``conftest.py`` en el formato del log.
FIXED_TS = "2026-11-07T10:15:30.123Z"


def test_system_clock_reports_utc_time_and_a_monotonic_counter():
    clock = SystemClock()
    assert clock.now().utcoffset() == timedelta(0)
    first = clock.monotonic()
    assert clock.monotonic() >= first


def test_each_event_is_one_json_line_with_the_common_fields(fake_clock):
    stream = io.StringIO()
    logger = EventLogger(service="hr-test", clock=fake_clock, stream=stream)
    logger.emit(
        "audit", request_id="req-1", tool="search_by_name", args={"name": "Sofía"}
    )
    logger.bind("req-2").emit("agent_run", steps=2)

    raw = stream.getvalue()
    lines = raw.splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == {
        "ts": FIXED_TS,
        "service": "hr-test",
        "event": "audit",
        "request_id": "req-1",
        "tool": "search_by_name",
        "args": {"name": "Sofía"},
    }
    second = json.loads(lines[1])
    assert (second["event"], second["request_id"], second["steps"]) == (
        "agent_run",
        "req-2",
        2,
    )
    assert "Sofía" in raw


# Sesión 5: nivel ``debug``, lista blanca, redactor y frames del stack trace.
# Los nombres nuevos se importan dentro de cada prueba para no romper la recolección.

FRAME_PATTERN = re.compile(r"^[^/\\:]+\.py:\d+:[^:\s]+$")
EXCEPTION_MESSAGE = "exception-message-with-private-data"


def test_debug_events_are_dropped_at_the_info_level(fake_clock):
    # pylint: disable=import-outside-toplevel
    from app.events import NullLog

    stream = io.StringIO()
    logger = EventLogger(
        service="hr-test", clock=fake_clock, stream=stream, level="info"
    )
    request_log = logger.bind("req-1", client="acme")

    request_log.debug("model_call", model="m", status="ok")
    NullLog().debug("model_call", model="m")
    request_log.emit("agent_run", steps=1)

    events = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert [event["event"] for event in events] == ["agent_run"]


def test_a_debug_event_keeps_only_its_whitelisted_fields(fake_clock):
    stream = io.StringIO()
    logger = EventLogger(
        service="hr-test", clock=fake_clock, stream=stream, level="debug"
    )

    logger.bind("req-1").debug(
        "model_call",
        model="small-model",
        status="ok",
        latency_ms=12.5,
        input_tokens=30,
        output_tokens=4,
        cached=False,
        headers={"Authorization": "Bearer leaked-value"},
        settings="Settings(model_provider='gateway')",
    )

    assert json.loads(stream.getvalue()) == {
        "ts": FIXED_TS,
        "service": "hr-test",
        "event": "model_call",
        "request_id": "req-1",
        "model": "small-model",
        "status": "ok",
        "latency_ms": 12.5,
        "input_tokens": 30,
        "output_tokens": 4,
        "cached": False,
    }


def test_every_emitted_event_goes_through_the_redactor_also_at_info(fake_clock):
    # pylint: disable=import-outside-toplevel
    from app.events import Redactor

    stream = io.StringIO()
    logger = EventLogger(
        service="hr-test",
        clock=fake_clock,
        stream=stream,
        level="info",
        redactor=Redactor(["known-secret-0001"]),
    )

    logger.bind("req-1").emit(
        "audit",
        args={"name": "has known-secret-0001 inside"},
        authorization="Bearer abc",
        note="sent Bearer xyz-123",
    )

    event = json.loads(stream.getvalue())
    assert event["args"] == {"name": "has [REDACTED] inside"}
    assert event["authorization"] == "[REDACTED]"
    assert event["note"] == "sent Bearer [REDACTED]"


def test_stack_frames_give_short_file_line_and_function_without_the_message():
    # pylint: disable=import-outside-toplevel
    from app.events import stack_frames

    def explode():
        raise ValueError(EXCEPTION_MESSAGE)

    frames = []
    try:
        explode()
    except ValueError as error:
        frames = stack_frames(error)

    assert frames
    for frame in frames:
        assert FRAME_PATTERN.match(frame), frame
        assert EXCEPTION_MESSAGE not in frame
    assert frames[-1].startswith("test_events.py:")
    assert frames[-1].endswith(":explode")
