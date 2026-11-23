Feature: Publish the HR assistant safely
  Every client uses its own API key, nobody can spend the whole model quota, and a
  production deployment refuses to start when its configuration is not safe.

  Scenario: A question with a valid key is answered
    Given the secure HR assistant is running
    When client "acme" asks "¿Quién es EMP-0004?"
    Then the response status is 200
    And the response carries a request id

  Scenario: A question without a key is rejected
    Given the secure HR assistant is running
    When someone asks "¿Quién es EMP-0004?" without a key
    Then the response status is 401
    And the response body says the API key is invalid or missing
    And the response carries a request id

  Scenario Outline: A protected endpoint rejects a wrong or missing key
    Given the secure HR assistant is running
    When someone calls "<method>" "<path>" with the key "<key>"
    Then the response status is 401
    And the response body says the API key is invalid or missing
    And the response does not contain the key "<key>"

    Examples:
      | method | path     | key                     |
      | POST   | /ask     | wrong-key-9999999999999 |
      | GET    | /metrics | none                    |

  Scenario Outline: The public pages do not ask for a key
    Given the secure HR assistant is running
    When someone opens "<path>" without a key
    Then the response status is 200

    Examples:
      | path    |
      | /       |
      | /health |
      | /docs   |

  Scenario: Too many questions in a minute are limited until the window frees up
    Given the secure HR assistant is running with a limit of 2 requests per minute
    When client "acme" asks "Hola" 2 times
    And client "acme" asks "Hola"
    Then the response status is 429
    And the response body says the rate limit was exceeded
    And the response asks to retry after 60 seconds
    When 61 seconds pass
    And client "acme" asks "Hola"
    Then the response status is 200

  Scenario: The rate limit of one client does not affect another client
    Given the secure HR assistant is running with a limit of 2 requests per minute
    When client "acme" asks "Hola" 2 times
    And client "acme" asks "Hola"
    Then the response status is 429
    When client "globex" asks "Hola"
    Then the response status is 200

  Scenario: The log names the client and never writes a key
    Given the secure HR assistant is running
    When client "acme" asks "¿Quién es EMP-0004?"
    And someone asks "Hola" with the wrong key "leaked-wrong-key-12345"
    Then the "request", "agent_run" and "audit" events name the client "acme"
    And no log line contains "leaked-wrong-key-12345" or the key of "acme"

  Scenario Outline: Production refuses to start with an unsafe configuration
    Given a production environment that follows every rule
    When the assistant starts with "<variable>" set to "<value>"
    Then the start fails with a configuration error that does not show any key

    Examples:
      | variable          | value                  |
      | MODEL_PROVIDER    | fake                   |
      | API_KEYS          | (empty)                |
      | API_KEYS          | acme:abcdefghijklmno   |
      | LANGSMITH_TRACING | true and inputs shown  |

  Scenario: Production starts when every rule is followed
    Given a production environment that follows every rule
    When the assistant starts
    Then client "acme" can ask "Hola" and gets status 200
