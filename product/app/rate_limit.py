"""Límite de peticiones por cliente con una ventana deslizante de 60 segundos.

El límite vive en la memoria del proceso: con varias copias del servicio, cada una
cuenta por su lado (ADR 0012).
"""

import math
import threading
from collections import deque

from fastapi import HTTPException

WINDOW_SECONDS = 60
MIN_RETRY_AFTER_SECONDS = 1
TOO_MANY_REQUESTS_STATUS = 429
TOO_MANY_REQUESTS_DETAIL = "rate limit exceeded"
RETRY_AFTER_HEADER = "Retry-After"


class RateLimiter:
    """Cuenta las peticiones de cada cliente en el último minuto.

    Cada cliente guarda como máximo ``limit`` marcas de tiempo.

    :param limit: Peticiones permitidas por cliente en la ventana
    :type limit: int
    :param clock: Reloj inyectado; se usa ``clock.monotonic()``
    :type clock: app.clock.Clock
    :param window_seconds: Largo de la ventana en segundos
    :type window_seconds: float
    """

    def __init__(self, limit, clock, window_seconds=WINDOW_SECONDS):
        self._limit = limit
        self._clock = clock
        self._window = window_seconds
        self._calls = {}
        self._lock = threading.Lock()

    def check(self, client):
        """Registra una petición del cliente si cabe en la ventana.

        :param client: Nombre del cliente
        :type client: str
        :return: ``None`` si la petición pasa; si no, los segundos enteros que faltan
            para que se libere un lugar (``Retry-After``), nunca menos de 1
        :rtype: int or None
        """
        now = self._clock.monotonic()
        with self._lock:
            calls = self._calls.setdefault(client, deque())
            while calls and now - calls[0] >= self._window:
                calls.popleft()
            if len(calls) < self._limit:
                calls.append(now)
                return None
            waiting = calls[0] + self._window - now
        return max(MIN_RETRY_AFTER_SECONDS, math.ceil(waiting))

    def enforce(self, client):
        """Aplica el límite: responde ``429`` si el cliente se pasó.

        :param client: Nombre del cliente ya identificado
        :type client: str
        :raises fastapi.HTTPException: ``429 {"detail": "rate limit exceeded"}`` con
            el encabezado ``Retry-After``
        """
        retry_after = self.check(client)
        if retry_after is not None:
            raise HTTPException(
                status_code=TOO_MANY_REQUESTS_STATUS,
                detail=TOO_MANY_REQUESTS_DETAIL,
                headers={RETRY_AFTER_HEADER: str(retry_after)},
            )
