"""Métricas en memoria de este proceso para ``GET /metrics``."""

import threading
from collections import deque

LATENCY_WINDOW = 1000
SERVER_ERROR_STATUS = 500
ERROR_RATE_DECIMALS = 4


def nearest_rank(sorted_values, percent):
    """Calcula un percentil por rango más cercano.

    :param sorted_values: Valores ordenados de menor a mayor
    :type sorted_values: list[float]
    :param percent: Percentil entero entre 1 y 100
    :type percent: int
    :return: Valor del percentil, o ``0`` si no hay datos
    :rtype: float or int
    """
    if not sorted_values:
        return 0
    rank = -(-percent * len(sorted_values) // 100)
    return sorted_values[max(rank, 1) - 1]


class Metrics:
    """Contadores del proceso protegidos con un candado.

    Las latencias se guardan en una ventana de las últimas ``LATENCY_WINDOW``.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._requests = 0
        self._errors = 0
        self._latencies = deque(maxlen=LATENCY_WINDOW)
        self._input_tokens = 0
        self._output_tokens = 0
        self._cost_usd = 0.0

    def record_request(self, status, latency_ms):
        """Registra una petición terminada.

        Solo las respuestas ``5xx`` cuentan como error; las ``4xx`` son del cliente.

        :param status: Código HTTP de la respuesta
        :type status: int
        :param latency_ms: Latencia en milisegundos
        :type latency_ms: float
        """
        with self._lock:
            self._requests += 1
            if status >= SERVER_ERROR_STATUS:
                self._errors += 1
            self._latencies.append(latency_ms)

    def add_tokens(self, input_tokens, output_tokens):
        """Suma los tokens de una corrida del agente.

        :param input_tokens: Tokens de entrada
        :type input_tokens: int
        :param output_tokens: Tokens de salida
        :type output_tokens: int
        """
        with self._lock:
            self._input_tokens += input_tokens
            self._output_tokens += output_tokens

    def add_cost(self, cost_usd):
        """Suma el costo de una respuesta, sin redondear.

        :param cost_usd: Costo en USD
        :type cost_usd: float
        """
        with self._lock:
            self._cost_usd += cost_usd

    def snapshot(self, pid, slo_p95_ms):
        """Arma el cuerpo de ``GET /metrics``.

        :param pid: Id del proceso
        :type pid: int
        :param slo_p95_ms: Meta de latencia p95 en milisegundos
        :type slo_p95_ms: int
        :return: Métricas del proceso
        :rtype: dict
        """
        with self._lock:
            requests = self._requests
            errors = self._errors
            latencies = sorted(self._latencies)
            tokens = {"input": self._input_tokens, "output": self._output_tokens}
            cost_usd = self._cost_usd
        error_rate = round(errors / requests, ERROR_RATE_DECIMALS) if requests else 0.0
        p95 = nearest_rank(latencies, 95)
        return {
            "pid": pid,
            "requests": requests,
            "error_rate": error_rate,
            "latency_ms": {"p50": nearest_rank(latencies, 50), "p95": p95},
            "tokens": tokens,
            "cost_usd": cost_usd,
            "slo": {"p95_ms_target": slo_p95_ms, "met": p95 < slo_p95_ms},
        }
