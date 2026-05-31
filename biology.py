HUMAN_EFFICIENCY = 0.22
HUMAN_EFFICIENCY_FACTOR = (1 - HUMAN_EFFICIENCY) / HUMAN_EFFICIENCY

DEHYDRATION_BUFFER = 0.02

SODIUM_PER_L_SWEAT = 1000
SODIUM_REPLACE_RATIO = 0.60

KCAL_PER_GRAM_CARB = 4
CARB_OXIDATION_RATIO = 0.50

RECOVERY_CARB_MULT = 1.2
RECOVERY_PRO_MULT = 0.4


def estimate_segment_biology(power_w, time_s, temp_c, humidity_pct):
    """
    Estimate energy, carbs, heat, sweat, and sodium for one segment.
    """
    heat_watts = power_w * HUMAN_EFFICIENCY_FACTOR
    kcal = (power_w * time_s / 4184) / HUMAN_EFFICIENCY
    carbs_g = (kcal * CARB_OXIDATION_RATIO) / KCAL_PER_GRAM_CARB

    humidity_multiplier = 1.0 + max(0, humidity_pct - 30) / 120
    temperature_multiplier = 2.0 if temp_c >= 30 else 1.0

    sweat_l = (
        (heat_watts / 1000)
        * humidity_multiplier
        * temperature_multiplier
        * (time_s / 3600)
    )

    sodium_mg = sweat_l * SODIUM_PER_L_SWEAT * SODIUM_REPLACE_RATIO

    return {
        "heat_watts": heat_watts,
        "kcal": kcal,
        "carbs_g": carbs_g,
        "sweat_l": sweat_l,
        "sodium_mg": sodium_mg,
    }


def estimate_recovery_meal(rider_mass_kg):
    return {
        "carbs_g": rider_mass_kg * RECOVERY_CARB_MULT,
        "protein_g": rider_mass_kg * RECOVERY_PRO_MULT,
    }


def estimate_fluid_goal_l(sweat_l, rider_mass_kg):
    allowed_deficit_l = rider_mass_kg * DEHYDRATION_BUFFER
    return max(0.0, sweat_l - allowed_deficit_l)