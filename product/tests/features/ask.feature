Feature: Ask the HR assistant about employees
  HR staff ask questions in a web page and the assistant answers
  using read-only tools over the employee directory.

  Scenario: Asking for an existing employee uses get_employee
    Given the HR assistant is running
    When I ask "¿Quién es EMP-0004?"
    Then the response status is 200
    And the answer mentions "Jorge Díaz"
    And the tools used are "get_employee"
    And the agent took 2 steps

  Scenario: Asking for an unknown employee still gets an answer
    Given the HR assistant is running
    When I ask "¿Quién es EMP-9999?"
    Then the response status is 200
    And the answer mentions "EMP-9999"
    And the tools used are "get_employee"

  Scenario: Asking for a department lists its people
    Given the HR assistant is running
    When I ask "¿Quiénes trabajan en Finanzas?"
    Then the response status is 200
    And the answer mentions "Sofía Gómez"
    And the tools used are "search_by_department"

  Scenario: A question without employee or department gets the help answer
    Given the HR assistant is running
    When I ask "¿Cuántos días de vacaciones tengo?"
    Then the response status is 200
    And the answer is exactly "Pregúntame por un empleado (EMP-0001) o un departamento."
    And no tools were used

  Scenario: An empty question is rejected
    Given the HR assistant is running
    When I send an empty question
    Then the response status is 422

  Scenario: A question longer than the limit is rejected
    Given the HR assistant is running
    When I send a question of 2001 characters
    Then the response status is 422

  Scenario: The history comes from the client and is not stored
    Given the HR assistant is running
    When I ask "¿Quién es EMP-0004?" in two requests with the same history
    Then both responses succeed with the same answer and steps

  Scenario: The step cap stops the loop
    Given the HR assistant is running with at most 1 agent step
    When I ask "¿Quién es EMP-0004?"
    Then the response status is 200
    And the answer is exactly "No pude completar la respuesta. Intenta con una pregunta más concreta."
    And the agent took 1 steps
