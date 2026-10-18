"""Доменные инварианты: простота, расход, имя, номер, роли объектов."""

import math

import pytest

from tests.conftest import bicycle, cabinet, dock, ebike, helmet, scooter
from vyshcat.domain._validation import MAX_DAILY_ENERGY_KWH
from vyshcat.domain.interfaces import IEnergyConsumer, IInventoryItem


@pytest.mark.parametrize("simplicity", [0, 11, -1])
def test_vehicle_simplicity_out_of_range_raises(simplicity: int) -> None:
    with pytest.raises(ValueError, match="Простота"):
        scooter(simplicity=simplicity)


@pytest.mark.parametrize("simplicity", [1, 10])
def test_vehicle_simplicity_scale_bounds_accepted(simplicity: int) -> None:
    assert bicycle(simplicity=simplicity).simplicity == simplicity


def test_vehicle_simplicity_string_rejected() -> None:
    with pytest.raises((TypeError, ValueError)):
        scooter(simplicity="7")  # type: ignore[arg-type]


def test_vehicle_simplicity_fractional_rejected() -> None:
    with pytest.raises((TypeError, ValueError)):
        scooter(simplicity=6.5)  # type: ignore[arg-type]


def test_vehicle_negative_energy_raises() -> None:
    with pytest.raises(ValueError, match="отрицательным"):
        ebike(kwh=-0.01)


def test_item_negative_energy_raises() -> None:
    with pytest.raises(ValueError, match="отрицательным"):
        dock(kwh=-1)


def test_vehicle_zero_energy_allowed() -> None:
    assert scooter(kwh=0).daily_energy_kwh == 0.0


def test_vehicle_nan_energy_rejected() -> None:
    with pytest.raises(ValueError):
        scooter(kwh=math.nan)


@pytest.mark.parametrize("kwh", [math.nan, math.inf, -math.inf])
def test_non_finite_energy_rejected_for_vehicles_and_items(kwh: float) -> None:
    with pytest.raises(ValueError, match="конечным"):
        ebike(kwh=kwh)
    with pytest.raises(ValueError, match="конечным"):
        dock(kwh=kwh)


def test_energy_upper_limit_inclusive() -> None:
    assert dock(kwh=MAX_DAILY_ENERGY_KWH).daily_energy_kwh == MAX_DAILY_ENERGY_KWH
    with pytest.raises(ValueError, match="превышать"):
        dock(kwh=MAX_DAILY_ENERGY_KWH + 0.001)
    with pytest.raises(ValueError, match="превышать"):
        ebike(kwh=1e308)


@pytest.mark.parametrize("simplicity", [True, False])
def test_vehicle_simplicity_bool_rejected(simplicity: bool) -> None:
    with pytest.raises(TypeError):
        scooter(simplicity=simplicity)


@pytest.mark.parametrize("name", ["", "   ", "\t\n"])
def test_vehicle_blank_name_raises(name: str) -> None:
    with pytest.raises(ValueError, match="Наименование"):
        scooter(name=name)


def test_item_blank_name_raises() -> None:
    with pytest.raises(ValueError, match="Наименование"):
        helmet(name=" ")


def test_name_is_trimmed() -> None:
    assert bicycle(name="  Stels 🚲  ").name == "Stels 🚲"


def test_beginner_rule_simplicity_6_is_friendly() -> None:
    assert scooter(simplicity=6).is_beginner_friendly is True


def test_beginner_rule_simplicity_5_is_not_friendly() -> None:
    assert scooter(simplicity=5).is_beginner_friendly is False


def test_beginner_rule_electric_energy_exactly_1_is_friendly() -> None:
    assert scooter(simplicity=6, kwh=1.0).is_beginner_friendly is True


def test_beginner_rule_electric_energy_above_1_is_not_friendly() -> None:
    assert scooter(simplicity=6, kwh=1.01).is_beginner_friendly is False


def test_beginner_rule_low_energy_does_not_override_simplicity() -> None:
    assert ebike(simplicity=5, kwh=0.3).is_beginner_friendly is False


def test_beginner_rule_bicycle_only_by_simplicity() -> None:
    assert bicycle(simplicity=6).is_beginner_friendly is True


def test_new_object_has_no_inventory_number() -> None:
    assert scooter().inventory_number is None


def test_inventory_number_assigned_once() -> None:
    v = scooter()
    v.assign_inventory_number("VC-000001")
    assert v.inventory_number == "VC-000001"


def test_inventory_number_second_assignment_raises_and_keeps_first() -> None:
    h = helmet()
    h.assign_inventory_number("IT-000001")
    with pytest.raises(ValueError, match="уже выдан"):
        h.assign_inventory_number("IT-000002")
    assert h.inventory_number == "IT-000001"


def test_defects_blank_entries_ignored() -> None:
    assert scooter(defects=["  ", "", " тормоз "]).defects == ("тормоз",)


@pytest.mark.parametrize("obj", [bicycle(), helmet()], ids=["bicycle", "helmet"])
def test_non_powered_objects_are_not_energy_consumers(obj: IInventoryItem) -> None:
    assert not isinstance(obj, IEnergyConsumer)


@pytest.mark.parametrize(
    "obj", [scooter(), ebike(), dock(), cabinet()], ids=["scooter", "ebike", "dock", "cabinet"]
)
def test_powered_objects_are_energy_consumers(obj: IInventoryItem) -> None:
    assert isinstance(obj, IEnergyConsumer)


@pytest.mark.parametrize(
    "obj",
    [scooter(), ebike(), bicycle(), helmet(), dock(), cabinet()],
    ids=["scooter", "ebike", "bicycle", "helmet", "dock", "cabinet"],
)
def test_all_balance_objects_are_inventory_items(obj: object) -> None:
    assert isinstance(obj, IInventoryItem)
