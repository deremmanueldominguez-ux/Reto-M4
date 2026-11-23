"""Pasos de los escenarios de ``features/ask.feature`` y ``search_by_name.feature``.

Ambos archivos comparten los pasos ``When`` y ``Then``; por eso viven en un solo módulo.
"""

from pytest_bdd import given, parsers, scenarios, then, when

scenarios("features/ask.feature")
scenarios("features/search_by_name.feature")

HISTORY = [
    {"role": "user", "content": "Hola"},
    {"role": "assistant", "content": "Hola, ¿en qué te ayudo?"},
]


@given("the HR assistant is running", target_fixture="client")
def running_assistant(make_client):
    """El asistente con la configuración por omisión."""
    return make_client()


@given(
    parsers.parse("the HR assistant is running with at most {steps:d} agent step"),
    target_fixture="client",
)
def running_assistant_with_step_cap(make_client, steps):
    """El asistente con el bucle limitado a ``steps`` vueltas."""
    return make_client(max_steps=steps)


@given("the HR assistant is running with name search", target_fixture="client")
def running_assistant_with_name_search(make_client):
    """El asistente con el modelo armado por ``build_model``, que conoce los nombres."""
    return make_client(built_model=True)


@given(
    parsers.parse(
        "the HR assistant is running with name search and at most {steps:d} agent step"
    ),
    target_fixture="client",
)
def running_assistant_with_name_search_and_step_cap(make_client, steps):
    """El asistente con búsqueda por nombre y el bucle limitado a ``steps`` vueltas."""
    return make_client(max_steps=steps, built_model=True)


@when(parsers.parse('I ask "{question}"'), target_fixture="response")
def ask_question(client, question):
    """Envía una pregunta sin historial."""
    return client.post("/ask", json={"question": question})


@when("I send an empty question", target_fixture="response")
def ask_empty_question(client):
    """Envía una pregunta vacía."""
    return client.post("/ask", json={"question": ""})


@when(
    parsers.parse("I send a question of {length:d} characters"),
    target_fixture="response",
)
def ask_long_question(client, length):
    """Envía una pregunta de ``length`` caracteres."""
    return client.post("/ask", json={"question": "a" * length})


@when(
    parsers.parse('I ask "{question}" in two requests with the same history'),
    target_fixture="responses",
)
def ask_twice_with_history(client, question):
    """Envía la misma pregunta e historial en dos peticiones independientes."""
    payload = {"question": question, "history": HISTORY}
    return [client.post("/ask", json=payload) for _ in range(2)]


@then(parsers.parse("the response status is {status:d}"))
def response_status_is(response, status):
    """Comprueba el código HTTP."""
    assert response.status_code == status


@then(parsers.parse('the answer mentions "{text}"'))
def answer_mentions(response, text):
    """Comprueba que la respuesta contiene ``text``."""
    assert text in response.json()["answer"]


@then(parsers.parse('the answer is exactly "{text}"'))
def answer_is_exactly(response, text):
    """Comprueba la respuesta literal."""
    assert response.json()["answer"] == text


@then(parsers.parse('the tools used are "{tools}"'))
def tools_used_are(response, tools):
    """Comprueba la lista de herramientas, separadas por comas."""
    assert response.json()["tools_used"] == tools.split(",")


@then("no tools were used")
def no_tools_were_used(response):
    """Comprueba que el agente no usó herramientas."""
    assert response.json()["tools_used"] == []


@then(parsers.parse("the agent took {steps:d} steps"))
def agent_took_steps(response, steps):
    """Comprueba cuántas veces se llamó al modelo."""
    assert response.json()["steps"] == steps


@then("both responses succeed with the same answer and steps")
def both_responses_match(responses):
    """Sin estado: la segunda petición no ve nada de la primera."""
    first, second = responses
    assert first.status_code == second.status_code == 200
    assert first.json()["answer"] == second.json()["answer"]
    assert first.json()["steps"] == second.json()["steps"] == 2
