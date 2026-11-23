Feature: Debug mode without leaks
  With LOG_LEVEL=debug the log explains a failure step by step, and it still never
  shows a credential or the text of a question or an answer.

  Scenario: The info level writes exactly the session 2 log
    Given the HR assistant is running with log level "info"
    When I ask "¿Quién es EMP-0004?" with request id "req-info-1"
    Then the log has only the "audit", "agent_run" and "request" events with their session 2 fields
    And the log is identical to the log of an assistant without LOG_LEVEL

  Scenario: The debug level adds agent steps and model calls with their fields only
    Given the HR assistant is running with log level "debug" and a model that takes 250 ms
    When I ask "¿Quién es EMP-0004?" with request id "req-debug-1"
    Then the log has 2 "agent_step" events that took 250 ms each
    And the log has 2 "model_call" events with status "ok" that took 250 ms each
    And every debug event carries only its whitelisted fields
    And no log line contains the question, the answer or the employee data

  Scenario: The startup event says whether each secret is set and never its value
    Given the HR assistant is running with log level "debug"
    Then the log has one "startup" event with request id "-"
    And the startup event describes the environment, the provider and the log level
    And the startup credentials are "API_KEYS=set", "CF_API_TOKEN=unset" and "LANGSMITH_API_KEY=unset"
    And no log line contains the API key of the test client

  Scenario Outline: A failure leaves an error event with stack frames and without its message
    Given the HR assistant is running with log level "debug" and <failure>
    When I ask "¿Quién es EMP-0004?" with request id "req-fail-1"
    Then the response status is <status>
    And the log has an "error" event of type "<error_type>" with stack frames
    And no log line contains the failure message

    Examples:
      | failure              | status | error_type            |
      | a failing model      | 500    | RuntimeError          |
      | a gateway that fails | 502    | ModelUnavailableError |

  Scenario: An unknown log level prevents start
    When the assistant starts with LOG_LEVEL "verbose"
    Then the start fails with a configuration error about LOG_LEVEL

  Scenario: Production refuses to start in debug mode without showing any key
    Given a production environment that follows every rule
    When the assistant starts in production with LOG_LEVEL "debug"
    Then the start fails with a configuration error that does not show any key
