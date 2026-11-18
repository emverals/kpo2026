from __future__ import annotations

from decimal import Decimal

from .model import Evaluation, Rubric, Score


class EvaluationFactory:
    """Фабрика оценок: резолвит критерий рубрикатора и создаёт оценку;
    инварианты диапазона и существования критерия охраняются в домене."""

    def create(
        self,
        rubric: Rubric,
        student_id: int,
        criterion_id: int,
        raw_score: Decimal,
        comment: str = "",
    ) -> Evaluation:
        criterion = rubric.criterion(criterion_id)
        return Evaluation(
            student_id=student_id,
            criterion=criterion,
            score=Score(raw_score),
            comment=comment.strip(),
        )
