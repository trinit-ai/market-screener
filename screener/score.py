"""Scoring and gating.

A high score is a candidate for diligence, never a buy signal. The model
cannot distinguish 'cheap because boring' (investable) from 'cheap because
broken' (not). That judgment needs the Stage-2 checks in diligence.py.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from .config import Config, DEFAULT


def _norm(s: pd.Series) -> pd.Series:
    lo, hi = s.min(), s.max()
    if hi - lo < 1e-12:
        return pd.Series(0.5, index=s.index)
    return (s - lo) / (hi - lo)


def apply_gates(d: pd.DataFrame, cfg: Config = DEFAULT) -> pd.DataFrame:
    g = cfg.gates
    d = d.copy()
    fails = []
    for _, r in d.iterrows():
        why = []
        if r.net_yield < g.min_net_yield:
            why.append(f"net yield {r.net_yield:.1%} < {g.min_net_yield:.1%}")
        if r.tax_share_of_rent > g.max_tax_share_of_rent:
            why.append(f"tax eats {r.tax_share_of_rent:.0%} of rent")
        if r.eviction_friction > g.max_eviction_friction:
            why.append("eviction friction")
        if r.insurance_volatility > g.max_ins_volatility:
            why.append("insurance volatility")
        fails.append("; ".join(why))
    d["gate_fail"] = fails
    d["passes"] = d.gate_fail == ""
    return d


def score(d: pd.DataFrame, cfg: Config = DEFAULT) -> pd.DataFrame:
    w = cfg.weights
    d = d.copy()
    d["s_spread"] = _norm(d.spread)
    d["s_yield"] = _norm(d.net_yield)
    d["s_tax"] = _norm(-d.tax_share_of_rent)
    d["s_evict"] = _norm(-d.eviction_friction.astype(float))
    d["s_insvol"] = _norm(-d.insurance_volatility.astype(float))
    d["score"] = (
        w.spread * d.s_spread
        + w.net_yield * d.s_yield
        + w.tax_efficiency * d.s_tax
        + w.eviction * d.s_evict
        + w.ins_volatility * d.s_insvol
    ) / (w.spread + w.net_yield + w.tax_efficiency + w.eviction + w.ins_volatility) * 100
    return d.sort_values("score", ascending=False).reset_index(drop=True)


REQUIRED_DILIGENCE = [
    "population_trend_5yr",     # Census ACS — is the exit impaired?
    "employer_concentration",   # BLS/QCEW — single-employer risk
    "median_income_trend",      # Census ACS — can rents actually grow?
    "rental_vacancy_rate",      # Census — is there real demand?
    "pm_availability",          # MANUAL: 3+ managers with 100+ doors, real reviews
    "county_tax_verified",      # state rate is a proxy; counties vary hugely
    "insurance_quoted",         # actual landlord DP-3 quote, not a state average
]


def diligence_gaps(d: pd.DataFrame) -> list[str]:
    """Fields the composite score does NOT yet incorporate."""
    return [c for c in REQUIRED_DILIGENCE if c not in d.columns]
