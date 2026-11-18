from __future__ import annotations

import io
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from pos.adapters.console import ConsoleUI
from pos.adapters.csv_export import CsvResultsWriter
from pos.adapters.memory import (
    InMemoryEvaluationSheetRepository,
    InMemoryRubricRepository,
    InMemoryStudentRepository,
)
from pos.application.facade import PosFacade
from pos.container import Container, build_container
from pos.domain.errors import DomainError
from pos.domain.factory import EvaluationFactory
from pos.domain.model import Criterion
from pos.domain.repositories import StudentRepository
from pos.domain.services import FinalScoreService, WeightedTotalStrategy


def d(value: str) -> Decimal:
    return Decimal(value)


class ContainerTests(unittest.TestCase):
    def test_singleton_identity(self) -> None:
        container = build_container()
        first = container.resolve(StudentRepository)
        second = container.resolve(StudentRepository)
        self.assertIs(first, second)

    def test_facade_shares_repositories(self) -> None:
        container = build_container()
        facade = container.resolve(PosFacade)
        students = container.resolve(StudentRepository)
        self.assertIs(facade._students, students)

    def test_unregistered_key_raises(self) -> None:
        class Unregistered:
            pass

        container = Container()
        with self.assertRaises(KeyError):
            container.resolve(Unregistered)


class ConsoleTestCase(unittest.TestCase):
    def make_ui(self, commands: str) -> tuple[ConsoleUI, io.StringIO, Path]:
        students = InMemoryStudentRepository()
        rubrics = InMemoryRubricRepository()
        sheets = InMemoryEvaluationSheetRepository()
        rubric = rubrics.load()
        rubric.add(Criterion(rubric.next_id(), "Активность", d("5"), d("1")))
        rubric.add(Criterion(rubric.next_id(), "Домашние работы", d("10"), d("3")))
        facade = PosFacade(
            students=students,
            rubrics=rubrics,
            sheets=sheets,
            factory=EvaluationFactory(),
            score_service=FinalScoreService(WeightedTotalStrategy()),
            writer=CsvResultsWriter(),
        )
        output = io.StringIO()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        ui = ConsoleUI(facade, stdin=io.StringIO(commands), stdout=output)
        return ui, output, Path(directory.name)

    def run_commands(self, commands: str) -> str:
        ui, output, _ = self.make_ui(commands)
        ui.run()
        return output.getvalue()


class CliEndToEndTests(ConsoleTestCase):
    def test_full_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_path = str(Path(tmp) / "results.csv")
            script = (
                "помощь\n"
                'студент-добавить "Иван Иванов"\n'
                'студент-добавить "Мария Петрова"\n'
                'критерий-добавить "Активность" 5 1\n'
                'критерий-добавить "Домашние работы" 10 3\n'
                'оценка-поставить 1 1 5 "работает на семинарах"\n'
                "оценка-поставить 1 2 5\n"
                "оценка-поставить 2 1 4\n"
                "итог 1\n"
                "итог 2\n"
                "итоги\n"
                "оценка-исправить 2 1 5\n"
                "итог 2\n"
                "оценка-отменить 2 1\n"
                "итог 2\n"
                "оценки 1\n"
                "стратегия средняя\n"
                "итог 1\n"
                "стратегия взвешенная\n"
                "стратегия\n"
                "оценка-поставить 99 1 3\n"
                "оценка-поставить 1 1 99\n"
                'критерий-добавить "Плохой" -1 1\n'
                'критерий-добавить "Активность" 5 1\n'
                "оценка-исправить 1 999 3\n"
                f"экспорт {export_path}\n"
                "абракадабра\n"
                "выход\n"
            )
            output = self.run_commands(script)

            self.assertIn("Команды:", output)
            self.assertIn("Иван Иванов", output)
            self.assertIn("Мария Петрова", output)
            self.assertIn("6.25", output)
            self.assertIn("2.5", output)
            self.assertIn("7.5", output)
            self.assertIn("Правило итога: взвешенная", output)
            self.assertIn("Ошибка", output)
            self.assertIn("не найден", output)
            self.assertIn("превышает максимум", output)
            self.assertIn("положительным", output)
            self.assertIn("уже существует", output)
            self.assertIn("Неизвестная команда", output)
            self.assertIn("Завершение работы", output)
            self.assertIn("Результаты записаны", output)

            import csv

            with open(export_path, encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.reader(handle, delimiter=";"))
            self.assertEqual(
                ["id", "Студент", "Активность", "Домашние работы", "Итог (0-10)"],
                rows[0],
            )
            self.assertEqual("6.25", rows[1][-1])

    def test_exit_stops_session(self) -> None:
        output = self.run_commands("выход\n")
        self.assertIn("Завершение работы", output)

    def test_eof_terminates(self) -> None:
        output = self.run_commands("")
        self.assertIn("Поток ввода закрыт", output)

    def test_unbalanced_quote_reports_error(self) -> None:
        output = self.run_commands('студент-добавить "Обрыв\nвыход\n')
        self.assertIn("кавычки", output)


class FacadeInvariantTests(unittest.TestCase):
    def setUp(self) -> None:
        students = InMemoryStudentRepository()
        rubrics = InMemoryRubricRepository()
        sheets = InMemoryEvaluationSheetRepository()
        rubric = rubrics.load()
        rubric.add(Criterion(rubric.next_id(), "Активность", d("5"), d("1")))
        self.facade = PosFacade(
            students=students,
            rubrics=rubrics,
            sheets=sheets,
            factory=EvaluationFactory(),
            score_service=FinalScoreService(WeightedTotalStrategy()),
            writer=CsvResultsWriter(),
        )

    def test_set_evaluation_requires_existing_student(self) -> None:
        with self.assertRaises(DomainError):
            self.facade.set_evaluation(42, 1, d("3"))

    def test_fix_requires_existing_evaluation(self) -> None:
        student = self.facade.add_student("Иван")
        with self.assertRaises(DomainError):
            self.facade.fix_evaluation(student.id, 1, d("4"))

    def test_cancel_requires_existing_evaluation(self) -> None:
        student = self.facade.add_student("Иван")
        with self.assertRaises(DomainError):
            self.facade.cancel_evaluation(student.id, 1)

    def test_unknown_strategy_rejected(self) -> None:
        with self.assertRaises(DomainError):
            self.facade.set_strategy("средняя по больнице")

    def test_empty_rubric_final_raises(self) -> None:
        students = InMemoryStudentRepository()
        rubrics = InMemoryRubricRepository()
        sheets = InMemoryEvaluationSheetRepository()
        empty = PosFacade(
            students=students,
            rubrics=rubrics,
            sheets=sheets,
            factory=EvaluationFactory(),
            score_service=FinalScoreService(WeightedTotalStrategy()),
            writer=CsvResultsWriter(),
        )
        student = empty.add_student("Мария")
        with self.assertRaises(DomainError):
            empty.final_for(student.id)


if __name__ == "__main__":
    unittest.main()
