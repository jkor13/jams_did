"""Robustness checks for salient unlock-fee threshold effects."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import OUTPUT_BASE, WEATHER_CONTROLS
from .data import load_panel, prepare_panel
from .modeling import fit_ols_cluster
from .reporting import add_report_columns, label_term


OUT = OUTPUT_BASE / "threshold_robustness"
OUT.mkdir(parents=True, exist_ok=True)

THRESHOLDS = {
    "unlock_fee_positive": 0.0001,
    "unlock_fee_ge_0_49": 0.49,
    "unlock_fee_ge_0_75": 0.75,
    "unlock_fee_ge_0_99": 0.99,
    "unlock_fee_ge_1_00": 1.00,
    "unlock_fee_ge_1_20": 1.20,
}
TYPE_TERMS = ["large_aggregator_only", "local_maas_only", "multi_platform"]
OPERATORS = ["BOLT", "NEXTBIKE", "TIER", "VOI"]


@dataclass(frozen=True)
class ThresholdSpec:
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


def add_threshold_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    unlock_fee = pd.to_numeric(out["unlock_fee"], errors="coerce").fillna(0)
    for name, threshold in THRESHOLDS.items():
        out[name] = unlock_fee.ge(threshold).astype(int)
    return out


def load_samples() -> dict[str, pd.DataFrame]:
    df = add_threshold_features(prepare_panel(load_panel()))
    samples = {
        "all": df,
        "no_weak_exposure": df.loc[df["weak_exposure_only"].eq(0)].copy(),
        "scooter_only": df.loc[df["scooter_operator"].eq(1)].copy(),
    }
    for operator in OPERATORS:
        samples[f"drop_{operator.lower()}"] = df.loc[df["operator"].ne(operator)].copy()
    return samples


def sample_summary(samples: dict[str, pd.DataFrame]) -> None:
    rows = []
    for name, data in samples.items():
        row = {
            "sample": name,
            "rows": len(data),
            "cities": data["city"].nunique(),
            "city_operators": data["city_operator"].nunique(),
            "platform_any_rows": int(data["platform_any"].sum()),
        }
        for threshold in THRESHOLDS:
            row[f"{threshold}_rows"] = int(data[threshold].sum())
            row[f"{threshold}_platform_rows"] = int((data[threshold] * data["platform_any"]).sum())
        rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / "sample_summary.csv", index=False)


def build_specs(samples: dict[str, pd.DataFrame]) -> list[ThresholdSpec]:
    specs: list[ThresholdSpec] = []
    controls = [
        "price_per_minute_z",
        "relative_fleet_size_z",
        "Coverage_z",
        "Exclusive_Coverage_z",
        "promo_active",
        *WEATHER_CONTROLS,
    ]
    for sample in ["all", "no_weak_exposure", "scooter_only"]:
        for threshold in THRESHOLDS:
            for fe in ["market_fe", "unit_fe"]:
                specs.append(
                    ThresholdSpec(
                        "threshold_any",
                        f"threshold_any_{threshold}_{fe}_{sample}",
                        sample,
                        f"ur_boxcox ~ {threshold} * platform_any + {plus(controls)} + {fe_terms(fe)}",
                        [f"{threshold}:platform_any"],
                        fe,
                    )
                )
                specs.append(
                    ThresholdSpec(
                        "threshold_type",
                        f"threshold_type_{threshold}_{fe}_{sample}",
                        sample,
                        f"ur_boxcox ~ {threshold} * ({plus(TYPE_TERMS)}) + {plus(controls)} + {fe_terms(fe)}",
                        [f"{threshold}:{platform_type}" for platform_type in TYPE_TERMS],
                        fe,
                    )
                )

    for operator_sample in [name for name in samples if name.startswith("drop_")]:
        for threshold in ["unlock_fee_ge_0_75", "unlock_fee_ge_0_99", "unlock_fee_ge_1_00", "unlock_fee_ge_1_20"]:
            for fe in ["market_fe", "unit_fe"]:
                specs.append(
                    ThresholdSpec(
                        "leave_one_operator",
                        f"leave_one_operator_{threshold}_{fe}_{operator_sample}",
                        operator_sample,
                        f"ur_boxcox ~ {threshold} * platform_any + {plus(controls)} + {fe_terms(fe)}",
                        [f"{threshold}:platform_any"],
                        fe,
                    )
                )
    return specs


def fit_specs(specs: list[ThresholdSpec], samples: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
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
        no_weak_market = group.loc[group["sample"].eq("no_weak_exposure") & group["fe_strategy"].eq("market_fe")]
        scooter_market = group.loc[group["sample"].eq("scooter_only") & group["fe_strategy"].eq("market_fe")]
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
                "no_weak_market_fe_coef": no_weak_market["coef"].iloc[0] if len(no_weak_market) else pd.NA,
                "no_weak_market_fe_p": no_weak_market["p_value"].iloc[0] if len(no_weak_market) else pd.NA,
                "scooter_market_fe_coef": scooter_market["coef"].iloc[0] if len(scooter_market) else pd.NA,
                "scooter_market_fe_p": scooter_market["p_value"].iloc[0] if len(scooter_market) else pd.NA,
            }
        )
    summary = pd.DataFrame(summary_rows).sort_values(
        ["family", "n_negative_sig_05", "n_positive_sig_05", "term"],
        ascending=[True, False, False, True],
    )
    summary.to_csv(OUT / "summary.csv", index=False)
    results.loc[results["significant_05"]].to_csv(OUT / "significant_terms.csv", index=False)
    (OUT / "README.md").write_text(
        """# Threshold Robustness

Robustness checks for the high-unlock-fee finding.

Thresholds:
- `unlock_fee_positive`: any positive unlock fee.
- `unlock_fee_ge_0_49`: unlock fee >= EUR 0.49.
- `unlock_fee_ge_0_75`: unlock fee >= EUR 0.75.
- `unlock_fee_ge_0_99`: unlock fee >= EUR 0.99.
- `unlock_fee_ge_1_00`: unlock fee >= EUR 1.00.
- `unlock_fee_ge_1_20`: unlock fee >= EUR 1.20.

Families:
- `threshold_any`: threshold x any platform membership.
- `threshold_type`: threshold x platform membership type.
- `leave_one_operator`: threshold x platform membership after dropping one major operator.
""",
        encoding="utf-8",
    )
    return results


def run_threshold_robustness() -> pd.DataFrame:
    samples = load_samples()
    sample_summary(samples)
    rows = fit_specs(build_specs(samples), samples)
    return write_outputs(rows)

