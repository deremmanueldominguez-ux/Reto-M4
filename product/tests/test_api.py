"""Pruebas de la API creada con ``create_app()`` y dependencias inyectadas."""

import os


def test_health_reports_ok_and_the_process_id(make_client):
    response = make_client().get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "pid": os.getpid()}


def test_home_page_has_the_form_and_never_uses_inner_html(make_client):
    response = make_client().get("/")
    assert response.status_code == 200
    page = response.text
    for test_id in ("question", "send", "answer"):
        assert f'data-testid="{test_id}"' in page
    assert "textContent" in page
    assert "innerHTML" not in page


def test_home_page_shows_the_request_id_of_each_response(make_client):
    page = make_client().get("/").text
    assert 'data-testid="request-id"' in page
    assert "request_id" in page
    assert "X-Request-ID" in page


def test_metrics_report_this_process_and_exclude_their_own_request(
    make_observed_app,
):
    observed = make_observed_app()
    observed.client.get("/health")
    observed.client.post("/ask", json={"question": ""})
    metrics = observed.client.get("/metrics").json()
    assert metrics["pid"] == os.getpid()
    assert metrics["requests"] == 2
    assert metrics["error_rate"] == 0.0
    assert metrics["tokens"] == {"input": 0, "output": 0}
