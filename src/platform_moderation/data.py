"""Data preparation for platform membership moderation models."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import INPUT_DATA, SCOOTER_OPERATORS


def zscore(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    sd = values.std()
    if not np.isfinite(sd) or sd == 0:
        return values * np.nan
    return (values - values.mean()) / sd


def load_panel(path=INPUT_DATA) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def prepare_panel(frame: pd.DataFrame) -> pd.DataFrame:
    df = frame.copy()
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["date_str"] = df["start_date"].dt.strftime("%Y-%m-%d")
    df["dow"] = df["start_date"].dt.day_name()
    df["log_trip_count_day"] = np.log1p(pd.to_numeric(df["trip_count_day"], errors="coerce"))

    df["platform_any"] = pd.to_numeric(df["platform_membership_clean"], errors="coerce").fillna(0).astype(int)
    df["large_aggregator_only"] = pd.to_numeric(df["platform_large_only_clean"], errors="coerce").fillna(0).astype(int)
    df["large_only"] = df["large_aggregator_only"]
    df["local_maas_only"] = pd.to_numeric(df["platform_local_only_clean"], errors="coerce").fillna(0).astype(int)
    df["local_only"] = df["local_maas_only"]
    df["multi_platform"] = pd.to_numeric(df["platform_both_large_and_local_clean"], errors="coerce").fillna(0).astype(int)
    df["weak_exposure_only"] = pd.to_numeric(df["platform_weak_exposure_type_clean"], errors="coerce").fillna(0).astype(int)
    df["promo_active"] = pd.to_numeric(df["promo_active_clean"], errors="coerce").fillna(0).astype(int)
    df["scooter_operator"] = df["operator"].isin(SCOOTER_OPERATORS).astype(int)

    for column in [
        "price_per_minute",
        "unlock_fee",
        "relative_fleet_size",
        "Coverage",
        "Exclusive_Coverage",
        "no_shared_provider_total",
        "avg_weather_temperature_c",
        "avg_weather_precipitation_mm",
        "share_weather_is_wet",
        "avg_network_distance_m",
        "avg_start_transit_distance_m",
    ]:
        if column in df.columns:
            df[f"{column}_z"] = zscore(df[column])

    if "no_shared_provider_total_z" in df.columns:
        df["competition_z"] = df["no_shared_provider_total_z"]

    return df


def analysis_samples(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "all": df,
        "no_weak_exposure": df.loc[df["weak_exposure_only"].eq(0)].copy(),
        "scooter_only": df.loc[df["scooter_operator"].eq(1)].copy(),
        "post_2024_03_29": df.loc[df["start_date"] >= pd.Timestamp("2024-03-29")].copy(),
    }

