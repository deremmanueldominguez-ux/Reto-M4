Feature: Search employees by name
  HR staff can ask about a person by first name, surname or full name,
  with or without accents, and the assistant uses search_by_name.
  Questions with an employee id or a department keep their tool.

  Scenario: Asking by first name uses search_by_name
    Given the HR assistant is running with name search
    When I ask "¿Quién es Sofía?"
    Then the response status is 200
    And the answer mentions "Sofía Gómez"
    And the tools used are "search_by_name"
    And the agent took 2 steps

  Scenario: Asking by surname without accent finds the employee
    Given the HR assistant is running with name search
    When I ask "¿Quién es Lopez?"
    Then the response status is 200
    And the answer mentions "Ana López"
    And the tools used are "search_by_name"

  Scenario: Asking by full name in lowercase finds the role
    Given the HR assistant is running with name search
    When I ask "¿qué rol tiene jorge diaz?"
    Then the response status is 200
    And the answer mentions "Líder técnico"
    And the tools used are "search_by_name"

  Scenario: An employee id wins over a name
    Given the HR assistant is running with name search
    When I ask "¿EMP-0004 es Ana?"
    Then the response status is 200
    And the answer mentions "Jorge Díaz"
    And the tools used are "get_employee"

  Scenario: A department wins over a name
    Given the HR assistant is running with name search
    When I ask "¿Ana trabaja en Tecnología?"
    Then the response status is 200
    And the tools used are "search_by_department"

  Scenario: The step cap also stops a name search
    Given the HR assistant is running with name search and at most 1 agent step
    When I ask "¿Quién es Sofía?"
    Then the response status is 200
    And the answer is exactly "No pude completar la respuesta. Intenta con una pregunta más concreta."
    And the agent took 1 steps
