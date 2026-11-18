from __future__ import annotations

import csv

from ..application.ports import ResultsWriter


class CsvResultsWriter(ResultsWriter):
    """CSV-адаптер: разделитель «;», кодировка utf-8-sig для Excel."""

    def write(self, rows: list[list[str]], destination: str) -> None:
        with open(destination, "w", newline="", encoding="utf-8-sig") as handle:
            csv.writer(handle, delimiter=";").writerows(rows)
