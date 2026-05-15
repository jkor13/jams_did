"""Test additional platform-mechanism feature ideas.

This module screens the ten feature ideas discussed after the core platform-membership
models. The goal is not to replace the main specification, but to identify which
additional feature families strengthen the comparison-salience and marketing-mix story.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import OUTPUT_BASE, REPO_ROOT, WEATHER_CONTROLS
from .data import prepare_panel, zscore
from .modeling import fit_ols_cluster
from .reporting import add_report_columns, label_term


INPUT = REPO_ROOT / "data/JAMS_df_platform_extended_features.csv"
OUT = OUTPUT_BASE / "mechanism_feature_tests"
OUT.mkdir(parents=True, exist_ok=True)

PLATFORM_TYPES = ["large_aggregator_only", "local_maas_only", "multi_platform"]
TOTAL_PRICE_DURATIONS = [5, 10, 15]

BASE_CONTROLS = [
    "price_per_minute_z",
    "unlock_fee_z",
    "relative_fleet_size_z",
    "Coverage_z",
    "Exclusive_Coverage_z",
    "promo_active",
    *WEATHER_CONTROLS,
]

SUPPLY_OUTCOME_CONTROLS = [
    "price_per_minute_z",
    "unlock_fee_z",
    "Coverage_z",
    "Exclusive_Coverage_z",
    "promo_active",
    *WEATHER_CONTROLS,
]


IDEA_LABELS = {
    "I1_effective_price": "Effective price and unlock-fee burden",
    "I2_relative_total_price": "Relative total trip price",
    "I3_short_last_mile": "Short-trip and last-mile sensitivity",
    "I4_demand_supply_decomposition": "Demand-supply decomposition",
    "I5_operational_reliability": "Operational reliability and stockout proxy",
    "I6_cheapest_rank": "Cheapest-position and price-rank effects",
    "I7_trip_purpose_fit": "Trip-purpose fit",
    "I8_maturity_adaptation": "Platform maturity and marketing-mix adaptation",
    "I9_outside_options": "Outside-option strength",
    "I10_pass_promotion_softeners": "Pass, free-unlock, and promotion softeners",
}


def plus(terms: list[str]) -> str:
    return " + ".join(terms)


def fe_terms(fe_strategy: str) -> str:
    if fe_strategy == "market_fe":
        return "C(city) + C(date_str) + C(operator)"
    if fe_strategy == "unit_fe":
        return "C(city_operator) + C(date_str)"
    raise ValueError(fe_strategy)


def _safe_divide(num: pd.Series, den: pd.Series) -> pd.Series:
    den = pd.to_numeric(den, errors="coerce").replace(0, np.nan)
    return pd.to_numeric(num, errors="coerce") / den


def _rank_within(frame: pd.DataFrame, value: str, group: list[str]) -> pd.Series:
    return frame.groupby(group)[value].rank(method="dense", ascending=True)


def _standardize_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        out[f"{column}_z"] = zscore(out[column]).fillna(0)
    return out


def add_mechanism_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["date"] = pd.to_datetime(out["start_date"]).dt.strftime("%Y-%m-%d")
    out["date_str"] = out["date"]

    numeric_columns = [
        "unlock_fee",
        "price_per_minute",
        "avg_duration_seconds",
        "avg_distance_meter",
        "avg_network_distance_m",
        "avg_start_transit_distance_m",
        "avg_end_transit_distance_m",
        "active_vehicles_day",
        "trip_count_day",
        "days_since_first_platform_start_clean",
        "PT_availability",
        "population_density",
        "stations_inhabitant",
        "mean_parkgebuehr_offroad",
        "no_shared_provider_total",
        "no_of_vehicle_types",
        "commute_peak_trip_share",
        "night_trip_share",
    ]
    for column in numeric_columns:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce")

    for column in [
        "group_ride",
        "free_unlock_pass_external",
        "minute_bundle_external",
        "pass_available_external",
        "reservation_available_external",
        "mandatory_parking_or_geofence_rules_external",
    ]:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce").fillna(0).astype(int)

    out["duration_min"] = (out["avg_duration_seconds"] / 60).clip(lower=0.1)
    out["expected_trip_price"] = out["unlock_fee"].fillna(0) + out["price_per_minute"].fillna(0) * out["duration_min"]
    out["unlock_fee_share_expected"] = _safe_divide(out["unlock_fee"].fillna(0), out["expected_trip_price"])

    mode_keys = ["city", "date", "vehicle_mode"]
    for minutes in TOTAL_PRICE_DURATIONS:
        total = f"total_price_{minutes}min"
        out[total] = out["unlock_fee"].fillna(0) + out["price_per_minute"].fillna(0) * minutes
        mode_min = out.groupby(mode_keys)[total].transform("min")
        mode_mean = out.groupby(mode_keys)[total].transform("mean")
        out[f"{total}_gap_to_same_mode_min"] = out[total] - mode_min
        out[f"{total}_minus_same_mode_mean"] = out[total] - mode_mean
        out[f"{total}_rank_same_mode"] = _rank_within(out, total, mode_keys)
        out[f"is_same_mode_cheapest_{total}"] = out[total].eq(mode_min).astype(int)

    out["log_trip_count_day"] = np.log1p(out["trip_count_day"].clip(lower=0))
    out["log_active_vehicles_day"] = np.log1p(out["active_vehicles_day"].clip(lower=0))

    out["short_trip_intensity"] = -out["duration_min"]
    out["short_distance_intensity"] = -out["avg_distance_meter"]
    out["transit_proximity"] = -out["avg_start_transit_distance_m"]
    out["network_proximity"] = -out["avg_network_distance_m"]
    out = _standardize_columns(
        out,
        [
            "unlock_fee_share_expected",
            "unlock_fee_rank_same_mode_day",
            "duration_min",
            "short_trip_intensity",
            "short_distance_intensity",
            "transit_proximity",
            "network_proximity",
            "log_active_vehicles_day",
            "commute_peak_trip_share",
            "night_trip_share",
            "no_of_vehicle_types",
        ],
    )
    out["short_last_mile_index_z"] = (
        out[["short_trip_intensity_z", "short_distance_intensity_z", "transit_proximity_z"]].mean(axis=1).pipe(zscore).fillna(0)
    )
    out["last_mile_transit_index_z"] = (
        out[["transit_proximity_z", "network_proximity_z"]].mean(axis=1).pipe(zscore).fillna(0)
    )

    for minutes in TOTAL_PRICE_DURATIONS:
        out = _standardize_columns(
            out,
            [
                f"total_price_{minutes}min",
                f"total_price_{minutes}min_gap_to_same_mode_min",
                f"total_price_{minutes}min_minus_same_mode_mean",
                f"total_price_{minutes}min_rank_same_mode",
            ],
        )

    unit_median_active = out.groupby("city_operator")["log_active_vehicles_day"].transform("median")
    out["active_vehicle_relative_to_unit_median"] = out["log_active_vehicles_day"] - unit_median_active
    out["active_vehicle_reliability_z"] = zscore(out["active_vehicle_relative_to_unit_median"]).fillna(0)
    unit_q25_active = out.groupby("city_operator")["active_vehicles_day"].transform(lambda s: s.quantile(0.25))
    out["low_availability_day"] = out["active_vehicles_day"].le(unit_q25_active).astype(int)

    outside_components = []
    for column in [
        "PT_availability",
        "population_density",
        "stations_inhabitant",
        "mean_parkgebuehr_offroad",
        "no_shared_provider_total",
    ]:
        z_col = f"{column}_outside_z"
        out[z_col] = zscore(out[column]).fillna(0)
        outside_components.append(z_col)
    out["outside_option_strength_index_z"] = out[outside_components].mean(axis=1).pipe(zscore).fillna(0)

    out["platform_age_days"] = out["days_since_first_platform_start_clean"].fillna(0)
    out["platform_age_z"] = zscore(out["platform_age_days"]).fillna(0)
    out["mature_platform_366_plus"] = out["days_since_first_platform_start_clean"].ge(366).fillna(False).astype(int)
    out["early_platform_0_180"] = out["days_since_first_platform_start_clean"].between(0, 180).fillna(False).astype(int)

    unlock_fee = out["unlock_fee"].fillna(0)
    out["unlock_fee_ge_1_00"] = unlock_fee.ge(1.00).astype(int)
    out["unlock_fee_ge_1_20"] = unlock_fee.ge(1.20).astype(int)

    promo_types = out["promo_types_clean"].fillna("").astype(str)
    out["promo_subscriber_free_minutes"] = promo_types.str.contains("subscriber_free_minutes", regex=False).astype(int)
    out["promo_voucher"] = promo_types.str.contains("voucher", regex=False).astype(int)
    out["promo_parking_credit"] = promo_types.str.contains("parking", regex=False).astype(int)
    out["pass_or_usage_cost_softener"] = (
        out[["free_unlock_pass_external", "minute_bundle_external", "promo_subscriber_free_minutes"]].max(axis=1).astype(int)
    )
    return out


def load_samples() -> dict[str, pd.DataFrame]:
    df = prepare_panel(pd.read_csv(INPUT, low_memory=False))
    df = add_mechanism_features(df)
    return {
        "all": df,
        "no_weak_exposure": df.loc[df["weak_exposure_only"].eq(0)].copy(),
        "scooter_only": df.loc[df["scooter_operator"].eq(1)].copy(),
    }


def sample_support(samples: dict[str, pd.DataFrame]) -> None:
    feature_columns = [
        "unlock_fee_share_expected",
        "expected_trip_price",
        "total_price_5min_gap_to_same_mode_min",
        "total_price_10min_gap_to_same_mode_min",
        "total_price_15min_gap_to_same_mode_min",
        "short_last_mile_index_z",
        "last_mile_transit_index_z",
        "active_vehicle_reliability_z",
        "low_availability_day",
        "outside_option_strength_index_z",
        "platform_age_days",
        "promo_subscriber_free_minutes",
        "pass_or_usage_cost_softener",
        "free_unlock_pass_external",
        "minute_bundle_external",
    ]
    rows = []
    for sample_name, data in samples.items():
        for feature in feature_columns:
            values = pd.to_numeric(data[feature], errors="coerce")
            row = {
                "sample": sample_name,
                "feature": feature,
                "non_missing": int(values.notna().sum()),
                "unique_values": int(values.nunique(dropna=True)),
                "mean": values.mean(),
                "sd": values.std(),
                "min": values.min(),
                "max": values.max(),
            }
            for platform in PLATFORM_TYPES:
                subset = data.loc[data[platform].eq(1)]
                row[f"{platform}_rows"] = len(subset)
                row[f"{platform}_nonzero_rows"] = int(pd.to_numeric(subset[feature], errors="coerce").fillna(0).ne(0).sum())
                row[f"{platform}_unique"] = int(pd.to_numeric(subset[feature], errors="coerce").nunique(dropna=True))
            rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / "sample_support.csv", index=False)


def _fit(
    rows: list[dict[str, object]],
    *,
    name: str,
    data: pd.DataFrame,
    outcome: str,
    formula: str,
    focus_terms: list[str],
    fe_strategy: str,
    sample: str,
    idea: str,
    family: str,
    feature: str,
    controls: list[str] | None = None,
) -> None:
    try:
        fitted = fit_ols_cluster(
            name,
            data,
            outcome,
            formula,
            focus_terms,
            OUT,
            fe_strategy=fe_strategy,
        )
    except Exception as exc:  # pragma: no cover - defensive logging for screening runs
        rows.append(
            {
                "model": name,
                "estimator": "ols_cluster",
                "fe_strategy": fe_strategy,
                "outcome": outcome,
                "term": "__MODEL_FAILED__",
                "coef": np.nan,
                "std_err": np.nan,
                "p_value": np.nan,
                "ci_low": np.nan,
                "ci_high": np.nan,
                "nobs": len(data),
                "city_operators": data["city_operator"].nunique(),
                "cities": data["city"].nunique(),
                "r2": np.nan,
                "adj_r2": np.nan,
                "sample": sample,
                "idea": idea,
                "idea_label": IDEA_LABELS[idea],
                "family": family,
                "feature": feature,
                "formula": formula,
                "controls": plus(controls or []),
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        return
    for row in fitted:
        row["sample"] = sample
        row["idea"] = idea
        row["idea_label"] = IDEA_LABELS[idea]
        row["family"] = family
        row["feature"] = feature
        row["formula"] = formula
        row["controls"] = plus(controls or [])
        row["error"] = ""
    rows.extend(fitted)


def fit_platform_feature(
    rows: list[dict[str, object]],
    samples: dict[str, pd.DataFrame],
    *,
    idea: str,
    family: str,
    feature: str,
    outcome: str = "ur_boxcox",
    controls: list[str] | None = None,
    sample_names: list[str] | None = None,
) -> None:
    controls = controls or BASE_CONTROLS
    sample_names = sample_names or list(samples)
    for sample_name in sample_names:
        data = samples[sample_name]
        for fe in ["market_fe", "unit_fe"]:
            focus = [f"{feature}:{platform}" for platform in PLATFORM_TYPES]
            _fit(
                rows,
                name=f"{idea}_{family}_{feature}_{outcome}_{fe}_{sample_name}",
                data=data,
                outcome=outcome,
                formula=f"{outcome} ~ {feature} * ({plus(PLATFORM_TYPES)}) + {plus(controls)} + {fe_terms(fe)}",
                focus_terms=focus,
                fe_strategy=fe,
                sample=sample_name,
                idea=idea,
                family=family,
                feature=feature,
                controls=controls,
            )


def fit_high_fee_triple(
    rows: list[dict[str, object]],
    samples: dict[str, pd.DataFrame],
    *,
    idea: str,
    family: str,
    feature: str,
    threshold: str = "unlock_fee_ge_1_00",
    outcome: str = "ur_boxcox",
    controls: list[str] | None = None,
    sample_names: list[str] | None = None,
) -> None:
    controls = controls or [c for c in BASE_CONTROLS if c != "unlock_fee_z"]
    sample_names = sample_names or list(samples)
    for sample_name in sample_names:
        data = samples[sample_name]
        for fe in ["market_fe", "unit_fe"]:
            focus = [f"{threshold}:{platform}:{feature}" for platform in PLATFORM_TYPES]
            _fit(
                rows,
                name=f"{idea}_{family}_{threshold}_{feature}_{outcome}_{fe}_{sample_name}",
                data=data,
                outcome=outcome,
                formula=f"{outcome} ~ {threshold} * ({plus(PLATFORM_TYPES)}) * {feature} + {plus(controls)} + {fe_terms(fe)}",
                focus_terms=focus,
                fe_strategy=fe,
                sample=sample_name,
                idea=idea,
                family=family,
                feature=f"{threshold} x {feature}",
                controls=controls,
            )


def fit_outside_option_triple(
    rows: list[dict[str, object]],
    samples: dict[str, pd.DataFrame],
    *,
    feature: str,
    sample_names: list[str] | None = None,
) -> None:
    controls = BASE_CONTROLS
    sample_names = sample_names or list(samples)
    for sample_name in sample_names:
        data = samples[sample_name]
        for fe in ["market_fe", "unit_fe"]:
            focus = [f"{feature}:{platform}:outside_option_strength_index_z" for platform in PLATFORM_TYPES]
            _fit(
                rows,
                name=f"I9_outside_options_{feature}_{fe}_{sample_name}",
                data=data,
                outcome="ur_boxcox",
                formula=(
                    f"ur_boxcox ~ {feature} * ({plus(PLATFORM_TYPES)}) * outside_option_strength_index_z "
                    f"+ {plus(controls)} + {fe_terms(fe)}"
                ),
                focus_terms=focus,
                fe_strategy=fe,
                sample=sample_name,
                idea="I9_outside_options",
                family="outside_option_triple",
                feature=f"{feature} x outside_option_strength",
                controls=controls,
            )


def fit_maturity_adaptation(rows: list[dict[str, object]], samples: dict[str, pd.DataFrame]) -> None:
    data = samples["all"]
    outcomes = {
        "unlock_fee_z": "price_access",
        "price_per_minute_z": "price_usage",
        "relative_fleet_size_z": "supply_scale",
        "log_active_vehicles_day_z": "active_supply",
        "no_of_vehicle_types_z": "product_breadth",
        "promo_active": "promotion_activity",
    }
    for platform in PLATFORM_TYPES:
        subset = data.loc[data[platform].eq(1)].copy()
        if subset["city_operator"].nunique() < 3:
            continue
        for outcome, feature_family in outcomes.items():
            _fit(
                rows,
                name=f"I8_maturity_adaptation_{feature_family}_{outcome}_{platform}",
                data=subset,
                outcome=outcome,
                formula=f"{outcome} ~ platform_age_z + C(city) + C(operator)",
                focus_terms=["platform_age_z"],
                fe_strategy="descriptive_city_operator",
                sample=platform,
                idea="I8_maturity_adaptation",
                family=f"maturity_adaptation_{feature_family}",
                feature=f"platform_age_z within {platform}",
                controls=[],
            )


def fit_demand_supply_decomposition(rows: list[dict[str, object]], samples: dict[str, pd.DataFrame]) -> None:
    outcomes = ["ur_boxcox", "log_trip_count_day", "log_active_vehicles_day"]
    features = ["unlock_fee_ge_1_00", "total_price_10min_gap_to_same_mode_min_z"]
    for outcome in outcomes:
        controls = SUPPLY_OUTCOME_CONTROLS if outcome == "log_active_vehicles_day" else BASE_CONTROLS
        for feature in features:
            if feature == "unlock_fee_ge_1_00":
                controls_for_model = [c for c in controls if c != "unlock_fee_z"]
            else:
                controls_for_model = controls
            fit_platform_feature(
                rows,
                samples,
                idea="I4_demand_supply_decomposition",
                family=f"decomposition_{outcome}",
                feature=feature,
                outcome=outcome,
                controls=controls_for_model,
                sample_names=["all", "no_weak_exposure"],
            )


def fit_all_models(samples: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    fit_platform_feature(
        rows,
        samples,
        idea="I1_effective_price",
        family="unlock_fee_burden",
        feature="unlock_fee_share_expected_z",
    )

    for minutes in TOTAL_PRICE_DURATIONS:
        fit_platform_feature(
            rows,
            samples,
            idea="I2_relative_total_price",
            family=f"relative_total_price_{minutes}min",
            feature=f"total_price_{minutes}min_gap_to_same_mode_min_z",
        )

    for feature in ["short_last_mile_index_z", "last_mile_transit_index_z"]:
        fit_high_fee_triple(
            rows,
            samples,
            idea="I3_short_last_mile",
            family="high_fee_context_triple",
            feature=feature,
        )

    fit_demand_supply_decomposition(rows, samples)

    for feature in ["active_vehicle_reliability_z", "low_availability_day"]:
        fit_platform_feature(
            rows,
            samples,
            idea="I5_operational_reliability",
            family="reliability_platform_fit",
            feature=feature,
        )
        fit_high_fee_triple(
            rows,
            samples,
            idea="I5_operational_reliability",
            family="high_fee_reliability_triple",
            feature=feature,
        )

    cheapest_features = [
        "is_same_mode_cheapest_unlock_fee",
        "unlock_fee_rank_same_mode_day_z",
        "is_same_mode_cheapest_total_price_5min",
        "total_price_5min_rank_same_mode_z",
        "is_same_mode_cheapest_total_price_10min",
        "total_price_10min_rank_same_mode_z",
        "is_same_mode_cheapest_total_price_15min",
        "total_price_15min_rank_same_mode_z",
    ]
    for feature in cheapest_features:
        fit_platform_feature(
            rows,
            samples,
            idea="I6_cheapest_rank",
            family="cheapest_rank_platform_fit",
            feature=feature,
        )

    for feature in ["commute_peak_trip_share_z", "night_trip_share_z"]:
        fit_platform_feature(
            rows,
            samples,
            idea="I7_trip_purpose_fit",
            family="trip_purpose_platform_fit",
            feature=feature,
        )
        fit_high_fee_triple(
            rows,
            samples,
            idea="I7_trip_purpose_fit",
            family="high_fee_trip_purpose_triple",
            feature=feature,
        )

    fit_maturity_adaptation(rows, samples)

    for feature in ["unlock_fee_share_expected_z", "total_price_10min_gap_to_same_mode_min_z"]:
        fit_outside_option_triple(rows, samples, feature=feature)

    for feature in [
        "promo_subscriber_free_minutes",
        "pass_or_usage_cost_softener",
        "free_unlock_pass_external",
        "minute_bundle_external",
    ]:
        fit_platform_feature(
            rows,
            samples,
            idea="I10_pass_promotion_softeners",
            family="cost_softener_platform_fit",
            feature=feature,
        )
        fit_high_fee_triple(
            rows,
            samples,
            idea="I10_pass_promotion_softeners",
            family="high_fee_cost_softener_triple",
            feature=feature,
        )

    return rows


def summarize(results: pd.DataFrame) -> pd.DataFrame:
    summary_rows = []
    valid = results.loc[~results["term"].eq("__MODEL_FAILED__")].copy()
    for (idea, family, feature, outcome, term), group in valid.groupby(["idea", "family", "feature", "outcome", "term"]):
        all_market = group.loc[group["sample"].eq("all") & group["fe_strategy"].eq("market_fe")]
        all_unit = group.loc[group["sample"].eq("all") & group["fe_strategy"].eq("unit_fe")]
        summary_rows.append(
            {
                "idea": idea,
                "idea_label": IDEA_LABELS[idea],
                "family": family,
                "feature": feature,
                "outcome": outcome,
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
                "all_market_fe_nobs": all_market["nobs"].iloc[0] if len(all_market) else pd.NA,
                "all_unit_fe_nobs": all_unit["nobs"].iloc[0] if len(all_unit) else pd.NA,
            }
        )
    summary = pd.DataFrame(summary_rows)
    summary.sort_values(
        ["idea", "n_negative_sig_05", "n_positive_sig_05", "family", "term"],
        ascending=[True, False, False, True, True],
    ).to_csv(OUT / "summary.csv", index=False)
    return summary


def write_curated_findings(summary: pd.DataFrame) -> None:
    rows = []
    for idea, group in summary.groupby("idea"):
        strongest = group.sort_values(
            ["n_negative_sig_05", "n_positive_sig_05", "n_models"], ascending=[False, False, False]
        ).head(8)
        rows.append(
            {
                "idea": idea,
                "idea_label": IDEA_LABELS[idea],
                "top_terms_json": strongest.to_json(orient="records"),
                "negative_significant_terms": int((group["n_negative_sig_05"] > 0).sum()),
                "positive_significant_terms": int((group["n_positive_sig_05"] > 0).sum()),
                "screening_note": "Screening summary only; inspect summary.csv and terms.csv before paper-facing interpretation.",
            }
        )
    pd.DataFrame(rows).to_csv(OUT / "curated_findings.csv", index=False)


def write_readme() -> None:
    (OUT / "README.md").write_text(
        """# Mechanism Feature Tests

Screens ten additional feature ideas for the platform-membership moderation paper.

Feature families:

1. Effective price and unlock-fee burden.
2. Relative total trip price for 5-, 10-, and 15-minute trips.
3. Short-trip and last-mile sensitivity.
4. Demand-supply decomposition across utilisation, trip volume, and active vehicles.
5. Operational reliability and low-availability proxies.
6. Cheapest-position and price-rank effects.
7. Trip-purpose fit through commute-peak and night-trip shares.
8. Platform maturity and marketing-mix adaptation.
9. Outside-option strength as a city-context boundary condition.
10. Pass, free-unlock, and promotion softeners.

Main outputs:

- `sample_support.csv`: support and variation for the new features.
- `terms.csv`: all estimated focal coefficients.
- `summary.csv`: stability summary by idea/family/feature/term.
- `curated_findings.csv`: compact idea-level screening output.

Identification note:

The module is a screening layer. Features that are provider-level or campaign-sparse
should be interpreted as mechanism probes rather than causal city-date estimates.
""",
        encoding="utf-8",
    )


def run_mechanism_feature_tests() -> pd.DataFrame:
    samples = load_samples()
    sample_support(samples)
    rows = fit_all_models(samples)
    results = add_report_columns(pd.DataFrame(rows))
    results.to_csv(OUT / "terms.csv", index=False)
    if "significant_05" in results:
        results.loc[results["significant_05"]].to_csv(OUT / "significant_terms.csv", index=False)
    failures = results.loc[results["term"].eq("__MODEL_FAILED__")]
    if not failures.empty:
        failures.to_csv(OUT / "model_failures.csv", index=False)
    summary = summarize(results)
    write_curated_findings(summary)
    write_readme()
    return results
