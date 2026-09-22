"""SQLite snapshot store. The loop's value is month-over-month diffs:
a county reassessment, an insurance shock, a rent inflection.

Schema note: the scored dataframe's columns change whenever the model gains an
input (adding investor tax rates added two). A naive to_sql(append) raises
OperationalError on any mismatch, which once silently broke a scheduled run.
save() reconciles the schema instead of failing.
"""
from __future__ import annotations
import sqlite3, datetime, pathlib
import pandas as pd

DB = pathlib.Path("data/snapshots.db")

_SQL_TYPE = {"int64": "INTEGER", "float64": "REAL", "bool": "INTEGER"}


def _table_columns(cx: sqlite3.Connection) -> list[str]:
    try:
        return [r[1] for r in cx.execute("PRAGMA table_info(snapshots)")]
    except sqlite3.OperationalError:
        return []


def _reconcile(cx: sqlite3.Connection, df: pd.DataFrame) -> None:
    """Add any columns the dataframe has that the table lacks. Columns the table
    has but the frame lacks simply land NULL, which is the correct semantics for
    'this run did not measure that'."""
    existing = _table_columns(cx)
    if not existing:
        return
    for col in df.columns:
        if col not in existing:
            sql_t = _SQL_TYPE.get(str(df[col].dtype), "TEXT")
            cx.execute(f'ALTER TABLE snapshots ADD COLUMN "{col}" {sql_t}')


def save(df: pd.DataFrame, run_date: str | None = None) -> str:
    DB.parent.mkdir(parents=True, exist_ok=True)
    run_date = run_date or datetime.date.today().isoformat()
    d = df.copy()
    d["run_date"] = run_date
    with sqlite3.connect(DB) as cx:
        _reconcile(cx, d)
        d.to_sql("snapshots", cx, if_exists="append", index=False)
    return run_date


def runs() -> list[str]:
    if not DB.exists():
        return []
    with sqlite3.connect(DB) as cx:
        try:
            return [r[0] for r in cx.execute(
                "SELECT DISTINCT run_date FROM snapshots ORDER BY run_date").fetchall()]
        except sqlite3.OperationalError:
            return []


def load(run_date: str) -> pd.DataFrame:
    with sqlite3.connect(DB) as cx:
        return pd.read_sql("SELECT * FROM snapshots WHERE run_date=?", cx, params=(run_date,))


def diff(a: str, b: str, key: str = "market") -> pd.DataFrame:
    """What changed between two runs. This is what you actually read each month."""
    x, y = load(a), load(b)
    cols = [key, "score", "net_yield", "spread", "tax_share_of_rent", "rent", "home_value"]
    cols = [c for c in cols if c in x.columns and c in y.columns]
    m = x[cols].merge(y[cols], on=key, suffixes=("_before", "_after"))
    for c in cols:
        if c == key:
            continue
        m[f"d_{c}"] = m[f"{c}_after"] - m[f"{c}_before"]
    return m.sort_values("d_score", ascending=False)
