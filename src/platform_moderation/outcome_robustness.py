"""Outcome robustness for high unlock-fee platform-type effects."""

from __future__ import annotations

import pandas as pd

from .config import OUTPUT_BASE, WEATHER_CONTROLS
from .data import load_panel, prepare_panel
from .modeling import fit_ols_cluster
from .reporting import add_report_columns, label_term


OUT = OUTPUT_BASE / "outcome_robustness"
OUT.mkdir(parents=True, exist_ok=True)

THRESHOLDS = {"unlock_fee_ge_1_00": 1.00, "unlock_fee_ge_1_20": 1.20}
TYPE_TERMS = ["local_maas_only", "multi_platform"]
OUTCOMES = ["ur_boxcox", "log_trip_count_day"]


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
    return {
        "all": df,
        "no_weak_exposure": df.loc[df["weak_exposure_only"].eq(0)].copy(),
        "scooter_only": df.loc[df["scooter_operator"].eq(1)].copy(),
    }


def fit_models(samples: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    controls = [
        "price_per_minute_z",
        "relative_fleet_size_z",
        "Coverage_z",
        "Exclusive_Coverage_z",
        "promo_active",
        *WEATHER_CONTROLS,
    ]
    for outcome in OUTCOMES:
        for sample_name, data in samples.items():
            for threshold in THRESHOLDS:
                for fe in ["market_fe", "unit_fe"]:
                    focus = [f"{threshold}:{term}" for term in TYPE_TERMS]
                    fitted = fit_ols_cluster(
                        f"outcome_robustness_{outcome}_{threshold}_{fe}_{sample_name}",
                        data,
                        outcome,
                        f"{outcome} ~ {threshold} * ({plus(TYPE_TERMS)}) + {plus(controls)} + {fe_terms(fe)}",
                        focus,
                        OUT,
                        fe_strategy=fe,
                    )
                    for row in fitted:
                        row["sample"] = sample_name
                        row["family"] = "outcome_robustness"
                    rows.extend(fitted)
    return rows


def write_outputs(rows: list[dict[str, object]]) -> pd.DataFrame:
    results = add_report_columns(pd.DataFrame(rows))
    results.to_csv(OUT / "terms.csv", index=False)
    summary_rows = []
    for (outcome, term), group in results.groupby(["outcome", "term"]):
        all_market = group.loc[group["sample"].eq("all") & group["fe_strategy"].eq("market_fe")]
        all_unit = group.loc[group["sample"].eq("all") & group["fe_strategy"].eq("unit_fe")]
        summary_rows.append(
            {
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
            }
        )
    pd.DataFrame(summary_rows).sort_values(["outcome", "term"]).to_csv(OUT / "summary.csv", index=False)
    results.loc[results["significant_05"]].to_csv(OUT / "significant_terms.csv", index=False)
    (OUT / "README.md").write_text(
        """# Outcome Robustness

Tests whether high-unlock-fee platform-type effects appear for both capacity utilisation (`ur_boxcox`) and demand volume (`log_trip_count_day`).

Model:

`outcome ~ unlock_fee_threshold * (local_maas_only + multi_platform) + controls + FE`

Thresholds:
- `unlock_fee_ge_1_00`
- `unlock_fee_ge_1_20`
""",
        encoding="utf-8",
    )
    return results


def run_outcome_robustness() -> pd.DataFrame:
    samples = load_samples()
    return write_outputs(fit_models(samples))

