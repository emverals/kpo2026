"""Каталог видов — точка расширения: новый вид = новый класс + одна строка здесь.

Консольное меню строится по каталогу, поэтому UI и сервисы при этом не меняются.
Нужен ли запрос расхода, выводится из класса (реализует ли он IEnergyConsumer),
поэтому рассинхрон каталога с доменом невозможен.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from vyshcat.domain.interfaces import IEnergyConsumer
from vyshcat.domain.items import ChargingCabinet, DockStation, Helmet, Item
from vyshcat.domain.vehicles import Bicycle, EBike, ElectricScooter, Vehicle


@dataclass(frozen=True)
class VehicleKind:
    title: str
    cls: type[Vehicle]
    # (наименование, простота, расход кВт·ч, дефекты); у неэлектрических расход игнорируется
    factory: Callable[[str, int, float, Sequence[str]], Vehicle]

    @property
    def consumes_energy(self) -> bool:
        return issubclass(self.cls, IEnergyConsumer)


@dataclass(frozen=True)
class ItemKind:
    title: str
    cls: type[Item]
    factory: Callable[[str, float], Item]

    @property
    def consumes_energy(self) -> bool:
        return issubclass(self.cls, IEnergyConsumer)


VEHICLE_KINDS: tuple[VehicleKind, ...] = (
    VehicleKind("Электросамокат", ElectricScooter, ElectricScooter),
    VehicleKind("Велосипед", Bicycle, lambda n, s, _e, d: Bicycle(n, s, d)),
    VehicleKind("Электровелосипед", EBike, EBike),
)

ITEM_KINDS: tuple[ItemKind, ...] = (
    ItemKind("Шлем", Helmet, lambda n, _e: Helmet(n)),
    ItemKind("Док-станция", DockStation, DockStation),
    ItemKind("Зарядный шкаф", ChargingCabinet, ChargingCabinet),
)
