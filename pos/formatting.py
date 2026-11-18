from __future__ import annotations

from decimal import Decimal


def format_decimal(value: Decimal) -> str:
    """Число без хвостовых нулей и без экспоненциальной записи."""
    return format(value.normalize(), "f")
