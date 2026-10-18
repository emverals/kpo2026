"""Ввод-вывод консоли. Вынесен, чтобы UI тестировался и демонстрировался без подмены stdin."""

from collections.abc import Callable, Iterable, Mapping


class ConsoleIO:
    def __init__(
        self,
        read: Callable[[str], str] = input,
        write: Callable[[str], None] = print,
    ) -> None:
        self._read = read
        self._write = write

    def read(self, prompt: str) -> str:
        return self._read(prompt)

    def write(self, text: str) -> None:
        self._write(text)


class ScriptedIO(ConsoleIO):
    """Отвечает заготовленными строками и печатает их, будто пользователь их ввёл.

    headings: номер ответа (с нуля) → строка, печатаемая перед его запросом.
    По окончании сценария бросает EOFError — так же, как настоящий input() на конце потока.
    """

    def __init__(
        self,
        write: Callable[[str], None] = print,
        answers: Iterable[str] = (),
        headings: Mapping[int, str] | None = None,
    ) -> None:
        super().__init__(write=write)
        self._answers = list(answers)
        self._headings = dict(headings or {})
        self._position = 0

    def read(self, prompt: str) -> str:
        if self._position >= len(self._answers):
            raise EOFError
        heading = self._headings.get(self._position)
        if heading is not None:
            self.write(heading)
        answer = self._answers[self._position]
        self._position += 1
        self.write(f"{prompt}{answer}")
        return answer
