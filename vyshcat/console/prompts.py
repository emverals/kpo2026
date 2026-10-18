"""Запрос значений с повтором до корректного ввода."""

import math
from collections.abc import Sequence

from vyshcat.console.io import ConsoleIO
from vyshcat.domain._validation import MAX_DAILY_ENERGY_KWH


class Prompter:
    def __init__(self, io: ConsoleIO) -> None:
        self._io = io

    def text(self, prompt: str) -> str:
        while True:
            value = self._io.read(prompt).strip()
            if value:
                return value
            self._io.write("Ошибка: значение не может быть пустым.")

    def integer(self, prompt: str, low: int, high: int) -> int:
        while True:
            raw = self._io.read(prompt).strip()
            try:
                value = int(raw)
            except ValueError:
                self._io.write(f"Ошибка: «{raw}» — не целое число.")
                continue
            if low <= value <= high:
                return value
            self._io.write(f"Ошибка: введите число от {low} до {high}.")

    def non_negative_float(self, prompt: str) -> float:
        while True:
            raw = self._io.read(prompt).strip().replace(",", ".")
            try:
                value = float(raw)
            except ValueError:
                self._io.write(f"Ошибка: «{raw}» — не число.")
                continue
            if not (math.isfinite(value) and value >= 0):
                self._io.write("Ошибка: значение должно быть неотрицательным конечным числом.")
            elif value > MAX_DAILY_ENERGY_KWH:
                self._io.write(f"Ошибка: значение не может превышать {MAX_DAILY_ENERGY_KWH:g}.")
            else:
                return value

    def choice(self, title: str, options: Sequence[str]) -> int:
        """Возвращает индекс выбранного варианта (с нуля)."""
        self._io.write(title)
        for i, option in enumerate(options, start=1):
            self._io.write(f"  {i}. {option}")
        return self.integer("Ваш выбор: ", 1, len(options)) - 1

    def csv_list(self, prompt: str) -> list[str]:
        raw = self._io.read(prompt)
        return [part.strip() for part in raw.split(",") if part.strip()]
