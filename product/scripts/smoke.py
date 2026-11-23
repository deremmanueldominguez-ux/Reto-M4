"""Prueba de humo contra el producto publicado (spec/04-production.md, punto 8).

Uso: ``SMOKE_API_KEY=<clave> python scripts/smoke.py https://<servicio>.onrender.com``

La clave se lee de la variable ``SMOKE_API_KEY`` y nunca de un argumento: así no
queda en el historial de la terminal. Tampoco se imprime.
"""

import os
import sys

import httpx

# Render despierta un servicio dormido en hasta un minuto.
TIMEOUT_SECONDS = 90
QUESTION = {"question": "¿Quién es EMP-0004?"}
USAGE = "Uso: SMOKE_API_KEY=<clave> python scripts/smoke.py <url>"


def status_of(client: httpx.Client, method: str, url: str, **kwargs) -> int | None:
    """Hace la petición y devuelve su código; ``None`` si no hubo respuesta.

    :param client: Cliente HTTP
    :type client: httpx.Client
    :param method: Método HTTP
    :type method: str
    :param url: URL completa
    :type url: str
    :return: Código de estado o ``None`` ante un error de red
    :rtype: int | None
    """
    try:
        return client.request(method, url, **kwargs).status_code
    except httpx.HTTPError as error:
        print(f"  error de red: {type(error).__name__}")
        return None


def smoke(base_url: str, key: str, client: httpx.Client) -> bool:
    """Comprueba ``/health``, ``/ask`` sin clave y ``/ask`` con clave.

    :param base_url: URL del servicio, sin barra final
    :type base_url: str
    :param key: Clave de API del cliente de prueba
    :type key: str
    :param client: Cliente HTTP
    :type client: httpx.Client
    :return: ``True`` si las tres comprobaciones pasan
    :rtype: bool
    """
    checks = [
        ("GET /health", 200, status_of(client, "GET", f"{base_url}/health")),
        ("POST /ask sin clave", 401,
         status_of(client, "POST", f"{base_url}/ask", json=QUESTION)),
        ("POST /ask con clave", 200,
         status_of(client, "POST", f"{base_url}/ask", json=QUESTION,
                   headers={"X-API-Key": key})),
    ]
    for name, expected, received in checks:
        label = "OK" if received == expected else "FAIL"
        print(f"[{label}] {name} -> {received} (esperado {expected})")
    return all(received == expected for _, expected, received in checks)


def main(args: list[str]) -> int:
    """Corre la prueba de humo: 0 si todo pasa, 1 si algo falla, 2 si falta algo.

    :param args: Argumentos de la línea de comandos sin el nombre del programa
    :type args: list[str]
    :return: Código de salida
    :rtype: int
    """
    key = os.environ.get("SMOKE_API_KEY", "")
    if len(args) != 1 or not key:
        print(USAGE)
        return 2
    with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
        passed = smoke(args[0].rstrip("/"), key, client)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
