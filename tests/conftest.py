"""Общие фабрики и самописные двойники техосмотра (без мок-библиотек)."""

from collections.abc import Sequence

import pytest

from vyshcat.domain.items import ChargingCabinet, DockStation, Helmet
from vyshcat.domain.vehicles import Bicycle, EBike, ElectricScooter, Vehicle
from vyshcat.services.fleet import FleetService
from vyshcat.services.reports import FleetReportService
from vyshcat.services.repository import FleetRepository
from vyshcat.services.service_center import InspectionResult, IServiceCenter


def scooter(
    name: str = "Ninebot", simplicity: int = 7, kwh: float = 0.5, defects: Sequence[str] = ()
) -> ElectricScooter:
    return ElectricScooter(name, simplicity, kwh, defects)


def ebike(
    name: str = "Eltreco", simplicity: int = 4, kwh: float = 1.2, defects: Sequence[str] = ()
) -> EBike:
    return EBike(name, simplicity, kwh, defects)


def bicycle(name: str = "Stels", simplicity: int = 9, defects: Sequence[str] = ()) -> Bicycle:
    return Bicycle(name, simplicity, defects)


def helmet(name: str = "Шлем M") -> Helmet:
    return Helmet(name)


def dock(name: str = "Док", kwh: float = 1.5) -> DockStation:
    return DockStation(name, kwh)


def cabinet(name: str = "Шкаф", kwh: float = 3.0) -> ChargingCabinet:
    return ChargingCabinet(name, kwh)


class AlwaysAcceptCenter(IServiceCenter):
    def inspect(self, vehicle: Vehicle) -> InspectionResult:
        return InspectionResult(True, "stub: принято")


class AlwaysRejectCenter(IServiceCenter):
    REASON = "stub: отклонено"

    def inspect(self, vehicle: Vehicle) -> InspectionResult:
        return InspectionResult(False, self.REASON)


class SpyServiceCenter(IServiceCenter):
    """Записывает, что видел в момент техосмотра: номер у техники и размер баланса."""

    def __init__(self, repository: FleetRepository, accept: bool = True) -> None:
        self._repository = repository
        self._accept = accept
        self.calls: list[tuple[Vehicle, str | None, int]] = []

    def inspect(self, vehicle: Vehicle) -> InspectionResult:
        self.calls.append((vehicle, vehicle.inventory_number, len(self._repository.all())))
        return InspectionResult(self._accept, "spy")


@pytest.fixture
def repo() -> FleetRepository:
    return FleetRepository()


@pytest.fixture
def reports(repo: FleetRepository) -> FleetReportService:
    return FleetReportService(repo)


@pytest.fixture
def accepting_fleet(repo: FleetRepository) -> FleetService:
    return FleetService(repo, AlwaysAcceptCenter())
