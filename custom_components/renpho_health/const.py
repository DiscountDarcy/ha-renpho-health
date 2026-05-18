"""Constants for the Renpho Health integration."""

from typing import Final

DOMAIN: Final = "renpho_health"
PLATFORMS: Final = ["sensor"]

# Config flow keys
CONF_EMAIL: Final = "email"
CONF_PASSWORD: Final = "password"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_UNIT_SYSTEM: Final = "unit_system"

DEFAULT_SCAN_INTERVAL_MINUTES: Final = 60
MIN_SCAN_INTERVAL_MINUTES: Final = 5

# Unit system choices
UNIT_IMPERIAL: Final = "imperial"
UNIT_METRIC: Final = "metric"
DEFAULT_UNIT_SYSTEM: Final = UNIT_IMPERIAL

# Conversion: 1 kg = 2.20462262185 lbs
KG_TO_LB: Final = 2.20462262185

# Metric keys that represent mass (kg) — these get converted to lbs in Imperial
WEIGHT_KEYS: Final = {"weight", "sinew", "fatFreeWeight"}

# Metric definitions: (key, name, unit, device_class, state_class, icon)
# Keys match the renpho-api response fields
METRICS: Final = [
    ("weight", "Weight", "kg", "weight", "measurement", "mdi:scale-bathroom"),
    ("bmi", "BMI", None, None, "measurement", "mdi:human"),
    ("bodyfat", "Body Fat", "%", None, "measurement", "mdi:water-percent"),
    ("water", "Body Water", "%", None, "measurement", "mdi:water"),
    ("muscle", "Muscle Mass", "%", None, "measurement", "mdi:arm-flex"),
    ("bone", "Bone Mass", "%", None, "measurement", "mdi:bone"),
    ("bmr", "BMR", "kcal/day", None, "measurement", "mdi:fire"),
    ("visfat", "Visceral Fat", None, None, "measurement", "mdi:human-greeting"),
    ("subfat", "Subcutaneous Fat", "%", None, "measurement", "mdi:water-percent"),
    ("protein", "Protein", "%", None, "measurement", "mdi:food-drumstick"),
    ("bodyage", "Body Age", "years", None, "measurement", "mdi:calendar-account"),
    ("sinew", "Lean Body Mass", "kg", "weight", "measurement", "mdi:weight-lifter"),
    ("fatFreeWeight", "Fat Free Weight", "kg", "weight", "measurement", "mdi:weight"),
    ("heartRate", "Heart Rate", "bpm", None, "measurement", "mdi:heart-pulse"),
    ("cardiacIndex", "Cardiac Index", None, None, "measurement", "mdi:heart"),
    ("bodyShape", "Body Shape", None, None, "measurement", "mdi:body"),
]

# API endpoints (from renpho-api constants.py)
API_BASE_URL: Final = "https://cloud.renpho.com"

# Coefficient table for converting raw values when needed
# (renpho-api already applies these, listed here for reference)
WEIGHT_FACTOR_LB_TO_KG: Final = 0.453592
