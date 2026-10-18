"""Решение техосмотра реального ServiceCenter."""

import pytest

from tests.conftest import bicycle, ebike, scooter
from vyshcat.services.service_center import MAX_NORMAL_DAILY_ENERGY_KWH, ServiceCenter


@pytest.fixture
def center() -> ServiceCenter:
    return ServiceCenter()


def test_inspect_serviceable_scooter_accepted(center: ServiceCenter) -> None:
    assert center.inspect(scooter(kwh=0.6)).accepted is True


def test_inspect_serviceable_bicycle_accepted(center: ServiceCenter) -> None:
    assert center.inspect(bicycle()).accepted is True


def test_inspect_with_defects_rejected_and_reason_lists_defects(center: ServiceCenter) -> None:
    result = center.inspect(scooter(defects=["тормоз", "люфт руля"]))
    assert result.accepted is False
    assert "тормоз" in result.reason
    assert "люфт руля" in result.reason


def test_inspect_bicycle_with_defects_rejected(center: ServiceCenter) -> None:
    assert center.inspect(bicycle(defects=["цепь"])).accepted is False


def test_inspect_energy_above_threshold_rejected(center: ServiceCenter) -> None:
    result = center.inspect(ebike(kwh=9.5))
    assert result.accepted is False
    assert "расход" in result.reason


def test_inspect_energy_exactly_at_threshold_accepted(center: ServiceCenter) -> None:
    assert center.inspect(ebike(kwh=MAX_NORMAL_DAILY_ENERGY_KWH)).accepted is True


def test_inspect_energy_just_above_threshold_rejected(center: ServiceCenter) -> None:
    assert center.inspect(ebike(kwh=MAX_NORMAL_DAILY_ENERGY_KWH + 0.01)).accepted is False


def test_inspect_whitespace_only_defects_do_not_reject(center: ServiceCenter) -> None:
    assert center.inspect(scooter(defects=["  ", ""])).accepted is True


def test_inspect_does_not_assign_inventory_number(center: ServiceCenter) -> None:
    v = scooter()
    center.inspect(v)
    assert v.inventory_number is None
