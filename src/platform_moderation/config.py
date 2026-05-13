"""Shared paths and model constants."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = Path.home() / "dev/ewgt_multilevel_model"
LOCAL_INPUT_DATA = REPO_ROOT / "data/JAMS_df_platform_clean_typed.csv"
LEGACY_INPUT_DATA = BASE / "outputs/reports/platform_feature_research/platform_types/JAMS_df_platform_clean_typed.csv"
INPUT_DATA = LOCAL_INPUT_DATA if LOCAL_INPUT_DATA.exists() else LEGACY_INPUT_DATA
OUTPUT_BASE = REPO_ROOT / "results"

SCOOTER_OPERATORS = {"BOLT", "LIME", "TIER", "VOI"}

MARKETING_VARS = [
    "price_per_minute_z",
    "unlock_fee_z",
    "relative_fleet_size_z",
    "Coverage_z",
    "Exclusive_Coverage_z",
    "promo_active",
]

WEATHER_CONTROLS = [
    "avg_weather_temperature_c_z",
    "avg_weather_precipitation_mm_z",
    "share_weather_is_wet_z",
]

PLATFORM_TYPE_DUMMIES = [
    "large_aggregator_only",
    "local_maas_only",
    "multi_platform",
    "weak_exposure_only",
]

PRICING_VARS = ["unlock_fee_z", "price_per_minute_z"]
