from __future__ import annotations

import csv
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from pos.adapters.csv_export import CsvResultsWriter
from pos.adapters.memory import (
    InMemoryEvaluationSheetRepository,
    InMemoryRubricRepository,
    InMemoryStudentRepository,
)
from pos.application.facade import PosFacade
from pos.domain.factory import EvaluationFactory
from pos.domain.model import Criterion
from pos.domain.services import FinalScoreService, WeightedTotalStrategy


def d(value: str) -> Decimal:
    return Decimal(value)


class ExportTests(unittest.TestCase):
    def setUp(self) -> None:
        students = InMemoryStudentRepository()
        rubrics = InMemoryRubricRepository()
        sheets = InMemoryEvaluationSheetRepository()
        rubric = rubrics.load()
        rubric.add(Criterion(rubric.next_id(), "Активность", d("5"), d("1")))
        rubric.add(Criterion(rubric.next_id(), "Домашние работы", d("10"), d("3")))
        self.facade = PosFacade(
            students=students,
            rubrics=rubrics,
            sheets=sheets,
            factory=EvaluationFactory(),
            score_service=FinalScoreService(WeightedTotalStrategy()),
            writer=CsvResultsWriter(),
        )
        self.ivan = self.facade.add_student("Иван Иванов")
        self.maria = self.facade.add_student("Мария Петрова")
        self.facade.set_evaluation(self.ivan.id, 1, d("5"), "активно")
        self.facade.set_evaluation(self.ivan.id, 2, d("5"))

    def test_export_rows_and_header(self) -> None:
        rows = self.facade.export_rows()
        self.assertEqual(
            ["id", "Студент", "Активность", "Домашние работы", "Итог (0-10)"],
            rows[0],
        )
        self.assertEqual(["1", "Иван Иванов", "5", "5", "6.25"], rows[1])
        self.assertEqual(["2", "Мария Петрова", "", "", "0"], rows[2])

    def test_csv_file_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destination = str(Path(tmp) / "results.csv")
            self.facade.export(destination)
            with open(destination, encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.reader(handle, delimiter=";"))
        self.assertEqual(3, len(rows))
        self.assertEqual("Итог (0-10)", rows[0][-1])
        self.assertEqual("6.25", rows[1][-1])
        self.assertEqual(["2", "Мария Петрова", "", "", "0"], rows[2])


if __name__ == "__main__":
    unittest.main()
