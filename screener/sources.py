"""Bulk data loaders. These run on YOUR machine — the sandbox that generated
this repo has an egress allowlist that blocks Zillow and Census.

No scraping. Every source here is a public bulk file or documented API.
"""
from __future__ import annotations
import io, pathlib, sys
import pandas as pd
import requests

ZILLOW = "https://files.zillowstatic.com/research/public_csvs"

FILES = {
    "zhvi_metro":  f"{ZILLOW}/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
    "zhvi_zip":    f"{ZILLOW}/zhvi/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
    "zhvi_county": f"{ZILLOW}/zhvi/County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
    "zori_metro":  f"{ZILLOW}/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv",
    "zori_zip":    f"{ZILLOW}/zori/Zip_zori_uc_sfrcondomfr_sm_month.csv",
}

CACHE = pathlib.Path("data/cache")


def fetch(key: str, refresh: bool = False) -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / f"{key}.csv"
    if dest.exists() and not refresh:
        return pd.read_csv(dest)
    url = FILES[key]
    print(f"  downloading {key} ...", file=sys.stderr)
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return pd.read_csv(io.BytesIO(r.content))


def _latest_and_trend(df: pd.DataFrame, id_cols: list[str], months_back: int = 12):
    """Zillow files are wide: id columns then one column per month."""
    date_cols = [c for c in df.columns if c[:4].isdigit() and "-" in c]
    date_cols.sort()
    latest, prior = date_cols[-1], date_cols[max(0, len(date_cols) - 1 - months_back)]
    out = df[id_cols].copy()
    out["value"] = df[latest]
    out["value_prior"] = df[prior]
    out["yoy"] = df[latest] / df[prior] - 1
    out["as_of"] = latest
    return out


def build_universe(level: str = "metro", refresh: bool = False) -> pd.DataFrame:
    """Join ZHVI and ZORI into one row per geography. This is Stage 1's input."""
    if level == "metro":
        zhvi = fetch("zhvi_metro", refresh)
        zori = fetch("zori_metro", refresh)
        idc = ["RegionName", "StateName"]
    elif level == "zip":
        zhvi = fetch("zhvi_zip", refresh)
        zori = fetch("zori_zip", refresh)
        idc = ["RegionName", "State", "Metro"]
    else:
        raise ValueError("level must be 'metro' or 'zip'")

    v = _latest_and_trend(zhvi, idc).rename(
        columns={"value": "home_value", "value_prior": "home_value_prior", "yoy": "hpa_yoy"})
    r = _latest_and_trend(zori, idc).rename(
        columns={"value": "rent", "value_prior": "rent_prior", "yoy": "rent_yoy"})
    m = v.merge(r[idc + ["rent", "rent_prior", "rent_yoy"]], on=idc, how="inner")
    m = m.dropna(subset=["home_value", "rent"])
    m = m.rename(columns={"RegionName": "market",
                          "StateName": "state", "State": "state"})
    return m


CENSUS_ACS = "https://api.census.gov/data/2023/acs/acs5"

def census_county(api_key: str | None = None) -> pd.DataFrame:
    """Population, median income, renter share, rental vacancy by county.
    Free; an API key raises the rate limit. https://api.census.gov/data/key_signup.html
    """
    vars_ = {
        "B01003_001E": "population",
        "B19013_001E": "median_income",
        "B25003_003E": "renter_households",
        "B25003_001E": "total_households",
        "B25004_002E": "vacant_for_rent",
    }
    params = {"get": "NAME," + ",".join(vars_), "for": "county:*"}
    if api_key:
        params["key"] = api_key
    r = requests.get(CENSUS_ACS, params=params, timeout=120)
    r.raise_for_status()
    rows = r.json()
    df = pd.DataFrame(rows[1:], columns=rows[0]).rename(columns=vars_)
    for c in vars_.values():
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["renter_share"] = df.renter_households / df.total_households
    return df
