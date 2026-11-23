"""Pruebas de punta a punta de la página del asistente (spec/04-production.md).

El producto corre con el modelo simulado; la URL base la pone la verificación.
La clave válida se lee de la variable ``E2E_API_KEY``; nunca se escribe aquí.
"""

import os
import re

from playwright.sync_api import Page, expect

FIRST_QUESTION = "¿Quién es EMP-0001?"
SECOND_QUESTION = "¿Y quién es EMP-0002?"
SPANISH_ERROR_PATTERN = re.compile(r"\b(pregunta|escribe|vac[ií]a)\b", re.IGNORECASE)
INVALID_KEY_MESSAGE = "Clave inválida"


def enter_api_key(page: Page, api_key=None):
    """Escribe la clave en el campo ``api-key`` de la página.

    :param page: Página de Playwright ya abierta en el asistente
    :type page: playwright.sync_api.Page
    :param api_key: Clave a escribir; por omisión, la de ``E2E_API_KEY``
    :type api_key: str or None
    """
    key = api_key if api_key is not None else os.environ["E2E_API_KEY"]
    page.get_by_test_id("api-key").fill(key)


def ask(page: Page, question):
    """Escribe una pregunta, la envía y devuelve el cuerpo JSON de ``/ask``.

    :param page: Página de Playwright ya abierta en el asistente
    :type page: playwright.sync_api.Page
    :param question: Pregunta a enviar
    :type question: str
    :return: Respuesta JSON de ``POST /ask``
    :rtype: dict
    """
    page.get_by_test_id("question").fill(question)
    with page.expect_response(
        lambda response: response.url.endswith("/ask")
        and response.request.method == "POST"
    ) as response_info:
        page.get_by_test_id("send").click()
    response = response_info.value
    assert response.ok, f"/ask respondió {response.status}"
    return response.json()


def test_sending_a_question_shows_the_answer_and_its_request_id(page: Page):
    """Con la clave, al enviar una pregunta se ven la respuesta y su ``request_id``."""
    page.goto("/")
    enter_api_key(page)

    data = ask(page, FIRST_QUESTION)

    conversation = page.get_by_test_id("answer")
    expect(conversation).to_contain_text(FIRST_QUESTION)
    expect(conversation).to_contain_text(data["answer"])
    assert data["request_id"], "la respuesta no trae request_id"
    expect(page.get_by_test_id("request-id")).to_contain_text(data["request_id"])


def test_empty_question_shows_an_error_message_in_spanish(page: Page):
    """Enviar una pregunta vacía muestra un mensaje de error en español."""
    page.goto("/")
    enter_api_key(page)

    page.get_by_test_id("question").fill("   ")
    page.get_by_test_id("send").click()

    expect(page.get_by_test_id("answer")).to_contain_text(SPANISH_ERROR_PATTERN)


def test_second_question_keeps_the_previous_conversation_on_screen(page: Page):
    """Una segunda pregunta no borra la conversación anterior."""
    page.goto("/")
    enter_api_key(page)

    first = ask(page, FIRST_QUESTION)
    conversation = page.get_by_test_id("answer")
    expect(conversation).to_contain_text(first["answer"])

    second = ask(page, SECOND_QUESTION)

    expect(conversation).to_contain_text(SECOND_QUESTION)
    expect(conversation).to_contain_text(second["answer"])
    expect(conversation).to_contain_text(FIRST_QUESTION)
    expect(conversation).to_contain_text(first["answer"])
    expect(page.get_by_test_id("request-id")).to_contain_text(second["request_id"])


def test_api_key_field_hides_what_is_typed(page: Page):
    """El campo de clave es de tipo contraseña."""
    page.goto("/")

    expect(page.get_by_test_id("api-key")).to_have_attribute("type", "password")


def test_wrong_api_key_shows_invalid_key_message(page: Page):
    """Una clave equivocada muestra «Clave inválida»."""
    page.goto("/")
    wrong_key = os.environ["E2E_API_KEY"] + "-wrong"
    enter_api_key(page, wrong_key)

    page.get_by_test_id("question").fill(FIRST_QUESTION)
    page.get_by_test_id("send").click()

    expect(page.get_by_test_id("answer")).to_contain_text(INVALID_KEY_MESSAGE)
