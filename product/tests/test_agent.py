"""Pruebas del bucle del agente con un modelo guionizado (no el simulado)."""

import json

from app.agent import Agent
from app.llm import Completion

GIVE_UP = "No pude completar la respuesta. Intenta con una pregunta más concreta."


class ScriptedModel:
    """Modelo de prueba que devuelve respuestas fijas y guarda lo que recibió.

    :param replies: Textos que devolverá en orden; el último se repite
    :type replies: list[str]
    :param input_tokens: Tokens de entrada que informa en cada llamada
    :type input_tokens: int
    :param output_tokens: Tokens de salida que informa en cada llamada
    :type output_tokens: int
    """

    def __init__(self, replies, input_tokens=1, output_tokens=1):
        self.replies = list(replies)
        self.calls = []
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    def complete(self, messages):
        """Devuelve la siguiente respuesta guionizada.

        :param messages: Conversación enviada por el agente
        :type messages: list[dict]
        :return: Respuesta con tokens fijos
        :rtype: app.llm.Completion
        """
        self.calls.append([dict(message) for message in messages])
        index = min(len(self.calls), len(self.replies)) - 1
        return Completion(
            text=self.replies[index],
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
        )


def tool(tool_name, /, **args):
    """Respuesta del modelo que pide una herramienta.

    ``tool_name`` es solo posicional para que ``name=`` pueda ir en ``args``.
    """
    return json.dumps({"tool": tool_name, "args": args})


def answer(text):
    """Respuesta final del modelo."""
    return json.dumps({"answer": text})


def test_direct_answer_takes_one_step_and_sees_the_history(directory):
    model = ScriptedModel([answer("Hola")])
    history = [{"role": "user", "content": "Antes"}]
    result = Agent(model=model, directory=directory, max_steps=3).run(
        "¿Qué tal?", history=history
    )
    assert (result.answer, result.steps, result.tools_used) == ("Hola", 1, [])
    contents = [message["content"] for message in model.calls[0]]
    assert contents[-2:] == ["Antes", "¿Qué tal?"]


def test_tool_result_goes_back_to_the_model_and_tokens_are_summed(directory):
    model = ScriptedModel(
        [tool("get_employee", employee_id="EMP-0004"), answer("Listo")],
        input_tokens=10,
        output_tokens=4,
    )
    result = Agent(model=model, directory=directory, max_steps=3).run("EMP-0004")
    assert (result.answer, result.steps) == ("Listo", 2)
    assert result.tools_used == ["get_employee"]
    assert (result.input_tokens, result.output_tokens) == (20, 8)
    last = model.calls[1][-1]
    assert last["role"] == "user"
    assert last["content"].startswith("Resultado de la herramienta: ")
    assert "Jorge Díaz" in last["content"]


def test_loop_stops_at_the_step_cap_with_the_fixed_message(directory):
    model = ScriptedModel([tool("search_by_department", department="Ventas")])
    result = Agent(model=model, directory=directory, max_steps=3).run("Ventas")
    assert result.answer == GIVE_UP
    assert result.steps == 3
    assert len(model.calls) == 3


def test_invalid_json_and_unknown_tool_are_reported_and_use_a_step(directory):
    replies = ["esto no es JSON", tool("delete_employee"), answer("Ok")]
    model = ScriptedModel(replies)
    result = Agent(model=model, directory=directory, max_steps=3).run("Hola")
    assert (result.answer, result.steps) == ("Ok", 3)
    assert "delete_employee" not in result.tools_used
    assert len(model.calls[1]) > len(model.calls[0])
    assert len(model.calls[2]) > len(model.calls[1])


# Herramienta ``search_by_name`` registrada en el agente.


def test_search_by_name_runs_and_is_recorded_in_tools_used(directory):
    model = ScriptedModel([tool("search_by_name", name="sofia"), answer("Listo")])
    result = Agent(model=model, directory=directory, max_steps=3).run("Sofía")
    assert (result.answer, result.steps) == ("Listo", 2)
    assert result.tools_used == ["search_by_name"]
    last = model.calls[1][-1]["content"]
    assert last.startswith("Resultado de la herramienta: ")
    assert "Sofía Gómez" in last


def test_wrong_arguments_for_search_by_name_are_reported(directory):
    model = ScriptedModel([tool("search_by_name", nombre="x"), answer("Ok")])
    result = Agent(model=model, directory=directory, max_steps=3).run("x")
    assert result.tools_used == []
    notice = model.calls[1][-1]["content"]
    assert notice == "Argumentos inválidos para la herramienta search_by_name."


def test_unknown_tool_notice_names_the_three_tools(directory):
    model = ScriptedModel([tool("delete_employee"), answer("Ok")])
    Agent(model=model, directory=directory, max_steps=3).run("Hola")
    notice = model.calls[1][-1]["content"]
    assert notice == (
        "Herramienta desconocida: delete_employee. "
        "Usa get_employee, search_by_department o search_by_name."
    )


# Sesión 2: eventos ``audit`` y ``agent_run`` del agente.


class RecordingLog:  # pylint: disable=too-few-public-methods
    """Log de prueba con el ``request_id`` ya fijado: guarda cada evento."""

    def __init__(self):
        self.events = []

    def emit(self, event, **fields):
        """Guarda el evento y sus campos.

        :param event: Nombre del evento
        :type event: str
        """
        self.events.append((event, fields))

    def named(self, event):
        """Devuelve los campos de los eventos con ese nombre.

        :rtype: list[dict]
        """
        return [fields for name, fields in self.events if name == event]


def test_every_registered_tool_call_is_audited_even_with_invalid_args(directory):
    replies = [
        tool("search_by_name", nombre="x"),
        tool("delete_employee"),
        tool("get_employee", employee_id="EMP-0001"),
        answer("Ok"),
    ]
    log = RecordingLog()
    agent = Agent(
        model=ScriptedModel(replies), directory=directory, max_steps=4, log=log
    )
    agent.run("Hola")
    assert log.named("audit") == [
        {"action": "tool_call", "tool": "search_by_name", "args": {"nombre": "x"}},
        {
            "action": "tool_call",
            "tool": "get_employee",
            "args": {"employee_id": "EMP-0001"},
        },
    ]


def test_agent_run_reports_counts_and_never_the_text(directory):
    question = "¿Quién trabaja en Ventas?"
    history = [
        {"role": "user", "content": "Hola"},
        {"role": "assistant", "content": "Hola"},
    ]
    model = ScriptedModel(
        [tool("search_by_department", department="Ventas"), answer("Luis Pérez")],
        input_tokens=5,
        output_tokens=2,
    )
    log = RecordingLog()
    result = Agent(model=model, directory=directory, max_steps=3, log=log).run(
        question, history=history
    )
    assert result.stopped == "answer"
    assert log.named("agent_run") == [
        {
            "question_chars": len(question),
            "history_messages": 2,
            "steps": 2,
            "tools": ["search_by_department"],
            "input_tokens": 10,
            "output_tokens": 4,
            "stopped": "answer",
        }
    ]
    everything = json.dumps(log.events, ensure_ascii=False)
    assert question not in everything
    assert "Luis Pérez" not in everything


def test_reaching_the_step_cap_is_reported_as_stopped_by_max_steps(directory):
    model = ScriptedModel([tool("get_employee", employee_id="EMP-0002")])
    log = RecordingLog()
    result = Agent(model=model, directory=directory, max_steps=2, log=log).run("x")
    assert result.stopped == "max_steps"
    assert log.named("agent_run")[0]["stopped"] == "max_steps"
    assert len(log.named("audit")) == 2
