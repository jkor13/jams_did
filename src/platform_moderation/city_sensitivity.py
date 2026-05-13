"""Leave-one-city sensitivity checks for platform-type threshold effects."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import OUTPUT_BASE, WEATHER_CONTROLS
from .data import load_panel, prepare_panel
from .modeling import fit_ols_cluster
from .reporting import add_report_columns, label_term


OUT = OUTPUT_BASE / "city_sensitivity"
OUT.mkdir(parents=True, exist_ok=True)

THRESHOLDS = {
    "unlock_fee_ge_0_99": 0.99,
    "unlock_fee_ge_1_00": 1.00,
    "unlock_fee_ge_1_20": 1.20,
}
TYPE_TERMS = ["local_maas_only", "multi_platform"]
MIN_PLATFORM_ROWS = 100


@dataclass(frozen=True)
class CitySpec:
    family: str
    name: str
    sample: str
    formula: str
    focus_terms: list[str]
    fe_strategy: str
    dropped_city: str | None = None


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


def platform_cities(df: pd.DataFrame) -> list[str]:
    city_counts = (
        df.loc[df[TYPE_TERMS].sum(axis=1).gt(0)]
        .groupby("city")
        .size()
        .rename("platform_type_rows")
        .reset_index()
    )
    return sorted(city_counts.loc[city_counts["platform_type_rows"].ge(MIN_PLATFORM_ROWS), "city"].tolist())


def load_samples() -> tuple[dict[str, pd.DataFrame], list[str]]:
    df = add_threshold_features(prepare_panel(load_panel()))
    cities = platform_cities(df)
    samples = {
        "all": df,
        "no_weak_exposure": df.loc[df["weak_exposure_only"].eq(0)].copy(),
    }
    for city in cities:
        key = f"drop_{city.lower().replace('-', '_')}"
        samples[key] = df.loc[df["city"].ne(city)].copy()
    return samples, cities


def sample_summary(samples: dict[str, pd.DataFrame], cities: list[str]) -> None:
    rows = []
    for name, data in samples.items():
        dropped_city = name.removeprefix("drop_").upper() if name.startswith("drop_") else ""
        row = {
            "sample": name,
            "dropped_city": dropped_city,
            "rows": len(data),
            "cities": data["city"].nunique(),
            "city_operators": data["city_operator"].nunique(),
            "local_maas_rows": int(data["local_maas_only"].sum()),
            "multi_platform_rows": int(data["multi_platform"].sum()),
        }
        for threshold in THRESHOLDS:
            row[f"{threshold}_local_maas_rows"] = int((data[threshold] * data["local_maas_only"]).sum())
            row[f"{threshold}_multi_platform_rows"] = int((data[threshold] * data["multi_platform"]).sum())
        rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / "sample_summary.csv", index=False)
    pd.DataFrame({"platform_city": cities}).to_csv(OUT / "platform_cities.csv", index=False)


def build_specs(samples: dict[str, pd.DataFrame]) -> list[CitySpec]:
    controls = [
        "price_per_minute_z",
        "relative_fleet_size_z",
        "Coverage_z",
        "Exclusive_Coverage_z",
        "promo_active",
        *WEATHER_CONTROLS,
    ]
    specs: list[CitySpec] = []
    sample_order = ["all", "no_weak_exposure", *[name for name in samples if name.startswith("drop_")]]
    for sample in sample_order:
        dropped_city = sample.removeprefix("drop_").upper() if sample.startswith("drop_") else None
        for threshold in THRESHOLDS:
            for fe in ["market_fe", "unit_fe"]:
                specs.append(
                    CitySpec(
                        "leave_one_platform_city" if dropped_city else "baseline",
                        f"city_sensitivity_{threshold}_{fe}_{sample}",
                        sample,
                        f"ur_boxcox ~ {threshold} * ({plus(TYPE_TERMS)}) + {plus(controls)} + {fe_terms(fe)}",
                        [f"{threshold}:{platform_type}" for platform_type in TYPE_TERMS],
                        fe,
                        dropped_city,
                    )
                )
    return specs


def fit_specs(specs: list[CitySpec], samples: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
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
            row["dropped_city"] = spec.dropped_city or ""
        rows.extend(fitted)
    return rows


def write_outputs(rows: list[dict[str, object]]) -> pd.DataFrame:
    results = add_report_columns(pd.DataFrame(rows))
    results.to_csv(OUT / "terms.csv", index=False)
    leave_one = results.loc[results["family"].eq("leave_one_platform_city")].copy()
    stability_rows = []
    for (term, fe), group in leave_one.groupby(["term", "fe_strategy"]):
        stability_rows.append(
            {
                "term": term,
                "label": label_term(term),
                "fe_strategy": fe,
                "n_city_drops": len(group),
                "n_negative_sig_05": int(((group["coef"] < 0) & group["significant_05"]).sum()),
                "n_positive_sig_05": int(((group["coef"] > 0) & group["significant_05"]).sum()),
                "median_coef": group["coef"].median(),
                "min_coef": group["coef"].min(),
                "max_coef": group["coef"].max(),
                "largest_p": group["p_value"].max(),
            }
        )
    pd.DataFrame(stability_rows).sort_values(["term", "fe_strategy"]).to_csv(OUT / "leave_one_city_stability.csv", index=False)
    results.loc[results["significant_05"]].to_csv(OUT / "significant_terms.csv", index=False)
    (OUT / "README.md").write_text(
        """# City Sensitivity

Leave-one-platform-city sensitivity checks for high unlock-fee platform-type effects.

The test drops each city with at least 100 local MaaS or multi-platform rows and re-estimates:

`ur_boxcox ~ unlock_fee_threshold * (local_maas_only + multi_platform) + controls + FE`

Thresholds:
- `unlock_fee_ge_0_99`
- `unlock_fee_ge_1_00`
- `unlock_fee_ge_1_20`

Outputs:
- `terms.csv`: all focal coefficients.
- `leave_one_city_stability.csv`: term-level stability across city drops.
- `significant_terms.csv`: significant focal coefficients.
- `sample_summary.csv`: sample diagnostics.
- `platform_cities.csv`: cities used for leave-one-city checks.
""",
        encoding="utf-8",
    )
    return results


def run_city_sensitivity() -> pd.DataFrame:
    samples, cities = load_samples()
    sample_summary(samples, cities)
    rows = fit_specs(build_specs(samples), samples)
    return write_outputs(rows)

