#!/usr/bin/env python3
"""Run the main concept-aligned platform moderation models."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from platform_moderation.config import (  # noqa: E402
    MARKETING_VARS,
    OUTPUT_BASE,
    PLATFORM_TYPE_DUMMIES,
    WEATHER_CONTROLS,
)
from platform_moderation.data import analysis_samples, load_panel, prepare_panel  # noqa: E402
from platform_moderation.modeling import fit_ols_cluster  # noqa: E402
from platform_moderation.reporting import add_report_columns, label_term  # noqa: E402


OUT = OUTPUT_BASE / "concept_aligned_moderation"
OUT.mkdir(parents=True, exist_ok=True)


def interaction_terms(marketing: list[str], moderators: list[str]) -> list[str]:
    return [f"{m}:{p}" for m in marketing for p in moderators]


def write_sample_summary(samples: dict[str, pd.DataFrame]) -> None:
    rows = []
    for name, sample in samples.items():
        rows.append(
            {
                "sample": name,
                "rows": len(sample),
                "cities": sample["city"].nunique(),
                "city_operators": sample["city_operator"].nunique(),
                "mean_ur": sample["ur"].mean(),
                "mean_ur_boxcox": sample["ur_boxcox"].mean(),
                "platform_any_rows": int(sample["platform_any"].sum()),
                "large_only_rows": int(sample["large_aggregator_only"].sum()),
                "local_only_rows": int(sample["local_maas_only"].sum()),
                "multi_platform_rows": int(sample["multi_platform"].sum()),
                "weak_exposure_rows": int(sample["weak_exposure_only"].sum()),
                "promo_rows": int(sample["promo_active"].sum()),
            }
        )
    pd.DataFrame(rows).to_csv(OUT / "concept_model_sample_summary.csv", index=False)


def write_summaries(results: pd.DataFrame) -> None:
    results = add_report_columns(results)
    results.to_csv(OUT / "concept_moderation_terms.csv", index=False)

    moderation = results.loc[results["term"].str.contains(":", regex=False)].copy()
    rows = []
    for term, group in moderation.groupby("term"):
        if "platform_any" in term:
            market_model = "any_platform_moderation_market_fe_all"
            unit_model = "any_platform_moderation_unit_fe_all"
        else:
            market_model = "type_moderation_market_fe_all"
            unit_model = "type_moderation_unit_fe_all"
        market = group.loc[(group["model"] == market_model) & (group["outcome"] == "ur_boxcox")]
        unit = group.loc[(group["model"] == unit_model) & (group["outcome"] == "ur_boxcox")]
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
    pd.DataFrame(rows).sort_values("label").to_csv(OUT / "moderation_synthesis.csv", index=False)

    primary = results.loc[
        results["outcome"].eq("ur_boxcox")
        & results["model"].isin(
            [
                "any_platform_moderation_market_fe_all",
                "any_platform_moderation_unit_fe_all",
                "type_moderation_market_fe_all",
                "type_moderation_unit_fe_all",
            ]
        )
        & results["term"].str.contains(":", regex=False)
    ].copy()
    primary["fe_strategy"] = primary["model"].map(lambda x: "unit_fe" if "unit_fe" in x else "market_fe")
    primary[
        ["fe_strategy", "model", "label", "coef", "std_err", "p_value", "estimate", "nobs", "city_operators"]
    ].to_csv(OUT / "primary_ur_moderation_terms.csv", index=False)


def main() -> int:
    df = prepare_panel(load_panel())
    samples = analysis_samples(df)
    write_sample_summary(samples)

    marketing = " + ".join(MARKETING_VARS)
    weather = " + ".join(WEATHER_CONTROLS)
    type_terms = " + ".join(PLATFORM_TYPE_DUMMIES)
    any_interactions = " + ".join(interaction_terms(MARKETING_VARS, ["platform_any"]))
    type_interactions = " + ".join(interaction_terms(MARKETING_VARS, PLATFORM_TYPE_DUMMIES))

    rows: list[dict[str, object]] = []
    for sample_name, sample in samples.items():
        for outcome in ["ur_boxcox", "log_trip_count_day"]:
            rows.extend(
                fit_ols_cluster(
                    f"any_platform_moderation_market_fe_{sample_name}",
                    sample,
                    outcome,
                    f"{outcome} ~ {marketing} + platform_any + {any_interactions} + {weather} + C(city) + C(date_str) + C(operator)",
                    ["platform_any", *interaction_terms(MARKETING_VARS, ["platform_any"])],
                    OUT,
                    fe_strategy="market_fe",
                )
            )
            rows.extend(
                fit_ols_cluster(
                    f"any_platform_moderation_unit_fe_{sample_name}",
                    sample,
                    outcome,
                    f"{outcome} ~ {marketing} + platform_any + {any_interactions} + {weather} + C(city_operator) + C(date_str)",
                    ["platform_any", *interaction_terms(MARKETING_VARS, ["platform_any"])],
                    OUT,
                    fe_strategy="unit_fe",
                )
            )
            rows.extend(
                fit_ols_cluster(
                    f"type_moderation_market_fe_{sample_name}",
                    sample,
                    outcome,
                    f"{outcome} ~ {marketing} + {type_terms} + {type_interactions} + {weather} + C(city) + C(date_str) + C(operator)",
                    [*PLATFORM_TYPE_DUMMIES, *interaction_terms(MARKETING_VARS, PLATFORM_TYPE_DUMMIES)],
                    OUT,
                    fe_strategy="market_fe",
                )
            )
            rows.extend(
                fit_ols_cluster(
                    f"type_moderation_unit_fe_{sample_name}",
                    sample,
                    outcome,
                    f"{outcome} ~ {marketing} + {type_terms} + {type_interactions} + {weather} + C(city_operator) + C(date_str)",
                    [*PLATFORM_TYPE_DUMMIES, *interaction_terms(MARKETING_VARS, PLATFORM_TYPE_DUMMIES)],
                    OUT,
                    fe_strategy="unit_fe",
                )
            )

    write_summaries(pd.DataFrame(rows))
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

