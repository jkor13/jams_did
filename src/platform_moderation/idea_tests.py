"""Separate hypothesis tests for the seven JAMS story extensions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .config import MARKETING_VARS, OUTPUT_BASE, PLATFORM_TYPE_DUMMIES, PRICING_VARS, WEATHER_CONTROLS
from .data import load_panel, prepare_panel, zscore
from .modeling import dml_residualize, fit_ols_cluster
from .reporting import add_report_columns, label_term


IDEA_OUTPUT_BASE = OUTPUT_BASE / "idea_tests"
TYPE_PLATFORMS = ["large_aggregator_only", "local_maas_only", "multi_platform"]


@dataclass(frozen=True)
class ModelSpec:
    name: str
    sample: str
    outcome: str
    formula: str
    focus_terms: list[str]
    fe_strategy: str


def plus(terms: list[str]) -> str:
    return " + ".join(terms)


def interactions(left: list[str], right: list[str]) -> list[str]:
    return [f"{a}:{b}" for a in left for b in right]


def fe_terms(fe_strategy: str) -> str:
    if fe_strategy == "market_fe":
        return "C(city) + C(date_str) + C(operator)"
    if fe_strategy == "unit_fe":
        return "C(city_operator) + C(date_str)"
    raise ValueError(fe_strategy)


def add_competition_measures(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["city_date"] = out["city"].astype(str) + "_" + out["date_str"].astype(str)
    active = out["trip_count_day"].fillna(0).gt(0)
    city_date_active = (
        out.loc[active]
        .groupby(["city", "date_str"])
        .agg(
            active_city_operators=("city_operator", "nunique"),
            active_operators=("operator", "nunique"),
            total_trips=("trip_count_day", "sum"),
        )
        .reset_index()
    )
    shares = out.loc[active, ["city", "date_str", "city_operator", "trip_count_day"]].copy()
    shares["city_date_trips"] = shares.groupby(["city", "date_str"])["trip_count_day"].transform("sum")
    shares["trip_share"] = shares["trip_count_day"] / shares["city_date_trips"]
    hhi = shares.groupby(["city", "date_str"])["trip_share"].apply(lambda x: float(np.square(x).sum())).rename("trip_hhi").reset_index()
    city_date_active = city_date_active.merge(hhi, on=["city", "date_str"], how="left")
    out = out.merge(city_date_active, on=["city", "date_str"], how="left")
    out["active_city_operators_z"] = zscore(out["active_city_operators"])
    out["active_operators_z"] = zscore(out["active_operators"])
    out["trip_hhi_z"] = zscore(out["trip_hhi"])
    out["comparison_intensity_z"] = out["active_city_operators_z"]

    for platform in ["platform_any", *TYPE_PLATFORMS]:
        for price in PRICING_VARS:
            out[f"{price}_x_{platform}_x_comparison_intensity_z"] = (
                out[price] * out[platform] * out["comparison_intensity_z"]
            )
    return out


def load_samples() -> dict[str, pd.DataFrame]:
    df = add_competition_measures(prepare_panel(load_panel()))
    return {
        "all": df,
        "no_weak_exposure": df.loc[df["weak_exposure_only"].eq(0)].copy(),
        "scooter_only": df.loc[df["scooter_operator"].eq(1)].copy(),
    }


def sample_summary(samples: dict[str, pd.DataFrame], out_dir: Path) -> None:
    rows = []
    for name, data in samples.items():
        rows.append(
            {
                "sample": name,
                "rows": len(data),
                "cities": data["city"].nunique(),
                "city_operators": data["city_operator"].nunique(),
                "mean_ur": data["ur"].mean(),
                "mean_ur_boxcox": data["ur_boxcox"].mean(),
                "mean_log_trips": data["log_trip_count_day"].mean(),
                "platform_any_rows": int(data["platform_any"].sum()),
                "large_only_rows": int(data["large_aggregator_only"].sum()),
                "local_only_rows": int(data["local_maas_only"].sum()),
                "multi_platform_rows": int(data["multi_platform"].sum()),
                "weak_exposure_rows": int(data["weak_exposure_only"].sum()),
                "promo_rows": int(data["promo_active"].sum()),
            }
        )
    pd.DataFrame(rows).to_csv(out_dir / "sample_summary.csv", index=False)


def write_outputs(rows: list[dict[str, object]], out_dir: Path) -> pd.DataFrame:
    results = add_report_columns(pd.DataFrame(rows))
    results.to_csv(out_dir / "terms.csv", index=False)
    summary_rows = []
    for term, group in results.groupby("term"):
        primary = group.loc[(group["sample"] == "all") & (group["outcome"] == "ur_boxcox")]
        summary_rows.append(
            {
                "term": term,
                "label": label_term(term),
                "n_models": len(group),
                "n_positive_sig_05": int(((group["coef"] > 0) & group["significant_05"]).sum()),
                "n_negative_sig_05": int(((group["coef"] < 0) & group["significant_05"]).sum()),
                "median_coef": group["coef"].median(),
                "all_ur_market_fe_coef": primary.loc[primary["fe_strategy"].eq("market_fe"), "coef"].iloc[0]
                if (primary["fe_strategy"].eq("market_fe")).any()
                else pd.NA,
                "all_ur_market_fe_p": primary.loc[primary["fe_strategy"].eq("market_fe"), "p_value"].iloc[0]
                if (primary["fe_strategy"].eq("market_fe")).any()
                else pd.NA,
                "all_ur_unit_fe_coef": primary.loc[primary["fe_strategy"].eq("unit_fe"), "coef"].iloc[0]
                if (primary["fe_strategy"].eq("unit_fe")).any()
                else pd.NA,
                "all_ur_unit_fe_p": primary.loc[primary["fe_strategy"].eq("unit_fe"), "p_value"].iloc[0]
                if (primary["fe_strategy"].eq("unit_fe")).any()
                else pd.NA,
            }
        )
    pd.DataFrame(summary_rows).sort_values("label").to_csv(out_dir / "summary.csv", index=False)
    return results


def fit_specs(specs: list[ModelSpec], samples: dict[str, pd.DataFrame], out_dir: Path) -> list[dict[str, object]]:
    rows = []
    for spec in specs:
        fitted = fit_ols_cluster(
            spec.name,
            samples[spec.sample],
            spec.outcome,
            spec.formula,
            spec.focus_terms,
            out_dir,
            fe_strategy=spec.fe_strategy,
        )
        for row in fitted:
            row["sample"] = spec.sample
            row["idea"] = out_dir.name
        rows.extend(fitted)
    return rows


def idea_01_pricing_architecture(samples: dict[str, pd.DataFrame], out_dir: Path) -> list[dict[str, object]]:
    controls = ["relative_fleet_size_z", "Coverage_z", "Exclusive_Coverage_z", "promo_active", *WEATHER_CONTROLS]
    focus = ["unlock_fee_z", "price_per_minute_z", "unlock_fee_z:platform_any", "price_per_minute_z:platform_any"]
    specs = []
    for sample in ["all", "no_weak_exposure", "scooter_only"]:
        for fe in ["market_fe", "unit_fe"]:
            specs.append(
                ModelSpec(
                    f"pricing_architecture_{fe}_{sample}",
                    sample,
                    "ur_boxcox",
                    f"ur_boxcox ~ unlock_fee_z * platform_any + price_per_minute_z * platform_any + {plus(controls)} + {fe_terms(fe)}",
                    focus,
                    fe,
                )
            )
    return fit_specs(specs, samples, out_dir)


def idea_02_marketing_mix_contingency(samples: dict[str, pd.DataFrame], out_dir: Path) -> list[dict[str, object]]:
    focus = interactions(MARKETING_VARS, ["platform_any"])
    specs = []
    for sample in ["all", "no_weak_exposure", "scooter_only"]:
        for fe in ["market_fe", "unit_fe"]:
            specs.append(
                ModelSpec(
                    f"marketing_mix_contingency_{fe}_{sample}",
                    sample,
                    "ur_boxcox",
                    f"ur_boxcox ~ ({plus(MARKETING_VARS)}) * platform_any + {plus(WEATHER_CONTROLS)} + {fe_terms(fe)}",
                    focus,
                    fe,
                )
            )
    return fit_specs(specs, samples, out_dir)


def idea_03_platform_type_boundary(samples: dict[str, pd.DataFrame], out_dir: Path) -> list[dict[str, object]]:
    controls = ["relative_fleet_size_z", "Coverage_z", "Exclusive_Coverage_z", "promo_active", *WEATHER_CONTROLS]
    type_terms = ["large_aggregator_only", "local_maas_only", "multi_platform", "weak_exposure_only"]
    focus = [*type_terms, *interactions(PRICING_VARS, type_terms)]
    specs = []
    for sample in ["all", "no_weak_exposure"]:
        for fe in ["market_fe", "unit_fe"]:
            specs.append(
                ModelSpec(
                    f"platform_type_boundary_{fe}_{sample}",
                    sample,
                    "ur_boxcox",
                    f"ur_boxcox ~ ({plus(PRICING_VARS)}) * ({plus(type_terms)}) + {plus(controls)} + {fe_terms(fe)}",
                    focus,
                    fe,
                )
            )
    return fit_specs(specs, samples, out_dir)


def idea_04_comparison_intensity(samples: dict[str, pd.DataFrame], out_dir: Path) -> list[dict[str, object]]:
    controls = ["relative_fleet_size_z", "Coverage_z", "Exclusive_Coverage_z", "promo_active", *WEATHER_CONTROLS]
    focus = [
        "unlock_fee_z:platform_any:comparison_intensity_z",
        "price_per_minute_z:platform_any:comparison_intensity_z",
        "unlock_fee_z:local_maas_only:comparison_intensity_z",
        "unlock_fee_z:multi_platform:comparison_intensity_z",
    ]
    specs = []
    for sample in ["all", "no_weak_exposure", "scooter_only"]:
        for fe in ["market_fe", "unit_fe"]:
            specs.append(
                ModelSpec(
                    f"comparison_intensity_{fe}_{sample}",
                    sample,
                    "ur_boxcox",
                    "ur_boxcox ~ "
                    "unlock_fee_z * platform_any * comparison_intensity_z + "
                    "price_per_minute_z * platform_any * comparison_intensity_z + "
                    "unlock_fee_z * local_maas_only * comparison_intensity_z + "
                    "unlock_fee_z * multi_platform * comparison_intensity_z + "
                    f"{plus(controls)} + {fe_terms(fe)}",
                    focus,
                    fe,
                )
            )
    rows = fit_specs(specs, samples, out_dir)
    dml_treatments = [
        "unlock_fee_z_x_platform_any_x_comparison_intensity_z",
        "price_per_minute_z_x_platform_any_x_comparison_intensity_z",
        "unlock_fee_z_x_local_maas_only_x_comparison_intensity_z",
        "unlock_fee_z_x_multi_platform_x_comparison_intensity_z",
    ]
    numeric_controls = [
        *PRICING_VARS,
        "platform_any",
        "local_maas_only",
        "multi_platform",
        "comparison_intensity_z",
        "active_operators_z",
        "trip_hhi_z",
        *controls,
        "avg_network_distance_m_z",
        "avg_start_transit_distance_m_z",
    ]
    categorical_controls = ["city", "operator", "date_str", "dow"]
    for sample in ["all", "no_weak_exposure"]:
        for learner in ["hgb", "rf"]:
            fitted = dml_residualize(
                f"comparison_intensity_dml_{sample}",
                samples[sample],
                "ur_boxcox",
                dml_treatments,
                numeric_controls,
                categorical_controls,
                learner,
                out_dir,
            )
            for row in fitted:
                row["sample"] = sample
                row["idea"] = out_dir.name
            rows.extend(fitted)
    return rows


def idea_05_outcome_comparison(samples: dict[str, pd.DataFrame], out_dir: Path) -> list[dict[str, object]]:
    controls = ["relative_fleet_size_z", "Coverage_z", "Exclusive_Coverage_z", "promo_active", *WEATHER_CONTROLS]
    focus = ["platform_any", "unlock_fee_z:platform_any", "promo_active:platform_any"]
    specs = []
    for outcome in ["ur_boxcox", "log_trip_count_day"]:
        for fe in ["market_fe", "unit_fe"]:
            specs.append(
                ModelSpec(
                    f"outcome_comparison_{fe}_{outcome}",
                    "all",
                    outcome,
                    f"{outcome} ~ unlock_fee_z * platform_any + promo_active * platform_any + {plus(controls)} + {fe_terms(fe)}",
                    focus,
                    fe,
                )
            )
    return fit_specs(specs, samples, out_dir)


def idea_06_promotion_channel_fit(samples: dict[str, pd.DataFrame], out_dir: Path) -> list[dict[str, object]]:
    controls = [*PRICING_VARS, "relative_fleet_size_z", "Coverage_z", "Exclusive_Coverage_z", *WEATHER_CONTROLS]
    type_terms = ["large_aggregator_only", "local_maas_only", "multi_platform", "weak_exposure_only"]
    focus = ["promo_active:platform_any", *interactions(["promo_active"], type_terms)]
    specs = []
    for sample in ["all", "no_weak_exposure"]:
        for fe in ["market_fe", "unit_fe"]:
            specs.append(
                ModelSpec(
                    f"promotion_channel_fit_any_{fe}_{sample}",
                    sample,
                    "ur_boxcox",
                    f"ur_boxcox ~ promo_active * platform_any + {plus(controls)} + {fe_terms(fe)}",
                    ["promo_active:platform_any"],
                    fe,
                )
            )
            specs.append(
                ModelSpec(
                    f"promotion_channel_fit_type_{fe}_{sample}",
                    sample,
                    "ur_boxcox",
                    f"ur_boxcox ~ promo_active * ({plus(type_terms)}) + {plus(controls)} + {fe_terms(fe)}",
                    interactions(["promo_active"], type_terms),
                    fe,
                )
            )
    return fit_specs(specs, samples, out_dir)


def idea_07_supply_side_adaptation(samples: dict[str, pd.DataFrame], out_dir: Path) -> list[dict[str, object]]:
    supply = ["relative_fleet_size_z", "Coverage_z", "Exclusive_Coverage_z"]
    controls = [*PRICING_VARS, "promo_active", *WEATHER_CONTROLS]
    type_terms = ["large_aggregator_only", "local_maas_only", "multi_platform"]
    focus = [*interactions(supply, ["platform_any"]), *interactions(supply, type_terms)]
    specs = []
    for sample in ["all", "no_weak_exposure", "scooter_only"]:
        for fe in ["market_fe", "unit_fe"]:
            specs.append(
                ModelSpec(
                    f"supply_side_any_{fe}_{sample}",
                    sample,
                    "ur_boxcox",
                    f"ur_boxcox ~ ({plus(supply)}) * platform_any + {plus(controls)} + {fe_terms(fe)}",
                    interactions(supply, ["platform_any"]),
                    fe,
                )
            )
            specs.append(
                ModelSpec(
                    f"supply_side_type_{fe}_{sample}",
                    sample,
                    "ur_boxcox",
                    f"ur_boxcox ~ ({plus(supply)}) * ({plus(type_terms)}) + {plus(controls)} + {fe_terms(fe)}",
                    interactions(supply, type_terms),
                    fe,
                )
            )
    return fit_specs(specs, samples, out_dir)


IDEAS = {
    "01_pricing_architecture": idea_01_pricing_architecture,
    "02_marketing_mix_contingency": idea_02_marketing_mix_contingency,
    "03_platform_type_boundary": idea_03_platform_type_boundary,
    "04_comparison_intensity": idea_04_comparison_intensity,
    "05_outcome_comparison": idea_05_outcome_comparison,
    "06_promotion_channel_fit": idea_06_promotion_channel_fit,
    "07_supply_side_adaptation": idea_07_supply_side_adaptation,
}


def run_idea(idea_name: str) -> pd.DataFrame:
    if idea_name not in IDEAS:
        raise ValueError(f"Unknown idea '{idea_name}'. Options: {', '.join(IDEAS)}")
    out_dir = IDEA_OUTPUT_BASE / idea_name
    out_dir.mkdir(parents=True, exist_ok=True)
    samples = load_samples()
    sample_summary(samples, out_dir)
    rows = IDEAS[idea_name](samples, out_dir)
    results = write_outputs(rows, out_dir)
    (out_dir / "README.md").write_text(idea_readme(idea_name), encoding="utf-8")
    return results


def run_all_ideas() -> None:
    all_rows = []
    for idea_name in IDEAS:
        results = run_idea(idea_name)
        all_rows.append(results)
    combined = pd.concat(all_rows, ignore_index=True)
    IDEA_OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
    combined.to_csv(IDEA_OUTPUT_BASE / "all_idea_terms.csv", index=False)
    combined.loc[combined["significant_05"]].to_csv(IDEA_OUTPUT_BASE / "significant_idea_terms.csv", index=False)
    (IDEA_OUTPUT_BASE / "README.md").write_text(
        """# Separate Idea Tests

Each subfolder contains one modular test family for a JAMS-oriented story extension.

1. `01_pricing_architecture`: fixed access fee versus per-minute price.
2. `02_marketing_mix_contingency`: platform membership as marketing-mix contingency.
3. `03_platform_type_boundary`: platform type as boundary condition.
4. `04_comparison_intensity`: comparison/competition mechanism, including DML.
5. `05_outcome_comparison`: capacity utilisation versus demand volume.
6. `06_promotion_channel_fit`: promotion effectiveness by platform context.
7. `07_supply_side_adaptation`: fleet and coverage adaptation by platform context.

Top-level files:
- `all_idea_terms.csv`
- `significant_idea_terms.csv`
""",
        encoding="utf-8",
    )


def idea_readme(idea_name: str) -> str:
    titles = {
        "01_pricing_architecture": "Pricing Architecture",
        "02_marketing_mix_contingency": "Marketing-Mix Contingency",
        "03_platform_type_boundary": "Platform-Type Boundary Condition",
        "04_comparison_intensity": "Comparison Intensity Mechanism",
        "05_outcome_comparison": "Capacity Utilisation versus Demand Volume",
        "06_promotion_channel_fit": "Promotion Channel Fit",
        "07_supply_side_adaptation": "Supply-Side Adaptation",
    }
    return f"""# {titles[idea_name]}

Files:
- `terms.csv`: long-form coefficient table.
- `summary.csv`: compact term-level robustness summary.
- `sample_summary.csv`: sample diagnostics.
- `*_summary.txt`: full statsmodels summaries, ignored by git.
- `*_folds.csv`: DML fold diagnostics where applicable, ignored by git.
"""

