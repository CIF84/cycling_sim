# ==========================================================
# SURFACE PRESETS
# ==========================================================
# Crr = rolling resistance coefficient.
# Higher Crr = more energy lost to tire/surface deformation.

SURFACE_PRESETS = {
    "smooth_road": {
        "label": "Smooth road",
        "crr": 0.004,
    },
    "normal_road": {
        "label": "Normal road",
        "crr": 0.005,
    },
    "hardpack_gravel": {
        "label": "Hardpack gravel",
        "crr": 0.007,
    },
    "mixed_gravel": {
        "label": "Mixed gravel",
        "crr": 0.010,
    },
    "rough_gravel": {
        "label": "Rough gravel",
        "crr": 0.014,
    },
}


# ==========================================================
# AERO PRESETS
# ==========================================================

AERO_PRESETS = {
    "upright_gravel": {
        "label": "Upright gravel",
        "cda": 0.42,
    },
    "endurance_road": {
        "label": "Endurance road",
        "cda": 0.35,
    },
    "aggressive_road": {
        "label": "Aggressive road",
        "cda": 0.30,
    },
}


def get_surface_crr(surface_key):
    if surface_key not in SURFACE_PRESETS:
        valid = ", ".join(SURFACE_PRESETS.keys())
        raise ValueError(f"Unknown surface '{surface_key}'. Valid options: {valid}")

    return SURFACE_PRESETS[surface_key]["crr"]


def get_aero_cda(aero_key):
    if aero_key not in AERO_PRESETS:
        valid = ", ".join(AERO_PRESETS.keys())
        raise ValueError(f"Unknown aero preset '{aero_key}'. Valid options: {valid}")

    return AERO_PRESETS[aero_key]["cda"]