"""Agente único con bucle con tope sobre el directorio de empleados."""

import json
from dataclasses import dataclass, field

from app.clock import SystemClock
from app.completion import ModelUnavailableError
from app.events import NullLog
from app.llm import TOOL_RESULT_PREFIX
from app.router import apply_window

MILLIS_PER_SECOND = 1000
LATENCY_DECIMALS = 1
MODEL_CALL_OK = "ok"
MODEL_CALL_ERROR = "error"
STOPPED_BY_ANSWER = "answer"
STOPPED_BY_MAX_STEPS = "max_steps"
GIVE_UP_ANSWER = (
    "No pude completar la respuesta. Intenta con una pregunta más concreta."
)
INVALID_JSON_NOTICE = (
    'Respuesta inválida: responde solo un objeto JSON con "tool" y "args" '
    'o con "answer".'
)
SYSTEM_PROMPT = (
    "Eres el asistente de Recursos Humanos. Responde siempre un único objeto JSON: "
    '{"tool": "<nombre>", "args": {...}} para pedir una herramienta o '
    '{"answer": "<respuesta en español>"} para responder. Herramientas: '
    "get_employee(employee_id) devuelve un empleado por id; "
    "search_by_department(department) lista los empleados de un departamento; "
    "search_by_name(name) lista los empleados cuyo nombre contiene el texto, "
    "sin distinguir mayúsculas ni tildes."
)


@dataclass(frozen=True)
class Billing:
    """Con qué modelo y precio se cobra una corrida del agente.

    :param model: Nombre del modelo enrutado; con él se busca el precio
    :type model: str
    :param route: Motivo del enrutador
    :type route: str
    :param prices: Tabla de precios
    :type prices: app.pricing.PriceTable
    """

    model: str
    route: str
    prices: object


@dataclass
class AgentResult:  # pylint: disable=too-many-instance-attributes
    """Resultado de una pregunta al agente.

    :param answer: Respuesta final en español
    :type answer: str
    :param steps: Número de llamadas al modelo
    :type steps: int
    :param tools_used: Herramientas ejecutadas, en orden
    :type tools_used: list[str]
    :param input_tokens: Suma de tokens de entrada
    :type input_tokens: int
    :param output_tokens: Suma de tokens de salida
    :type output_tokens: int
    :param stopped: Por qué terminó: ``answer`` o ``max_steps``
    :type stopped: str
    :param cached_calls: Llamadas que respondió la caché del gateway
    :type cached_calls: int
    :param billable_input_tokens: Tokens de entrada de llamadas no cacheadas
    :type billable_input_tokens: int
    :param billable_output_tokens: Tokens de salida de llamadas no cacheadas
    :type billable_output_tokens: int
    :param cost_usd: Costo en USD sin redondear (0 si no hay ``Billing``)
    :type cost_usd: float
    """

    answer: str
    steps: int = 0
    tools_used: list = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    stopped: str = STOPPED_BY_MAX_STEPS
    cached_calls: int = 0
    billable_input_tokens: int = 0
    billable_output_tokens: int = 0
    cost_usd: float = 0.0


def _no_trace(function, name, run_type):  # pylint: disable=unused-argument
    """Trazador nulo: devuelve la misma función.

    :param function: Función que se envolvería
    :type function: collections.abc.Callable
    :param name: Nombre de la traza
    :type name: str
    :param run_type: Tipo de traza
    :type run_type: str
    :return: La misma función
    :rtype: collections.abc.Callable
    """
    return function


def _elapsed_ms(clock, started):
    """Milisegundos desde ``started`` según el reloj inyectado.

    :param clock: Reloj inyectado
    :type clock: app.clock.Clock
    :param started: Valor previo de ``clock.monotonic()``
    :type started: float
    :return: Milisegundos redondeados a un decimal
    :rtype: float
    """
    return round((clock.monotonic() - started) * MILLIS_PER_SECOND, LATENCY_DECIMALS)


class Agent:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Agente sin estado: todo lo recibe por argumento en cada llamada.

    :param model: Modelo que cumple ``complete(messages)``
    :type model: app.llm.LanguageModel
    :param directory: Directorio de empleados de solo lectura
    :type directory: app.directory.EmployeeDirectory
    :param max_steps: Tope de llamadas al modelo
    :type max_steps: int
    :param log: Log con el ``request_id`` ya fijado; ``None`` descarta los eventos
    :type log: app.events.RequestLog or None
    :param trace: Función ``trace(function, name, run_type)`` que envuelve con
        trazas; ``None`` no envuelve
    :type trace: collections.abc.Callable or None
    :param history_window: Mensajes de historial que se mandan; ``None`` manda
        todo
    :type history_window: int or None
    :param billing: Modelo, ruta y precios para calcular ``cost_usd``; ``None`` no
        calcula costo
    :type billing: Billing or None
    :param clock: Reloj para medir ``agent_step`` y ``model_call``; ``None`` usa el
        del sistema
    :type clock: app.clock.Clock or None
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        model,
        directory,
        max_steps,
        *,
        log=None,
        trace=None,
        history_window=None,
        billing=None,
        clock=None,
    ):
        self._history_window = history_window
        self._billing = billing
        self._trace = trace or _no_trace
        self._complete = self._trace(model.complete, "complete", "llm")
        self._max_steps = max_steps
        self._log = log or NullLog()
        # Un log sin ``debug`` (por ejemplo, uno de prueba) descarta esos eventos.
        self._debug = getattr(self._log, "debug", None) or NullLog().debug
        self._clock = clock or SystemClock()
        self._model_name = (
            billing.model if billing is not None else getattr(model, "name", "")
        ) or type(model).__name__
        tools = {
            "get_employee": directory.get_employee,
            "search_by_department": directory.search_by_department,
            "search_by_name": directory.search_by_name,
        }
        self._tools = {
            name: self._trace(function, name, "tool")
            for name, function in tools.items()
        }

    def run(self, question, history=None):
        """Responde una pregunta usando herramientas si el modelo las pide.

        Solo se recorta el historial del cliente con la ventana; la pregunta y los
        mensajes del bucle actual siempre se mandan. Al terminar emite el evento
        ``agent_run`` solo con conteos (y, con ``Billing``, modelo, ruta, llamadas
        cacheadas y costo), nunca con el texto de la pregunta ni de la respuesta.

        :param question: Pregunta de la persona
        :type question: str
        :param history: Turnos previos con ``role`` y ``content``
        :type history: list[dict] or None
        :return: Respuesta, pasos, herramientas, tokens, costo y motivo de término
        :rtype: AgentResult
        """
        history = history or []
        sent = history
        if self._history_window is not None:
            sent = apply_window(history, self._history_window)
        result = self._trace(self._loop, "agent_run", "chain")(question, sent)
        fields = {}
        if self._billing is not None:
            result.cost_usd = self._billing.prices.cost(
                self._billing.model,
                input_tokens=result.billable_input_tokens,
                output_tokens=result.billable_output_tokens,
            )
            fields = {
                "model": self._billing.model,
                "route": self._billing.route,
                "cached_calls": result.cached_calls,
                "cost_usd": result.cost_usd,
            }
        self._log.emit(
            "agent_run",
            question_chars=len(question),
            history_messages=len(history),
            steps=result.steps,
            tools=list(result.tools_used),
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            stopped=result.stopped,
            **fields,
        )
        return result

    def _loop(self, question, history):
        """Bucle con tope de llamadas al modelo.

        :param question: Pregunta de la persona
        :type question: str
        :param history: Turnos previos con ``role`` y ``content``
        :type history: list[dict]
        :return: Resultado de la corrida
        :rtype: AgentResult
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for turn in history:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": question})
        result = AgentResult(answer=GIVE_UP_ANSWER)
        while result.steps < self._max_steps:
            step_started = self._clock.monotonic()
            tools_before = len(result.tools_used)
            completion = self._call_model(messages)
            result.steps += 1
            result.input_tokens += completion.input_tokens
            result.output_tokens += completion.output_tokens
            if completion.cached:
                result.cached_calls += 1
            else:
                result.billable_input_tokens += completion.input_tokens
                result.billable_output_tokens += completion.output_tokens
            reply = _parse_reply(completion.text)
            if reply is not None and isinstance(reply.get("answer"), str):
                result.answer = reply["answer"]
                result.stopped = STOPPED_BY_ANSWER
                self._log_step(result, tools_before, step_started)
                return result
            messages.append({"role": "assistant", "content": completion.text})
            messages.append({"role": "user", "content": self._feedback(reply, result)})
            self._log_step(result, tools_before, step_started)
        result.answer = GIVE_UP_ANSWER
        result.stopped = STOPPED_BY_MAX_STEPS
        return result

    def _call_model(self, messages):
        """Llama al modelo y emite ``model_call`` (solo en ``debug``).

        Si el modelo no está disponible, emite ``model_call`` con ``status="error"``
        y relanza la excepción. Nunca registra mensajes ni texto de la respuesta.

        :param messages: Mensajes con ``role`` y ``content``
        :type messages: list[dict]
        :return: Respuesta del modelo
        :rtype: app.completion.Completion
        :raises app.completion.ModelUnavailableError: Si el modelo falla
        """
        started = self._clock.monotonic()
        try:
            completion = self._complete(messages)
        except ModelUnavailableError:
            self._debug(
                "model_call",
                model=self._model_name,
                status=MODEL_CALL_ERROR,
                latency_ms=_elapsed_ms(self._clock, started),
                input_tokens=0,
                output_tokens=0,
                cached=False,
            )
            raise
        self._debug(
            "model_call",
            model=self._model_name,
            status=MODEL_CALL_OK,
            latency_ms=_elapsed_ms(self._clock, started),
            input_tokens=completion.input_tokens,
            output_tokens=completion.output_tokens,
            cached=completion.cached,
        )
        return completion

    def _log_step(self, result, tools_before, started):
        """Emite ``agent_step`` (solo en ``debug``) con las herramientas del paso.

        :param result: Resultado parcial de la corrida
        :type result: AgentResult
        :param tools_before: Herramientas usadas antes de este paso
        :type tools_before: int
        :param started: Valor de ``clock.monotonic()`` al empezar el paso
        :type started: float
        """
        self._debug(
            "agent_step",
            step=result.steps,
            tools=list(result.tools_used[tools_before:]),
            latency_ms=_elapsed_ms(self._clock, started),
        )

    def _feedback(self, reply, result):
        """Ejecuta la herramienta pedida o arma el aviso de error para el modelo.

        :param reply: Objeto JSON del modelo o ``None`` si no era válido
        :type reply: dict or None
        :param result: Resultado parcial donde se registran las herramientas
        :type result: AgentResult
        :return: Contenido del mensaje ``user`` que vuelve al modelo
        :rtype: str
        """
        if reply is None or "tool" not in reply:
            return INVALID_JSON_NOTICE
        name = reply.get("tool")
        tool = self._tools.get(name) if isinstance(name, str) else None
        if tool is None:
            return (
                f"Herramienta desconocida: {name}. "
                "Usa get_employee, search_by_department o search_by_name."
            )
        args = reply.get("args") or {}
        self._log.emit("audit", action="tool_call", tool=name, args=args)
        try:
            output = tool(**args) if isinstance(args, dict) else None
        except TypeError:
            output = None
        if output is None:
            return f"Argumentos inválidos para la herramienta {name}."
        result.tools_used.append(name)
        return TOOL_RESULT_PREFIX + json.dumps(output, ensure_ascii=False)


def _parse_reply(text):
    """Interpreta el texto del modelo como un objeto JSON.

    :param text: Texto devuelto por el modelo
    :type text: str
    :return: El objeto si es un diccionario JSON válido, si no ``None``
    :rtype: dict or None
    """
    try:
        reply = json.loads(text)
    except (TypeError, ValueError):
        return None
    return reply if isinstance(reply, dict) else None
