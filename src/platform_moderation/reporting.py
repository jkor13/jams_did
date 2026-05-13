"""Shared reporting helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def star(p_value: float) -> str:
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    if p_value < 0.1:
        return "+"
    return ""


def label_term(term: str) -> str:
    return (
        term.replace("price_per_minute_z", "Price/min")
        .replace("unlock_fee_z", "Unlock fee")
        .replace("relative_fleet_size_z", "Relative fleet")
        .replace("Coverage_z", "Coverage")
        .replace("Exclusive_Coverage_z", "Exclusive coverage")
        .replace("promo_active", "Promotion")
        .replace("platform_any", "Any platform")
        .replace("large_aggregator_only", "FreeNow only")
        .replace("large_only", "FreeNow only")
        .replace("local_maas_only", "Local MaaS only")
        .replace("local_only", "Local MaaS only")
        .replace("multi_platform", "Multi-platform")
        .replace("weak_exposure_only", "Weak exposure only")
        .replace("competition_z", "Competition")
    )


def add_report_columns(results: pd.DataFrame) -> pd.DataFrame:
    df = results.copy()
    df["significant_05"] = df["p_value"] < 0.05
    df["label"] = df["term"].map(label_term)
    df["estimate"] = df.apply(lambda r: f"{r['coef']:.3f}{star(r['p_value'])}", axis=1)
    df["effect_direction"] = np.select([df["coef"] > 0, df["coef"] < 0], ["positive", "negative"], default="zero")
    return df

