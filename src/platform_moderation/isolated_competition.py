"""Isolated competition mechanism tests.

The model family here deliberately keeps the specification narrow:

    unlock fee x platform membership x competition

It avoids simultaneous platform-type and full marketing-mix interactions to test
whether the comparison/competition mechanism can be stabilized.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import OUTPUT_BASE, WEATHER_CONTROLS
from .data import load_panel, prepare_panel, zscore
from .modeling import dml_residualize, fit_ols_cluster
from .reporting import add_report_columns, label_term


OUT = OUTPUT_BASE / "isolated_competition_pricing"
OUT.mkdir(parents=True, exist_ok=True)

COMPETITION_MEASURES = [
    "city_competition_z",
    "active_city_operators_z",
    "active_operators_z",
    "market_fragmentation_z",
    "leave_one_out_competitor_trips_z",
]


def plus(terms: list[str]) -> str:
    return " + ".join(terms)


def fe_terms(fe: str) -> str:
    if fe == "market_fe":
        return "C(city) + C(date_str) + C(operator)"
    if fe == "unit_fe":
        return "C(city_operator) + C(date_str)"
    if fe == "citydate_fe":
        return "C(city_operator) + C(city):C(date_str)"
    raise ValueError(fe)


def add_competition_measures(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["city_competition_z"] = out["no_shared_provider_total_z"]
    active = out["trip_count_day"].fillna(0).gt(0)

    city_date = (
        out.loc[active]
        .groupby(["city", "date_str"])
        .agg(
            active_city_operators=("city_operator", "nunique"),
            active_operators=("operator", "nunique"),
            city_date_trips=("trip_count_day", "sum"),
        )
        .reset_index()
    )
    shares = out.loc[active, ["city", "date_str", "city_operator", "trip_count_day"]].copy()
    shares["city_date_trips"] = shares.groupby(["city", "date_str"])["trip_count_day"].transform("sum")
    shares["trip_share"] = shares["trip_count_day"] / shares["city_date_trips"]
    hhi = shares.groupby(["city", "date_str"])["trip_share"].apply(lambda s: float(np.square(s).sum())).rename("trip_hhi")
    city_date = city_date.merge(hhi.reset_index(), on=["city", "date_str"], how="left")
    out = out.merge(city_date, on=["city", "date_str"], how="left")
    out["leave_one_out_competitor_trips"] = out["city_date_trips"] - out["trip_count_day"]
    out["market_fragmentation"] = 1 - out["trip_hhi"]

    for col in [
        "active_city_operators",
        "active_operators",
        "market_fragmentation",
        "leave_one_out_competitor_trips",
    ]:
        out[f"{col}_z"] = zscore(out[col])

    for measure in COMPETITION_MEASURES:
        out[f"unlock_fee_z_x_platform_any_x_{measure}"] = out["unlock_fee_z"] * out["platform_any"] * out[measure]
    return out


def samples(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "all": df,
        "no_weak_exposure": df.loc[df["weak_exposure_only"].eq(0)].copy(),
        "scooter_only": df.loc[df["scooter_operator"].eq(1)].copy(),
        "bookable_or_none": df.loc[df["platform_any"].eq(1) | df["weak_exposure_only"].eq(0)].copy(),
    }


def write_sample_summary(sample_map: dict[str, pd.DataFrame]) -> None:
    rows = []
    for name, data in sample_map.items():
        rows.append(
            {
                "sample": name,
                "rows": len(data),
                "cities": data["city"].nunique(),
                "city_operators": data["city_operator"].nunique(),
                "mean_ur": data["ur"].mean(),
                "mean_city_competition": data["no_shared_provider_total"].mean(),
                "mean_active_city_operators": data["active_city_operators"].mean(),
                "mean_market_fragmentation": data["market_fragmentation"].mean(),
                "platform_any_rows": int(data["platform_any"].sum()),
            }
        )
    pd.DataFrame(rows).to_csv(OUT / "sample_summary.csv", index=False)


def fit_narrow_models(sample_map: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    rows = []
    controls = [
        "price_per_minute_z",
        "relative_fleet_size_z",
        "Coverage_z",
        "Exclusive_Coverage_z",
        "promo_active",
        *WEATHER_CONTROLS,
    ]
    for sample_name, data in sample_map.items():
        for measure in COMPETITION_MEASURES:
            focus = [
                "unlock_fee_z:platform_any",
                f"unlock_fee_z:platform_any:{measure}",
            ]
            for fe in ["market_fe", "unit_fe"]:
                name = f"isolated_competition_{measure}_{fe}_{sample_name}"
                formula = (
                    f"ur_boxcox ~ unlock_fee_z * platform_any * {measure} + {plus(controls)} + {fe_terms(fe)}"
                )
                fitted = fit_ols_cluster(name, data, "ur_boxcox", formula, focus, OUT, fe_strategy=fe)
                for row in fitted:
                    row["sample"] = sample_name
                    row["competition_measure"] = measure
                    row["idea"] = "isolated_competition_pricing"
                rows.extend(fitted)
    return rows


def fit_dml_models(sample_map: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    rows = []
    base_controls = [
        "unlock_fee_z",
        "platform_any",
        "price_per_minute_z",
        "relative_fleet_size_z",
        "Coverage_z",
        "Exclusive_Coverage_z",
        "promo_active",
        *WEATHER_CONTROLS,
        "avg_network_distance_m_z",
        "avg_start_transit_distance_m_z",
    ]
    categorical = ["city", "operator", "date_str", "dow"]
    for sample_name in ["all", "no_weak_exposure"]:
        data = sample_map[sample_name]
        for measure in COMPETITION_MEASURES:
            treatment = f"unlock_fee_z_x_platform_any_x_{measure}"
            for learner in ["hgb", "rf"]:
                fitted = dml_residualize(
                    f"isolated_competition_dml_{measure}_{sample_name}",
                    data,
                    "ur_boxcox",
                    [treatment],
                    [*base_controls, measure],
                    categorical,
                    learner,
                    OUT,
                )
                for row in fitted:
                    row["sample"] = sample_name
                    row["competition_measure"] = measure
                    row["idea"] = "isolated_competition_pricing"
                rows.extend(fitted)
    return rows


def write_outputs(rows: list[dict[str, object]]) -> pd.DataFrame:
    results = add_report_columns(pd.DataFrame(rows))
    results.to_csv(OUT / "terms.csv", index=False)
    triples = results.loc[
        results["term"].str.contains("unlock_fee_z", regex=False)
        & results["term"].str.contains("platform_any", regex=False)
        & results["term"].str.contains("z", regex=False)
        & (
            results["term"].str.count(":").eq(2)
            | results["term"].str.contains("_x_platform_any_x_", regex=False)
        )
    ].copy()
    summary_rows = []
    for (measure, estimator, fe), group in triples.groupby(["competition_measure", "estimator", "fe_strategy"], dropna=False):
        summary_rows.append(
            {
                "competition_measure": measure,
                "estimator": estimator,
                "fe_strategy": fe,
                "n_models": len(group),
                "n_negative_sig_05": int(((group["coef"] < 0) & (group["p_value"] < 0.05)).sum()),
                "n_positive_sig_05": int(((group["coef"] > 0) & (group["p_value"] < 0.05)).sum()),
                "median_coef": group["coef"].median(),
                "all_coef": group.loc[group["sample"].eq("all"), "coef"].iloc[0] if group["sample"].eq("all").any() else pd.NA,
                "all_p": group.loc[group["sample"].eq("all"), "p_value"].iloc[0] if group["sample"].eq("all").any() else pd.NA,
                "no_weak_coef": group.loc[group["sample"].eq("no_weak_exposure"), "coef"].iloc[0]
                if group["sample"].eq("no_weak_exposure").any()
                else pd.NA,
                "no_weak_p": group.loc[group["sample"].eq("no_weak_exposure"), "p_value"].iloc[0]
                if group["sample"].eq("no_weak_exposure").any()
                else pd.NA,
            }
        )
    pd.DataFrame(summary_rows).sort_values(["competition_measure", "estimator", "fe_strategy"]).to_csv(
        OUT / "triple_interaction_stability.csv", index=False
    )
    return results


def run_isolated_competition() -> pd.DataFrame:
    df = add_competition_measures(prepare_panel(load_panel()))
    sample_map = samples(df)
    write_sample_summary(sample_map)
    rows = []
    rows.extend(fit_narrow_models(sample_map))
    rows.extend(fit_dml_models(sample_map))
    results = write_outputs(rows)
    (OUT / "README.md").write_text(
        """# Isolated Competition Pricing Mechanism

This folder isolates the competition mechanism around one focal term:

`unlock_fee x platform_any x competition`

Competition is tested with five separate measures:

- `city_competition_z`: standardized `no_shared_provider_total`.
- `active_city_operators_z`: active city-operator count per city-day.
- `active_operators_z`: active operator count per city-day.
- `market_fragmentation_z`: `1 - trip_hhi` based on city-day trip shares.
- `leave_one_out_competitor_trips_z`: city-day trips by all other providers.

Outputs:

- `terms.csv`: all focal coefficients.

The OLS tests use market-FE and unit-FE specifications. A fully saturated city-date FE dummy model is intentionally omitted here because it is computationally unstable for this exploratory mechanism scan; DML residualization provides the nonlinear robustness check.
- `triple_interaction_stability.csv`: stability summary by competition measure and estimator.
- `sample_summary.csv`: sample diagnostics.
""",
        encoding="utf-8",
    )
    return results

