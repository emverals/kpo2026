"""Композиция зависимостей. Единственное место, где выбираются конкретные реализации."""

import punq

from vyshcat.console.app import ConsoleApp
from vyshcat.console.io import ConsoleIO
from vyshcat.services.catalog import ITEM_KINDS, VEHICLE_KINDS
from vyshcat.services.fleet import FleetService
from vyshcat.services.reports import FleetReportService
from vyshcat.services.repository import FleetRepository
from vyshcat.services.service_center import IServiceCenter, ServiceCenter


def build_container(
    service_center: IServiceCenter | None = None, io: ConsoleIO | None = None
) -> punq.Container:
    """Параметры позволяют подменить техосмотр и ввод-вывод (тесты, демо) без перерегистрации."""
    container = punq.Container()
    container.register(FleetRepository, instance=FleetRepository())
    container.register(
        IServiceCenter, instance=ServiceCenter() if service_center is None else service_center
    )
    container.register(ConsoleIO, instance=ConsoleIO() if io is None else io)
    container.register(FleetService, scope=punq.Scope.singleton)
    container.register(FleetReportService, scope=punq.Scope.singleton)
    container.register(
        ConsoleApp,
        factory=lambda: ConsoleApp(
            container.resolve(FleetService),
            container.resolve(FleetReportService),
            VEHICLE_KINDS,
            ITEM_KINDS,
            container.resolve(ConsoleIO),
        ),
    )
    return container
