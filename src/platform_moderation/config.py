"""Shared paths and model constants."""

from __future__ import annotations

from pathlib import Path


BASE = Path.home() / "dev/ewgt_multilevel_model"
INPUT_DATA = BASE / "outputs/reports/platform_feature_research/platform_types/JAMS_df_platform_clean_typed.csv"
OUTPUT_BASE = BASE / "platform_membership_moderation/results"

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

