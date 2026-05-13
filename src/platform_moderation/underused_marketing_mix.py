"""Tests for underused marketing-mix features already present in the panel."""

from __future__ import annotations

import pandas as pd

from .config import OUTPUT_BASE, WEATHER_CONTROLS
from .data import load_panel, prepare_panel, zscore
from .modeling import fit_ols_cluster
from .reporting import add_report_columns, label_term


OUT = OUTPUT_BASE / "underused_marketing_mix"
OUT.mkdir(parents=True, exist_ok=True)

FEATURES = [
    "group_ride",
    "subscription_options",
    "complementary_services",
    "no_of_vehicle_types_z",
]
TYPE_TERMS = ["local_maas_only", "multi_platform", "large_aggregator_only"]


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
    for col in ["group_ride", "subscription_options", "complementary_services"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(int)
    out["no_of_vehicle_types_z"] = zscore(out["no_of_vehicle_types"]).fillna(0)
    unlock_fee = pd.to_numeric(out["unlock_fee"], errors="coerce").fillna(0)
    out["unlock_fee_ge_1_00"] = unlock_fee.ge(1.0).astype(int)
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
        row = {
            "sample": sample_name,
            "rows": len(data),
            "cities": data["city"].nunique(),
            "city_operators": data["city_operator"].nunique(),
        }
        for feature in FEATURES:
            values = pd.to_numeric(data[feature], errors="coerce")
            row[f"{feature}_mean"] = values.mean()
            row[f"{feature}_nonzero_rows"] = int(values.ne(0).sum())
        rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / "sample_summary.csv", index=False)


def fit_models(samples: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    controls = [
        "unlock_fee_z",
        "price_per_minute_z",
        "relative_fleet_size_z",
        "Coverage_z",
        "Exclusive_Coverage_z",
        "promo_active",
        *WEATHER_CONTROLS,
    ]
    for sample_name, data in samples.items():
        for feature in FEATURES:
            for fe in ["market_fe", "unit_fe"]:
                focus_any = [f"{feature}:platform_any"]
                fitted = fit_ols_cluster(
                    f"underused_any_{feature}_{fe}_{sample_name}",
                    data,
                    "ur_boxcox",
                    f"ur_boxcox ~ {feature} * platform_any + {plus(controls)} + {fe_terms(fe)}",
                    focus_any,
                    OUT,
                    fe_strategy=fe,
                )
                for row in fitted:
                    row["sample"] = sample_name
                    row["family"] = "feature_x_any_platform"
                    row["feature"] = feature
                rows.extend(fitted)

                focus_type = [f"{feature}:{platform_type}" for platform_type in TYPE_TERMS]
                fitted = fit_ols_cluster(
                    f"underused_type_{feature}_{fe}_{sample_name}",
                    data,
                    "ur_boxcox",
                    f"ur_boxcox ~ {feature} * ({plus(TYPE_TERMS)}) + {plus(controls)} + {fe_terms(fe)}",
                    focus_type,
                    OUT,
                    fe_strategy=fe,
                )
                for row in fitted:
                    row["sample"] = sample_name
                    row["family"] = "feature_x_platform_type"
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
        """# Underused Marketing-Mix Features

Tests marketing-mix variables that are already present in the panel but were not central in prior models:

- `group_ride`
- `subscription_options`
- `complementary_services`
- `no_of_vehicle_types_z`

Models test each feature interacted with any platform membership and platform type.
""",
        encoding="utf-8",
    )
    return results


def run_underused_marketing_mix() -> pd.DataFrame:
    samples = load_samples()
    sample_summary(samples)
    return write_outputs(fit_models(samples))

