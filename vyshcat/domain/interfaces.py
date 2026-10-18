"""Роли объектов учёта. Разделены (ISP): велосипед и шлем на балансе, но энергию не тратят."""

from abc import ABC, abstractmethod


class IInventoryItem(ABC):
    """Объект, стоящий на балансе: имеет наименование и инвентарный номер."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def inventory_number(self) -> str | None:
        """None — номер ещё не выдан (объект не поставлен на баланс)."""

    @abstractmethod
    def assign_inventory_number(self, number: str) -> None: ...


class IEnergyConsumer(ABC):
    """Потребитель энергии: учитывается в суммарном суточном расходе парка."""

    @property
    @abstractmethod
    def daily_energy_kwh(self) -> float: ...
