"""Additional exploratory effect probes for the platform membership paper."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .config import OUTPUT_BASE, PRICING_VARS, WEATHER_CONTROLS
from .data import load_panel, prepare_panel, zscore
from .modeling import fit_ols_cluster
from .reporting import add_report_columns, label_term


OUT = OUTPUT_BASE / "deep_dive_effects"
OUT.mkdir(parents=True, exist_ok=True)

TYPE_TERMS = ["large_aggregator_only", "local_maas_only", "multi_platform"]
PLATFORM_DUMMIES = [
    "platform_Free_Now_clean",
    "platform_Jelbi_clean",
    "platform_hvv_switch_clean",
    "platform_myVRN_clean",
    "platform_redy_clean",
    "platform_BONNmobil_clean",
    "platform_KVV_regiomove_clean",
    "platform_LeipzigMOVE_clean",
]
CITY_CONTEXT = [
    "population_density",
    "share_15to29y",
    "average_montly_income",
    "PT_availability",
    "stations_inhabitant",
    "Zentralitätskennziffer_2023",
    "mean_parkgebuehr_offroad",
    "mean_parking_garage_fee_1h",
    "Congestion_Rank_in_Germany",
    "ADFC_Gesamt_2022_rev",
]
TRIP_CONTEXT = [
    "avg_network_distance_m",
    "avg_start_transit_distance_m",
    "avg_weather_precipitation_mm",
    "share_weather_is_wet",
]


@dataclass(frozen=True)
class ProbeSpec:
    family: str
    name: str
    sample: str
    formula: str
    focus_terms: list[str]
    fe_strategy: str


def plus(terms: list[str]) -> str:
    return " + ".join(terms)


def fe_terms(fe_strategy: str) -> str:
    if fe_strategy == "market_fe":
        return "C(city) + C(date_str) + C(operator)"
    if fe_strategy == "unit_fe":
        return "C(city_operator) + C(date_str)"
    raise ValueError(fe_strategy)


def add_probe_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["platform_count_intensity"] = pd.to_numeric(out["platform_count_clean"], errors="coerce").fillna(0)
    out["platform_exposure_count_intensity"] = pd.to_numeric(out["platform_exposure_count_clean"], errors="coerce").fillna(0)
    out["platform_maturity_days"] = pd.to_numeric(out["days_since_first_platform_start_clean"], errors="coerce").fillna(0)
    for col in ["platform_count_intensity", "platform_exposure_count_intensity", "platform_maturity_days"]:
        out[f"{col}_z"] = zscore(out[col]).fillna(0)

    out["high_unlock_fee"] = (
        pd.to_numeric(out["unlock_fee"], errors="coerce")
        > pd.to_numeric(out.loc[out["unlock_fee"].gt(0), "unlock_fee"], errors="coerce").median()
    ).astype(int)
    out["zero_unlock_fee"] = pd.to_numeric(out["unlock_fee"], errors="coerce").fillna(0).eq(0).astype(int)
    out["high_price_per_minute"] = (
        pd.to_numeric(out["price_per_minute"], errors="coerce")
        > pd.to_numeric(out["price_per_minute"], errors="coerce").median()
    ).astype(int)

    for col in CITY_CONTEXT + TRIP_CONTEXT:
        if col in out.columns:
            out[f"{col}_z"] = zscore(out[col]).fillna(0)

    for col in PLATFORM_DUMMIES:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(int)

    promo = out["promo_types_clean"].fillna("").astype(str)
    out["promo_voucher_20eur"] = promo.str.contains("voucher_20eur_limited_eligibility", regex=False).astype(int)
    out["promo_subscriber_minutes"] = promo.str.contains("subscriber_free_minutes_15_per_month", regex=False).astype(int)
    out["promo_parking_credit"] = promo.str.contains("parking_station_credit_0_50_eur", regex=False).astype(int)
    return out


def load_samples() -> dict[str, pd.DataFrame]:
    df = add_probe_features(prepare_panel(load_panel()))
    return {
        "all": df,
        "no_weak_exposure": df.loc[df["weak_exposure_only"].eq(0)].copy(),
        "scooter_only": df.loc[df["scooter_operator"].eq(1)].copy(),
    }


def sample_summary(samples: dict[str, pd.DataFrame]) -> None:
    rows = []
    for name, data in samples.items():
        rows.append(
            {
                "sample": name,
                "rows": len(data),
                "cities": data["city"].nunique(),
                "city_operators": data["city_operator"].nunique(),
                "platform_any_rows": int(data["platform_any"].sum()),
                "multi_platform_rows": int(data["multi_platform"].sum()),
                "mean_platform_count": data["platform_count_intensity"].mean(),
                "mean_platform_maturity_days": data["platform_maturity_days"].mean(),
                "high_unlock_fee_rows": int(data["high_unlock_fee"].sum()),
                "zero_unlock_fee_rows": int(data["zero_unlock_fee"].sum()),
                "promo_voucher_rows": int(data["promo_voucher_20eur"].sum()),
                "promo_subscriber_rows": int(data["promo_subscriber_minutes"].sum()),
                "promo_parking_rows": int(data["promo_parking_credit"].sum()),
            }
        )
    pd.DataFrame(rows).to_csv(OUT / "sample_summary.csv", index=False)


def build_specs(samples: dict[str, pd.DataFrame]) -> list[ProbeSpec]:
    specs: list[ProbeSpec] = []
    controls = ["relative_fleet_size_z", "Coverage_z", "Exclusive_Coverage_z", "promo_active", *WEATHER_CONTROLS]
    pricing_controls = [*PRICING_VARS, "relative_fleet_size_z", "Coverage_z", "Exclusive_Coverage_z", *WEATHER_CONTROLS]

    intensity_terms = [
        "platform_count_intensity_z",
        "platform_exposure_count_intensity_z",
        "platform_maturity_days_z",
    ]
    for sample in ["all", "no_weak_exposure", "scooter_only"]:
        for fe in ["market_fe", "unit_fe"]:
            specs.append(
                ProbeSpec(
                    "platform_intensity_maturity",
                    f"platform_intensity_maturity_{fe}_{sample}",
                    sample,
                    f"ur_boxcox ~ ({plus(PRICING_VARS)}) * ({plus(intensity_terms)}) + {plus(controls)} + {fe_terms(fe)}",
                    [f"{price}:{term}" for price in PRICING_VARS for term in intensity_terms],
                    fe,
                )
            )

    available_platforms = [
        col
        for col in PLATFORM_DUMMIES
        if col in samples["all"].columns and samples["all"][col].sum() >= 250 and samples["all"].loc[samples["all"][col].eq(1), "city_operator"].nunique() >= 2
    ]
    for sample in ["all", "no_weak_exposure"]:
        for fe in ["market_fe", "unit_fe"]:
            specs.append(
                ProbeSpec(
                    "platform_specific_pricing",
                    f"platform_specific_pricing_{fe}_{sample}",
                    sample,
                    f"ur_boxcox ~ ({plus(PRICING_VARS)}) * ({plus(available_platforms)}) + {plus(controls)} + {fe_terms(fe)}",
                    [f"{price}:{platform}" for price in PRICING_VARS for platform in available_platforms],
                    fe,
                )
            )

    for moderator in [f"{col}_z" for col in CITY_CONTEXT if f"{col}_z" in samples["all"].columns]:
        for sample in ["all", "no_weak_exposure"]:
            for fe in ["market_fe", "unit_fe"]:
                specs.append(
                    ProbeSpec(
                        "city_context_boundary",
                        f"city_context_{moderator}_{fe}_{sample}",
                        sample,
                        f"ur_boxcox ~ unlock_fee_z * platform_any * {moderator} + price_per_minute_z * platform_any * {moderator} + {plus(controls)} + {fe_terms(fe)}",
                        [
                            f"unlock_fee_z:platform_any:{moderator}",
                            f"price_per_minute_z:platform_any:{moderator}",
                        ],
                        fe,
                    )
                )

    threshold_terms = ["high_unlock_fee", "zero_unlock_fee", "high_price_per_minute"]
    for sample in ["all", "no_weak_exposure", "scooter_only"]:
        for fe in ["market_fe", "unit_fe"]:
            specs.append(
                ProbeSpec(
                    "pricing_thresholds",
                    f"pricing_thresholds_any_{fe}_{sample}",
                    sample,
                    f"ur_boxcox ~ ({plus(threshold_terms)}) * platform_any + {plus(controls)} + {fe_terms(fe)}",
                    [f"{term}:platform_any" for term in threshold_terms],
                    fe,
                )
            )
            specs.append(
                ProbeSpec(
                    "pricing_thresholds",
                    f"pricing_thresholds_type_{fe}_{sample}",
                    sample,
                    f"ur_boxcox ~ ({plus(threshold_terms)}) * ({plus(TYPE_TERMS)}) + {plus(controls)} + {fe_terms(fe)}",
                    [f"{term}:{typ}" for term in threshold_terms for typ in TYPE_TERMS],
                    fe,
                )
            )

    for moderator in [f"{col}_z" for col in TRIP_CONTEXT if f"{col}_z" in samples["all"].columns]:
        for sample in ["all", "scooter_only"]:
            for fe in ["market_fe", "unit_fe"]:
                specs.append(
                    ProbeSpec(
                        "trip_context_boundary",
                        f"trip_context_{moderator}_{fe}_{sample}",
                        sample,
                        f"ur_boxcox ~ unlock_fee_z * platform_any * {moderator} + price_per_minute_z * platform_any * {moderator} + {plus(controls)} + {fe_terms(fe)}",
                        [
                            f"unlock_fee_z:platform_any:{moderator}",
                            f"price_per_minute_z:platform_any:{moderator}",
                        ],
                        fe,
                    )
                )

    promo_terms = ["promo_voucher_20eur", "promo_subscriber_minutes", "promo_parking_credit"]
    for sample in ["all", "no_weak_exposure"]:
        for fe in ["market_fe", "unit_fe"]:
            specs.append(
                ProbeSpec(
                    "promotion_type_fit",
                    f"promotion_type_fit_any_{fe}_{sample}",
                    sample,
                    f"ur_boxcox ~ ({plus(promo_terms)}) * platform_any + {plus(pricing_controls)} + {fe_terms(fe)}",
                    [f"{term}:platform_any" for term in promo_terms],
                    fe,
                )
            )
            specs.append(
                ProbeSpec(
                    "promotion_type_fit",
                    f"promotion_type_fit_type_{fe}_{sample}",
                    sample,
                    f"ur_boxcox ~ ({plus(promo_terms)}) * ({plus(TYPE_TERMS)}) + {plus(pricing_controls)} + {fe_terms(fe)}",
                    [f"{term}:{typ}" for term in promo_terms for typ in TYPE_TERMS],
                    fe,
                )
            )
    return specs


def fit_specs(specs: list[ProbeSpec], samples: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for spec in specs:
        fitted = fit_ols_cluster(
            spec.name,
            samples[spec.sample],
            "ur_boxcox",
            spec.formula,
            spec.focus_terms,
            OUT,
            fe_strategy=spec.fe_strategy,
        )
        for row in fitted:
            row["sample"] = spec.sample
            row["family"] = spec.family
        rows.extend(fitted)
    return rows


def write_outputs(rows: list[dict[str, object]]) -> pd.DataFrame:
    results = add_report_columns(pd.DataFrame(rows))
    results.to_csv(OUT / "terms.csv", index=False)
    summary_rows = []
    for (family, term), group in results.groupby(["family", "term"]):
        all_market = group.loc[group["sample"].eq("all") & group["fe_strategy"].eq("market_fe")]
        all_unit = group.loc[group["sample"].eq("all") & group["fe_strategy"].eq("unit_fe")]
        summary_rows.append(
            {
                "family": family,
                "term": term,
                "label": label_term(term),
                "n_models": len(group),
                "n_negative_sig_05": int(((group["coef"] < 0) & group["significant_05"]).sum()),
                "n_positive_sig_05": int(((group["coef"] > 0) & group["significant_05"]).sum()),
                "median_coef": group["coef"].median(),
                "all_market_fe_coef": all_market["coef"].iloc[0] if len(all_market) else pd.NA,
                "all_market_fe_p": all_market["p_value"].iloc[0] if len(all_market) else pd.NA,
                "all_unit_fe_coef": all_unit["coef"].iloc[0] if len(all_unit) else pd.NA,
                "all_unit_fe_p": all_unit["p_value"].iloc[0] if len(all_unit) else pd.NA,
            }
        )
    summary = pd.DataFrame(summary_rows).sort_values(
        ["n_negative_sig_05", "n_positive_sig_05", "family", "term"], ascending=[False, False, True, True]
    )
    summary.to_csv(OUT / "summary.csv", index=False)
    results.loc[results["significant_05"]].to_csv(OUT / "significant_terms.csv", index=False)
    (OUT / "README.md").write_text(
        """# Deep Dive Effects

Additional exploratory probes beyond the seven main idea tests.

Families:
- `platform_intensity_maturity`: platform count, exposure count, and membership maturity.
- `platform_specific_pricing`: pricing moderation by individual platform membership.
- `city_context_boundary`: city mobility and demographic context as boundary conditions.
- `pricing_thresholds`: nonlinear high/zero pricing-friction indicators.
- `trip_context_boundary`: route/transit/weather context as boundary conditions.
- `promotion_type_fit`: promotion type by platform context.

Outputs:
- `terms.csv`: all focal coefficients.
- `summary.csv`: term-level stability summary.
- `significant_terms.csv`: significant focal coefficients.
- `sample_summary.csv`: sample diagnostics.
""",
        encoding="utf-8",
    )
    return results


def run_deep_dive_effects() -> pd.DataFrame:
    samples = load_samples()
    sample_summary(samples)
    specs = build_specs(samples)
    rows = fit_specs(specs, samples)
    return write_outputs(rows)
