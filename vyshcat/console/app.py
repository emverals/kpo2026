"""Интерактивное меню учёта парка. Виды техники и вещей берутся из каталога."""

from collections.abc import Callable, Sequence

from vyshcat.console.io import ConsoleIO
from vyshcat.console.prompts import Prompter
from vyshcat.domain.vehicles import MAX_SIMPLICITY, MIN_SIMPLICITY
from vyshcat.services.catalog import ItemKind, VehicleKind
from vyshcat.services.fleet import FleetService
from vyshcat.services.reports import FleetReportService

MENU = """
===== ВышКат: учёт парка =====
1. Принять транспорт (с техосмотром)
2. Поставить вещь на баланс
3. Отчёт: количество и суточная энергия
4. Транспорт для новичков
5. Инвентарная опись
0. Выход"""


class ConsoleApp:
    def __init__(
        self,
        fleet: FleetService,
        reports: FleetReportService,
        vehicle_kinds: Sequence[VehicleKind],
        item_kinds: Sequence[ItemKind],
        io: ConsoleIO,
    ) -> None:
        self._fleet = fleet
        self._reports = reports
        self._vehicle_kinds = vehicle_kinds
        self._item_kinds = item_kinds
        self._io = io
        self._ask = Prompter(io)
        self._actions: dict[str, Callable[[], None]] = {
            "1": self.accept_vehicle,
            "2": self.add_item,
            "3": self.show_report,
            "4": self.show_beginner_friendly,
            "5": self.show_inventory,
        }

    def run(self) -> None:
        try:
            while True:
                self._io.write(MENU)
                choice = self._io.read("Пункт меню: ").strip()
                if choice == "0":
                    break
                action = self._actions.get(choice)
                if action is None:
                    self._io.write(f"Нет пункта «{choice}». Выберите 0–{len(self._actions)}.")
                    continue
                action()
        except (EOFError, KeyboardInterrupt):
            self._io.write("")
        self._io.write("До свидания! Доедем до дедлайна.")

    def accept_vehicle(self) -> None:
        kind = self._vehicle_kinds[
            self._ask.choice("Вид транспорта:", [k.title for k in self._vehicle_kinds])
        ]
        name = self._ask.text("Наименование: ")
        simplicity = self._ask.integer(
            f"Простота для новичка ({MIN_SIMPLICITY}–{MAX_SIMPLICITY}): ",
            MIN_SIMPLICITY,
            MAX_SIMPLICITY,
        )
        energy = (
            self._ask.non_negative_float("Суточный расход, кВт·ч: ")
            if kind.consumes_energy
            else 0.0
        )
        defects = self._ask.csv_list("Заявленные неисправности через запятую (Enter — нет): ")
        vehicle = kind.factory(name, simplicity, energy, defects)
        result = self._fleet.accept_vehicle(vehicle)
        if result.accepted:
            self._io.write(f"ПРИНЯТ: «{vehicle.name}», инв. № {vehicle.inventory_number}.")
        else:
            self._io.write(f"ОТКЛОНЁН: «{vehicle.name}» — {result.reason}.")

    def add_item(self) -> None:
        kind = self._item_kinds[self._ask.choice("Вид вещи:", [k.title for k in self._item_kinds])]
        name = self._ask.text("Наименование: ")
        energy = (
            self._ask.non_negative_float("Суточный расход, кВт·ч: ")
            if kind.consumes_energy
            else 0.0
        )
        item = kind.factory(name, energy)
        number = self._fleet.add_item(item)
        self._io.write(f"На балансе: «{item.name}», инв. № {number}.")

    def show_report(self) -> None:
        counts = self._reports.counts()
        self._io.write(f"Транспорт: {counts.vehicles} ед.")
        self._io.write(f"Вещи: {counts.items} ед.")
        self._io.write(f"Всего на балансе: {counts.total} ед.")
        self._io.write(f"Суточное потребление: {self._reports.total_daily_energy_kwh():.2f} кВт·ч")

    def show_beginner_friendly(self) -> None:
        vehicles = self._reports.beginner_friendly_vehicles()
        if not vehicles:
            self._io.write("Подходящего для новичков транспорта нет.")
            return
        self._io.write("Можно выдавать новичкам:")
        for v in vehicles:
            self._io.write(f"  {v.inventory_number}  {v.name} (простота {v.simplicity})")

    def show_inventory(self) -> None:
        lines = self._reports.inventory()
        if not lines:
            self._io.write("На балансе пока ничего нет.")
            return
        self._io.write("Инв. номер  | Вид       | Наименование")
        for line in lines:
            self._io.write(f"{line.number:<11} | {line.kind:<9} | {line.name}")
