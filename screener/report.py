"""Turn a scored run into a human digest. This is what you actually read."""
from __future__ import annotations
import datetime, pathlib
import pandas as pd
from . import store


def digest(d: pd.DataFrame, prev: pd.DataFrame | None = None, top: int = 20) -> str:
    L = []
    today = datetime.date.today().isoformat()
    p = d[d.passes]
    L.append(f"# Market screen — {today}\n")
    L.append(f"**{len(p)} of {len(d)} markets clear the hard gates.**\n")

    pos = (d.spread > 0).sum()
    L.append(f"- Markets with positive spread over {d.attrs.get('rate', 0.076):.1%} debt: **{pos}**")
    L.append(f"- Beating risk-free unlevered: **{(d.net_yield >= 0.05).sum()}**")
    L.append(f"- Median yield retention (net/gross): **{d.yield_retention.median():.0%}**")
    L.append(f"- Median net yield: **{d.net_yield.median():.2%}** (median gross: {d.gross_yield.median():.2%})\n")

    if pos == 0:
        L.append("> No market in the universe produces positive leverage at current rates. "
                 "The achievable strategies are all-cash, value-add, or buying below the index — "
                 "none of which are market-selection problems.\n")

    L.append(f"## Top {top} candidates\n")
    L.append("| # | Market | ST | Value | Rent | Gross | Net | Tax% | Spread | Score |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for i, (_, r) in enumerate(p.head(top).iterrows(), 1):
        L.append(f"| {i} | {r.market} | {r.state} | ${r.home_value:,.0f} | ${r.rent:,.0f} | "
                 f"{r.gross_yield:.2%} | {r.net_yield:.2%} | {r.tax_share_of_rent:.0%} | "
                 f"{r.spread:+.2%} | {r.score:.1f} |")
    L.append("")

    if prev is not None and len(prev):
        L.append("## Changes since last run\n")
        m = d[["market", "score", "net_yield", "rent", "home_value"]].merge(
            prev[["market", "score", "net_yield", "rent", "home_value"]],
            on="market", suffixes=("", "_prev"))
        m["d_score"] = m.score - m.score_prev
        m["d_yield"] = m.net_yield - m.net_yield_prev
        movers = m.reindex(m.d_score.abs().sort_values(ascending=False).index).head(10)
        big = movers[movers.d_score.abs() > 0.5]
        if len(big) == 0:
            L.append("_No material movement._\n")
        else:
            L.append("| Market | Score | Δ | Net yield | Δ |")
            L.append("|---|---|---|---|---|")
            for _, r in big.iterrows():
                L.append(f"| {r.market} | {r.score:.1f} | {r.d_score:+.1f} | "
                         f"{r.net_yield:.2%} | {r.d_yield:+.2%} |")
            L.append("")
        entered = set(d[d.passes].market) - set(prev[prev.passes].market) if "passes" in prev else set()
        exited = set(prev[prev.passes].market) - set(d[d.passes].market) if "passes" in prev else set()
        if entered:
            L.append(f"**Newly passing gates:** {', '.join(sorted(entered))}\n")
        if exited:
            L.append(f"**Dropped out:** {', '.join(sorted(exited))}\n")

    L.append("## Reminder\n")
    L.append("Score ranks candidates for diligence, not for purchase. Nothing here sees "
             "condition, county-level tax variance, real insurance quotes, or whether a "
             "competent property manager exists. Run `screener diligence \"<market>\"` "
             "before acting on any row.\n")
    return "\n".join(L)


def write(d: pd.DataFrame, prev: pd.DataFrame | None, out: pathlib.Path, top: int = 20) -> pathlib.Path:
    out.mkdir(parents=True, exist_ok=True)
    txt = digest(d, prev, top)
    (out / "latest.md").write_text(txt)
    (out / f"{datetime.date.today().isoformat()}.md").write_text(txt)
    keep = ["market", "state", "home_value", "rent", "gross_yield", "net_yield",
            "tax_share_of_rent", "spread", "dscr", "score", "passes", "gate_fail"]
    d[[c for c in keep if c in d.columns]].to_csv(out / "latest.csv", index=False)
    return out / "latest.md"
