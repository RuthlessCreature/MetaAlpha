from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


C_GRID = (0.01, 0.1, 1.0, 10.0)
INNER_TRAIN_CUTS = (0.60, 0.70, 0.80)
INNER_VALIDATION_FRACTION = 0.10


@dataclass(frozen=True)
class MetricSet:
    n: int
    log_loss: float
    brier_score: float
    roc_auc: float
    accuracy: float
    calibration_slope: float
    probability_spread_return: float


def make_ridge_logistic_pipeline(
    numeric_cols: list[str],
    categorical_cols: list[str],
    *,
    C: float,
) -> Pipeline:
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=True),
            ),
        ]
    )
    pre = ColumnTransformer(
        transformers=[
            ("num", numeric, numeric_cols),
            ("cat", categorical, categorical_cols),
        ],
        remainder="drop",
        sparse_threshold=0.3,
    )
    model = LogisticRegression(
        penalty="l2",
        C=float(C),
        solver="liblinear",
        max_iter=3000,
        class_weight=None,
        random_state=20260816,
    )
    return Pipeline(steps=[("pre", pre), ("model", model)])


def _inner_splits(n: int) -> list[tuple[np.ndarray, np.ndarray]]:
    if n < 300:
        raise ValueError("inner tuning requires at least 300 rows")
    val_n = max(50, int(np.floor(n * INNER_VALIDATION_FRACTION)))
    splits: list[tuple[np.ndarray, np.ndarray]] = []
    for frac in INNER_TRAIN_CUTS:
        cut = int(np.floor(n * frac))
        # one-row embargo between fit and validation
        train_end = max(1, cut - 1)
        val_start = cut
        val_end = min(n, val_start + val_n)
        if train_end < 100 or val_end - val_start < 30:
            continue
        splits.append((np.arange(train_end), np.arange(val_start, val_end)))
    if not splits:
        raise ValueError("no valid expanding inner splits")
    return splits


def choose_c_by_inner_logloss(
    train_df: pd.DataFrame,
    *,
    numeric_cols: list[str],
    categorical_cols: list[str],
    target_col: str,
    c_grid: Iterable[float] = C_GRID,
) -> tuple[float, pd.DataFrame]:
    train_df = train_df.sort_values("date").reset_index(drop=True)
    splits = _inner_splits(len(train_df))
    rows: list[dict[str, float | int]] = []

    for C in sorted(float(c) for c in c_grid):
        fold_losses: list[float] = []
        for fold, (fit_idx, val_idx) in enumerate(splits):
            fit_df = train_df.iloc[fit_idx]
            val_df = train_df.iloc[val_idx]
            y_fit = fit_df[target_col].astype(int).to_numpy()
            y_val = val_df[target_col].astype(int).to_numpy()
            if np.unique(y_fit).size < 2 or np.unique(y_val).size < 2:
                continue
            pipe = make_ridge_logistic_pipeline(numeric_cols, categorical_cols, C=C)
            pipe.fit(fit_df[numeric_cols + categorical_cols], y_fit)
            p = pipe.predict_proba(val_df[numeric_cols + categorical_cols])[:, 1]
            loss = float(log_loss(y_val, p, labels=[0, 1]))
            fold_losses.append(loss)
            rows.append({"C": C, "fold": fold, "log_loss": loss, "n_validation": len(val_df)})
        if not fold_losses:
            rows.append({"C": C, "fold": -1, "log_loss": np.nan, "n_validation": 0})

    table = pd.DataFrame(rows)
    means = (
        table.loc[table["fold"] >= 0]
        .groupby("C", as_index=False)["log_loss"]
        .mean()
        .sort_values(["log_loss", "C"], ascending=[True, True])
    )
    if means.empty:
        raise ValueError("all inner tuning folds were invalid")
    # Stable tie break: stronger regularization = smaller C.
    best_loss = float(means.iloc[0]["log_loss"])
    close = means.loc[np.isclose(means["log_loss"], best_loss, rtol=0.0, atol=1e-12)]
    best_c = float(close["C"].min())
    return best_c, table


def fit_predict_probability(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    *,
    numeric_cols: list[str],
    categorical_cols: list[str],
    target_col: str,
) -> tuple[np.ndarray, float, pd.DataFrame]:
    best_c, tuning = choose_c_by_inner_logloss(
        train_df,
        numeric_cols=numeric_cols,
        categorical_cols=categorical_cols,
        target_col=target_col,
    )
    pipe = make_ridge_logistic_pipeline(numeric_cols, categorical_cols, C=best_c)
    y_train = train_df[target_col].astype(int).to_numpy()
    pipe.fit(train_df[numeric_cols + categorical_cols], y_train)
    p = pipe.predict_proba(test_df[numeric_cols + categorical_cols])[:, 1]
    return p.astype(float), best_c, tuning


def _calibration_slope(y: np.ndarray, p: np.ndarray) -> float:
    # Logistic calibration slope fitted by Newton iterations on intercept + logit(p).
    eps = 1e-6
    p = np.clip(p.astype(float), eps, 1.0 - eps)
    x = np.log(p / (1.0 - p))
    X = np.column_stack([np.ones(len(x)), x])
    beta = np.array([0.0, 1.0], dtype=float)
    for _ in range(50):
        eta = X @ beta
        mu = 1.0 / (1.0 + np.exp(-np.clip(eta, -40, 40)))
        w = np.clip(mu * (1.0 - mu), 1e-8, None)
        grad = X.T @ (y - mu)
        hess = -(X.T * w) @ X
        try:
            step = np.linalg.solve(hess, grad)
        except np.linalg.LinAlgError:
            return float("nan")
        beta_new = beta - step
        if np.max(np.abs(beta_new - beta)) < 1e-9:
            beta = beta_new
            break
        beta = beta_new
    return float(beta[1])


def _probability_spread_return(p: np.ndarray, returns: np.ndarray) -> float:
    if len(p) < 20:
        return float("nan")
    lo = float(np.quantile(p, 0.20))
    hi = float(np.quantile(p, 0.80))
    low_mask = p <= lo
    high_mask = p >= hi
    if low_mask.sum() < 3 or high_mask.sum() < 3:
        return float("nan")
    return float(np.mean(returns[high_mask]) - np.mean(returns[low_mask]))


def evaluate_probabilities(y: np.ndarray, p: np.ndarray, returns: np.ndarray) -> MetricSet:
    y = np.asarray(y, dtype=int)
    p = np.asarray(p, dtype=float)
    returns = np.asarray(returns, dtype=float)
    if len(y) != len(p) or len(y) != len(returns):
        raise ValueError("metric arrays must have identical lengths")
    auc = float(roc_auc_score(y, p)) if np.unique(y).size == 2 else float("nan")
    return MetricSet(
        n=int(len(y)),
        log_loss=float(log_loss(y, p, labels=[0, 1])),
        brier_score=float(brier_score_loss(y, p)),
        roc_auc=auc,
        accuracy=float(accuracy_score(y, p >= 0.5)),
        calibration_slope=_calibration_slope(y.astype(float), p),
        probability_spread_return=_probability_spread_return(p, returns),
    )


def rowwise_log_loss(y: np.ndarray, p: np.ndarray) -> np.ndarray:
    eps = 1e-12
    p = np.clip(np.asarray(p, dtype=float), eps, 1.0 - eps)
    y = np.asarray(y, dtype=float)
    return -(y * np.log(p) + (1.0 - y) * np.log(1.0 - p))


def rowwise_brier(y: np.ndarray, p: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    return (p - y) ** 2


def block_bootstrap_mean_improvement_probability(
    improvements: np.ndarray,
    *,
    block_size: int = 20,
    repetitions: int = 2000,
    seed: int = 20260816,
) -> tuple[float, float, float]:
    values = np.asarray(improvements, dtype=float)
    values = values[np.isfinite(values)]
    n = len(values)
    if n < block_size * 3:
        raise ValueError("too few rows for requested block bootstrap")
    rng = np.random.default_rng(seed)
    starts = np.arange(0, max(1, n - block_size + 1))
    means = np.empty(repetitions, dtype=float)
    blocks_needed = int(np.ceil(n / block_size))
    for i in range(repetitions):
        picked = rng.choice(starts, size=blocks_needed, replace=True)
        sample = np.concatenate([values[s : s + block_size] for s in picked])[:n]
        means[i] = float(np.mean(sample))
    probability_positive = float(np.mean(means > 0.0))
    lower = float(np.quantile(means, 0.025))
    upper = float(np.quantile(means, 0.975))
    return probability_positive, lower, upper


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    """Holm family-wise adjusted p-values keyed by model/block id."""
    finite = [(k, float(v)) for k, v in p_values.items() if np.isfinite(v)]
    m = len(finite)
    if m == 0:
        return {k: float("nan") for k in p_values}
    ordered = sorted(finite, key=lambda kv: kv[1])
    adjusted_raw: dict[str, float] = {}
    running = 0.0
    for rank, (key, p) in enumerate(ordered):
        adj = min(1.0, (m - rank) * p)
        running = max(running, adj)
        adjusted_raw[key] = running
    return {k: adjusted_raw.get(k, float("nan")) for k in p_values}
