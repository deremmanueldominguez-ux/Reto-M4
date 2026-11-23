"""Pruebas del modelo simulado (``MODEL_PROVIDER=fake``)."""

import json

import pytest

from app.llm import FakeModel

DEPARTMENTS = ["Tecnología", "Ventas", "Finanzas"]


@pytest.fixture
def model():
    """Modelo simulado que conoce los departamentos de prueba."""
    return FakeModel(DEPARTMENTS)


def reply(model, *contents):
    """Llama al modelo con mensajes ``user`` y devuelve el JSON que respondió."""
    messages = [{"role": "user", "content": content} for content in contents]
    return json.loads(model.complete(messages).text)


def test_tool_result_is_answered_even_if_it_contains_an_id(model):
    result = '{"id": "EMP-0004", "name": "Jorge Díaz"}'
    tool_message = f"Resultado de la herramienta: {result}"
    body = reply(model, "¿Quién es EMP-0004?", tool_message)
    assert body == {"answer": f"Según el directorio: {result}"}


def test_employee_id_requests_get_employee(model):
    body = reply(model, "¿Quién es EMP-0004?")
    assert body == {"tool": "get_employee", "args": {"employee_id": "EMP-0004"}}


def test_known_department_requests_search_by_department(model):
    body = reply(model, "¿Quiénes trabajan en Finanzas?")
    assert body == {
        "tool": "search_by_department",
        "args": {"department": "Finanzas"},
    }


def test_other_questions_get_help_and_words_are_counted_as_tokens(model):
    messages = [
        {"role": "system", "content": "uno dos tres"},
        {"role": "user", "content": "hola"},
    ]
    completion = model.complete(messages)
    help_text = "Pregúntame por un empleado (EMP-0001) o un departamento."
    assert json.loads(completion.text) == {"answer": help_text}
    assert completion.input_tokens == 4
    assert completion.output_tokens == len(completion.text.split())


# Regla 4 del simulado: búsqueda por nombre.

NAMES = ["Ana López", "Luis Pérez", "Marta Ruiz", "Jorge Díaz", "Sofía Gómez"]
HELP = {"answer": "Pregúntame por un empleado (EMP-0001) o un departamento."}


@pytest.fixture
def name_model():
    """Modelo simulado que conoce departamentos y nombres de prueba."""
    return FakeModel(DEPARTMENTS, NAMES)


def search_by_name(name):
    """Respuesta esperada cuando el simulado pide ``search_by_name``."""
    return {"tool": "search_by_name", "args": {"name": name}}


def test_first_name_requests_search_by_name(name_model):
    assert reply(name_model, "¿Quién es Sofía?") == search_by_name("Sofía")


def test_surname_without_accent_is_sent_as_written_in_the_data(name_model):
    assert reply(name_model, "¿Quién es Lopez?") == search_by_name("López")


def test_full_name_is_sent_whole(name_model):
    body = reply(name_model, "¿qué rol tiene jorge diaz?")
    assert body == search_by_name("Jorge Díaz")


def test_common_words_and_short_name_parts_get_the_help_answer():
    model = FakeModel(DEPARTMENTS, NAMES + ["Al Bo"])
    assert reply(model, "¿Cuántos días de vacaciones tengo?") == HELP
    assert reply(model, "¿Quién es Al?") == HELP
    assert reply(model, "¿Quién es Mar?") == HELP


def test_id_and_department_rules_win_over_the_name_rule(name_model):
    by_id = reply(name_model, "¿EMP-0004 es Ana?")
    assert by_id == {"tool": "get_employee", "args": {"employee_id": "EMP-0004"}}
    by_department = reply(name_model, "¿Ana trabaja en Tecnología?")
    assert by_department == {
        "tool": "search_by_department",
        "args": {"department": "Tecnología"},
    }


def test_tool_result_with_a_name_is_still_answered(name_model):
    result = '[{"id": "EMP-0005", "name": "Sofía Gómez"}]'
    tool_message = f"Resultado de la herramienta: {result}"
    body = reply(name_model, "¿Quién es Sofía?", tool_message)
    assert body == {"answer": f"Según el directorio: {result}"}


def test_model_without_names_never_searches_by_name(model):
    assert reply(model, "¿Quién es Sofía?") == HELP


def test_build_model_gives_the_fake_model_the_employee_names(
    employees_file, directory
):
    # pylint: disable=import-outside-toplevel
    from app.config import load_settings
    from app.llm import build_model

    settings = load_settings(
        {"MODEL_PROVIDER": "fake", "EMPLOYEES_PATH": str(employees_file)}
    )
    model = build_model(settings, directory)
    assert reply(model, "¿Quién es Sofía?") == search_by_name("Sofía")
