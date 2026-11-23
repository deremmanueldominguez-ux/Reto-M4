"""Decide el id de cada petición."""

import re
import uuid

REQUEST_ID_HEADER = "X-Request-ID"
VALID_REQUEST_ID = re.compile(r"[A-Za-z0-9._:-]{1,128}")


def resolve_request_id(header_value):
    """Usa el id que mandó el cliente si es seguro; si no, genera un UUID4.

    Se acepta de 1 a 128 caracteres de ``[A-Za-z0-9._:-]`` para que el log no
    reciba encabezados enormes ni caracteres de control.

    :param header_value: Valor del encabezado ``X-Request-ID`` o ``None``
    :type header_value: str or None
    :return: Id de la petición
    :rtype: str
    """
    if header_value and VALID_REQUEST_ID.fullmatch(header_value):
        return header_value
    return str(uuid.uuid4())
