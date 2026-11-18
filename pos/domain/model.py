from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from ..formatting import format_decimal
from .errors import DomainError


def _finite(value: Decimal, what: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise DomainError(f"{what}: ожидается число.")
    if not value.is_finite():
        raise DomainError(f"{what}: число должно быть конечным.")
    return value


def _positive(value: Decimal, what: str) -> Decimal:
    _finite(value, what)
    if value <= 0:
        raise DomainError(f"{what}: должно быть положительным числом.")
    return value


def _non_empty(text: object, what: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise DomainError(f"{what}: не может быть пустым.")
    return text.strip()


@dataclass(frozen=True)
class Score:
    """Балл: конечное неотрицательное число (value object)."""

    value: Decimal

    def __post_init__(self) -> None:
        _finite(self.value, "Балл")
        if self.value < 0:
            raise DomainError("Балл: не может быть отрицательным.")


@dataclass(frozen=True)
class FinalScore:
    """Итоговый балл студента: значение в диапазоне 0..10 и имя правила расчёта."""

    value: Decimal
    strategy: str

    def __post_init__(self) -> None:
        _finite(self.value, "Итоговый балл")
        if not 0 <= self.value <= 10:
            raise DomainError("Итоговый балл: должен быть в диапазоне от 0 до 10.")
        _non_empty(self.strategy, "Название правила итога")


@dataclass(frozen=True)
class Student:
    """Студент: сущность с идентификатором, неизменяемая после создания."""

    id: int
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _non_empty(self.name, "Имя студента"))


@dataclass(frozen=True)
class Criterion:
    """Критерий оценивания: максимум балла и вклад в итог, неизменяемый после создания."""

    id: int
    name: str
    max_score: Decimal
    weight: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _non_empty(self.name, "Название критерия"))
        _positive(self.max_score, "Максимальный балл критерия")
        _positive(self.weight, "Вес критерия")


@dataclass(frozen=True)
class Evaluation:
    """Оценка: студент, критерий, балл; дата и комментарий по желанию.

    Инвариант диапазона охраняется конструктором: оценка не может существовать
    с баллом выше максимума своего критерия."""

    student_id: int
    criterion: Criterion
    score: Score
    comment: str = ""
    date: date = field(default_factory=date.today)

    @property
    def criterion_id(self) -> int:
        return self.criterion.id

    def __post_init__(self) -> None:
        if self.score.value > self.criterion.max_score:
            raise DomainError(
                f"Балл {format_decimal(self.score.value)} превышает максимум критерия "
                f"«{self.criterion.name}» ({format_decimal(self.criterion.max_score)})."
            )


class Rubric:
    """Рубрикатор: агрегат-корень, владеет критериями и их уникальностью."""

    def __init__(self) -> None:
        self._criteria: dict[int, Criterion] = {}

    def add(self, criterion: Criterion) -> None:
        if criterion.id in self._criteria:
            raise DomainError(f"Критерий с id {criterion.id} уже существует.")
        if any(
            existing.name.lower() == criterion.name.lower()
            for existing in self._criteria.values()
        ):
            raise DomainError(
                f"Критерий с названием «{criterion.name}» уже существует."
            )
        self._criteria[criterion.id] = criterion

    def next_id(self) -> int:
        return max(self._criteria, default=0) + 1

    def criterion(self, criterion_id: int) -> Criterion:
        try:
            return self._criteria[criterion_id]
        except KeyError:
            raise DomainError(
                f"Критерий с id {criterion_id} не найден в рубрикаторе."
            ) from None

    def all(self) -> list[Criterion]:
        return sorted(self._criteria.values(), key=lambda item: item.id)

    def total_weight(self) -> Decimal:
        return sum((item.weight for item in self._criteria.values()), Decimal(0))

    def is_empty(self) -> bool:
        return not self._criteria

    def __len__(self) -> int:
        return len(self._criteria)


class EvaluationSheet:
    """Лист оценок: агрегат с ключом (студент, критерий), одна оценка на пару."""

    def __init__(self) -> None:
        self._items: dict[tuple[int, int], Evaluation] = {}

    def put(self, evaluation: Evaluation, rubric: Rubric) -> None:
        """Граница агрегата: оценка принимается только по каноническому критерию
        актуального рубрикатора; отклонение не меняет состояние листа."""
        canonical = rubric.criterion(evaluation.criterion_id)
        if canonical != evaluation.criterion:
            raise DomainError(
                f"Критерий «{evaluation.criterion.name}» не совпадает с критерием "
                f"«{canonical.name}» из рубрикатора."
            )
        key = (evaluation.student_id, evaluation.criterion_id)
        self._items[key] = evaluation

    def find(self, student_id: int, criterion_id: int) -> Evaluation | None:
        return self._items.get((student_id, criterion_id))

    def require(self, student_id: int, criterion_id: int) -> Evaluation:
        evaluation = self.find(student_id, criterion_id)
        if evaluation is None:
            raise DomainError(
                f"Оценка студента {student_id} по критерию {criterion_id} не выставлена."
            )
        return evaluation

    def remove(self, student_id: int, criterion_id: int) -> None:
        self.require(student_id, criterion_id)
        del self._items[(student_id, criterion_id)]

    def for_student(self, student_id: int) -> list[Evaluation]:
        return sorted(
            (item for (sid, _), item in self._items.items() if sid == student_id),
            key=lambda item: item.criterion_id,
        )

    def all(self) -> list[Evaluation]:
        return sorted(
            self._items.values(), key=lambda item: (item.student_id, item.criterion_id)
        )

    def __len__(self) -> int:
        return len(self._items)
