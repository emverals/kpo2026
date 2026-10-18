"""Техосмотр: решает, допускается ли транспорт в активный парк."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from vyshcat.domain.interfaces import IEnergyConsumer
from vyshcat.domain.vehicles import Vehicle

MAX_NORMAL_DAILY_ENERGY_KWH = 5.0


@dataclass(frozen=True)
class InspectionResult:
    accepted: bool
    reason: str


class IServiceCenter(ABC):
    """Абстракция нужна FleetService и тестам: в тестах подставляется заглушка."""

    @abstractmethod
    def inspect(self, vehicle: Vehicle) -> InspectionResult: ...


class ServiceCenter(IServiceCenter):
    def inspect(self, vehicle: Vehicle) -> InspectionResult:
        if vehicle.defects:
            return InspectionResult(False, "заявлены неисправности: " + ", ".join(vehicle.defects))
        if (
            isinstance(vehicle, IEnergyConsumer)
            and vehicle.daily_energy_kwh > MAX_NORMAL_DAILY_ENERGY_KWH
        ):
            return InspectionResult(
                False,
                f"аномальный расход {vehicle.daily_energy_kwh:.2f} кВт·ч/сутки "
                f"(норма не более {MAX_NORMAL_DAILY_ENERGY_KWH:.2f})",
            )
        return InspectionResult(True, "техосмотр пройден")
