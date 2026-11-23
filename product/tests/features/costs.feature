Feature: Know and lower the cost of every answer
  Each answer says which model it used, why, and how much it cost, so the cost
  levers can be measured without lowering the quality of the answers.

  Scenario: A short question goes to the small model and has a cost
    Given the costed HR assistant is running
    When I ask "¿Quién es EMP-0001?"
    Then the response status is 200
    And the answer used the model "small-model" with route "short_question"
    And the cost is the price of "small-model" for the reported tokens

  Scenario Outline: A demanding question goes to the large model
    Given the costed HR assistant is running
    When I ask "<question>"
    Then the response status is 200
    And the answer used the model "large-model" with route "<route>"

    Examples:
      | question                                                                                | route           |
      | Compara Tecnología y Ventas                                                             | keyword:compara |
      | Necesito saber en qué departamento trabaja actualmente la persona con el id EMP-0001 hoy | long_question   |

  Scenario: With routing off every question goes to the large model
    Given the costed HR assistant is running with routing off
    When I ask "¿Quién es EMP-0001?"
    Then the answer used the model "large-model" with route "routing_off"

  Scenario: The history window lowers input tokens without changing the answer
    Given one costed HR assistant with a history window of 6 and another of 1000
    When both are asked "¿Quién es EMP-0001?" with 10 history messages
    Then the windowed assistant used fewer input tokens
    And both assistants gave the same answer

  Scenario: The metrics accumulate the cost of every answer
    Given the costed HR assistant is running
    When I ask two questions "¿Quién es EMP-0001?" and "¿Quién trabaja en Ventas?"
    Then the metrics cost is the sum of both answer costs

  Scenario: A call served by the gateway cache is counted and costs nothing
    Given the HR assistant is running on a gateway that answers from its cache
    When I ask "Hola"
    Then the response status is 200
    And the answer reports 1 cached call and a cost of 0

  Scenario: A gateway failure returns model unavailable with the request id
    Given the HR assistant is running on a gateway that fails
    When I ask with request id "gw-down-1" the question "Hola"
    Then the response status is 502
    And the response body is model unavailable for request id "gw-down-1"
