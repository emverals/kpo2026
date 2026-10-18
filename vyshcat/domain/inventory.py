"""Базовая реализация инвентаризируемого объекта — общая для транспорта и вещей."""

from vyshcat.domain.interfaces import IInventoryItem


class InventoryObject(IInventoryItem):
    def __init__(self, name: str) -> None:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Наименование не может быть пустым")
        self._name = cleaned
        self._inventory_number: str | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def inventory_number(self) -> str | None:
        return self._inventory_number

    def assign_inventory_number(self, number: str) -> None:
        # Номер выдаётся один раз: повторная выдача означает двойную постановку на баланс.
        if self._inventory_number is not None:
            raise ValueError(f"Объекту «{self._name}» уже выдан номер {self._inventory_number}")
        self._inventory_number = number
