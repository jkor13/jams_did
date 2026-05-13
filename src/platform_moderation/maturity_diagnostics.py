"""Maturity diagnostics for platform threshold effects."""

from __future__ import annotations

import pandas as pd

from .config import OUTPUT_BASE, WEATHER_CONTROLS
from .data import load_panel, prepare_panel
from .modeling import fit_ols_cluster
from .reporting import add_report_columns


OUT = OUTPUT_BASE / "maturity_diagnostics"
OUT.mkdir(parents=True, exist_ok=True)

THRESHOLDS = {"unlock_fee_ge_1_00": 1.00, "unlock_fee_ge_1_20": 1.20}
PLATFORM_TYPES = {
    "large_aggregator_only": "large_aggregator_only",
    "local_maas_only": "local_maas_only",
    "multi_platform": "multi_platform",
}


def plus(terms: list[str]) -> str:
    return " + ".join(terms)


def fe_terms(fe_strategy: str) -> str:
    if fe_strategy == "market_fe":
        return "C(city) + C(date_str) + C(operator)"
    if fe_strategy == "unit_fe":
        return "C(city_operator) + C(date_str)"
    raise ValueError(fe_strategy)


def add_maturity_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    days = pd.to_numeric(out["days_since_first_platform_start_clean"], errors="coerce")
    out["maturity_segment"] = pd.cut(
        days,
        bins=[-1, 180, 365, 99999],
        labels=["early_0_180", "mid_181_365", "mature_366_plus"],
    ).astype("object")
    out.loc[days.isna(), "maturity_segment"] = "no_platform"
    out["mature_366_plus"] = out["maturity_segment"].eq("mature_366_plus").astype(int)
    unlock_fee = pd.to_numeric(out["unlock_fee"], errors="coerce").fillna(0)
    for name, threshold in THRESHOLDS.items():
        out[name] = unlock_fee.ge(threshold).astype(int)
    return out


def load_samples() -> dict[str, pd.DataFrame]:
    df = add_maturity_features(prepare_panel(load_panel()))
    return {
        "all": df,
        "no_weak_exposure": df.loc[df["weak_exposure_only"].eq(0)].copy(),
        "scooter_only": df.loc[df["scooter_operator"].eq(1)].copy(),
    }


def write_support_tables(samples: dict[str, pd.DataFrame]) -> None:
    rows = []
    for sample_name, data in samples.items():
        for platform_label, platform_col in PLATFORM_TYPES.items():
            typed = data.loc[data[platform_col].eq(1)].copy()
            for segment, segment_data in typed.groupby("maturity_segment", dropna=False):
                if segment == "no_platform":
                    continue
                row = {
                    "sample": sample_name,
                    "platform_type": platform_label,
                    "maturity_segment": segment,
                    "rows": len(segment_data),
                    "cities": segment_data["city"].nunique(),
                    "city_operators": segment_data["city_operator"].nunique(),
                }
                for threshold in THRESHOLDS:
                    high = segment_data.loc[segment_data[threshold].eq(1)]
                    row[f"{threshold}_rows"] = len(high)
                    row[f"{threshold}_cities"] = high["city"].nunique()
                    row[f"{threshold}_city_operators"] = high["city_operator"].nunique()
                rows.append(row)
    support = pd.DataFrame(rows)
    support.to_csv(OUT / "maturity_support.csv", index=False)
    support.assign(
        estimable_high_fee=lambda x: (x["unlock_fee_ge_1_00_rows"] > 0) & (x["rows"] > x["unlock_fee_ge_1_00_rows"])
    ).to_csv(OUT / "maturity_estimability.csv", index=False)


def fit_large_aggregator_maturity(samples: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    controls = [
        "price_per_minute_z",
        "relative_fleet_size_z",
        "Coverage_z",
        "Exclusive_Coverage_z",
        "promo_active",
        *WEATHER_CONTROLS,
    ]
    for sample_name in ["all", "no_weak_exposure", "scooter_only"]:
        data = samples[sample_name]
        for threshold in THRESHOLDS:
            for fe in ["market_fe", "unit_fe"]:
                focus = [
                    f"{threshold}:large_aggregator_only",
                    f"{threshold}:large_aggregator_only:mature_366_plus",
                ]
                fitted = fit_ols_cluster(
                    f"large_aggregator_maturity_{threshold}_{fe}_{sample_name}",
                    data,
                    "ur_boxcox",
                    f"ur_boxcox ~ {threshold} * large_aggregator_only * mature_366_plus + {plus(controls)} + {fe_terms(fe)}",
                    focus,
                    OUT,
                    fe_strategy=fe,
                )
                for row in fitted:
                    row["sample"] = sample_name
                    row["family"] = "large_aggregator_maturity"
                rows.extend(fitted)
    return rows


def write_outputs(rows: list[dict[str, object]]) -> pd.DataFrame:
    results = add_report_columns(pd.DataFrame(rows))
    results.to_csv(OUT / "terms.csv", index=False)
    summary_rows = []
    for term, group in results.groupby("term"):
        all_market = group.loc[group["sample"].eq("all") & group["fe_strategy"].eq("market_fe")]
        all_unit = group.loc[group["sample"].eq("all") & group["fe_strategy"].eq("unit_fe")]
        summary_rows.append(
            {
                "term": term,
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
    pd.DataFrame(summary_rows).sort_values("term").to_csv(OUT / "summary.csv", index=False)
    results.loc[results["significant_05"]].to_csv(OUT / "significant_terms.csv", index=False)
    (OUT / "README.md").write_text(
        """# Maturity Diagnostics

Diagnostics for whether the high-unlock-fee platform effect can be separated from platform maturity.

Outputs:
- `maturity_support.csv`: support by platform type and maturity segment.
- `maturity_estimability.csv`: basic support flag for high-fee variation within maturity segment.
- `terms.csv`: large-aggregator maturity interaction models.
- `summary.csv`: compact coefficient summary.

Key identification note: local MaaS and multi-platform high unlock fees occur almost exclusively in mature platform observations, so maturity and high-fee salience cannot be cleanly separated for those platform types with the current panel.
""",
        encoding="utf-8",
    )
    return results


def run_maturity_diagnostics() -> pd.DataFrame:
    samples = load_samples()
    write_support_tables(samples)
    rows = fit_large_aggregator_maturity(samples)
    return write_outputs(rows)

