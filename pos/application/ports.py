from __future__ import annotations

from abc import ABC, abstractmethod


class ResultsWriter(ABC):
    """Порт записи итоговых результатов (файлы, внешние системы)."""

    @abstractmethod
    def write(self, rows: list[list[str]], destination: str) -> None: ...
