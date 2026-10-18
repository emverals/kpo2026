"""Проверка расхода энергии — общая для электротранспорта и вещей-потребителей."""

import math

# Физический предел учёта: суточный расход одной единицы парка выше 1 МВт·ч невозможен
# и означает ошибку ввода; заодно исключает переполнение суммы в отчёте до inf.
MAX_DAILY_ENERGY_KWH = 1000.0


def require_energy(daily_energy_kwh: float) -> float:
    value = float(daily_energy_kwh)
    if not math.isfinite(value):
        raise ValueError("Суточный расход энергии должен быть конечным числом")
    if value < 0:
        raise ValueError("Суточный расход энергии не может быть отрицательным")
    if value > MAX_DAILY_ENERGY_KWH:
        raise ValueError(
            f"Суточный расход энергии не может превышать {MAX_DAILY_ENERGY_KWH:g} кВт·ч"
        )
    return value
