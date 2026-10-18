"""Отчёты: количество, суточная энергия, новички, инвентарная опись."""

import pytest

from tests.conftest import bicycle, cabinet, dock, ebike, helmet, scooter
from vyshcat.services.fleet import FleetService
from vyshcat.services.reports import FleetReportService


def test_counts_empty_fleet_zero(reports: FleetReportService) -> None:
    counts = reports.counts()
    assert (counts.vehicles, counts.items, counts.total) == (0, 0, 0)


def test_counts_vehicles_and_items_separately(
    accepting_fleet: FleetService, reports: FleetReportService
) -> None:
    for v in (scooter(), bicycle(), ebike()):
        accepting_fleet.accept_vehicle(v)
    for i in (helmet(), dock()):
        accepting_fleet.add_item(i)
    counts = reports.counts()
    assert (counts.vehicles, counts.items, counts.total) == (3, 2, 5)


def test_total_energy_empty_fleet_zero(reports: FleetReportService) -> None:
    assert reports.total_daily_energy_kwh() == 0


def test_total_energy_sums_vehicles_and_items(
    accepting_fleet: FleetService, reports: FleetReportService
) -> None:
    accepting_fleet.accept_vehicle(scooter(kwh=0.6))
    accepting_fleet.accept_vehicle(ebike(kwh=1.2))
    accepting_fleet.add_item(dock(kwh=1.5))
    accepting_fleet.add_item(cabinet(kwh=3.0))
    assert reports.total_daily_energy_kwh() == pytest.approx(6.3)


def test_total_energy_bicycle_and_helmet_do_not_change_sum(
    accepting_fleet: FleetService, reports: FleetReportService
) -> None:
    accepting_fleet.accept_vehicle(scooter(kwh=0.5))
    accepting_fleet.add_item(dock(kwh=1.5))
    before = reports.total_daily_energy_kwh()
    accepting_fleet.accept_vehicle(bicycle())
    accepting_fleet.add_item(helmet())
    assert reports.total_daily_energy_kwh() == pytest.approx(before)
    assert before == pytest.approx(2.0)


def test_total_energy_decimal_precision(
    accepting_fleet: FleetService, reports: FleetReportService
) -> None:
    accepting_fleet.accept_vehicle(scooter(kwh=0.1))
    accepting_fleet.accept_vehicle(scooter(kwh=0.2))
    assert reports.total_daily_energy_kwh() == pytest.approx(0.3)


def test_beginner_list_empty_fleet(reports: FleetReportService) -> None:
    assert reports.beginner_friendly_vehicles() == []


def test_beginner_list_includes_only_simplicity_6_and_above(
    accepting_fleet: FleetService, reports: FleetReportService
) -> None:
    easy6 = scooter("Six", simplicity=6)
    hard5 = scooter("Five", simplicity=5)
    easy10 = bicycle("Ten", simplicity=10)
    hard1 = ebike("One", simplicity=1)
    for v in (easy6, hard5, easy10, hard1):
        accepting_fleet.accept_vehicle(v)
    assert reports.beginner_friendly_vehicles() == [easy6, easy10]


def test_beginner_list_excludes_items(
    accepting_fleet: FleetService, reports: FleetReportService
) -> None:
    accepting_fleet.add_item(helmet())
    accepting_fleet.add_item(dock())
    assert reports.beginner_friendly_vehicles() == []


def test_inventory_lists_vehicles_and_items_with_numbers(
    accepting_fleet: FleetService, reports: FleetReportService
) -> None:
    v, h, d = scooter("Ninebot"), helmet("Шлем S"), dock("Док Покровка")
    accepting_fleet.accept_vehicle(v)
    accepting_fleet.add_item(h)
    accepting_fleet.add_item(d)
    lines = {(line.number, line.name, line.kind) for line in reports.inventory()}
    assert lines == {
        (v.inventory_number, "Ninebot", "транспорт"),
        (h.inventory_number, "Шлем S", "вещь"),
        (d.inventory_number, "Док Покровка", "вещь"),
    }


def test_inventory_empty_fleet(reports: FleetReportService) -> None:
    assert reports.inventory() == []
