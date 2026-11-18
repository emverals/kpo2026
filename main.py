"""Точка входа модуля ПОС: composition root и запуск консольного интерфейса."""

from pos.adapters.console import ConsoleUI
from pos.container import build_container


def main() -> None:
    container = build_container()
    container.resolve(ConsoleUI).run()


if __name__ == "__main__":
    main()
