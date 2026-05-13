"""Do underused product features moderate high unlock-fee platform penalties?"""

from __future__ import annotations

import pandas as pd

from .config import OUTPUT_BASE, WEATHER_CONTROLS
from .data import load_panel, prepare_panel, zscore
from .modeling import fit_ols_cluster
from .reporting import add_report_columns, label_term


OUT = OUTPUT_BASE / "feature_fee_moderation"
OUT.mkdir(parents=True, exist_ok=True)

THRESHOLDS = {"unlock_fee_ge_1_00": 1.00, "unlock_fee_ge_1_20": 1.20}
PLATFORM_TYPES = ["local_maas_only", "multi_platform"]
FEATURES = ["group_ride", "no_of_vehicle_types_z", "complementary_services"]


def plus(terms: list[str]) -> str:
    return " + ".join(terms)


def fe_terms(fe_strategy: str) -> str:
    if fe_strategy == "market_fe":
        return "C(city) + C(date_str) + C(operator)"
    if fe_strategy == "unit_fe":
        return "C(city_operator) + C(date_str)"
    raise ValueError(fe_strategy)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["group_ride", "complementary_services"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(int)
    out["no_of_vehicle_types_z"] = zscore(out["no_of_vehicle_types"]).fillna(0)
    unlock_fee = pd.to_numeric(out["unlock_fee"], errors="coerce").fillna(0)
    for name, threshold in THRESHOLDS.items():
        out[name] = unlock_fee.ge(threshold).astype(int)
    return out


def load_samples() -> dict[str, pd.DataFrame]:
    df = add_features(prepare_panel(load_panel()))
    return {
        "all": df,
        "no_weak_exposure": df.loc[df["weak_exposure_only"].eq(0)].copy(),
        "scooter_only": df.loc[df["scooter_operator"].eq(1)].copy(),
    }


def sample_summary(samples: dict[str, pd.DataFrame]) -> None:
    rows = []
    for sample_name, data in samples.items():
        for platform_type in PLATFORM_TYPES:
            typed = data.loc[data[platform_type].eq(1)]
            row = {
                "sample": sample_name,
                "platform_type": platform_type,
                "rows": len(typed),
                "cities": typed["city"].nunique(),
                "city_operators": typed["city_operator"].nunique(),
            }
            for threshold in THRESHOLDS:
                high = typed.loc[typed[threshold].eq(1)]
                row[f"{threshold}_rows"] = len(high)
                for feature in FEATURES:
                    values = pd.to_numeric(high[feature], errors="coerce")
                    row[f"{threshold}_{feature}_mean"] = values.mean()
                    row[f"{threshold}_{feature}_nonzero_rows"] = int(values.ne(0).sum())
            rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / "sample_summary.csv", index=False)


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
    for sample_name, data in samples.items():
        for threshold in THRESHOLDS:
            for feature in FEATURES:
                for fe in ["market_fe", "unit_fe"]:
                    focus = [f"{threshold}:{platform_type}:{feature}" for platform_type in PLATFORM_TYPES]
                    fitted = fit_ols_cluster(
                        f"feature_fee_{threshold}_{feature}_{fe}_{sample_name}",
                        data,
                        "ur_boxcox",
                        f"ur_boxcox ~ {threshold} * ({plus(PLATFORM_TYPES)}) * {feature} + {plus(controls)} + {fe_terms(fe)}",
                        focus,
                        OUT,
                        fe_strategy=fe,
                    )
                    for row in fitted:
                        row["sample"] = sample_name
                        row["family"] = "feature_fee_moderation"
                        row["feature"] = feature
                    rows.extend(fitted)
    return rows


def write_outputs(rows: list[dict[str, object]]) -> pd.DataFrame:
    results = add_report_columns(pd.DataFrame(rows))
    results.to_csv(OUT / "terms.csv", index=False)
    summary_rows = []
    for (feature, term), group in results.groupby(["feature", "term"]):
        all_market = group.loc[group["sample"].eq("all") & group["fe_strategy"].eq("market_fe")]
        all_unit = group.loc[group["sample"].eq("all") & group["fe_strategy"].eq("unit_fe")]
        summary_rows.append(
            {
                "feature": feature,
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
    pd.DataFrame(summary_rows).sort_values(
        ["n_negative_sig_05", "n_positive_sig_05", "feature"], ascending=[False, False, True]
    ).to_csv(OUT / "summary.csv", index=False)
    results.loc[results["significant_05"]].to_csv(OUT / "significant_terms.csv", index=False)
    (OUT / "README.md").write_text(
        """# Feature-Fee Moderation

Tests whether underused product/service features moderate the high-unlock-fee platform penalty.

Model:

`ur_boxcox ~ unlock_fee_threshold * (local_maas_only + multi_platform) * feature + controls + FE`

Features:
- `group_ride`
- `no_of_vehicle_types_z`
- `complementary_services`
""",
        encoding="utf-8",
    )
    return results


def run_feature_fee_moderation() -> pd.DataFrame:
    samples = load_samples()
    sample_summary(samples)
    return write_outputs(fit_models(samples))

