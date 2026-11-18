from __future__ import annotations

from ..domain.errors import DomainError
from ..domain.model import EvaluationSheet, Rubric, Student
from ..domain.repositories import (
    EvaluationSheetRepository,
    RubricRepository,
    StudentRepository,
)


class InMemoryStudentRepository(StudentRepository):
    """Хранение студентов в памяти процесса."""

    def __init__(self) -> None:
        self._students: dict[int, Student] = {}
        self._counter = 0

    def next_id(self) -> int:
        self._counter += 1
        return self._counter

    def add(self, student: Student) -> None:
        if student.id in self._students:
            raise DomainError(f"Студент с id {student.id} уже существует.")
        self._students[student.id] = student

    def find(self, student_id: int) -> Student | None:
        return self._students.get(student_id)

    def all(self) -> list[Student]:
        return sorted(self._students.values(), key=lambda item: item.id)


class InMemoryRubricRepository(RubricRepository):
    """Хранение агрегата рубрикатора в памяти процесса."""

    def __init__(self) -> None:
        self._rubric = Rubric()

    def load(self) -> Rubric:
        return self._rubric

    def save(self, rubric: Rubric) -> None:
        self._rubric = rubric


class InMemoryEvaluationSheetRepository(EvaluationSheetRepository):
    """Хранение агрегата листа оценок в памяти процесса."""

    def __init__(self) -> None:
        self._sheet = EvaluationSheet()

    def load(self) -> EvaluationSheet:
        return self._sheet

    def save(self, sheet: EvaluationSheet) -> None:
        self._sheet = sheet
