"""Хранилище объектов на балансе (в памяти).

Интерфейса нет сознательно: реализация одна, тестам подмена не нужна. Появится второе
хранилище (файл, БД) — тогда и будет выделен интерфейс из этих методов.
"""

from vyshcat.domain.interfaces import IInventoryItem
from vyshcat.domain.items import Item
from vyshcat.domain.vehicles import Vehicle


class FleetRepository:
    def __init__(self) -> None:
        self._objects: list[IInventoryItem] = []
        self._last_number = 0

    def add(self, obj: IInventoryItem) -> None:
        if obj.inventory_number is None:
            raise ValueError(f"Нельзя хранить «{obj.name}» без инвентарного номера")
        self._objects.append(obj)

    def next_number(self) -> int:
        """Монотонный счётчик: номер не переиспользуется, даже если объект потом спишут."""
        self._last_number += 1
        return self._last_number

    def all(self) -> list[IInventoryItem]:
        return list(self._objects)

    def vehicles(self) -> list[Vehicle]:
        return [o for o in self._objects if isinstance(o, Vehicle)]

    def items(self) -> list[Item]:
        return [o for o in self._objects if isinstance(o, Item)]
