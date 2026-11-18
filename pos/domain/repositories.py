from __future__ import annotations

from abc import ABC, abstractmethod

from .errors import DomainError
from .model import EvaluationSheet, Rubric, Student


class StudentRepository(ABC):
    """Порт хранения студентов."""

    @abstractmethod
    def next_id(self) -> int: ...

    @abstractmethod
    def add(self, student: Student) -> None: ...

    @abstractmethod
    def find(self, student_id: int) -> Student | None: ...

    @abstractmethod
    def all(self) -> list[Student]: ...

    def get(self, student_id: int) -> Student:
        student = self.find(student_id)
        if student is None:
            raise DomainError(f"Студент с id {student_id} не найден.")
        return student


class RubricRepository(ABC):
    """Порт хранения рубрикатора (агрегат целиком)."""

    @abstractmethod
    def load(self) -> Rubric: ...

    @abstractmethod
    def save(self, rubric: Rubric) -> None: ...


class EvaluationSheetRepository(ABC):
    """Порт хранения листа оценок (агрегат целиком)."""

    @abstractmethod
    def load(self) -> EvaluationSheet: ...

    @abstractmethod
    def save(self, sheet: EvaluationSheet) -> None: ...
