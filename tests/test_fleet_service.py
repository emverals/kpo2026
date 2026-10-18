"""Постановка на баланс: техосмотр до постановки, уникальные номера, вещи без техосмотра."""

import pytest

from tests.conftest import (
    AlwaysAcceptCenter,
    AlwaysRejectCenter,
    SpyServiceCenter,
    bicycle,
    cabinet,
    dock,
    ebike,
    helmet,
    scooter,
)
from vyshcat.services.fleet import FleetService
from vyshcat.services.repository import FleetRepository
from vyshcat.services.service_center import ServiceCenter


def test_accept_vehicle_accepted_goes_to_balance(
    repo: FleetRepository, accepting_fleet: FleetService
) -> None:
    v = scooter()
    result = accepting_fleet.accept_vehicle(v)
    assert result.accepted is True
    assert repo.all() == [v]


def test_accept_vehicle_accepted_gets_inventory_number(accepting_fleet: FleetService) -> None:
    v = scooter()
    accepting_fleet.accept_vehicle(v)
    assert v.inventory_number


def test_accept_vehicle_rejected_not_on_balance(repo: FleetRepository) -> None:
    fleet = FleetService(repo, AlwaysRejectCenter())
    fleet.accept_vehicle(scooter())
    assert repo.all() == []


def test_accept_vehicle_rejected_gets_no_number(repo: FleetRepository) -> None:
    fleet = FleetService(repo, AlwaysRejectCenter())
    v = scooter()
    fleet.accept_vehicle(v)
    assert v.inventory_number is None


def test_accept_vehicle_returns_service_center_verdict_with_reason(
    repo: FleetRepository,
) -> None:
    result = FleetService(repo, AlwaysRejectCenter()).accept_vehicle(scooter())
    assert result.accepted is False
    assert result.reason == AlwaysRejectCenter.REASON


def test_accept_vehicle_inspection_happens_before_registration(
    repo: FleetRepository,
) -> None:
    spy = SpyServiceCenter(repo, accept=True)
    fleet = FleetService(repo, spy)
    v = scooter()
    fleet.accept_vehicle(v)
    assert len(spy.calls) == 1
    inspected, number_at_inspection, balance_at_inspection = spy.calls[0]
    assert inspected is v
    assert number_at_inspection is None
    assert balance_at_inspection == 0
    assert v.inventory_number is not None


def test_accept_vehicle_each_vehicle_inspected_once(repo: FleetRepository) -> None:
    spy = SpyServiceCenter(repo)
    fleet = FleetService(repo, spy)
    vehicles = [scooter(), bicycle(), ebike()]
    for v in vehicles:
        fleet.accept_vehicle(v)
    assert [call[0] for call in spy.calls] == vehicles


def test_add_item_skips_inspection(repo: FleetRepository) -> None:
    spy = SpyServiceCenter(repo, accept=False)
    fleet = FleetService(repo, spy)
    h = helmet()
    number = fleet.add_item(h)
    assert spy.calls == []
    assert repo.all() == [h]
    assert h.inventory_number == number


def test_add_item_with_rejecting_center_still_registered(repo: FleetRepository) -> None:
    fleet = FleetService(repo, AlwaysRejectCenter())
    fleet.add_item(dock())
    assert len(repo.all()) == 1


def test_inventory_numbers_unique_across_vehicles_and_items(
    accepting_fleet: FleetService,
) -> None:
    vehicles = [scooter(), bicycle(), ebike()]
    items = [helmet(), dock(), cabinet()]
    for v in vehicles:
        accepting_fleet.accept_vehicle(v)
    for i in items:
        accepting_fleet.add_item(i)
    numbers = [o.inventory_number for o in [*vehicles, *items]]
    assert None not in numbers
    assert len(set(numbers)) == len(numbers)


def test_two_fleet_services_on_one_repository_give_unique_numbers(
    repo: FleetRepository,
) -> None:
    first = FleetService(repo, AlwaysAcceptCenter())
    second = FleetService(repo, AlwaysAcceptCenter())
    a, b, c = helmet("a"), helmet("b"), helmet("c")
    first.add_item(a)
    second.add_item(b)
    first.add_item(c)
    numbers = [a.inventory_number, b.inventory_number, c.inventory_number]
    assert len(set(numbers)) == 3


def test_rejected_vehicle_does_not_consume_number(repo: FleetRepository) -> None:
    real = FleetService(repo, ServiceCenter())
    first = scooter()
    broken = scooter(defects=["тормоз"])
    second = scooter()
    real.accept_vehicle(first)
    real.accept_vehicle(broken)
    real.accept_vehicle(second)
    assert broken.inventory_number is None
    assert repo.all() == [first, second]
    assert first.inventory_number != second.inventory_number


def test_vehicle_and_item_numbers_distinguishable(accepting_fleet: FleetService) -> None:
    v, h = scooter(), helmet()
    accepting_fleet.accept_vehicle(v)
    accepting_fleet.add_item(h)
    assert v.inventory_number is not None and h.inventory_number is not None
    assert v.inventory_number.split("-")[0] != h.inventory_number.split("-")[0]


def test_accept_same_vehicle_twice_raises_and_not_duplicated(
    repo: FleetRepository, accepting_fleet: FleetService
) -> None:
    v = scooter()
    accepting_fleet.accept_vehicle(v)
    with pytest.raises(ValueError):
        accepting_fleet.accept_vehicle(v)
    assert repo.all() == [v]


def test_add_same_item_twice_raises_and_not_duplicated(
    repo: FleetRepository, accepting_fleet: FleetService
) -> None:
    h = helmet()
    accepting_fleet.add_item(h)
    with pytest.raises(ValueError):
        accepting_fleet.add_item(h)
    assert repo.all() == [h]


def test_numbering_continues_on_prefilled_repository(repo: FleetRepository) -> None:
    FleetService(repo, AlwaysAcceptCenter()).add_item(helmet("a"))
    second_service = FleetService(repo, AlwaysAcceptCenter())
    h = helmet("b")
    second_service.add_item(h)
    numbers = [o.inventory_number for o in repo.all()]
    assert len(set(numbers)) == 2
    assert h.inventory_number in numbers


def test_repository_refuses_object_without_number(repo: FleetRepository) -> None:
    with pytest.raises(ValueError, match="без инвентарного номера"):
        repo.add(helmet())
    assert repo.all() == []


def test_repository_all_returns_copy(repo: FleetRepository) -> None:
    h = helmet()
    h.assign_inventory_number("IT-1")
    repo.add(h)
    repo.all().clear()
    assert repo.all() == [h]


def test_repository_next_number_is_monotonic_and_independent_of_size(
    repo: FleetRepository,
) -> None:
    assert [repo.next_number(), repo.next_number()] == [1, 2]
    assert repo.all() == []
    h = helmet()
    FleetService(repo, AlwaysAcceptCenter()).add_item(h)
    assert h.inventory_number == "IT-000003"
