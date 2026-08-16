from pathlib import Path

import yaml

from metaalpha.market_baseline import BASE_CATEGORICAL, BASE_CONTINUOUS
from metaalpha.research_hybrid_alpha import SYMBOLIC_BLOCKS


def test_hybrid_code_matches_preregistered_feature_lists():
    spec = yaml.safe_load(Path("registry/hybrid_alpha_hypotheses.yaml").read_text(encoding="utf-8"))["hypotheses"][0]
    assert spec["id"] == "HYBRID_ALPHA_001"
    assert spec["baseline_features"]["continuous"] == list(BASE_CONTINUOUS)
    assert spec["baseline_features"]["categorical"] == list(BASE_CATEGORICAL)

    registered = {row["id"]: row for row in spec["symbolic_blocks"]}
    for block_id in ("cycle", "qimen", "ziping"):
        assert registered[block_id]["features"] == SYMBOLIC_BLOCKS[block_id]
    expected_all = list(dict.fromkeys(SYMBOLIC_BLOCKS["cycle"] + SYMBOLIC_BLOCKS["qimen"] + SYMBOLIC_BLOCKS["ziping"]))
    assert SYMBOLIC_BLOCKS["all_symbolic"] == expected_all
    assert registered["all_symbolic"]["composition"] == ["cycle", "qimen", "ziping"]
