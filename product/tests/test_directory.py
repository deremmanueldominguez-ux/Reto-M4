"""Pruebas del directorio de empleados de solo lectura."""


def test_employee_is_found_by_id_in_any_case(directory):
    assert directory.get_employee("EMP-0004")["name"] == "Jorge Díaz"
    assert directory.get_employee("emp-0004")["name"] == "Jorge Díaz"


def test_unknown_employee_is_reported(directory):
    result = directory.get_employee("EMP-9999")
    assert "name" not in result
    assert "EMP-9999" in result["error"]


def test_department_search_ignores_case_and_accents(directory):
    people = directory.search_by_department("tecnologia")
    names = {person["name"] for person in people}
    assert names == {"Ana López", "Marta Ruiz", "Jorge Díaz"}
    assert directory.search_by_department("Recursos Humanos") == []
    assert set(directory.departments()) == {"Tecnología", "Ventas", "Finanzas"}


# Búsqueda por nombre (plan: herramienta ``search_by_name``).


def names_of(people):
    """Nombres de una lista de empleados, en el orden recibido."""
    return [person["name"] for person in people]


def test_exact_name_returns_a_copy_of_the_employee(directory):
    people = directory.search_by_name("Ana López")
    assert names_of(people) == ["Ana López"]
    people[0]["name"] = "Cambiado"
    assert names_of(directory.search_by_name("Ana López")) == ["Ana López"]


def test_part_of_a_name_is_enough_to_find_the_employee(directory):
    assert names_of(directory.search_by_name("mar")) == ["Marta Ruiz"]


def test_name_search_ignores_case_accents_and_extra_spaces(directory):
    assert names_of(directory.search_by_name("SOFIA")) == ["Sofía Gómez"]
    assert names_of(directory.search_by_name("gomez")) == ["Sofía Gómez"]
    assert names_of(directory.search_by_name("  ana   LOPEZ ")) == ["Ana López"]


def test_every_match_is_returned_in_file_order(directory):
    people = directory.search_by_name("ez")
    assert names_of(people) == ["Ana López", "Luis Pérez", "Sofía Gómez"]


def test_name_without_matches_is_reported_with_the_name_as_received(directory):
    result = directory.search_by_name("  Pedro  ")
    assert result == {"error": "No hay empleados cuyo nombre contenga Pedro."}


def test_name_search_needs_at_least_two_characters(directory):
    expected = {"error": "La búsqueda por nombre necesita al menos 2 caracteres."}
    assert directory.search_by_name("a") == expected
    assert directory.search_by_name("   é   ") == expected
    assert directory.search_by_name("") == expected


def test_names_are_listed_in_file_order(directory):
    assert directory.names() == [
        "Ana López",
        "Luis Pérez",
        "Marta Ruiz",
        "Jorge Díaz",
        "Sofía Gómez",
    ]
