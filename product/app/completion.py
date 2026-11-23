"""Tipos que comparten todos los proveedores de modelo.

Vive aparte de ``app.llm`` para que ``app.gateway`` los use sin importar
``app.llm`` (que a su vez arma el ``GatewayModel``): así no hay import cíclico.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Completion:
    """Respuesta de un modelo.

    :param text: Texto devuelto por el modelo (un objeto JSON)
    :type text: str
    :param input_tokens: Tokens de entrada consumidos
    :type input_tokens: int
    :param output_tokens: Tokens de salida producidos
    :type output_tokens: int
    :param cached: Si la respondió la caché del gateway (no se cobra)
    :type cached: bool
    """

    text: str
    input_tokens: int
    output_tokens: int
    cached: bool = False


class ModelUnavailableError(RuntimeError):
    """El proveedor del modelo no respondió bien; la API responde ``502``.

    El mensaje nunca lleva el token ni el texto de la conversación.
    """
