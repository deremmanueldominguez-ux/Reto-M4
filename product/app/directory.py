"""Directorio de empleados de solo lectura cargado desde un archivo JSON."""

import json
import unicodedata
from pathlib import Path

MIN_NAME_SEARCH_CHARS = 2


def normalize_text(text):
    """Normaliza un texto para comparar sin mayúsculas ni tildes.

    :param text: Texto original
    :type text: str
    :return: Texto en minúsculas, sin tildes y sin espacios en los extremos
    :rtype: str
    """
    decomposed = unicodedata.normalize("NFKD", text)
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return plain.casefold().strip()


def _collapse_spaces(text):
    """Reemplaza cualquier secuencia de espacios por un solo espacio.

    :param text: Texto original
    :type text: str
    :return: Texto con los espacios internos colapsados y sin espacios en los extremos
    :rtype: str
    """
    return " ".join(text.split())


class EmployeeDirectory:
    """Directorio de empleados inmutable durante la vida del proceso.

    :param path: Ruta del archivo JSON con la lista de empleados
    :type path: str or pathlib.Path
    """

    def __init__(self, path):
        with Path(path).open(encoding="utf-8") as handle:
            records = json.load(handle)
        self._employees = tuple(dict(record) for record in records)

    def get_employee(self, employee_id):
        """Busca un empleado por id sin distinguir mayúsculas.

        :param employee_id: Id del empleado, por ejemplo ``EMP-0004``
        :type employee_id: str
        :return: Copia del empleado o ``{"error": ...}`` si no existe
        :rtype: dict
        """
        wanted = str(employee_id).strip().upper()
        for employee in self._employees:
            if employee["id"].upper() == wanted:
                return dict(employee)
        return {"error": f"No existe un empleado con id {wanted}."}

    def search_by_department(self, department):
        """Lista los empleados de un departamento sin distinguir mayúsculas ni tildes.

        :param department: Nombre del departamento
        :type department: str
        :return: Copias de los empleados del departamento (vacía si no hay)
        :rtype: list[dict]
        """
        wanted = normalize_text(str(department))
        return [
            dict(employee)
            for employee in self._employees
            if normalize_text(employee["department"]) == wanted
        ]

    def search_by_name(self, name):
        """Busca empleados cuyo nombre contenga el texto, sin mayúsculas ni tildes.

        La búsqueda es parcial: basta con que el texto normalizado, con los espacios
        internos colapsados, sea subcadena del nombre completo normalizado.

        :param name: Texto a buscar dentro del nombre completo
        :type name: str
        :return: Copias de los empleados en el orden del archivo, o ``{"error": ...}``
            si el texto es muy corto o no hay coincidencias
        :rtype: list[dict] or dict
        """
        received = str(name).strip()
        wanted = _collapse_spaces(normalize_text(received))
        if len(wanted) < MIN_NAME_SEARCH_CHARS:
            return {
                "error": (
                    "La búsqueda por nombre necesita al menos "
                    f"{MIN_NAME_SEARCH_CHARS} caracteres."
                )
            }
        people = [
            dict(employee)
            for employee in self._employees
            if wanted in _collapse_spaces(normalize_text(employee["name"]))
        ]
        if not people:
            return {"error": f"No hay empleados cuyo nombre contenga {received}."}
        return people

    def names(self):
        """Devuelve los nombres completos de los empleados en orden de aparición.

        :return: Nombres completos
        :rtype: list[str]
        """
        return [employee["name"] for employee in self._employees]

    def departments(self):
        """Devuelve los departamentos existentes, sin repetir y en orden de aparición.

        :return: Nombres de los departamentos
        :rtype: list[str]
        """
        names = []
        for employee in self._employees:
            if employee["department"] not in names:
                names.append(employee["department"])
        return names
