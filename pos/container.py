from __future__ import annotations

from typing import Any, Callable

from .adapters.console import ConsoleUI
from .adapters.csv_export import CsvResultsWriter
from .adapters.memory import (
    InMemoryEvaluationSheetRepository,
    InMemoryRubricRepository,
    InMemoryStudentRepository,
)
from .application.facade import PosFacade
from .application.ports import ResultsWriter
from .domain.factory import EvaluationFactory
from .domain.repositories import (
    EvaluationSheetRepository,
    RubricRepository,
    StudentRepository,
)
from .domain.services import FinalScoreService, WeightedTotalStrategy


class Container:
    """DI-контейнер: регистрация фабрик зависимостей и ленивое разрешение графа."""

    def __init__(self) -> None:
        self._factories: dict[type, Callable[[Container], Any]] = {}
        self._instances: dict[type, Any] = {}
        self._shared: set[type] = set()

    def register(
        self,
        key: type,
        factory: Callable[[Container], Any],
        *,
        singleton: bool = False,
    ) -> None:
        if key in self._factories:
            raise ValueError(f"Зависимость {key.__name__} уже зарегистрирована.")
        self._factories[key] = factory
        if singleton:
            self._shared.add(key)

    def resolve(self, key: type) -> Any:
        if key not in self._factories:
            raise KeyError(f"Зависимость {key.__name__} не зарегистрирована.")
        if key in self._shared:
            if key not in self._instances:
                self._instances[key] = self._factories[key](self)
            return self._instances[key]
        return self._factories[key](self)


def build_container() -> Container:
    """Composition root: сборка графа зависимостей приложения."""
    container = Container()
    container.register(
        StudentRepository, lambda c: InMemoryStudentRepository(), singleton=True
    )
    container.register(
        RubricRepository, lambda c: InMemoryRubricRepository(), singleton=True
    )
    container.register(
        EvaluationSheetRepository,
        lambda c: InMemoryEvaluationSheetRepository(),
        singleton=True,
    )
    container.register(EvaluationFactory, lambda c: EvaluationFactory(), singleton=True)
    container.register(
        FinalScoreService,
        lambda c: FinalScoreService(WeightedTotalStrategy()),
        singleton=True,
    )
    container.register(ResultsWriter, lambda c: CsvResultsWriter(), singleton=True)
    container.register(
        PosFacade,
        lambda c: PosFacade(
            students=c.resolve(StudentRepository),
            rubrics=c.resolve(RubricRepository),
            sheets=c.resolve(EvaluationSheetRepository),
            factory=c.resolve(EvaluationFactory),
            score_service=c.resolve(FinalScoreService),
            writer=c.resolve(ResultsWriter),
        ),
        singleton=True,
    )
    container.register(ConsoleUI, lambda c: ConsoleUI(c.resolve(PosFacade)))
    return container
