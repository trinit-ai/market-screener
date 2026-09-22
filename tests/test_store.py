"""Guards for the failure that silently broke a scheduled run: adding a model
input changed the dataframe schema, and to_sql(append) raised."""
import pandas as pd, pathlib, tempfile, pytest
from screener import store


@pytest.fixture
def tmpdb(monkeypatch):
    with tempfile.TemporaryDirectory() as t:
        p = pathlib.Path(t) / "snap.db"
        monkeypatch.setattr(store, "DB", p)
        yield p


def test_save_tolerates_new_columns(tmpdb):
    """The exact regression: a later run carries columns the table lacks."""
    store.save(pd.DataFrame({"market": ["A"], "score": [1.0]}), "2026-01-01")
    store.save(pd.DataFrame({"market": ["A"], "score": [2.0],
                             "owner_occ_rate": [0.0058],
                             "investor_multiple": [5.0]}), "2026-02-01")
    assert store.runs() == ["2026-01-01", "2026-02-01"]
    later = store.load("2026-02-01")
    assert later.owner_occ_rate.iloc[0] == 0.0058


def test_save_tolerates_missing_columns(tmpdb):
    """A run that measures fewer things must not fail either."""
    store.save(pd.DataFrame({"market": ["A"], "score": [1.0], "extra": [9]}), "2026-01-01")
    store.save(pd.DataFrame({"market": ["A"], "score": [2.0]}), "2026-02-01")
    assert len(store.load("2026-02-01")) == 1


def test_diff_computes_deltas(tmpdb):
    store.save(pd.DataFrame({"market": ["A", "B"], "score": [1.0, 5.0],
                             "net_yield": [0.03, 0.06]}), "2026-01-01")
    store.save(pd.DataFrame({"market": ["A", "B"], "score": [4.0, 5.0],
                             "net_yield": [0.05, 0.06]}), "2026-02-01")
    d = store.diff("2026-01-01", "2026-02-01").set_index("market")
    assert d.loc["A", "d_score"] == 3.0
    assert d.loc["B", "d_score"] == 0.0
