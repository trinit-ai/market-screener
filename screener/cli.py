"""CLI. `python -m screener.cli --help`"""
from __future__ import annotations
import argparse, sys
import pandas as pd
from . import model, score, store, diligence, report
from .config import DEFAULT

def load_burden(path="data/state_burden.csv") -> pd.DataFrame:
    return pd.read_csv(path)

def run_seed(args):
    mk = pd.read_csv("data/seed_markets.csv")
    d = mk.merge(load_burden(), on="state", how="left")
    d = model.underwrite(d, DEFAULT)
    d = score.apply_gates(d, DEFAULT)
    d = score.score(d, DEFAULT)
    if args.save:
        print(f"saved snapshot {store.save(d)}", file=sys.stderr)
    show(d, args.top)

def run_live(args):
    from . import sources
    print("building universe from Zillow bulk files...", file=sys.stderr)
    u = sources.build_universe(level=args.level, refresh=args.refresh)
    u["state"] = u.state.astype(str).str.strip().str[:2].str.upper()
    d = u.merge(load_burden(), on="state", how="left").dropna(subset=["prop_tax_rate"])
    d = model.underwrite(d, DEFAULT)
    d = score.apply_gates(d, DEFAULT)
    d = score.score(d, DEFAULT)
    prev = None
    rs = store.runs()
    if rs:
        import sqlite3, pandas as _pd
        with sqlite3.connect(store.DB) as cx:
            prev = _pd.read_sql("SELECT * FROM snapshots WHERE run_date=?", cx, params=(rs[-1],))
    if args.save:
        print(f"saved snapshot {store.save(d)}", file=sys.stderr)
    if getattr(args, "report", None):
        import pathlib as _pl
        out = report.write(d, prev, _pl.Path(args.report), args.top)
        print(f"wrote {out}", file=sys.stderr)
    show(d, args.top)
    gaps = score.diligence_gaps(d)
    if gaps:
        print(f"\nNOT yet priced into the score: {', '.join(gaps)}", file=sys.stderr)

def show(d: pd.DataFrame, top: int):
    p = d[d.passes]
    print(f"\n{len(p)} of {len(d)} markets clear the hard gates\n")
    cols = ["market","state","home_value","rent","gross_yield","net_yield",
            "tax_share_of_rent","spread","dscr","score"]
    v = p.head(top)[cols].copy()
    print(f"{'#':<4}{'Market':32}{'ST':4}{'Value':>10}{'Rent':>7}{'Gross':>8}{'Net':>8}{'Tax%':>7}{'Spread':>8}{'DSCR':>7}{'Score':>7}")
    for i,(_,r) in enumerate(v.iterrows(),1):
        print(f"{i:<4}{r.market[:31]:32}{r.state:4}${r.home_value:>9,.0f}${r.rent:>6,.0f}"
              f"{r.gross_yield:>8.2%}{r.net_yield:>8.2%}{r.tax_share_of_rent:>7.0%}"
              f"{r.spread:>+8.2%}{r.dscr:>7.2f}{r.score:>7.1f}")

def cmd_diff(args):
    rs = store.runs()
    if len(rs) < 2:
        print("need two snapshots; run with --save on separate dates", file=sys.stderr); return
    a,b = (args.a or rs[-2]), (args.b or rs[-1])
    print(store.diff(a,b).head(args.top).to_string(index=False))

def cmd_dd(args):
    diligence.print_checklist(args.market)

def main():
    ap = argparse.ArgumentParser(prog="screener", description="National rental-market screener")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("seed", help="score the bundled seed markets (works offline)")
    s.add_argument("--top", type=int, default=25); s.add_argument("--save", action="store_true")
    s.set_defaults(func=run_seed)

    l = sub.add_parser("live", help="download Zillow bulk data and score the nation")
    l.add_argument("--level", choices=["metro","zip"], default="metro")
    l.add_argument("--refresh", action="store_true"); l.add_argument("--top", type=int, default=30)
    l.add_argument("--save", action="store_true")
    l.add_argument("--report", metavar="DIR", help="write a markdown digest to DIR")
    l.set_defaults(func=run_live)

    d = sub.add_parser("diff", help="what changed between two snapshots")
    d.add_argument("--a"); d.add_argument("--b"); d.add_argument("--top", type=int, default=20)
    d.set_defaults(func=cmd_diff)

    dd = sub.add_parser("diligence", help="print the Stage-2 checklist")
    dd.add_argument("market"); dd.set_defaults(func=cmd_dd)

    a = ap.parse_args(); a.func(a)

if __name__ == "__main__":
    main()
