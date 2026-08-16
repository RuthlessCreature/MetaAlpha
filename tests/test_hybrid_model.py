import numpy as np
import pandas as pd

from metaalpha.hybrid_model import (
    block_bootstrap_mean_improvement_probability,
    fit_predict_probability,
    holm_adjust,
)


def _synthetic(n=1400):
    rng = np.random.default_rng(7)
    dates = pd.bdate_range("2010-01-04", periods=n)
    x = rng.normal(size=n)
    state = np.where(np.arange(n) % 4 < 2, "A", "B")
    logits = 0.15 * x + np.where(state == "A", 0.8, -0.8)
    prob = 1.0 / (1.0 + np.exp(-logits))
    y = rng.binomial(1, prob)
    return pd.DataFrame({"date": dates, "x": x, "weekday": dates.weekday, "state": state, "y": y})


def test_augmented_model_uses_registered_symbolic_state_incrementally():
    df = _synthetic()
    train = df.iloc[:1100].reset_index(drop=True)
    test = df.iloc[1100:].reset_index(drop=True)

    p_base, _, _ = fit_predict_probability(
        train,
        test,
        numeric_cols=["x"],
        categorical_cols=["weekday"],
        target_col="y",
    )
    p_aug, _, _ = fit_predict_probability(
        train,
        test,
        numeric_cols=["x"],
        categorical_cols=["weekday", "state"],
        target_col="y",
    )

    eps = 1e-12
    y = test["y"].to_numpy(float)
    loss_base = -(y * np.log(np.clip(p_base, eps, 1-eps)) + (1-y) * np.log(np.clip(1-p_base, eps, 1-eps))).mean()
    loss_aug = -(y * np.log(np.clip(p_aug, eps, 1-eps)) + (1-y) * np.log(np.clip(1-p_aug, eps, 1-eps))).mean()
    assert loss_aug < loss_base - 0.03


def test_block_bootstrap_and_holm_are_deterministic_and_conservative():
    improvements = np.linspace(0.001, 0.01, 500)
    prob, lo, hi = block_bootstrap_mean_improvement_probability(
        improvements,
        block_size=20,
        repetitions=500,
        seed=123,
    )
    assert prob == 1.0
    assert lo > 0.0
    assert hi > lo

    adjusted = holm_adjust({"a": 0.001, "b": 0.02, "c": 0.04, "d": 0.2})
    assert adjusted["a"] >= 0.001
    assert adjusted["b"] >= 0.02
    assert adjusted["c"] >= 0.04
    assert adjusted["d"] >= 0.2
    assert adjusted["a"] <= adjusted["b"] <= adjusted["c"] <= adjusted["d"]
