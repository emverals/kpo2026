from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal

from pos.domain.errors import DomainError
from pos.domain.factory import EvaluationFactory
from pos.domain.model import (
    Criterion,
    Evaluation,
    EvaluationSheet,
    FinalScore,
    Rubric,
    Score,
    Student,
)


def d(value: str) -> Decimal:
    return Decimal(value)


class ScoreTests(unittest.TestCase):
    def test_accepts_zero_and_fraction(self) -> None:
        self.assertEqual(d("0"), Score(d("0")).value)
        self.assertEqual(d("7.5"), Score(d("7.5")).value)

    def test_rejects_negative(self) -> None:
        with self.assertRaises(DomainError):
            Score(d("-0.1"))

    def test_rejects_nan(self) -> None:
        with self.assertRaises(DomainError):
            Score(Decimal("NaN"))

    def test_rejects_infinity(self) -> None:
        with self.assertRaises(DomainError):
            Score(Decimal("Infinity"))


class StudentTests(unittest.TestCase):
    def test_accepts_valid_name(self) -> None:
        student = Student(1, "  Иван Иванов  ")
        self.assertEqual("Иван Иванов", student.name)

    def test_rejects_empty_name(self) -> None:
        with self.assertRaises(DomainError):
            Student(1, "   ")

    def test_rejects_non_string_name(self) -> None:
        with self.assertRaises(DomainError):
            Student(1, 42)  # type: ignore[arg-type]


class CriterionTests(unittest.TestCase):
    def test_accepts_valid(self) -> None:
        criterion = Criterion(1, "Активность", d("5"), d("1.5"))
        self.assertEqual(d("5"), criterion.max_score)
        self.assertEqual(d("1.5"), criterion.weight)

    def test_rejects_empty_name(self) -> None:
        with self.assertRaises(DomainError):
            Criterion(1, "", d("5"), d("1"))

    def test_rejects_zero_max_score(self) -> None:
        with self.assertRaises(DomainError):
            Criterion(1, "Активность", d("0"), d("1"))

    def test_rejects_negative_max_score(self) -> None:
        with self.assertRaises(DomainError):
            Criterion(1, "Активность", d("-3"), d("1"))

    def test_rejects_non_positive_weight(self) -> None:
        with self.assertRaises(DomainError):
            Criterion(1, "Активность", d("5"), d("0"))

    def test_rejects_non_finite_max_score(self) -> None:
        with self.assertRaises(DomainError):
            Criterion(1, "Активность", Decimal("NaN"), d("1"))


class RubricTests(unittest.TestCase):
    def make_criterion(self, cid: int, name: str) -> Criterion:
        return Criterion(cid, name, d("5"), d("1"))

    def test_add_and_next_id(self) -> None:
        rubric = Rubric()
        rubric.add(self.make_criterion(1, "Активность"))
        rubric.add(self.make_criterion(2, "Домашние работы"))
        self.assertEqual(3, rubric.next_id())
        self.assertEqual(2, len(rubric))

    def test_rejects_duplicate_id(self) -> None:
        rubric = Rubric()
        rubric.add(self.make_criterion(1, "Активность"))
        with self.assertRaises(DomainError):
            rubric.add(self.make_criterion(1, "Другое"))

    def test_rejects_duplicate_name(self) -> None:
        rubric = Rubric()
        rubric.add(self.make_criterion(1, "Активность"))
        with self.assertRaises(DomainError):
            rubric.add(self.make_criterion(2, "активность"))

    def test_missing_criterion_raises(self) -> None:
        rubric = Rubric()
        with self.assertRaises(DomainError):
            rubric.criterion(7)

    def test_total_weight(self) -> None:
        rubric = Rubric()
        rubric.add(Criterion(1, "А", d("5"), d("1")))
        rubric.add(Criterion(2, "Б", d("10"), d("3")))
        self.assertEqual(d("4"), rubric.total_weight())


class EvaluationSheetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rubric = Rubric()
        self.rubric.add(Criterion(1, "Активность", d("5"), d("1")))
        self.rubric.add(Criterion(2, "Домашние работы", d("10"), d("3")))

    def make_evaluation(
        self, student_id: int, criterion_id: int, value: str
    ) -> Evaluation:
        return Evaluation(
            student_id=student_id,
            criterion=self.rubric.criterion(criterion_id),
            score=Score(Decimal(value)),
        )

    def test_put_and_find(self) -> None:
        sheet = EvaluationSheet()
        evaluation = self.make_evaluation(1, 1, "4")
        sheet.put(evaluation, self.rubric)
        self.assertIs(evaluation, sheet.find(1, 1))
        self.assertIsNone(sheet.find(1, 2))

    def test_upsert_replaces(self) -> None:
        sheet = EvaluationSheet()
        sheet.put(self.make_evaluation(1, 1, "4"), self.rubric)
        sheet.put(self.make_evaluation(1, 1, "5"), self.rubric)
        self.assertEqual(d("5"), sheet.find(1, 1).score.value)
        self.assertEqual(1, len(sheet.all()))

    def test_require_missing_raises(self) -> None:
        sheet = EvaluationSheet()
        with self.assertRaises(DomainError):
            sheet.require(1, 1)

    def test_remove_missing_raises(self) -> None:
        sheet = EvaluationSheet()
        with self.assertRaises(DomainError):
            sheet.remove(1, 1)

    def test_remove_existing(self) -> None:
        sheet = EvaluationSheet()
        sheet.put(self.make_evaluation(1, 1, "4"), self.rubric)
        sheet.remove(1, 1)
        self.assertIsNone(sheet.find(1, 1))

    def test_for_student_filters(self) -> None:
        sheet = EvaluationSheet()
        sheet.put(self.make_evaluation(1, 1, "4"), self.rubric)
        sheet.put(self.make_evaluation(2, 1, "3"), self.rubric)
        self.assertEqual(1, len(sheet.for_student(1)))


class InvariantBypassTests(unittest.TestCase):
    """Обходы доменных инвариантов вне фабрики и консоли."""

    def test_student_is_immutable(self) -> None:
        student = Student(1, "Иван")
        with self.assertRaises(FrozenInstanceError):
            student.name = "Другой"

    def test_criterion_is_immutable(self) -> None:
        criterion = Criterion(1, "Активность", d("5"), d("1"))
        with self.assertRaises(FrozenInstanceError):
            criterion.max_score = d("0")

    def test_direct_evaluation_rejects_score_above_max(self) -> None:
        criterion = Criterion(1, "Активность", d("5"), d("1"))
        with self.assertRaises(DomainError) as ctx:
            Evaluation(1, criterion, Score(d("100")))
        self.assertIn("превышает максимум", str(ctx.exception))

    def test_sheet_put_rejects_criterion_outside_rubric(self) -> None:
        rubric = Rubric()
        rubric.add(Criterion(1, "Активность", d("5"), d("1")))
        outsider = Criterion(9, "Сторонний", d("5"), d("1"))
        sheet = EvaluationSheet()
        with self.assertRaises(DomainError) as ctx:
            sheet.put(Evaluation(1, outsider, Score(d("3"))), rubric)
        self.assertIn("не найден в рубрикаторе", str(ctx.exception))

    def test_sheet_put_accepts_criterion_from_rubric(self) -> None:
        rubric = Rubric()
        rubric.add(Criterion(1, "Активность", d("5"), d("1")))
        sheet = EvaluationSheet()
        sheet.put(Evaluation(1, rubric.criterion(1), Score(d("3"))), rubric)
        self.assertEqual(1, len(sheet.all()))

    def test_sheet_put_rejects_substituted_criterion(self) -> None:
        rubric = Rubric()
        rubric.add(Criterion(1, "Real", d("5"), d("1")))
        fake = Criterion(1, "Fake", d("1000"), d("1"))
        sheet = EvaluationSheet()
        with self.assertRaises(DomainError):
            sheet.put(Evaluation(1, fake, Score(d("999"))), rubric)

    def test_rejected_put_preserves_previous_evaluation(self) -> None:
        rubric = Rubric()
        rubric.add(Criterion(1, "Real", d("5"), d("1")))
        sheet = EvaluationSheet()
        good = Evaluation(1, rubric.criterion(1), Score(d("4")))
        sheet.put(good, rubric)
        fake = Criterion(1, "Fake", d("1000"), d("1"))
        with self.assertRaises(DomainError):
            sheet.put(Evaluation(1, fake, Score(d("999"))), rubric)
        stored = sheet.find(1, 1)
        self.assertIs(good, stored)
        self.assertEqual(d("4"), stored.score.value)


class FinalScoreTests(unittest.TestCase):
    def test_accepts_bounds(self) -> None:
        self.assertEqual(d("0"), FinalScore(d("0"), "взвешенная").value)
        self.assertEqual(d("10"), FinalScore(d("10"), "взвешенная").value)

    def test_rejects_above_ten(self) -> None:
        with self.assertRaises(DomainError):
            FinalScore(d("12"), "взвешенная")

    def test_rejects_negative(self) -> None:
        with self.assertRaises(DomainError):
            FinalScore(d("-1"), "взвешенная")


class EvaluationFactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rubric = Rubric()
        self.rubric.add(Criterion(1, "Активность", d("5"), d("1")))
        self.rubric.add(Criterion(2, "Домашние работы", d("10"), d("3")))
        self.factory = EvaluationFactory()

    def test_creates_valid_evaluation(self) -> None:
        evaluation = self.factory.create(self.rubric, 1, 2, d("7"), "хорошо")
        self.assertEqual(1, evaluation.student_id)
        self.assertEqual(2, evaluation.criterion_id)
        self.assertEqual(d("7"), evaluation.score.value)
        self.assertEqual("хорошо", evaluation.comment)

    def test_rejects_unknown_criterion(self) -> None:
        with self.assertRaises(DomainError):
            self.factory.create(self.rubric, 1, 99, d("3"))

    def test_rejects_score_above_max(self) -> None:
        with self.assertRaises(DomainError) as ctx:
            self.factory.create(self.rubric, 1, 1, d("6"))
        self.assertIn("превышает максимум", str(ctx.exception))

    def test_rejects_negative_score(self) -> None:
        with self.assertRaises(DomainError):
            self.factory.create(self.rubric, 1, 1, d("-1"))

    def test_rejects_non_finite_score(self) -> None:
        with self.assertRaises(DomainError):
            self.factory.create(self.rubric, 1, 1, Decimal("Infinity"))

    def test_accepts_boundary_scores(self) -> None:
        low = self.factory.create(self.rubric, 1, 1, d("0"))
        high = self.factory.create(self.rubric, 1, 1, d("5"))
        self.assertEqual(d("0"), low.score.value)
        self.assertEqual(d("5"), high.score.value)


if __name__ == "__main__":
    unittest.main()
