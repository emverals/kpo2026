from __future__ import annotations

import shlex
import sys
from decimal import Decimal, InvalidOperation

from ..application.facade import PosFacade
from ..domain.errors import DomainError
from ..formatting import format_decimal

HELP_TEXT = """Команды:
  студент-добавить <имя>
      Добавить студента; имя с пробелами возьмите в кавычки.
  студенты
      Список студентов.
  критерий-добавить <название> <макс_балл> <вес>
      Добавить критерий, например: критерий-добавить "Активность" 5 1
  критерии
      Список критериев рубрикатора.
  оценка-поставить <студент> <критерий> <балл> [комментарий]
      Выставить оценку; балл не может выходить за максимум критерия.
  оценка-исправить <студент> <критерий> <балл>
      Исправить существующую оценку.
  оценка-отменить <студент> <критерий>
      Отменить оценку.
  оценки [студент]
      Список оценок: всех или одного студента.
  итог <студент>
      Итоговый балл студента по текущему правилу.
  итоги
      Итоговые баллы всех студентов.
  стратегия [взвешенная | средняя]
      Показать или сменить правило расчёта итога.
  экспорт <файл.csv>
      Выгрузить итоги в CSV (разделитель «;», кодировка utf-8-sig).
  выход
      Завершить работу (также exit, quit, Ctrl+D)."""


class ConsoleUI:
    """Интерактивный консольный интерфейс модуля ПОС."""

    PROMPT = "ПОС> "

    def __init__(self, facade: PosFacade, stdin=None, stdout=None) -> None:
        self._facade = facade
        self._in = stdin if stdin is not None else sys.stdin
        self._out = stdout if stdout is not None else sys.stdout
        self._stop = False
        self._commands = {
            "помощь": self._cmd_help,
            "help": self._cmd_help,
            "студент-добавить": self._cmd_add_student,
            "студенты": self._cmd_list_students,
            "критерий-добавить": self._cmd_add_criterion,
            "критерии": self._cmd_list_criteria,
            "оценка-поставить": self._cmd_set_evaluation,
            "оценка-исправить": self._cmd_fix_evaluation,
            "оценка-отменить": self._cmd_cancel_evaluation,
            "оценки": self._cmd_list_evaluations,
            "итог": self._cmd_final,
            "итоги": self._cmd_final_all,
            "стратегия": self._cmd_strategy,
            "экспорт": self._cmd_export,
            "выход": self._cmd_exit,
            "exit": self._cmd_exit,
            "quit": self._cmd_exit,
        }

    def run(self) -> None:
        self._say(
            "ПОС: преподавательская оценка студентов. Введите «помощь» для списка команд."
        )
        while not self._stop:
            self._write(self.PROMPT)
            line = self._in.readline()
            if not line:
                self._say("Поток ввода закрыт. Завершение работы.")
                break
            self._handle(line.strip())

    def _handle(self, line: str) -> None:
        if not line:
            return
        try:
            tokens = shlex.split(line)
        except ValueError:
            self._say("Ошибка: не удалось разобрать команду, проверьте кавычки.")
            return
        if not tokens:
            return
        name, args = tokens[0], tokens[1:]
        handler = self._commands.get(name)
        if handler is None:
            self._say(
                f"Неизвестная команда: {name}. Введите «помощь» для списка команд."
            )
            return
        try:
            handler(args)
        except (DomainError, ValueError, OSError) as error:
            self._say(f"Ошибка: {error}")

    def _say(self, text: str) -> None:
        self._write(text + "\n")

    def _write(self, text: str) -> None:
        self._out.write(text)
        self._out.flush()

    def _int(self, raw: str, what: str) -> int:
        try:
            return int(raw)
        except ValueError:
            raise ValueError(
                f"{what}: ожидается целое число, получено «{raw}»."
            ) from None

    def _decimal(self, raw: str, what: str) -> Decimal:
        try:
            return Decimal(raw)
        except InvalidOperation:
            raise ValueError(f"{what}: ожидается число, получено «{raw}».") from None

    def _cmd_help(self, args: list[str]) -> None:
        self._say(HELP_TEXT)

    def _cmd_exit(self, args: list[str]) -> None:
        self._stop = True
        self._say("Завершение работы.")

    def _cmd_add_student(self, args: list[str]) -> None:
        if not args:
            raise ValueError("Ожидается: студент-добавить <имя>")
        student = self._facade.add_student(" ".join(args))
        self._say(f"Добавлен студент [{student.id}] {student.name}.")

    def _cmd_list_students(self, args: list[str]) -> None:
        students = self._facade.list_students()
        if not students:
            self._say("Студентов нет.")
            return
        for student in students:
            self._say(f"[{student.id}] {student.name}")

    def _cmd_add_criterion(self, args: list[str]) -> None:
        if len(args) < 3:
            raise ValueError(
                "Ожидается: критерий-добавить <название> <макс_балл> <вес>"
            )
        weight = self._decimal(args[-1], "Вес")
        max_score = self._decimal(args[-2], "Максимальный балл")
        name = " ".join(args[:-2])
        criterion = self._facade.add_criterion(name, max_score, weight)
        self._say(
            f"Добавлен критерий [{criterion.id}] {criterion.name} "
            f"(максимум {format_decimal(criterion.max_score)}, "
            f"вес {format_decimal(criterion.weight)})."
        )

    def _cmd_list_criteria(self, args: list[str]) -> None:
        criteria = self._facade.list_criteria()
        if not criteria:
            self._say("Рубрикатор пуст.")
            return
        for criterion in criteria:
            self._say(
                f"[{criterion.id}] {criterion.name}: максимум "
                f"{format_decimal(criterion.max_score)}, вес {format_decimal(criterion.weight)}"
            )

    def _cmd_set_evaluation(self, args: list[str]) -> None:
        if len(args) < 3:
            raise ValueError(
                "Ожидается: оценка-поставить <студент> <критерий> <балл> [комментарий]"
            )
        student_id = self._int(args[0], "id студента")
        criterion_id = self._int(args[1], "id критерия")
        score = self._decimal(args[2], "Балл")
        comment = " ".join(args[3:])
        evaluation = self._facade.set_evaluation(
            student_id, criterion_id, score, comment
        )
        self._say(
            f"Оценка выставлена: {self._facade.student(evaluation.student_id).name}, "
            f"критерий «{self._facade.criterion(evaluation.criterion_id).name}»: "
            f"{format_decimal(evaluation.score.value)}."
        )

    def _cmd_fix_evaluation(self, args: list[str]) -> None:
        if len(args) != 3:
            raise ValueError("Ожидается: оценка-исправить <студент> <критерий> <балл>")
        student_id = self._int(args[0], "id студента")
        criterion_id = self._int(args[1], "id критерия")
        score = self._decimal(args[2], "Балл")
        evaluation = self._facade.fix_evaluation(student_id, criterion_id, score)
        self._say(
            f"Оценка исправлена: {self._facade.student(evaluation.student_id).name}, "
            f"критерий «{self._facade.criterion(evaluation.criterion_id).name}»: "
            f"{format_decimal(evaluation.score.value)}."
        )

    def _cmd_cancel_evaluation(self, args: list[str]) -> None:
        if len(args) != 2:
            raise ValueError("Ожидается: оценка-отменить <студент> <критерий>")
        student_id = self._int(args[0], "id студента")
        criterion_id = self._int(args[1], "id критерия")
        evaluation = self._facade.cancel_evaluation(student_id, criterion_id)
        self._say(
            f"Оценка отменена: {self._facade.student(evaluation.student_id).name}, "
            f"критерий «{self._facade.criterion(evaluation.criterion_id).name}»."
        )

    def _cmd_list_evaluations(self, args: list[str]) -> None:
        if len(args) > 1:
            raise ValueError("Ожидается: оценки [студент]")
        student_id = self._int(args[0], "id студента") if args else None
        rows = self._facade.list_evaluations(student_id)
        if not rows:
            self._say("Оценок нет.")
            return
        for row in rows:
            evaluation = row.evaluation
            details = evaluation.date.strftime("%d.%m.%Y")
            if evaluation.comment:
                details += f", {evaluation.comment}"
            self._say(
                f"[{row.student_id}] {row.student_name}, критерий "
                f"«{row.criterion_name}»: {format_decimal(evaluation.score.value)} из "
                f"{format_decimal(row.criterion_max)} ({details})"
            )

    def _cmd_final(self, args: list[str]) -> None:
        if len(args) != 1:
            raise ValueError("Ожидается: итог <студент>")
        student_id = self._int(args[0], "id студента")
        student = self._facade.student(student_id)
        final = self._facade.final_for(student_id)
        self._say(
            f"Итог [{student.id}] {student.name}: "
            f"{format_decimal(final.value)} из 10 ({final.strategy})."
        )

    def _cmd_final_all(self, args: list[str]) -> None:
        results = self._facade.final_all()
        if not results:
            self._say("Студентов нет.")
            return
        for student, final in results:
            self._say(
                f"Итог [{student.id}] {student.name}: "
                f"{format_decimal(final.value)} из 10 ({final.strategy})."
            )

    def _cmd_strategy(self, args: list[str]) -> None:
        if not args:
            self._say(f"Правило итога: {self._facade.strategy_name()}.")
            return
        if len(args) != 1:
            raise ValueError("Ожидается: стратегия [взвешенная | средняя]")
        name = self._facade.set_strategy(args[0])
        self._say(f"Правило итога: {name}.")

    def _cmd_export(self, args: list[str]) -> None:
        if len(args) != 1:
            raise ValueError("Ожидается: экспорт <файл.csv>")
        destination = args[0]
        self._facade.export(destination)
        self._say(f"Результаты записаны в файл: {destination}")
