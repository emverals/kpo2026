from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ..domain.errors import DomainError
from ..domain.factory import EvaluationFactory
from ..domain.model import Criterion, Evaluation, FinalScore, Student
from ..domain.repositories import (
    EvaluationSheetRepository,
    RubricRepository,
    StudentRepository,
)
from ..domain.services import (
    FinalScoreService,
    FinalScoreStrategy,
    NormalizedAverageStrategy,
    WeightedTotalStrategy,
)
from ..formatting import format_decimal
from .ports import ResultsWriter


@dataclass(frozen=True)
class EvaluationRow:
    """Строка для показа оценки в интерфейсе."""

    student_id: int
    student_name: str
    criterion_id: int
    criterion_name: str
    criterion_max: Decimal
    evaluation: Evaluation


_STRATEGIES: dict[str, FinalScoreStrategy] = {
    WeightedTotalStrategy.name: WeightedTotalStrategy(),
    NormalizedAverageStrategy.name: NormalizedAverageStrategy(),
    "средняя": NormalizedAverageStrategy(),
}


class PosFacade:
    """Единая точка сценариев модуля для консольного интерфейса."""

    def __init__(
        self,
        students: StudentRepository,
        rubrics: RubricRepository,
        sheets: EvaluationSheetRepository,
        factory: EvaluationFactory,
        score_service: FinalScoreService,
        writer: ResultsWriter,
    ) -> None:
        self._students = students
        self._rubrics = rubrics
        self._sheets = sheets
        self._factory = factory
        self._score_service = score_service
        self._writer = writer

    def add_student(self, name: str) -> Student:
        student = Student(self._students.next_id(), name)
        self._students.add(student)
        return student

    def list_students(self) -> list[Student]:
        return self._students.all()

    def student(self, student_id: int) -> Student:
        return self._students.get(student_id)

    def add_criterion(
        self, name: str, max_score: Decimal, weight: Decimal
    ) -> Criterion:
        rubric = self._rubrics.load()
        criterion = Criterion(rubric.next_id(), name, max_score, weight)
        rubric.add(criterion)
        self._rubrics.save(rubric)
        return criterion

    def list_criteria(self) -> list[Criterion]:
        return self._rubrics.load().all()

    def criterion(self, criterion_id: int) -> Criterion:
        return self._rubrics.load().criterion(criterion_id)

    def set_evaluation(
        self,
        student_id: int,
        criterion_id: int,
        score: Decimal,
        comment: str = "",
    ) -> Evaluation:
        self._students.get(student_id)
        rubric = self._rubrics.load()
        evaluation = self._factory.create(
            rubric, student_id, criterion_id, score, comment
        )
        sheet = self._sheets.load()
        sheet.put(evaluation, rubric)
        self._sheets.save(sheet)
        return evaluation

    def fix_evaluation(
        self, student_id: int, criterion_id: int, score: Decimal
    ) -> Evaluation:
        rubric = self._rubrics.load()
        sheet = self._sheets.load()
        existing = sheet.require(student_id, criterion_id)
        evaluation = self._factory.create(
            rubric, student_id, criterion_id, score, existing.comment
        )
        sheet.put(evaluation, rubric)
        self._sheets.save(sheet)
        return evaluation

    def cancel_evaluation(self, student_id: int, criterion_id: int) -> Evaluation:
        sheet = self._sheets.load()
        existing = sheet.require(student_id, criterion_id)
        sheet.remove(student_id, criterion_id)
        self._sheets.save(sheet)
        return existing

    def list_evaluations(self, student_id: int | None = None) -> list[EvaluationRow]:
        sheet = self._sheets.load()
        evaluations = (
            sheet.for_student(student_id) if student_id is not None else sheet.all()
        )
        rows: list[EvaluationRow] = []
        for evaluation in evaluations:
            student = self._students.get(evaluation.student_id)
            criterion = self._rubrics.load().criterion(evaluation.criterion_id)
            rows.append(
                EvaluationRow(
                    student_id=student.id,
                    student_name=student.name,
                    criterion_id=criterion.id,
                    criterion_name=criterion.name,
                    criterion_max=criterion.max_score,
                    evaluation=evaluation,
                )
            )
        return rows

    def final_for(self, student_id: int) -> FinalScore:
        self._students.get(student_id)
        return self._score_service.for_student(
            self._rubrics.load(), self._sheets.load(), student_id
        )

    def final_all(self) -> list[tuple[Student, FinalScore]]:
        rubric = self._rubrics.load()
        sheet = self._sheets.load()
        return [
            (student, self._score_service.for_student(rubric, sheet, student.id))
            for student in self._students.all()
        ]

    def strategy_name(self) -> str:
        return self._score_service.strategy_name()

    def set_strategy(self, name: str) -> str:
        strategy = _STRATEGIES.get(name.strip())
        if strategy is None:
            known = " или ".join(f"«{item}»" for item in _STRATEGIES)
            raise DomainError(f"Неизвестное правило итога, доступно: {known}.")
        self._score_service.use_strategy(strategy)
        return strategy.name

    def export_rows(self) -> list[list[str]]:
        rubric = self._rubrics.load()
        sheet = self._sheets.load()
        criteria = rubric.all()
        header = ["id", "Студент", *[item.name for item in criteria], "Итог (0-10)"]
        rows: list[list[str]] = [header]
        for student in self._students.all():
            scores = {item.criterion_id: item for item in sheet.for_student(student.id)}
            cells = [
                format_decimal(scores[item.id].score.value) if item.id in scores else ""
                for item in criteria
            ]
            final = self._score_service.for_student(rubric, sheet, student.id)
            rows.append(
                [str(student.id), student.name, *cells, format_decimal(final.value)]
            )
        return rows

    def export(self, destination: str) -> None:
        self._writer.write(self.export_rows(), destination)
