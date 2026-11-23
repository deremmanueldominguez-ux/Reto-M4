"""Pruebas del límite de peticiones por cliente con ventana de 60 segundos.

``RateLimiter(limit, clock).check(client)`` devuelve ``None`` si la petición pasa, o los
segundos de ``Retry-After`` si se pasa del límite.
"""

from conftest import FakeClock

from app.rate_limit import RateLimiter


def test_requests_up_to_the_limit_pass_and_one_more_is_limited():
    limiter = RateLimiter(2, FakeClock())

    assert limiter.check("acme") is None
    assert limiter.check("acme") is None
    assert limiter.check("acme") == 60


def test_retry_after_counts_the_seconds_left_and_is_never_zero():
    clock = FakeClock()
    limiter = RateLimiter(2, clock)
    limiter.check("acme")
    clock.advance(10)
    limiter.check("acme")

    clock.advance(10)
    assert limiter.check("acme") == 40

    clock.advance(39.9)
    assert limiter.check("acme") == 1


def test_the_window_frees_up_as_the_clock_advances_for_each_client_alone():
    clock = FakeClock()
    limiter = RateLimiter(1, clock)
    assert limiter.check("acme") is None
    assert limiter.check("acme") == 60
    assert limiter.check("globex") is None

    clock.advance(60.5)
    assert limiter.check("acme") is None
