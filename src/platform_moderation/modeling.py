"""Model estimators used by the clean platform moderation analysis."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def fit_ols_cluster(
    name: str,
    data: pd.DataFrame,
    outcome: str,
    formula: str,
    focus_terms: list[str],
    out_dir: Path,
    estimator: str = "ols_cluster",
    fe_strategy: str | None = None,
) -> list[dict[str, object]]:
    model = smf.ols(formula, data=data).fit(cov_type="cluster", cov_kwds={"groups": data["city_operator"]})
    (out_dir / f"{name}_{outcome}_summary.txt").write_text(str(model.summary()), encoding="utf-8")
    conf = model.conf_int()
    rows = []
    for term in focus_terms:
        if term not in model.params.index:
            continue
        rows.append(
            {
                "model": name,
                "estimator": estimator,
                "fe_strategy": fe_strategy,
                "outcome": outcome,
                "term": term,
                "coef": model.params[term],
                "std_err": model.bse[term],
                "p_value": model.pvalues[term],
                "ci_low": conf.loc[term, 0],
                "ci_high": conf.loc[term, 1],
                "nobs": int(model.nobs),
                "city_operators": data["city_operator"].nunique(),
                "cities": data["city"].nunique(),
                "r2": model.rsquared,
                "adj_r2": model.rsquared_adj,
            }
        )
    return rows


def dml_residualize(
    name: str,
    data: pd.DataFrame,
    outcome: str,
    treatment_terms: list[str],
    numeric_controls: list[str],
    categorical_controls: list[str],
    learner: str,
    out_dir: Path,
) -> list[dict[str, object]]:
    needed = [outcome, "city_operator", *treatment_terms, *numeric_controls, *categorical_controls]
    df = data[needed].dropna().copy()
    x = df[numeric_controls + categorical_controls]
    y = pd.to_numeric(df[outcome], errors="coerce").to_numpy(dtype=float)
    dmat = df[treatment_terms].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    groups = df["city_operator"].astype(str)

    if learner == "hgb":
        regressor = HistGradientBoostingRegressor(
            max_iter=250,
            learning_rate=0.05,
            max_leaf_nodes=31,
            min_samples_leaf=20,
            l2_regularization=0.05,
            random_state=42,
        )
    elif learner == "rf":
        regressor = RandomForestRegressor(
            n_estimators=350,
            min_samples_leaf=10,
            max_features="sqrt",
            random_state=42,
            n_jobs=-1,
        )
    else:
        raise ValueError(f"Unknown learner: {learner}")

    preprocessor = ColumnTransformer(
        [
            ("num", StandardScaler(), numeric_controls),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_controls),
        ],
        sparse_threshold=0.0,
    )
    splitter = GroupKFold(n_splits=5)
    y_hat = np.zeros_like(y)
    d_hat = np.zeros_like(dmat)
    fold_rows = []
    for fold, (train_idx, test_idx) in enumerate(splitter.split(x, y, groups=groups), start=1):
        y_model = Pipeline([("prep", preprocessor), ("model", regressor)])
        y_model.fit(x.iloc[train_idx], y[train_idx])
        y_hat[test_idx] = y_model.predict(x.iloc[test_idx])
        for j in range(dmat.shape[1]):
            d_model = Pipeline([("prep", preprocessor), ("model", regressor)])
            d_model.fit(x.iloc[train_idx], dmat[train_idx, j])
            d_hat[test_idx, j] = d_model.predict(x.iloc[test_idx])
        fold_rows.append({"model": name, "learner": learner, "fold": fold, "test_city_operators": groups.iloc[test_idx].nunique()})

    y_res = y - y_hat
    d_res = dmat - d_hat
    design = pd.DataFrame(d_res, columns=treatment_terms, index=df.index)
    result = sm.OLS(y_res, design).fit(cov_type="cluster", cov_kwds={"groups": groups})
    pd.DataFrame(fold_rows).to_csv(out_dir / f"{name}_{outcome}_{learner}_folds.csv", index=False)
    (out_dir / f"{name}_{outcome}_{learner}_summary.txt").write_text(str(result.summary()), encoding="utf-8")

    conf = result.conf_int()
    rows = []
    for term in treatment_terms:
        rows.append(
            {
                "model": name,
                "estimator": f"dml_{learner}",
                "fe_strategy": "ml_residualized",
                "outcome": outcome,
                "term": term,
                "coef": result.params[term],
                "std_err": result.bse[term],
                "p_value": result.pvalues[term],
                "ci_low": conf.loc[term, 0],
                "ci_high": conf.loc[term, 1],
                "nobs": int(result.nobs),
                "city_operators": df["city_operator"].nunique(),
                "cities": data["city"].nunique(),
                "r2": result.rsquared,
                "adj_r2": result.rsquared_adj,
            }
        )
    return rows

