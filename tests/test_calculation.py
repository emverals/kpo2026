from __future__ import annotations

import unittest
from decimal import Decimal

from pos.domain.errors import DomainError
from pos.domain.factory import EvaluationFactory
from pos.domain.model import Criterion, EvaluationSheet, Rubric
from pos.domain.services import (
    FinalScoreService,
    NormalizedAverageStrategy,
    WeightedTotalStrategy,
)


def d(value: str) -> Decimal:
    return Decimal(value)


class CalculationTestCase(unittest.TestCase):
    """Рубрикатор: Активность (max 5, вес 1) и Домашние работы (max 10, вес 3)."""

    def setUp(self) -> None:
        self.rubric = Rubric()
        self.rubric.add(Criterion(1, "Активность", d("5"), d("1")))
        self.rubric.add(Criterion(2, "Домашние работы", d("10"), d("3")))
        self.factory = EvaluationFactory()
        self.sheet = EvaluationSheet()
        self.weighted = WeightedTotalStrategy()
        self.average = NormalizedAverageStrategy()

    def grade(self, student_id: int, criterion_id: int, value: str) -> None:
        self.sheet.put(
            self.factory.create(self.rubric, student_id, criterion_id, d(value)),
            self.rubric,
        )

    def final(self, service: FinalScoreService, student_id: int = 1) -> Decimal:
        return service.for_student(self.rubric, self.sheet, student_id).value


class WeightedTotalTests(CalculationTestCase):
    def test_full_scores_exact_value(self) -> None:
        self.grade(1, 1, "5")
        self.grade(1, 2, "5")
        service = FinalScoreService(self.weighted)
        self.assertEqual(d("6.25"), self.final(service))

    def test_missing_evaluation_zero_contribution_full_denominator(self) -> None:
        self.grade(1, 1, "5")
        service = FinalScoreService(self.weighted)
        self.assertEqual(d("2.5"), self.final(service))

    def test_zero_evaluations_give_zero(self) -> None:
        service = FinalScoreService(self.weighted)
        self.assertEqual(d("0"), self.final(service))

    def test_recalculation_after_fix(self) -> None:
        self.grade(1, 2, "5")
        service = FinalScoreService(self.weighted)
        self.assertEqual(d("3.75"), self.final(service))
        self.grade(1, 2, "8")
        self.assertEqual(d("6"), self.final(service))

    def test_recalculation_after_cancel(self) -> None:
        self.grade(1, 1, "5")
        self.grade(1, 2, "8")
        service = FinalScoreService(self.weighted)
        self.assertEqual(d("8.5"), self.final(service))
        self.sheet.remove(1, 2)
        self.assertEqual(d("2.5"), self.final(service))

    def test_result_never_above_ten(self) -> None:
        self.grade(1, 1, "5")
        self.grade(1, 2, "10")
        service = FinalScoreService(self.weighted)
        self.assertEqual(d("10"), self.final(service))


class NormalizedAverageTests(CalculationTestCase):
    def test_average_over_graded_only(self) -> None:
        self.grade(1, 1, "5")
        self.grade(1, 2, "5")
        service = FinalScoreService(self.average)
        self.assertEqual(d("7.5"), self.final(service))

    def test_no_evaluations_give_zero(self) -> None:
        service = FinalScoreService(self.average)
        self.assertEqual(d("0"), self.final(service))


class StrategySwitchTests(CalculationTestCase):
    def test_switch_changes_result(self) -> None:
        self.grade(1, 1, "5")
        self.grade(1, 2, "5")
        service = FinalScoreService(self.weighted)
        self.assertEqual("взвешенная", service.strategy_name())
        self.assertEqual(d("6.25"), self.final(service))
        service.use_strategy(self.average)
        self.assertEqual("средняя нормализованная", service.strategy_name())
        self.assertEqual(d("7.5"), self.final(service))


class EmptyRubricTests(CalculationTestCase):
    def test_weighted_raises_domain_error(self) -> None:
        self.rubric = Rubric()
        service = FinalScoreService(self.weighted)
        with self.assertRaises(DomainError) as ctx:
            self.final(service)
        self.assertIn("Рубрикатор пуст", str(ctx.exception))

    def test_average_raises_domain_error(self) -> None:
        self.rubric = Rubric()
        service = FinalScoreService(self.average)
        with self.assertRaises(DomainError) as ctx:
            self.final(service)
        self.assertIn("Рубрикатор пуст", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
