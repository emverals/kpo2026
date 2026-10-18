"""Вещи на балансе: не катаются, техосмотр не проходят."""

from vyshcat.domain._validation import require_energy
from vyshcat.domain.interfaces import IEnergyConsumer
from vyshcat.domain.inventory import InventoryObject


class Item(InventoryObject):
    """Инвентаризируемая вещь (не транспорт)."""


class Helmet(Item):
    """Шлем — энергию не потребляет."""


class _PoweredItem(Item, IEnergyConsumer):
    def __init__(self, name: str, daily_energy_kwh: float) -> None:
        super().__init__(name)
        self._daily_energy_kwh = require_energy(daily_energy_kwh)

    @property
    def daily_energy_kwh(self) -> float:
        return self._daily_energy_kwh


class DockStation(_PoweredItem):
    """Док-станция."""


class ChargingCabinet(_PoweredItem):
    """Зарядный шкаф."""
