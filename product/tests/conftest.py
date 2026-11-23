"""Fixtures compartidas por las pruebas del HR Assistant.

Las pruebas no dependen de ``data/employees.json``: escriben su propia copia de los
datos en una carpeta temporal y la inyectan con ``EMPLOYEES_PATH``.
"""

import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PRODUCT_ROOT = Path(__file__).resolve().parent.parent
if str(PRODUCT_ROOT) not in sys.path:
    sys.path.insert(0, str(PRODUCT_ROOT))

EMPLOYEES = [
    {
        "id": "EMP-0001",
        "name": "Ana López",
        "department": "Tecnología",
        "role": "Analista de datos",
        "start_date": "2019-03-04",
        "status": "activo",
    },
    {
        "id": "EMP-0002",
        "name": "Luis Pérez",
        "department": "Ventas",
        "role": "Ejecutivo de cuenta",
        "start_date": "2021-07-19",
        "status": "activo",
    },
    {
        "id": "EMP-0003",
        "name": "Marta Ruiz",
        "department": "Tecnología",
        "role": "Desarrolladora",
        "start_date": "2016-11-02",
        "status": "baja",
    },
    {
        "id": "EMP-0004",
        "name": "Jorge Díaz",
        "department": "Tecnología",
        "role": "Líder técnico",
        "start_date": "2022-01-10",
        "status": "activo",
    },
    {
        "id": "EMP-0005",
        "name": "Sofía Gómez",
        "department": "Finanzas",
        "role": "Contadora",
        "start_date": "2020-05-25",
        "status": "activo",
    },
]

# Sesión 4: desde ahora ``/ask`` y ``/metrics`` piden clave. Las pruebas de las sesiones
# 1 a 3 mandan esta clave de prueba en cada petición; es un texto de ejemplo, no un
# secreto real.
TEST_CLIENT = "test-client"
TEST_API_KEY = "test-api-key-0123456789"
TEST_API_KEYS = f"{TEST_CLIENT}:{TEST_API_KEY}"
TEST_HEADERS = {"X-API-Key": TEST_API_KEY}


@pytest.fixture
def employees_file(tmp_path):
    """Escribe los empleados de prueba en un JSON temporal.

    :return: Ruta del archivo escrito
    :rtype: pathlib.Path
    """
    path = tmp_path / "employees.json"
    path.write_text(json.dumps(EMPLOYEES, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture
def directory(employees_file):
    """Directorio de empleados cargado desde el archivo temporal.

    :return: Directorio de solo lectura
    :rtype: app.directory.EmployeeDirectory
    """
    # pylint: disable=import-outside-toplevel
    from app.directory import EmployeeDirectory

    return EmployeeDirectory(employees_file)


@pytest.fixture
def make_client(employees_file):
    """Fábrica de clientes HTTP con dependencias inyectadas.

    :return: Función que recibe ``max_steps`` y devuelve un ``TestClient``
    :rtype: collections.abc.Callable
    """
    # pylint: disable=import-outside-toplevel
    # Se importan aquí para que un fallo de importación no rompa toda la recolección.
    from app.config import load_settings
    from app.directory import EmployeeDirectory
    from app.llm import FakeModel
    from app.main import create_app

    def build(max_steps=3, built_model=False):
        # Con ``built_model=True`` no se inyecta el modelo: ``create_app`` lo arma con
        # ``build_model``, igual que en producción (el simulado conoce los nombres).
        settings = load_settings(
            {
                "MODEL_PROVIDER": "fake",
                "AGENT_MAX_STEPS": str(max_steps),
                "EMPLOYEES_PATH": str(employees_file),
                "API_KEYS": TEST_API_KEYS,
            }
        )
        directory = EmployeeDirectory(settings.employees_path)
        model = None if built_model else FakeModel(directory.departments())
        app = create_app(settings=settings, model=model, directory=directory)
        return TestClient(app, headers=TEST_HEADERS)

    return build


# Sesión 2: observabilidad. Reloj falso, modelos de apoyo y app con log capturado.

FIXED_NOW = datetime(2026, 11, 7, 10, 15, 30, 123000, tzinfo=timezone.utc)
FIXED_TS = "2026-11-07T10:15:30.123Z"


class FakeClock:
    """Reloj de prueba: la hora es fija y el monotónico solo avanza a mano.

    :param now: Fecha y hora que devuelve ``now()``
    :type now: datetime.datetime
    """

    def __init__(self, now=FIXED_NOW):
        self._now = now
        self._seconds = 0.0

    def now(self):
        """Devuelve la hora fija con zona UTC.

        :return: Hora fija
        :rtype: datetime.datetime
        """
        return self._now

    def monotonic(self):
        """Devuelve los segundos acumulados con ``advance``.

        :return: Segundos
        :rtype: float
        """
        return self._seconds

    def advance(self, seconds):
        """Avanza el reloj monotónico.

        :param seconds: Segundos que pasan
        :type seconds: float
        """
        self._seconds += seconds


class DelayedModel:  # pylint: disable=too-few-public-methods
    """Envuelve un modelo y hace que cada llamada tarde ``seconds`` en el reloj falso.

    :param inner: Modelo real de prueba
    :type inner: app.llm.LanguageModel
    :param clock: Reloj falso que se avanza
    :type clock: FakeClock
    :param seconds: Segundos por llamada
    :type seconds: float
    """

    def __init__(self, inner, clock, seconds):
        self._inner = inner
        self._clock = clock
        self._seconds = seconds

    def complete(self, messages):
        """Avanza el reloj y delega en el modelo envuelto."""
        self._clock.advance(self._seconds)
        return self._inner.complete(messages)


class FailingModel:  # pylint: disable=too-few-public-methods
    """Modelo que siempre lanza una excepción con un mensaje que no debe filtrarse."""

    SECRET = "secret-failure-details"

    def complete(self, messages):
        """Lanza ``RuntimeError`` siempre."""
        raise RuntimeError(f"{self.SECRET}: {messages[-1]['content']}")


class ObservedApp:
    """Cliente HTTP junto con su reloj falso y el log capturado.

    :param client: Cliente de prueba
    :type client: fastapi.testclient.TestClient
    :param clock: Reloj falso inyectado
    :type clock: FakeClock
    :param stream: Flujo donde la app escribe el log JSON
    :type stream: io.StringIO
    """

    def __init__(self, client, clock, stream):
        self.client = client
        self.clock = clock
        self.stream = stream

    def raw_log(self):
        """Devuelve el texto completo del log.

        :rtype: str
        """
        return self.stream.getvalue()

    def events(self, name=None):
        """Interpreta cada línea del log como JSON y filtra por evento.

        :param name: Nombre del evento, o ``None`` para todos
        :type name: str or None
        :rtype: list[dict]
        """
        lines = [line for line in self.raw_log().splitlines() if line.strip()]
        parsed = [json.loads(line) for line in lines]
        return [event for event in parsed if name is None or event["event"] == name]


@pytest.fixture
def fake_clock():
    """Reloj falso nuevo para cada prueba.

    :rtype: FakeClock
    """
    return FakeClock()


@pytest.fixture
def make_observed_app(employees_file):
    """Fábrica de apps con reloj falso, log capturado y modelo configurable.

    :return: Función que devuelve un ``ObservedApp``
    :rtype: collections.abc.Callable
    """
    # pylint: disable=import-outside-toplevel
    from app.config import load_settings
    from app.directory import EmployeeDirectory
    from app.llm import FakeModel
    from app.main import create_app

    def build(model_delay_ms=0, slo_p95_ms=2000, failing=False):
        settings = load_settings(
            {
                "MODEL_PROVIDER": "fake",
                "EMPLOYEES_PATH": str(employees_file),
                "SERVICE_NAME": "hr-test",
                "SLO_P95_MS": str(slo_p95_ms),
                "API_KEYS": TEST_API_KEYS,
            }
        )
        clock = FakeClock()
        stream = io.StringIO()
        directory = EmployeeDirectory(settings.employees_path)
        if failing:
            model = FailingModel()
        else:
            inner = FakeModel(directory.departments(), directory.names())
            model = DelayedModel(inner, clock, model_delay_ms / 1000)
        app = create_app(
            settings=settings,
            model=model,
            directory=directory,
            clock=clock,
            log_stream=stream,
        )
        client = TestClient(app, raise_server_exceptions=False, headers=TEST_HEADERS)
        return ObservedApp(client, clock, stream)

    return build


# Sesión 3: costos. Precios de prueba con números redondos para revisar las cuentas a
# mano, y respuestas del gateway armadas sin red.

SMALL_MODEL = "small-model"
LARGE_MODEL = "large-model"
SMALL_PRICE = {"input": 1.0, "output": 2.0}
LARGE_PRICE = {"input": 10.0, "output": 20.0}
CF_ENV = {
    "CF_ACCOUNT_ID": "acct-123",
    "CF_GATEWAY_ID": "gw-test",
    "CF_API_TOKEN": "cf-secret-token-xyz",
}


def gateway_reply(content, prompt_tokens=11, completion_tokens=5, cache_status=None):
    """Arma una respuesta de Workers AI (formato chat completions) del gateway.

    :param content: Texto que devuelve el modelo
    :type content: str
    :param prompt_tokens: Valor de ``usage.prompt_tokens``
    :type prompt_tokens: int
    :param completion_tokens: Valor de ``usage.completion_tokens``
    :type completion_tokens: int
    :param cache_status: Valor de ``cf-aig-cache-status``; ``None`` no lo manda
    :type cache_status: str or None
    :return: Respuesta HTTP simulada
    :rtype: httpx.Response
    """
    # pylint: disable=import-outside-toplevel
    import httpx

    headers = {"cf-aig-cache-status": cache_status} if cache_status else {}
    body = {
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        },
    }
    return httpx.Response(200, json=body, headers=headers)


@pytest.fixture
def prices_file(tmp_path):
    """Escribe una tabla de precios de prueba para ``SMALL_MODEL`` y ``LARGE_MODEL``.

    :return: Ruta del archivo escrito
    :rtype: pathlib.Path
    """
    path = tmp_path / "model_prices.json"
    prices = {
        "currency": "USD",
        "unit": "per million tokens",
        "models": {SMALL_MODEL: SMALL_PRICE, LARGE_MODEL: LARGE_PRICE},
    }
    path.write_text(json.dumps(prices), encoding="utf-8")
    return path


@pytest.fixture
def cost_env(employees_file, prices_file):
    """Variables de entorno de un asistente con modelos y precios de prueba.

    :rtype: dict
    """
    return {
        "MODEL_PROVIDER": "fake",
        "EMPLOYEES_PATH": str(employees_file),
        "PRICES_PATH": str(prices_file),
        "MODEL_SMALL": SMALL_MODEL,
        "MODEL_LARGE": LARGE_MODEL,
        "API_KEYS": TEST_API_KEYS,
    }


@pytest.fixture
def make_costed_client(cost_env):
    """Fábrica de clientes con precios de prueba y modelos opcionales.

    :return: Función que recibe ``models_factory`` (``settings -> dict`` de nombre a
        modelo; ``None`` deja que ``create_app`` arme los simulados) y variables que
        reemplazan a las de ``cost_env``
    :rtype: collections.abc.Callable
    """
    # pylint: disable=import-outside-toplevel
    from app.config import load_settings
    from app.main import create_app

    def build(models_factory=None, **overrides):
        settings = load_settings({**cost_env, **overrides})
        models = models_factory(settings) if models_factory else None
        app = create_app(settings=settings, models=models)
        return TestClient(app, raise_server_exceptions=False, headers=TEST_HEADERS)

    return build


# Sesión 4: producción. Dos clientes con claves de ejemplo, reloj falso para el límite
# de peticiones y un entorno de producción bien configurado sin red.

ACME_KEY = "acme-key-0123456789abc"
GLOBEX_KEY = "globex-key-0123456789abc"
SECURE_API_KEYS = f"acme:{ACME_KEY},globex:{GLOBEX_KEY}"


@pytest.fixture
def make_secure_app(employees_file):
    """Fábrica de apps con dos clientes, reloj falso y log capturado.

    El cliente HTTP no manda clave por omisión: cada prueba decide qué encabezado usa.

    :return: Función que recibe ``rate_limit`` y devuelve un ``ObservedApp``
    :rtype: collections.abc.Callable
    """
    # pylint: disable=import-outside-toplevel
    from app.config import load_settings
    from app.directory import EmployeeDirectory
    from app.llm import FakeModel
    from app.main import create_app

    def build(rate_limit=30):
        settings = load_settings(
            {
                "MODEL_PROVIDER": "fake",
                "EMPLOYEES_PATH": str(employees_file),
                "SERVICE_NAME": "hr-test",
                "API_KEYS": SECURE_API_KEYS,
                "RATE_LIMIT_PER_MINUTE": str(rate_limit),
            }
        )
        clock = FakeClock()
        stream = io.StringIO()
        directory = EmployeeDirectory(settings.employees_path)
        model = FakeModel(directory.departments(), directory.names())
        app = create_app(
            settings=settings,
            model=model,
            directory=directory,
            clock=clock,
            log_stream=stream,
        )
        client = TestClient(app, raise_server_exceptions=False)
        return ObservedApp(client, clock, stream)

    return build


@pytest.fixture
def production_env(cost_env):
    """Variables de un entorno de producción que cumple todas las reglas.

    :rtype: dict
    """
    return {
        **cost_env,
        **CF_ENV,
        "ENVIRONMENT": "production",
        "MODEL_PROVIDER": "gateway",
        "API_KEYS": SECURE_API_KEYS,
        "HIDE_INPUTS": "true",
        "HIDE_OUTPUTS": "true",
    }


@pytest.fixture
def start_assistant(directory):
    """Arranca el asistente con un entorno dado y modelos simulados inyectados.

    Los modelos simulados reemplazan al gateway para no usar la red; la configuración
    sigue diciendo ``gateway``, que es lo que revisa compliance.

    :return: Función que recibe las variables de entorno y devuelve un ``TestClient``
    :rtype: collections.abc.Callable
    :raises app.config.ConfigError: Si la configuración no permite arrancar
    """
    # pylint: disable=import-outside-toplevel
    from app.config import load_settings
    from app.llm import FakeModel
    from app.main import create_app

    def start(env):
        settings = load_settings(env)
        model = FakeModel(directory.departments(), directory.names())
        models = {settings.model_small: model, settings.model_large: model}
        app = create_app(settings=settings, models=models, directory=directory)
        return TestClient(app, raise_server_exceptions=False)

    return start


# Sesión 5: modo debug. App con ``LOG_LEVEL`` configurable, reloj falso, log
# capturado y modelos simulados, fallidos o del gateway sin red.


@pytest.fixture
def make_debug_app(cost_env):
    """Fábrica de apps con ``LOG_LEVEL`` elegido, reloj falso y log capturado.

    :return: Función que recibe ``log_level`` (``None`` no define la variable),
        ``model_delay_ms``, ``failing``, ``models_factory`` (``settings -> dict``
        de nombre a modelo) y variables que reemplazan a las de ``cost_env``; devuelve
        un ``ObservedApp``
    :rtype: collections.abc.Callable
    """
    # pylint: disable=import-outside-toplevel
    from app.config import load_settings
    from app.directory import EmployeeDirectory
    from app.llm import FakeModel
    from app.main import create_app

    def build(  # pylint: disable=too-many-arguments
        log_level="debug",
        model_delay_ms=0,
        failing=False,
        models_factory=None,
        **overrides,
    ):
        env = {**cost_env, "SERVICE_NAME": "hr-test", **overrides}
        if log_level is not None:
            env["LOG_LEVEL"] = log_level
        settings = load_settings(env)
        clock = FakeClock()
        stream = io.StringIO()
        directory = EmployeeDirectory(settings.employees_path)
        if models_factory is not None:
            models = models_factory(settings)
        else:
            if failing:
                model = FailingModel()
            else:
                inner = FakeModel(directory.departments(), directory.names())
                model = DelayedModel(inner, clock, model_delay_ms / 1000)
            models = {settings.model_small: model, settings.model_large: model}
        app = create_app(
            settings=settings,
            models=models,
            directory=directory,
            clock=clock,
            log_stream=stream,
        )
        client = TestClient(app, raise_server_exceptions=False, headers=TEST_HEADERS)
        return ObservedApp(client, clock, stream)

    return build
