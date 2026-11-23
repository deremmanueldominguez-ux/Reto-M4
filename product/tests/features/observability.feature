Feature: Trace what happened with any request
  Support staff receive a request id from a person and use it to find,
  in the JSON log and in the metrics, what happened with that request.

  Scenario: A request without an id gets a generated UUID
    Given the observed HR assistant is running
    When I check the health without a request id
    Then the response carries a generated UUID request id

  Scenario: The client request id is kept in the header and the body
    Given the observed HR assistant is running
    When I ask "¿Quién es EMP-0004?" with request id "demo-123"
    Then the response status is 200
    And the response header request id is "demo-123"
    And the response body request id is "demo-123"

  Scenario: A rejected question also carries the request id
    Given the observed HR assistant is running
    When I send an empty question with request id "bad-input-1"
    Then the response status is 422
    And the response header request id is "bad-input-1"

  Scenario: A question is logged by request id without its text
    Given the observed HR assistant is running
    When I ask "¿Quién es EMP-0004?" with request id "trace-42"
    Then the log has one "audit" event for tool "get_employee" with request id "trace-42"
    And the log has one "agent_run" event with request id "trace-42"
    And the log has a "request" event for "POST" "/ask" with status 200 and request id "trace-42"
    And no log line contains the question, the answer or the employee data

  Scenario: A model failure returns an internal error with the request id
    Given the observed HR assistant is running with a failing model
    When I ask "¿Quién es EMP-0004?" with request id "boom-7"
    Then the response status is 500
    And the response body is the internal error for request id "boom-7"
    And the log has an "error" event of type "RuntimeError" with request id "boom-7"
    And the log has a "request" event for "POST" "/ask" with status 500 and request id "boom-7"
    And no log line contains the failure message

  Scenario Outline: Metrics report requests, tokens, latency and the SLO
    Given the observed HR assistant is running with a model that takes <delay> ms and an SLO of 2000 ms
    When I ask "¿Quién es EMP-0004?" twice
    And I request the metrics
    Then the metrics count at least 2 requests and no errors
    And the metrics report input and output tokens above zero
    And the metrics p95 latency is <p95> ms
    And the metrics say the SLO met is <met>

    Examples:
      | delay | p95  | met   |
      | 1500  | 3000 | false |
      | 400   | 800  | true  |
