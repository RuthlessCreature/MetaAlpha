import numpy as np

from metaalpha.validation import benjamini_hochberg, expanding_walk_forward_splits


def test_bh_adjustment_is_bounded_and_monotone_in_ranked_order():
    p = [0.01, 0.04, 0.03, 0.20]
    adjusted = benjamini_hochberg(p)
    assert np.all((adjusted >= 0) & (adjusted <= 1))
    ranked = adjusted[np.argsort(p)]
    assert np.all(np.diff(ranked) >= -1e-12)


def test_walk_forward_never_trains_on_future_rows():
    splits = expanding_walk_forward_splits(100, min_train=40, test_size=10)
    assert len(splits) == 6
    for split in splits:
        assert split.train_start == 0
        assert split.train_end == split.test_start
        assert split.test_start < split.test_end
