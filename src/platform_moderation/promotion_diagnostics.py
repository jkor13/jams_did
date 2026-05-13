"""Diagnostics for promotion-type effect interpretability."""

from __future__ import annotations

import pandas as pd

from .config import OUTPUT_BASE
from .data import load_panel, prepare_panel


OUT = OUTPUT_BASE / "promotion_diagnostics"
OUT.mkdir(parents=True, exist_ok=True)

PROMO_TYPES = [
    "voucher_20eur_limited_eligibility",
    "subscriber_free_minutes_15_per_month",
    "parking_station_credit_0_50_eur",
]


def add_promo_type_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    promo = out["promo_types_clean"].fillna("").astype(str)
    for promo_type in PROMO_TYPES:
        out[f"promo_type_{promo_type}"] = promo.str.contains(promo_type, regex=False).astype(int)
    return out


def write_promotion_support(df: pd.DataFrame) -> None:
    rows = []
    unit_rows = []
    for promo_type in PROMO_TYPES:
        flag = f"promo_type_{promo_type}"
        active = df.loc[df[flag].eq(1)].copy()
        rows.append(
            {
                "promo_type": promo_type,
                "rows": len(active),
                "cities": active["city"].nunique(),
                "city_operators": active["city_operator"].nunique(),
                "operators": active["operator"].nunique(),
                "min_date": active["start_date"].min().date() if len(active) else "",
                "max_date": active["start_date"].max().date() if len(active) else "",
                "platforms": "; ".join(sorted(set(map(str, active["platforms_clean"].dropna())))),
            }
        )
        for city_operator, group in df.groupby("city_operator"):
            if group[flag].sum() == 0:
                continue
            unit_rows.append(
                {
                    "promo_type": promo_type,
                    "city_operator": city_operator,
                    "city": group["city"].iloc[0],
                    "operator": group["operator"].iloc[0],
                    "rows": len(group),
                    "promo_rows": int(group[flag].sum()),
                    "nonpromo_rows": int((1 - group[flag]).sum()),
                    "has_within_unit_switch": group[flag].nunique() > 1,
                    "promo_min_date": group.loc[group[flag].eq(1), "start_date"].min().date(),
                    "promo_max_date": group.loc[group[flag].eq(1), "start_date"].max().date(),
                }
            )
    pd.DataFrame(rows).to_csv(OUT / "promotion_type_support.csv", index=False)
    pd.DataFrame(unit_rows).to_csv(OUT / "promotion_unit_support.csv", index=False)


def write_curated_findings() -> None:
    pd.DataFrame(
        [
            {
                "finding_id": "PD1",
                "finding": "Promotion-type effects are not event-window identified",
                "status": "identification_caveat",
                "evidence": "Each observed promotion type is concentrated in one city and one to three city-operator cells. Subscriber-free-minutes occurs only for VOI in Nuremberg (144 rows), parking credit only for VOI in Stuttgart (144 rows), and voucher_20eur only in Berlin across BOLT, NEXTBIKE, and VOI (450 rows).",
                "interpretation": "Promotion-type coefficients should be interpreted as exploratory campaign-context diagnostics, not causal event-window estimates.",
                "caveat": "The current promo flags do not provide enough within-city or within-operator variation to isolate campaign effects from city-operator context.",
            },
            {
                "finding_id": "PD2",
                "finding": "Subscriber-free-minutes result is substantively interesting but highly localized",
                "status": "moderate_caveat",
                "evidence": "The subscriber-free-minutes promotion that appeared positive for platform_any and multi-platform is based on 144 VOI-Nuremberg observations from 2024-03-11 to 2024-08-22.",
                "interpretation": "The result can motivate a mechanism about marginal-cost-reducing promotions in multi-platform contexts, but it should not be written as a general promotion law.",
                "caveat": "Use as supporting qualitative/mechanism evidence unless additional campaign variation is added.",
            },
        ]
    ).to_csv(OUT / "curated_findings.csv", index=False)


def run_promotion_diagnostics() -> pd.DataFrame:
    df = add_promo_type_flags(prepare_panel(load_panel()))
    write_promotion_support(df)
    write_curated_findings()
    (OUT / "README.md").write_text(
        """# Promotion Diagnostics

Support diagnostics for interpreting promotion-type findings.

Outputs:
- `promotion_type_support.csv`: support by promotion type.
- `promotion_unit_support.csv`: promotion support within city-operator cells.
- `curated_findings.csv`: interpretability caveats for findings.md.
""",
        encoding="utf-8",
    )
    return pd.read_csv(OUT / "curated_findings.csv")

