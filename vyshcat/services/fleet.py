"""Постановка на баланс: техосмотр транспорта и выдача инвентарных номеров."""

from vyshcat.domain.interfaces import IInventoryItem
from vyshcat.domain.items import Item
from vyshcat.domain.vehicles import Vehicle
from vyshcat.services.repository import FleetRepository
from vyshcat.services.service_center import InspectionResult, IServiceCenter

VEHICLE_PREFIX = "VC"
ITEM_PREFIX = "IT"


class FleetService:
    def __init__(self, repository: FleetRepository, service_center: IServiceCenter) -> None:
        self._repository = repository
        self._service_center = service_center

    def accept_vehicle(self, vehicle: Vehicle) -> InspectionResult:
        """Номер выдаётся только принятой технике — отклонённая на баланс не попадает."""
        result = self._service_center.inspect(vehicle)
        if result.accepted:
            self._register(vehicle, VEHICLE_PREFIX)
        return result

    def add_item(self, item: Item) -> str:
        """Вещи не ездят, поэтому ставятся на баланс без техосмотра."""
        return self._register(item, ITEM_PREFIX)

    def _register(self, obj: IInventoryItem, prefix: str) -> str:
        # Источник истины — репозиторий: номера сквозные и не дублируются между сервисами.
        number = f"{prefix}-{self._repository.next_number():06d}"
        obj.assign_inventory_number(number)
        self._repository.add(obj)
        return number
