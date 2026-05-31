import math

# ==========================================================
# PHYSICS CONSTANTS
# ==========================================================

G = 9.81
AIR_DENSITY = 1.225

DEFAULT_CDA = 0.35
DEFAULT_CRR = 0.005

WHEEL_CIRCUMFERENCE = 2.11


# ==========================================================
# SPEED SOLVER
# ==========================================================

def solve_speed_from_power(
    power_w,
    total_mass_kg,
    grade_pct,
    wind_kmh=0.0,
    cda=DEFAULT_CDA,
    crr=DEFAULT_CRR,
    max_iter=80,
):
    """
    Estimate cycling speed from rider power.

    Uses binary search because aerodynamic drag depends on v².

    Returns:
        speed (m/s)
    """

    grade = grade_pct / 100
    wind_ms = wind_kmh / 3.6

    def required_power(v):
        """
        Calculate power required to ride at speed v.
        """

        v_air = v + wind_ms

        f_gravity = total_mass_kg * G * grade
        f_rolling = total_mass_kg * G * crr

        # aerodynamic drag
        f_aero = 0.5 * AIR_DENSITY * cda * (v_air ** 2)

        total_force = f_gravity + f_rolling + f_aero
        total_force = max(total_force, 0.1)

        return total_force * v

    low = 0.1
    high = 25.0

    for _ in range(max_iter):
        mid = (low + high) / 2
        p_mid = required_power(mid)

        if p_mid < power_w:
            low = mid
        else:
            high = mid

    return (low + high) / 2


# ==========================================================
# CADENCE
# ==========================================================

def estimate_cadence_rpm(
    speed_kmh,
    chainring_teeth,
    cassette_teeth,
    wheel_circumference_m=WHEEL_CIRCUMFERENCE,
):
    """
    Estimate cadence from speed and gearing.

    Returns:
        cadence (RPM)
    """

    development_m = (
        wheel_circumference_m
        * (chainring_teeth / cassette_teeth)
    )

    speed_m_per_min = speed_kmh * 1000 / 60

    cadence_rpm = speed_m_per_min / development_m

    return cadence_rpm


# ==========================================================
# PACING MODEL
# ==========================================================

def assign_target_power(
    grade_pct,
    base_power_w,
):
    """
    Simple rule-based pacing model.

    Positive grades:
        more power

    Downhill:
        reduced power
    """

    if grade_pct >= 8:
        return base_power_w * 1.08

    if grade_pct >= 4:
        return base_power_w * 1.00

    if grade_pct >= 1:
        return base_power_w * 0.92

    if grade_pct >= -2:
        return base_power_w * 0.82

    return base_power_w * 0.45


# ==========================================================
# SEGMENT SIMULATION
# ==========================================================

def simulate_segment(
    distance_m,
    grade_pct,
    rider_mass_kg,
    bike_mass_kg,
    base_power_w,
    wind_kmh=0.0,
    cda=DEFAULT_CDA,
    crr=DEFAULT_CRR,
):
    """
    Simulate one route segment.

    Returns:
        dict
    """

    total_mass = rider_mass_kg + bike_mass_kg

    target_power = assign_target_power(
        grade_pct,
        base_power_w,
    )

    speed_ms = solve_speed_from_power(
        power_w=target_power,
        total_mass_kg=total_mass,
        grade_pct=grade_pct,
        wind_kmh=wind_kmh,
        cda=cda,
        crr=crr,
    )

    speed_kmh = speed_ms * 3.6

    time_s = distance_m / speed_ms

    return {
        "distance_m": distance_m,
        "grade_pct": grade_pct,
        "target_power_w": target_power,
        "speed_ms": speed_ms,
        "speed_kmh": speed_kmh,
        "time_s": time_s,
    }


# ==========================================================
# QUICK MANUAL TEST
# ==========================================================

if __name__ == "__main__":

    speed_ms = solve_speed_from_power(
        power_w=250,
        total_mass_kg=90,
        grade_pct=2,
        wind_kmh=0,
    )

    print(f"Speed: {speed_ms * 3.6:.1f} km/h")