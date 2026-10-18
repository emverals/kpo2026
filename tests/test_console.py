"""Консольное меню через инжектируемый ScriptedIO; демо и точка входа."""

import io as stdio

import pytest

from tests.conftest import AlwaysAcceptCenter, AlwaysRejectCenter
from vyshcat.__main__ import main
from vyshcat.console.app import ConsoleApp
from vyshcat.console.demo import DEMO_STEPS, build_demo_io
from vyshcat.console.io import ConsoleIO, ScriptedIO
from vyshcat.console.prompts import Prompter
from vyshcat.container import build_container
from vyshcat.domain.interfaces import IEnergyConsumer
from vyshcat.services.catalog import ITEM_KINDS, VEHICLE_KINDS, ItemKind, VehicleKind
from vyshcat.services.reports import FleetReportService
from vyshcat.services.service_center import IServiceCenter


class Session:
    """Прогоняет ConsoleApp по сценарию и даёт доступ к выводу и состоянию парка."""

    def __init__(self, answers: list[str], service_center: IServiceCenter | None = None) -> None:
        self.out: list[str] = []
        self.container = build_container(
            service_center=service_center, io=ScriptedIO(write=self.out.append, answers=answers)
        )
        self.app = self.container.resolve(ConsoleApp)

    def run(self) -> "Session":
        self.app.run()
        return self

    @property
    def text(self) -> str:
        return "\n".join(self.out)

    @property
    def reports(self) -> FleetReportService:
        return self.container.resolve(FleetReportService)


def test_menu_accept_scooter_registers_and_prints_number() -> None:
    s = Session(["1", "1", "Ninebot", "8", "0.6", "", "0"]).run()
    vehicles = s.reports.beginner_friendly_vehicles()
    assert len(vehicles) == 1
    assert vehicles[0].name == "Ninebot"
    assert f"ПРИНЯТ: «Ninebot», инв. № {vehicles[0].inventory_number}" in s.text


def test_menu_accept_with_defects_rejected_and_not_on_balance() -> None:
    s = Session(["1", "1", "Kugoo", "7", "0.5", "тормоз, люфт руля", "0"]).run()
    assert "ОТКЛОНЁН: «Kugoo»" in s.text
    assert "тормоз" in s.text
    assert s.reports.counts().total == 0


def test_menu_accept_bicycle_does_not_ask_energy() -> None:
    s = Session(["1", "2", "Stels", "9", "", "0"]).run()
    assert "Суточный расход" not in s.text
    assert s.reports.counts().vehicles == 1


def test_menu_accept_uses_injected_service_center() -> None:
    s = Session(["1", "1", "Ninebot", "8", "0.6", "", "0"], AlwaysRejectCenter()).run()
    assert "ОТКЛОНЁН" in s.text
    assert s.reports.counts().total == 0


def test_menu_add_item_registers_without_inspection() -> None:
    s = Session(["2", "2", "Док Покровка", "1,5", "0"], AlwaysRejectCenter()).run()
    assert s.reports.counts().items == 1
    assert s.reports.total_daily_energy_kwh() == pytest.approx(1.5)
    assert "На балансе: «Док Покровка», инв. №" in s.text


def test_menu_add_helmet_does_not_ask_energy() -> None:
    s = Session(["2", "1", "Шлем S", "0"]).run()
    assert "Суточный расход" not in s.text
    assert s.reports.counts().items == 1


def test_menu_report_shows_counts_and_energy() -> None:
    s = Session(
        ["1", "1", "A", "8", "0.6", "", "2", "3", "Шкаф", "3", "2", "1", "Шлем", "3", "0"]
    ).run()
    assert "Транспорт: 1 ед." in s.text
    assert "Вещи: 2 ед." in s.text
    assert "Всего на балансе: 3 ед." in s.text
    assert "Суточное потребление: 3.60 кВт·ч" in s.text


def test_menu_beginner_list_shows_only_friendly() -> None:
    s = Session(["1", "1", "Easy", "6", "0.5", "", "1", "3", "Hard", "5", "1", "", "4", "0"]).run()
    tail = s.text.split("Можно выдавать новичкам:")[1]
    assert "Easy (простота 6)" in tail
    assert "Hard" not in tail


def test_menu_beginner_list_empty_message() -> None:
    s = Session(["4", "0"]).run()
    assert "Подходящего для новичков транспорта нет." in s.text


def test_menu_inventory_lists_vehicle_and_item_numbers() -> None:
    s = Session(["1", "2", "Stels", "9", "", "2", "1", "Шлем S", "5", "0"]).run()
    inventory = s.text.split("Инв. номер")[1]
    for line in s.reports.inventory():
        assert line.number in inventory
        assert line.name in inventory
    assert len(s.reports.inventory()) == 2


def test_menu_inventory_empty_message() -> None:
    s = Session(["5", "0"]).run()
    assert "На балансе пока ничего нет." in s.text


def test_menu_unknown_choice_reports_and_continues() -> None:
    s = Session(["7", "abc", "", "5", "0"]).run()
    assert "Нет пункта «7»" in s.text
    assert "Нет пункта «abc»" in s.text
    assert "На балансе пока ничего нет." in s.text  # после мусора меню продолжило работу
    assert s.text.rstrip().endswith("До свидания! Доедем до дедлайна.")


def test_menu_garbage_inputs_reprompted_then_accepted() -> None:
    answers = [
        "1",
        "abc",
        "9",
        "1",
        "",
        "  ",
        "Xiaomi",
        "11",
        "0",
        "x",
        "7",
        "-1",
        "inf",
        "nan",
        "zz",
        "0,45",
        "",
        "0",
    ]
    s = Session(answers).run()
    assert "не целое число" in s.text
    assert f"введите число от 1 до {len(VEHICLE_KINDS)}" in s.text
    assert "введите число от 1 до 10" in s.text
    assert "не может быть пустым" in s.text
    assert "неотрицательным конечным" in s.text
    assert "не число" in s.text
    vehicles = s.reports.beginner_friendly_vehicles()
    assert [(v.name, v.simplicity) for v in vehicles] == [("Xiaomi", 7)]
    assert s.reports.total_daily_energy_kwh() == pytest.approx(0.45)


def test_menu_eof_at_menu_exits_gracefully() -> None:
    s = Session([]).run()
    assert s.out[-1] == "До свидания! Доедем до дедлайна."


def test_menu_eof_mid_scenario_exits_without_registering() -> None:
    s = Session(["1", "1", "Ninebot"]).run()
    assert s.out[-1] == "До свидания! Доедем до дедлайна."
    assert s.reports.counts().total == 0


def test_menu_keyboard_interrupt_exits_gracefully() -> None:
    out: list[str] = []

    def interrupt(_prompt: str) -> str:
        raise KeyboardInterrupt

    app = build_container(io=ConsoleIO(read=interrupt, write=out.append)).resolve(ConsoleApp)
    app.run()
    assert out[-1] == "До свидания! Доедем до дедлайна."


def test_menu_exit_stops_reading_further_input() -> None:
    s = Session(["0", "1", "1", "Ninebot", "8", "0.6", ""]).run()
    assert s.reports.counts().total == 0


def test_prompter_csv_list_trims_and_drops_empty() -> None:
    io = ScriptedIO(write=lambda _s: None, answers=[" тормоз ,, люфт ,  "])
    assert Prompter(io).csv_list("> ") == ["тормоз", "люфт"]


def test_scripted_io_echoes_prompt_with_answer_and_raises_eof() -> None:
    out: list[str] = []
    io = ScriptedIO(write=out.append, answers=["42"])
    assert io.read("Число: ") == "42"
    assert out == ["Число: 42"]
    with pytest.raises(EOFError):
        io.read("Ещё: ")


def test_demo_runs_and_shows_key_scenarios() -> None:
    out: list[str] = []
    io = build_demo_io(ConsoleIO(write=out.append))
    container = build_container(io=io)
    container.resolve(ConsoleApp).run()
    text = "\n".join(out)
    for title, _ in DEMO_STEPS:
        assert f"ДЕМО: {title}" in text
    assert "ПРИНЯТ: «Ninebot Max G30»" in text
    assert "ОТКЛОНЁН: «Kugoo S3»" in text
    assert "ОТКЛОНЁН: «Монстр 3000»" in text
    assert "ПРИНЯТ: «Xiaomi 4 Pro»" in text
    counts = container.resolve(FleetReportService).counts()
    # приняты: самокат, велосипед, электровелосипед, Xiaomi; вещи: шлем, док, шкаф
    assert (counts.vehicles, counts.items) == (4, 3)
    # 0.6 + 1.2 + 0.45 + 1.5 + 3 = 6.75
    assert "Суточное потребление: 6.75 кВт·ч" in text
    assert out[-1] == "До свидания! Доедем до дедлайна."


def test_main_demo_flag_runs_demo(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--demo"]) == 0
    printed = capsys.readouterr().out
    assert "ДЕМО: Инвентарная опись техники и вещей" in printed
    assert "До свидания! Доедем до дедлайна." in printed


def test_main_interactive_reads_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", stdio.StringIO("5\n0\n"))
    assert main([]) == 0
    printed = capsys.readouterr().out
    assert "На балансе пока ничего нет." in printed
    assert "До свидания! Доедем до дедлайна." in printed


def test_main_interactive_empty_stdin_exits_on_eof(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", stdio.StringIO(""))
    assert main([]) == 0
    assert "До свидания! Доедем до дедлайна." in capsys.readouterr().out


def test_main_invalid_utf8_stdin_does_not_crash(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    stdin = stdio.TextIOWrapper(stdio.BytesIO(b"\xff\n0\n"), encoding="utf-8")
    monkeypatch.setattr("sys.stdin", stdin)
    assert main([]) == 0
    assert "До свидания" in capsys.readouterr().out


def test_energy_above_limit_is_reprompted() -> None:
    s = Session(["1", "1", "Ninebot", "7", "1000.5", "1000", "", "0"], AlwaysAcceptCenter()).run()
    assert "не может превышать 1000" in s.text
    assert s.reports.total_daily_energy_kwh() == pytest.approx(1000.0)


@pytest.mark.parametrize("kind", [*VEHICLE_KINDS, *ITEM_KINDS])
def test_catalog_consumes_energy_matches_domain_class(kind: VehicleKind | ItemKind) -> None:
    assert kind.consumes_energy == issubclass(kind.cls, IEnergyConsumer)
