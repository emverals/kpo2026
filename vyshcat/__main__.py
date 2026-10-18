"""Точка входа: `python -m vyshcat` — меню, `python -m vyshcat --demo` — демонстрация."""

import io as stdio
import sys

from vyshcat.console.app import ConsoleApp
from vyshcat.console.demo import build_demo_io
from vyshcat.container import build_container


def main(argv: list[str] | None = None) -> int:
    # Невалидный UTF-8 (в т.ч. Backspace по кириллице в терминале) не должен ронять программу.
    if isinstance(sys.stdin, stdio.TextIOWrapper):
        sys.stdin.reconfigure(errors="replace")
    args = sys.argv[1:] if argv is None else argv
    io = build_demo_io() if "--demo" in args else None
    app: ConsoleApp = build_container(io=io).resolve(ConsoleApp)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
