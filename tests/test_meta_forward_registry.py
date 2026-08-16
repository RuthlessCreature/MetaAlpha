from pathlib import Path

import yaml

from metaalpha.meta_branch import META_CANDIDATE_FEATURES, META_NEGATIVE_CONTROL_FEATURES


def test_meta_forward_code_matches_preregistered_branch_features():
    spec = yaml.safe_load(Path("registry/meta_forward_hypotheses.yaml").read_text(encoding="utf-8"))
    assert spec["family_id"] == "META_FWD_001"
    registered = {row["id"]: row["features"] for row in spec["candidate_branches"]}
    assert registered == META_CANDIDATE_FEATURES
    controls = {row["id"]: row["features"] for row in spec["negative_controls"]}
    assert controls == META_NEGATIVE_CONTROL_FEATURES
    assert list(registered) == ["cycle", "ziping", "qimen", "meihua"]
