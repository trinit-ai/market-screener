"""If a model change stops reproducing the hand-underwritten studies, it's wrong."""
import pandas as pd
from screener import model, score
from screener.config import DEFAULT

def _run():
    mk = pd.read_csv("data/seed_markets.csv")
    b = pd.read_csv("data/state_burden.csv")
    d = model.underwrite(mk.merge(b, on="state"), DEFAULT)
    return score.score(score.apply_gates(d, DEFAULT), DEFAULT)

def test_dayton_beats_pinehurst():
    d = _run().set_index("market")
    assert d.loc["Dayton, OH (calibration)", "net_yield"] > \
           d.loc["Pinehurst, NC (calibration)", "net_yield"]

def test_both_calibration_markets_are_weak():
    d = _run().set_index("market")
    for m in ["Dayton, OH (calibration)", "Pinehurst, NC (calibration)"]:
        assert d.loc[m, "net_yield"] < 0.045, f"{m} should fail the yield gate"

def test_gross_yield_is_misleading():
    d = _run()
    assert d.yield_retention.median() < 0.5

def test_high_burden_states_lose_their_gross_advantage():
    d = _run()
    il = d[d.state == "IL"]
    assert (il.yield_retention < 0.45).all()
