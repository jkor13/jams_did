#!/usr/bin/env python3
"""Run platform x pricing friction x competition mechanism tests and DML."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from platform_moderation.config import OUTPUT_BASE, PRICING_VARS, WEATHER_CONTROLS  # noqa: E402
from platform_moderation.data import load_panel, prepare_panel  # noqa: E402
from platform_moderation.modeling import dml_residualize, fit_ols_cluster  # noqa: E402
from platform_moderation.reporting import add_report_columns, label_term  # noqa: E402


OUT = OUTPUT_BASE / "competition_mechanism_dml"
OUT.mkdir(parents=True, exist_ok=True)
PLATFORMS = ["platform_any", "large_only", "local_only", "multi_platform"]
CONTROLS = [
    "relative_fleet_size_z",
    "Coverage_z",
    "Exclusive_Coverage_z",
    "promo_active",
    *WEATHER_CONTROLS,
]


def add_mechanism_terms(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for platform in PLATFORMS:
        out[f"{platform}_x_competition_z"] = out[platform] * out["competition_z"]
        for price in PRICING_VARS:
            out[f"{price}_x_{platform}"] = out[price] * out[platform]
            out[f"{price}_x_competition_z"] = out[price] * out["competition_z"]
            out[f"{price}_x_{platform}_x_competition_z"] = out[price] * out[platform] * out["competition_z"]
    return out


def focus_terms(platforms: list[str]) -> list[str]:
    terms = []
    for platform in platforms:
        for price in PRICING_VARS:
            terms.extend(
                [
                    f"{price}:competition_z",
                    f"{platform}:competition_z",
                    f"{price}:{platform}:competition_z",
                ]
            )
    return list(dict.fromkeys(terms))


def fit_mechanism(name: str, data: pd.DataFrame, outcome: str, platforms: list[str], fe_strategy: str) -> list[dict[str, object]]:
    base_terms = " + ".join(PRICING_VARS + ["competition_z"] + platforms + CONTROLS)
    interactions = " + ".join([f"{price} * {platform} * competition_z" for platform in platforms for price in PRICING_VARS])
    fe_terms = "C(city) + C(date_str) + C(operator)" if fe_strategy == "market_fe" else "C(city_operator) + C(date_str)"
    return fit_ols_cluster(
        name,
        data,
        outcome,
        f"{outcome} ~ {base_terms} + {interactions} + {fe_terms}",
        focus_terms(platforms),
        OUT,
        fe_strategy=fe_strategy,
    )


def write_sample_summary(samples: dict[str, pd.DataFrame]) -> None:
    rows = []
    for name, sample in samples.items():
        rows.append(
            {
                "sample": name,
                "rows": len(sample),
                "cities": sample["city"].nunique(),
                "city_operators": sample["city_operator"].nunique(),
                "mean_competition": sample["no_shared_provider_total"].mean(),
                "platform_any_rows": int(sample["platform_any"].sum()),
                "large_only_rows": int(sample["large_only"].sum()),
                "local_only_rows": int(sample["local_only"].sum()),
                "multi_platform_rows": int(sample["multi_platform"].sum()),
            }
        )
    pd.DataFrame(rows).to_csv(OUT / "competition_mechanism_sample_summary.csv", index=False)


def write_summaries(results: pd.DataFrame) -> None:
    results = add_report_columns(results)
    results.to_csv(OUT / "competition_mechanism_terms.csv", index=False)
    triples = results.loc[results["term"].str.contains(":competition_z") & results["term"].str.count(":").eq(2)].copy()
    rows = []
    for term, group in triples.groupby("term"):
        market = group.loc[(group["model"] == "type_market_fe_all") & (group["outcome"] == "ur_boxcox")]
        unit = group.loc[(group["model"] == "type_unit_fe_all") & (group["outcome"] == "ur_boxcox")]
        rows.append(
            {
                "term": term,
                "label": label_term(term),
                "n_models": len(group),
                "n_positive_sig_05": int(((group["coef"] > 0) & group["significant_05"]).sum()),
                "n_negative_sig_05": int(((group["coef"] < 0) & group["significant_05"]).sum()),
                "median_coef": group["coef"].median(),
                "market_fe_all_ur_coef": market["coef"].iloc[0] if len(market) else pd.NA,
                "market_fe_all_ur_p": market["p_value"].iloc[0] if len(market) else pd.NA,
                "unit_fe_all_ur_coef": unit["coef"].iloc[0] if len(unit) else pd.NA,
                "unit_fe_all_ur_p": unit["p_value"].iloc[0] if len(unit) else pd.NA,
            }
        )
    pd.DataFrame(rows).sort_values("label").to_csv(OUT / "competition_mechanism_synthesis.csv", index=False)


def main() -> int:
    df = add_mechanism_terms(prepare_panel(load_panel()))
    samples = {
        "all": df,
        "no_weak_exposure": df.loc[df["weak_exposure_only"].eq(0)].copy(),
        "scooter_only": df.loc[df["scooter_operator"].eq(1)].copy(),
    }
    write_sample_summary(samples)

    rows: list[dict[str, object]] = []
    for sample_name, sample in samples.items():
        for outcome in ["ur_boxcox", "log_trip_count_day"]:
            for fe_strategy in ["market_fe", "unit_fe"]:
                rows.extend(fit_mechanism(f"any_{fe_strategy}_{sample_name}", sample, outcome, ["platform_any"], fe_strategy))
                rows.extend(
                    fit_mechanism(f"type_{fe_strategy}_{sample_name}", sample, outcome, ["large_only", "local_only", "multi_platform"], fe_strategy)
                )

    dml_treatments = [
        "unlock_fee_z_x_platform_any_x_competition_z",
        "price_per_minute_z_x_platform_any_x_competition_z",
        "unlock_fee_z_x_large_only_x_competition_z",
        "unlock_fee_z_x_local_only_x_competition_z",
        "unlock_fee_z_x_multi_platform_x_competition_z",
        "price_per_minute_z_x_large_only_x_competition_z",
        "price_per_minute_z_x_local_only_x_competition_z",
        "price_per_minute_z_x_multi_platform_x_competition_z",
    ]
    dml_numeric_controls = [
        *PRICING_VARS,
        "competition_z",
        "platform_any",
        "large_only",
        "local_only",
        "multi_platform",
        *CONTROLS,
        "avg_network_distance_m_z",
        "avg_start_transit_distance_m_z",
    ]
    dml_categorical_controls = ["city", "operator", "date_str", "dow"]
    for sample_name in ["all", "no_weak_exposure"]:
        for outcome in ["ur_boxcox", "log_trip_count_day"]:
            for learner in ["hgb", "rf"]:
                rows.extend(
                    dml_residualize(
                        f"dml_competition_{sample_name}",
                        samples[sample_name],
                        outcome,
                        dml_treatments,
                        dml_numeric_controls,
                        dml_categorical_controls,
                        learner,
                        OUT,
                    )
                )

    write_summaries(pd.DataFrame(rows))
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

