"""Net-yield model.

The whole point: gross rent-to-price is a near-useless ranking metric.
Dayton OH beat Pinehurst NC by 60% on rent-to-price and landed at the same
cap rate, because Ohio property tax ate 27% of gross rent against 12% in NC.
This module prices that burden explicitly.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from .config import Config, DEFAULT


def underwrite(df: pd.DataFrame, cfg: Config = DEFAULT) -> pd.DataFrame:
    """Expects columns: market, state, home_value, rent, prop_tax_rate,
    insurance_annual, eviction_friction, insurance_volatility."""
    o, f = cfg.ops, cfg.fin
    d = df.copy()

    d["gross_rent"] = d.rent * 12
    d["gross_yield"] = d.gross_rent / d.home_value

    d["vacancy_loss"] = d.gross_rent * o.vacancy
    d["bad_debt_loss"] = d.gross_rent * o.bad_debt
    d["egi"] = d.gross_rent - d.vacancy_loss - d.bad_debt_loss

    # Insurance table is priced at $300k dwelling coverage; scale to the
    # market's own value, with a floor (cheap houses still cost a minimum).
    d["tax"] = d.home_value * d.prop_tax_rate
    d["insurance"] = np.maximum(
        d.insurance_annual * (d.home_value / 300_000) ** 0.6, 900
    ) * o.landlord_ins_multiple

    d["management"] = d.egi * o.management
    d["maintenance"] = d.gross_rent * o.maintenance
    d["capex"] = d.gross_rent * o.capex
    d["opex"] = d[["tax", "insurance", "management", "maintenance", "capex"]].sum(axis=1)

    d["noi"] = d.egi - d.opex
    d["net_yield"] = d.noi / (d.home_value * (1 + f.closing_pct))
    d["noi_margin"] = d.noi / d.gross_rent
    d["tax_share_of_rent"] = d.tax / d.gross_rent
    d["opex_share_of_rent"] = (d.opex + d.vacancy_loss + d.bad_debt_loss) / d.gross_rent

    # Levered
    i = f.rate / 12
    basis = d.home_value * (1 + f.closing_pct)
    d["debt_service"] = basis * f.ltv * i / (1 - (1 + i) ** -f.amort_months) * 12
    d["dscr"] = d.noi / d.debt_service
    d["monthly_cf"] = (d.noi - d.debt_service) / 12
    d["cash_invested"] = basis * (1 - f.ltv)
    d["cash_on_cash"] = (d.noi - d.debt_service) / d.cash_invested

    # The number that matters: yield over the cost of money.
    d["spread"] = d.net_yield - f.rate
    d["spread_vs_riskfree"] = d.net_yield - f.risk_free

    # How much of the gross-yield advantage survives the burden
    d["yield_retention"] = d.net_yield / d.gross_yield
    return d
