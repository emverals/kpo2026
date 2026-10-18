"""Транспорт. Виды с электроприводом дополнительно реализуют IEnergyConsumer."""

from collections.abc import Iterable

from vyshcat.domain._validation import require_energy
from vyshcat.domain.interfaces import IEnergyConsumer
from vyshcat.domain.inventory import InventoryObject

MIN_SIMPLICITY = 1
MAX_SIMPLICITY = 10
BEGINNER_SIMPLICITY_THRESHOLD = 6
# Мощная техника быстрее разгоняется и тяжелее в управлении — новичку её не выдают.
BEGINNER_MAX_DAILY_ENERGY_KWH = 1.0


class Vehicle(InventoryObject):
    """Прокатная техника: простота для новичка и заявленные при приёмке неисправности."""

    def __init__(self, name: str, simplicity: int, defects: Iterable[str] = ()) -> None:
        super().__init__(name)
        # bool — подкласс int, но «простота True» бессмысленна; дробные шкала не допускает.
        if isinstance(simplicity, bool) or not isinstance(simplicity, int):
            raise TypeError(f"Простота должна быть целым числом, получено {simplicity!r}")
        if not MIN_SIMPLICITY <= simplicity <= MAX_SIMPLICITY:
            raise ValueError(
                f"Простота должна быть от {MIN_SIMPLICITY} до {MAX_SIMPLICITY}, "
                f"получено {simplicity}"
            )
        self._simplicity = simplicity
        self._defects = tuple(d.strip() for d in defects if d.strip())

    @property
    def simplicity(self) -> int:
        return self._simplicity

    @property
    def defects(self) -> tuple[str, ...]:
        return self._defects

    @property
    def is_beginner_friendly(self) -> bool:
        return self._simplicity >= BEGINNER_SIMPLICITY_THRESHOLD


class Bicycle(Vehicle):
    """Обычный велосипед — энергию не потребляет."""


class _ElectricVehicle(Vehicle, IEnergyConsumer):
    def __init__(
        self, name: str, simplicity: int, daily_energy_kwh: float, defects: Iterable[str] = ()
    ) -> None:
        super().__init__(name, simplicity, defects)
        self._daily_energy_kwh = require_energy(daily_energy_kwh)

    @property
    def daily_energy_kwh(self) -> float:
        return self._daily_energy_kwh

    @property
    def is_beginner_friendly(self) -> bool:
        # Подтип только усиливает правило базы: простота по-прежнему обязательна.
        return (
            super().is_beginner_friendly and self._daily_energy_kwh <= BEGINNER_MAX_DAILY_ENERGY_KWH
        )


class ElectricScooter(_ElectricVehicle):
    """Электросамокат."""


class EBike(_ElectricVehicle):
    """Электровелосипед."""
