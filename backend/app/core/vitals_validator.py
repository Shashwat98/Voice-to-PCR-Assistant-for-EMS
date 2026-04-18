"""Vitals validation — reject impossible physiological values before applying to PCR state."""

VITAL_RANGES = {
    "bp_systolic": (40, 300),
    "bp_diastolic": (20, 200),
    "heart_rate": (20, 300),
    "respiratory_rate": (4, 60),
    "spo2": (30, 100),
    "gcs_total": (3, 15),
    "pain_scale": (0, 10),
    "temperature": (85.0, 110.0),
    "blood_glucose": (10, 800),
    "etco2": (5, 100),
    "age": (0, 120),
}


def is_valid_vital(field_name: str, value) -> bool:
    """Return True if the value is within acceptable physiological range."""
    if field_name not in VITAL_RANGES:
        return True

    if value is None:
        return True

    try:
        num = float(value)
    except (ValueError, TypeError):
        return True

    low, high = VITAL_RANGES[field_name]
    return low <= num <= high