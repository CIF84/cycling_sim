import pandas as pd


def _get_time_saved_per_unit(
    roi_table: pd.DataFrame,
    change_name: str,
    units: float,
) -> float:
    row = roi_table[roi_table["change"] == change_name]

    if row.empty:
        return 0.0

    time_saved_min = row.iloc[0]["time_saved_min"]

    return time_saved_min / units


def estimate_custom_improvement(
    roi_table: pd.DataFrame,
    power_gain_w: float = 0.0,
    weight_loss_kg: float = 0.0,
    aero_gain_pct: float = 0.0,
    bike_weight_loss_kg: float = 0.0,
) -> dict:
    """
    Estimate route-specific time savings for custom rider-selected improvements.

    Uses linear interpolation from existing benchmark scenarios.
    This is directional, not a guaranteed prediction.
    """

    power_per_w = _get_time_saved_per_unit(
        roi_table=roi_table,
        change_name="+20 W",
        units=20,
    )

    weight_per_kg = _get_time_saved_per_unit(
        roi_table=roi_table,
        change_name="-5 kg rider",
        units=5,
    )

    aero_per_pct = _get_time_saved_per_unit(
        roi_table=roi_table,
        change_name="10% aero gain",
        units=10,
    )

    bike_weight_per_kg = _get_time_saved_per_unit(
        roi_table=roi_table,
        change_name="-1 kg bike",
        units=1,
    )

    power_saved_min = power_gain_w * power_per_w
    weight_saved_min = weight_loss_kg * weight_per_kg
    aero_saved_min = aero_gain_pct * aero_per_pct
    bike_saved_min = bike_weight_loss_kg * bike_weight_per_kg

    total_saved_min = (
        power_saved_min
        + weight_saved_min
        + aero_saved_min
        + bike_saved_min
    )

    return {
        "power_saved_min": round(power_saved_min, 1),
        "weight_saved_min": round(weight_saved_min, 1),
        "aero_saved_min": round(aero_saved_min, 1),
        "bike_saved_min": round(bike_saved_min, 1),
        "total_saved_min": round(total_saved_min, 1),
    }