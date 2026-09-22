"""SQLite snapshot store. The loop's value is month-over-month diffs:
a county reassessment, an insurance shock, a rent inflection."""
from __future__ import annotations
import sqlite3, datetime, pathlib
import pandas as pd

DB = pathlib.Path("data/snapshots.db")

def save(df: pd.DataFrame, run_date: str | None = None) -> str:
    DB.parent.mkdir(parents=True, exist_ok=True)
    run_date = run_date or datetime.date.today().isoformat()
    d = df.copy(); d["run_date"] = run_date
    with sqlite3.connect(DB) as cx:
        d.to_sql("snapshots", cx, if_exists="append", index=False)
    return run_date

def runs() -> list[str]:
    if not DB.exists(): return []
    with sqlite3.connect(DB) as cx:
        try:
            return [r[0] for r in cx.execute(
                "SELECT DISTINCT run_date FROM snapshots ORDER BY run_date").fetchall()]
        except sqlite3.OperationalError:
            return []

def diff(a: str, b: str, key: str = "market") -> pd.DataFrame:
    """What changed between two runs. This is what you actually read each month."""
    with sqlite3.connect(DB) as cx:
        x = pd.read_sql("SELECT * FROM snapshots WHERE run_date=?", cx, params=(a,))
        y = pd.read_sql("SELECT * FROM snapshots WHERE run_date=?", cx, params=(b,))
    cols = [key, "score", "net_yield", "spread", "tax_share_of_rent", "rent", "home_value"]
    cols = [c for c in cols if c in x.columns and c in y.columns]
    m = x[cols].merge(y[cols], on=key, suffixes=("_before", "_after"))
    for c in cols:
        if c == key: continue
        m[f"d_{c}"] = m[f"{c}_after"] - m[f"{c}_before"]
    return m.sort_values("d_score", ascending=False)
