"""Trazas opcionales en LangSmith.

Apagado, no importa ``langsmith`` ni intenta conectarse: ``wrap`` devuelve la misma
función. La clave ``LANGSMITH_API_KEY`` la lee ``langsmith`` del entorno; este
módulo nunca la toca.
"""

import importlib
import threading


class Tracer:
    """Envuelve funciones con ``traceable`` cuando las trazas están encendidas.

    :param enabled: Si las trazas están encendidas
    :type enabled: bool
    :param hide_inputs: No mandar las entradas a LangSmith
    :type hide_inputs: bool
    :param hide_outputs: No mandar las salidas a LangSmith
    :type hide_outputs: bool
    :param traceable: Decorador ``traceable``; ``None`` usa el de ``langsmith``
    :type traceable: collections.abc.Callable or None
    :param client_factory: Crea el cliente; ``None`` usa ``langsmith.Client``
    :type client_factory: collections.abc.Callable or None
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        enabled,
        *,
        hide_inputs=True,
        hide_outputs=True,
        traceable=None,
        client_factory=None,
    ):
        self.enabled = enabled
        self._hide_inputs = hide_inputs
        self._hide_outputs = hide_outputs
        self._traceable = traceable
        self._client_factory = client_factory
        self._client = None
        self._lock = threading.Lock()

    @classmethod
    def from_settings(cls, settings):
        """Crea el trazador según la configuración.

        :param settings: Configuración validada
        :type settings: app.config.Settings
        :return: Trazador encendido solo si hay clave y ``LANGSMITH_TRACING``
        :rtype: Tracer
        """
        return cls(
            enabled=settings.tracing_enabled,
            hide_inputs=settings.hide_inputs,
            hide_outputs=settings.hide_outputs,
        )

    def _load(self):
        """Importa ``langsmith`` y crea el cliente una sola vez.

        :return: Decorador ``traceable`` y cliente
        :rtype: tuple
        """
        with self._lock:
            if self._traceable is None or self._client_factory is None:
                # Import diferido: solo se carga con las trazas encendidas.
                langsmith = importlib.import_module("langsmith")
                self._traceable = self._traceable or langsmith.traceable
                self._client_factory = self._client_factory or langsmith.Client
            if self._client is None:
                self._client = self._client_factory(
                    hide_inputs=self._hide_inputs, hide_outputs=self._hide_outputs
                )
            return self._traceable, self._client

    def wrap(  # pylint: disable=too-many-arguments
        self, function, name, run_type, request_id, *, client=None
    ):
        """Envuelve una función para que quede como traza.

        :param function: Función a envolver
        :type function: collections.abc.Callable
        :param name: Nombre de la traza
        :type name: str
        :param run_type: Tipo de traza (``chain``, ``llm`` o ``tool``)
        :type run_type: str
        :param request_id: Id de la petición, va en los metadatos
        :type request_id: str
        :param client: Nombre del cliente, va en los metadatos; nunca la clave
        :type client: str or None
        :return: La misma función si está apagado; si no, la función envuelta
        :rtype: collections.abc.Callable
        """
        if not self.enabled:
            return function
        traceable, langsmith_client = self._load()
        metadata = {"request_id": request_id}
        if client is not None:
            metadata["client"] = client
        decorator = traceable(
            name=name,
            run_type=run_type,
            metadata=metadata,
            client=langsmith_client,
        )
        return decorator(function)

    def bind(self, request_id, client=None):
        """Devuelve una función ``trace(function, name, run_type)`` de una petición.

        :param request_id: Id de la petición
        :type request_id: str
        :param client: Nombre del cliente identificado, o ``None``
        :type client: str or None
        :return: Función que envuelve con el ``request_id`` y el cliente ya fijados
        :rtype: collections.abc.Callable
        """

        def trace(function, name, run_type):
            return self.wrap(function, name, run_type, request_id, client=client)

        return trace
