"""Pruebas de las métricas en memoria que expone ``GET /metrics``."""

import pytest

from app.metrics import Metrics


def test_metrics_without_requests_report_zeros_and_a_met_slo():
    assert Metrics().snapshot(pid=42, slo_p95_ms=2000) == {
        "pid": 42,
        "requests": 0,
        "error_rate": 0.0,
        "latency_ms": {"p50": 0, "p95": 0},
        "tokens": {"input": 0, "output": 0},
        "cost_usd": 0.0,
        "slo": {"p95_ms_target": 2000, "met": True},
    }


def test_cost_accumulates_without_rounding_tiny_amounts():
    metrics = Metrics()
    for _ in range(3):
        metrics.add_cost(0.000000004)
    assert metrics.snapshot(pid=1, slo_p95_ms=2000)["cost_usd"] == pytest.approx(
        0.000000012, abs=1e-15
    )


def test_percentiles_use_nearest_rank_and_only_server_errors_count():
    metrics = Metrics()
    for latency in range(1, 21):
        status = {5: 500, 6: 404}.get(latency, 200)
        metrics.record_request(status=status, latency_ms=float(latency))
    metrics.add_tokens(input_tokens=30, output_tokens=7)
    metrics.add_tokens(input_tokens=12, output_tokens=3)

    snapshot = metrics.snapshot(pid=1, slo_p95_ms=100)
    assert snapshot["requests"] == 20
    assert snapshot["error_rate"] == 0.05
    assert snapshot["latency_ms"] == {"p50": 10.0, "p95": 19.0}
    assert snapshot["tokens"] == {"input": 42, "output": 10}
    assert snapshot["slo"]["met"] is True


def test_latency_percentiles_only_use_the_last_thousand_requests():
    metrics = Metrics()
    for _ in range(1000):
        metrics.record_request(status=200, latency_ms=1.0)
    for _ in range(1000):
        metrics.record_request(status=200, latency_ms=50.0)
    snapshot = metrics.snapshot(pid=1, slo_p95_ms=2000)
    assert snapshot["requests"] == 2000
    assert snapshot["latency_ms"] == {"p50": 50.0, "p95": 50.0}


def test_slo_is_not_met_when_p95_equals_the_target():
    metrics = Metrics()
    for _ in range(10):
        metrics.record_request(status=200, latency_ms=2000.0)
    assert metrics.snapshot(pid=1, slo_p95_ms=2000)["slo"] == {
        "p95_ms_target": 2000,
        "met": False,
    }
