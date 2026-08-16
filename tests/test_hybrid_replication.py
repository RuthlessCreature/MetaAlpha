import pandas as pd

from metaalpha.research_hybrid_replication import replication_decision


def test_replication_requires_three_of_four_indices_per_model():
    rows = []
    for index_id, cycle_pass, ziping_pass in [
        ("a", 1, 1),
        ("b", 1, 0),
        ("c", 1, 1),
        ("d", 0, 0),
    ]:
        rows.append({"index_id": index_id, "model_id": "cycle", "gate_pass": cycle_pass})
        rows.append({"index_id": index_id, "model_id": "ziping", "gate_pass": ziping_pass})
    out = replication_decision(pd.DataFrame(rows)).set_index("model_id")
    assert out.loc["cycle", "indices_passed"] == 3
    assert out.loc["cycle", "replication_pass"] == 1
    assert out.loc["ziping", "indices_passed"] == 2
    assert out.loc["ziping", "replication_pass"] == 0
