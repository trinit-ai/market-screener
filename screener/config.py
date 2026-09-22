"""Model assumptions and scoring weights. Every number here is a lever."""
from dataclasses import dataclass, field

@dataclass
class OpAssumptions:
    """Operating model. Defaults are the 'moderate' case from the Dayton study —
    what a competent local operator would actually underwrite, not a broker pro-forma."""
    vacancy: float = 0.06
    bad_debt: float = 0.03          # the line most pro-formas omit entirely
    management: float = 0.09        # of effective gross income
    maintenance: float = 0.09       # of gross rent
    capex: float = 0.05             # of gross rent
    # Insurance from the state table is an OWNER-OCCUPIED HO-3 premium.
    # Landlord DP-3 typically runs 15-25% higher.
    landlord_ins_multiple: float = 1.20

@dataclass
class FinanceAssumptions:
    rate: float = 0.076             # investor 30yr, Sep 2026
    ltv: float = 0.75
    amort_months: int = 360
    closing_pct: float = 0.02
    risk_free: float = 0.05         # 10yr T-note, 18 Sep 2026

@dataclass
class ScoreWeights:
    """What the composite score rewards. Spread is the core: yield alone is a trap."""
    spread: float = 1.00            # net yield minus cost of debt
    net_yield: float = 0.45
    tax_efficiency: float = 0.20    # how little of gross rent the tax eats
    eviction: float = 0.20          # landlord-tenant friction
    ins_volatility: float = 0.15    # insurance-crisis exposure

@dataclass
class Thresholds:
    """Hard gates. A market failing these is excluded regardless of yield."""
    min_net_yield: float = 0.045
    max_tax_share_of_rent: float = 0.30   # Dayton was 0.274 and that was fatal
    max_eviction_friction: int = 4
    max_ins_volatility: int = 3

@dataclass
class Config:
    ops: OpAssumptions = field(default_factory=OpAssumptions)
    fin: FinanceAssumptions = field(default_factory=FinanceAssumptions)
    weights: ScoreWeights = field(default_factory=ScoreWeights)
    gates: Thresholds = field(default_factory=Thresholds)

DEFAULT = Config()
