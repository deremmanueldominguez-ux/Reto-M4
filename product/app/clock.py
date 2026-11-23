"""Reloj inyectable: el único lugar que lee la hora del sistema."""

import time
from datetime import datetime, timezone
from typing import Protocol


class Clock(Protocol):
    """Protocolo de reloj que reciben los módulos que necesitan la hora."""

    def now(self):
        """Devuelve la hora actual con zona UTC.

        :return: Fecha y hora con zona
        :rtype: datetime.datetime
        """

    def monotonic(self):
        """Devuelve segundos de un contador que nunca retrocede.

        :return: Segundos
        :rtype: float
        """


class SystemClock:
    """Reloj real basado en el sistema operativo."""

    def now(self):
        """Devuelve la hora actual en UTC.

        :return: Fecha y hora con zona UTC
        :rtype: datetime.datetime
        """
        return datetime.now(timezone.utc)

    def monotonic(self):
        """Devuelve el contador monotónico del sistema.

        :return: Segundos
        :rtype: float
        """
        return time.monotonic()
