"""DI: подмена техосмотра через build_container и общие singleton-зависимости."""

from tests.conftest import AlwaysAcceptCenter, AlwaysRejectCenter, ebike, helmet, scooter
from vyshcat.console.app import ConsoleApp
from vyshcat.console.io import ConsoleIO, ScriptedIO
from vyshcat.container import build_container
from vyshcat.services.fleet import FleetService
from vyshcat.services.reports import FleetReportService
from vyshcat.services.repository import FleetRepository
from vyshcat.services.service_center import IServiceCenter, ServiceCenter


def test_container_with_rejecting_stub_fleet_rejects_serviceable_vehicle() -> None:
    container = build_container(service_center=AlwaysRejectCenter())
    fleet = container.resolve(FleetService)
    v = scooter(kwh=0.5)  # реальный техосмотр принял бы
    result = fleet.accept_vehicle(v)
    assert result.accepted is False
    assert v.inventory_number is None
    assert container.resolve(FleetReportService).counts().vehicles == 0


def test_container_with_accepting_stub_fleet_accepts_defective_vehicle() -> None:
    container = build_container(service_center=AlwaysAcceptCenter())
    fleet = container.resolve(FleetService)
    v = ebike(kwh=50.0, defects=["нет тормозов"])  # реальный техосмотр отклонил бы
    result = fleet.accept_vehicle(v)
    assert result.accepted is True
    assert v.inventory_number is not None
    assert container.resolve(FleetReportService).counts().vehicles == 1


def test_container_resolves_injected_stub_as_service_center() -> None:
    stub = AlwaysRejectCenter()
    assert build_container(service_center=stub).resolve(IServiceCenter) is stub


def test_default_container_uses_real_service_center() -> None:
    container = build_container()
    assert type(container.resolve(IServiceCenter)) is ServiceCenter


def test_default_container_fleet_applies_real_inspection() -> None:
    fleet = build_container().resolve(FleetService)
    assert fleet.accept_vehicle(scooter(kwh=0.5)).accepted is True
    assert fleet.accept_vehicle(scooter(defects=["тормоз"])).accepted is False


def test_container_fleet_and_reports_share_repository() -> None:
    container = build_container(service_center=AlwaysAcceptCenter())
    fleet = container.resolve(FleetService)
    reports = container.resolve(FleetReportService)
    fleet.accept_vehicle(scooter(kwh=0.5))
    fleet.add_item(helmet())
    counts = reports.counts()
    assert (counts.vehicles, counts.items) == (1, 1)
    assert len(container.resolve(FleetRepository).all()) == 2


def test_container_repository_is_singleton() -> None:
    container = build_container()
    assert container.resolve(FleetRepository) is container.resolve(FleetRepository)


def test_container_fleet_service_is_singleton_numbers_not_reused() -> None:
    container = build_container(service_center=AlwaysAcceptCenter())
    a, b = helmet("a"), helmet("b")
    assert container.resolve(FleetService) is container.resolve(FleetService)
    container.resolve(FleetService).add_item(a)
    container.resolve(FleetService).add_item(b)
    assert a.inventory_number != b.inventory_number


def test_separate_containers_have_isolated_fleets() -> None:
    first = build_container(service_center=AlwaysAcceptCenter())
    first.resolve(FleetService).add_item(helmet())
    second = build_container(service_center=AlwaysAcceptCenter())
    assert second.resolve(FleetReportService).counts().total == 0


def test_container_injects_io_into_console_app() -> None:
    out: list[str] = []
    io = ScriptedIO(write=out.append, answers=["0"])
    build_container(io=io).resolve(ConsoleApp).run()
    assert any("До свидания" in line for line in out)


def test_default_container_io_is_console_io() -> None:
    assert type(build_container().resolve(ConsoleIO)) is ConsoleIO
