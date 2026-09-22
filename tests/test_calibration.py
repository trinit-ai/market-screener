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


def test_uses_investor_not_owner_occupied_rates():
    """Owner-occupied medians understate landlord burden by up to 5x and invert
    the rankings. Regression guard: the model must run on rental rates."""
    b = pd.read_csv("data/state_burden.csv")
    assert "owner_occ_rate" in b.columns, "owner-occupied column missing"
    # the states with the biggest landlord penalty must show it
    for st, floor in [("MS", 0.025), ("SC", 0.015), ("AL", 0.009), ("IN", 0.020)]:
        rate = b.loc[b.state == st, "prop_tax_rate"].iloc[0]
        assert rate >= floor, f"{st} rate {rate:.4f} looks like an owner-occupied rate"
    assert b.loc[b.state == "NC", "prop_tax_rate"].iloc[0] < 0.008, "NC should stay low"


def test_mississippi_no_longer_screens_as_top_market():
    """Meridian MS ranked 3rd nationally on owner-occupied rates. It should not."""
    d = _run()
    ms = d[d.state == "MS"]
    assert not ms.passes.any(), "MS markets should fail gates at a 2.91% rental rate"
