"""Modelo real: Cloudflare Workers AI a través de AI Gateway.

El cliente HTTP (``httpx.Client``) se inyecta para que las pruebas usen
``httpx.MockTransport`` y nunca la red. El token solo viaja en el encabezado
``Authorization``: nunca se registra ni va en los mensajes de error.
"""

import httpx

from app.completion import Completion, ModelUnavailableError

GATEWAY_URL_TEMPLATE = (
    "https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}"
    "/workers-ai/v1/chat/completions"
)
GATEWAY_TIMEOUT_SECONDS = 30.0
CACHE_TTL_HEADER = "cf-aig-cache-ttl"
CACHE_STATUS_HEADER = "cf-aig-cache-status"
CACHE_HIT = "HIT"
FIRST_ERROR_STATUS = 400


def build_http_client(timeout=GATEWAY_TIMEOUT_SECONDS):
    """Crea el cliente HTTP del gateway con un tiempo de espera fijo.

    :param timeout: Segundos máximos de espera por llamada
    :type timeout: float
    :return: Cliente listo para usar
    :rtype: httpx.Client
    """
    return httpx.Client(timeout=timeout)


class GatewayModel:  # pylint: disable=too-few-public-methods
    """Modelo de Workers AI que cumple ``complete(messages)``.

    :param name: Nombre del modelo en Workers AI (por ejemplo ``@cf/meta/...``)
    :type name: str
    :param settings: Configuración validada con las variables ``CF_*``
    :type settings: app.config.Settings
    :param http_client: Cliente HTTP inyectado
    :type http_client: httpx.Client
    """

    def __init__(self, name, settings, http_client):
        self.name = name
        self._client = http_client
        self._url = GATEWAY_URL_TEMPLATE.format(
            account_id=settings.cf_account_id, gateway_id=settings.cf_gateway_id
        )
        self._headers = {"Authorization": f"Bearer {settings.cf_api_token}"}
        if settings.cache_ttl_seconds > 0:
            self._headers[CACHE_TTL_HEADER] = str(settings.cache_ttl_seconds)
        self._max_tokens = settings.model_max_tokens
        self._temperature = settings.model_temperature

    def complete(self, messages):
        """Manda la conversación al gateway y lee el texto, los tokens y la caché.

        :param messages: Mensajes con ``role`` y ``content``
        :type messages: list[dict]
        :return: Respuesta del modelo
        :rtype: app.llm.Completion
        :raises app.llm.ModelUnavailableError: Si falla la red, vence el tiempo de
            espera, el estado es ``4xx/5xx`` o el cuerpo no es el esperado
        """
        body = {
            "model": self.name,
            "messages": messages,
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
        }
        try:
            response = self._client.post(self._url, json=body, headers=self._headers)
        except httpx.HTTPError as error:
            raise ModelUnavailableError(
                f"gateway request failed: {type(error).__name__}"
            ) from None
        if response.status_code >= FIRST_ERROR_STATUS:
            raise ModelUnavailableError(
                f"gateway returned status {response.status_code}"
            )
        text, input_tokens, output_tokens = _parse_body(response)
        cached = response.headers.get(CACHE_STATUS_HEADER, "").upper() == CACHE_HIT
        return Completion(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached=cached,
        )


def _parse_body(response):
    """Lee el texto y los tokens de una respuesta de chat completions.

    :param response: Respuesta HTTP exitosa del gateway
    :type response: httpx.Response
    :return: Texto, tokens de entrada y tokens de salida
    :rtype: tuple[str, int, int]
    :raises app.llm.ModelUnavailableError: Si el cuerpo no es JSON o le faltan
        ``choices`` o ``usage``
    """
    try:
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        usage = data["usage"]
        input_tokens = int(usage["prompt_tokens"])
        output_tokens = int(usage["completion_tokens"])
    except (ValueError, KeyError, IndexError, TypeError):
        raise ModelUnavailableError("gateway returned an invalid body") from None
    if not isinstance(text, str):
        raise ModelUnavailableError("gateway returned an invalid body")
    return text, input_tokens, output_tokens
