from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Sequence

from .errors import DomainError
from .model import Evaluation, EvaluationSheet, FinalScore, Rubric


class FinalScoreStrategy(ABC):
    """Стратегия расчёта итога: возвращает долю 0..1 от максимума курса."""

    name: str = ""

    @abstractmethod
    def calculate(
        self, rubric: Rubric, evaluations: Sequence[Evaluation]
    ) -> Decimal: ...


class WeightedTotalStrategy(FinalScoreStrategy):
    """Взвешенный итог: знаменатель равен сумме весов всех критериев,
    отсутствующие оценки дают нулевой вклад."""

    name = "взвешенная"

    def calculate(self, rubric: Rubric, evaluations: Sequence[Evaluation]) -> Decimal:
        if rubric.is_empty():
            raise DomainError(
                "Рубрикатор пуст: добавьте критерии, чтобы рассчитать итог."
            )
        by_criterion = {item.criterion_id: item for item in evaluations}
        numerator = Decimal(0)
        for criterion in rubric.all():
            evaluation = by_criterion.get(criterion.id)
            if evaluation is not None:
                numerator += (
                    evaluation.score.value / criterion.max_score
                ) * criterion.weight
        return numerator / rubric.total_weight()


class NormalizedAverageStrategy(FinalScoreStrategy):
    """Среднее нормализованное: средняя доля максимума по выставленным оценкам."""

    name = "средняя нормализованная"

    def calculate(self, rubric: Rubric, evaluations: Sequence[Evaluation]) -> Decimal:
        if rubric.is_empty():
            raise DomainError(
                "Рубрикатор пуст: добавьте критерии, чтобы рассчитать итог."
            )
        if not evaluations:
            return Decimal(0)
        total = sum(
            (
                item.score.value / rubric.criterion(item.criterion_id).max_score
                for item in evaluations
            ),
            Decimal(0),
        )
        return total / len(evaluations)


class FinalScoreService:
    """Domain Service: итог студента из его оценок и рубрикатора."""

    def __init__(self, strategy: FinalScoreStrategy) -> None:
        self._strategy = strategy

    def strategy_name(self) -> str:
        return self._strategy.name

    def use_strategy(self, strategy: FinalScoreStrategy) -> None:
        self._strategy = strategy

    def for_student(
        self, rubric: Rubric, sheet: EvaluationSheet, student_id: int
    ) -> FinalScore:
        share = self._strategy.calculate(rubric, sheet.for_student(student_id))
        return FinalScore(share * 10, self._strategy.name)
