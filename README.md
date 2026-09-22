# National Rental-Market Screener

Two-stage system for finding remote-landlording markets. Stage 1 is a cheap wide
filter over public bulk data. Stage 2 is expensive per-market diligence you run
on a handful of finalists.

Built out of two hand-underwritten market studies (Pinehurst NC, Dayton OH), which
are bundled as calibration rows: if a change to the model stops reproducing those
results, the change is wrong.

## The thesis this encodes

**Gross rent-to-price is a nearly useless ranking metric.** Dayton OH beat
Pinehurst NC by 60% on rent-to-price and landed at the same cap rate, because Ohio
property tax ate 27% of gross rent against 12% in North Carolina.

Across the 81 seed markets, **median yield retention — net yield divided by gross
yield — is 37%**. Nearly two-thirds of the headline number is burden. The markets
that top every "highest rent-to-price" listicle are disproportionately in states
where tax or insurance takes it all back.

Run the same $150,000 house at $1,300 rent through all 50 states and net yield
ranges from **6.03% (HI) to 1.87% (FL)** — a 4.16-point spread driven entirely by
state burden, with the property held identical. That spread is larger than most
of the variation people chase between markets.

## Install

```bash
pip install -r requirements.txt
```

## Use

```bash
# Score the bundled seed markets. Works offline.
python -m screener.cli seed --top 25

# Download Zillow bulk files and score the nation. Needs network.
python -m screener.cli live --level metro --save
python -m screener.cli live --level zip --top 50     # ~30k ZIPs

# What changed since last month — this is the point of looping.
python -m screener.cli diff

# Stage-2 checklist for a finalist.
python -m screener.cli diligence "Meridian, MS"
```

Run `live --save` monthly on a scheduler; read `diff` output.

## Where it runs

The Zillow/Census fetch runs in GitHub Actions (`.github/workflows/screen.yml`),
not locally — see `SETUP.md`. Both the Claude cloud sandbox and the desktop
workspace VM block those hosts. Results are committed to `reports/`.

## Data sources

No scraping. All public bulk files or documented APIs.

| What | Source | Notes |
|---|---|---|
| Home values | Zillow ZHVI bulk CSV | metro / county / ZIP |
| Rents | Zillow ZORI bulk CSV | metro / county / ZIP |
| Population, income, vacancy | Census ACS 5-year API | free; key raises rate limit |
| Property tax | state table in `data/` | **state medians — see limitations** |
| Insurance | state table in `data/` | HO-3 at $300k, scaled and marked up for landlord DP-3 |

## What the score means

`score` ranks candidates **for diligence**. It is not a buy signal.

The composite weights spread over cost of debt most heavily, then net yield, then
tax efficiency, eviction friction, and insurance volatility. Hard gates in
`config.Thresholds` exclude a market outright regardless of yield.

## Limitations — read these

- **State tax rates are medians and hide enormous county variance.** Dayton's
  actual effective rate is 2.04% against Ohio's 1.36% state median. The screener
  therefore *understates* Dayton's tax problem. Always verify county rates in
  Stage 2, and check reassessment-on-sale rules.
- **Insurance is a state average**, which is badly wrong in states with high
  internal variance — coastal vs inland North Carolina, wildfire vs not in
  California, hail alley in Texas. Get a real quote before trusting any ranking.
- **No condition data anywhere.** The Dayton study found the median sub-$100k
  listing needed rehab equal to 60% of purchase price. Nothing here sees that.
- **ZHVI/ZORI are typical values for a geography**, not the specific asset you
  would buy. A metro can screen well while every actually-listed property is
  priced above the index.
- **The model cannot distinguish "cheap because boring" (investable) from "cheap
  because broken" (not).** They are identical in a dataframe. That is what the
  MANUAL items in `diligence.py` exist for, and the property-manager check is the
  binding constraint for remote landlording specifically: a market with great
  numbers and no competent PM industry is untouchable from a distance.

## A finding you should sit with

**Zero of the 81 seed markets produce a positive spread over a 7.6% investor
mortgage.** None. Not the high-yield micropolitans, not the Midwest cash-flow
metros. At current rates, buying a median-priced home at market price and renting
it out does not produce positive leverage anywhere in the seed set.

That is not a bug in the model — it is the 2026 market. It means the achievable
strategies are all-cash, value-add and forced appreciation, or buying meaningfully
below the index. Market selection alone will not fix a negative spread, and any
tool promising otherwise is mismodeling the expense stack.
