"""Отчёты по парку — только чтение из репозитория."""

from dataclasses import dataclass

from vyshcat.domain.interfaces import IEnergyConsumer
from vyshcat.domain.vehicles import Vehicle
from vyshcat.services.repository import FleetRepository


@dataclass(frozen=True)
class FleetCounts:
    vehicles: int
    items: int

    @property
    def total(self) -> int:
        return self.vehicles + self.items


@dataclass(frozen=True)
class InventoryLine:
    number: str
    name: str
    kind: str


class FleetReportService:
    def __init__(self, repository: FleetRepository) -> None:
        self._repository = repository

    def counts(self) -> FleetCounts:
        return FleetCounts(len(self._repository.vehicles()), len(self._repository.items()))

    def total_daily_energy_kwh(self) -> float:
        return sum(
            o.daily_energy_kwh for o in self._repository.all() if isinstance(o, IEnergyConsumer)
        )

    def beginner_friendly_vehicles(self) -> list[Vehicle]:
        return [v for v in self._repository.vehicles() if v.is_beginner_friendly]

    def inventory(self) -> list[InventoryLine]:
        lines: list[InventoryLine] = []
        for o in self._repository.all():
            number = o.inventory_number
            # FleetRepository.add не принимает объекты без номера — здесь он всегда есть.
            assert number is not None
            lines.append(
                InventoryLine(number, o.name, "транспорт" if isinstance(o, Vehicle) else "вещь")
            )
        return lines
