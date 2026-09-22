# Setup

The data fetch runs in **GitHub Actions**, not on your machine. Zillow and Census
are blocked by the egress allowlist in both the Claude cloud sandbox and the
desktop workspace VM — GitHub runners have open internet, so that is where the
fetch lives. It also means the monthly run does not depend on your laptop being
awake.

## One time

```bash
cd ~/market-screener
git init && git add -A && git commit -m "initial"
gh repo create market-screener --private --source=. --push
```

That's it. The workflow fires on the 22nd of each month and commits results to
`reports/`. Nothing else to configure — `GITHUB_TOKEN` is provided automatically
and `permissions: contents: write` in the workflow lets it push.

## Check it works before waiting a month

```bash
gh workflow run monthly-screen
gh run watch
```

Then `git pull && cat reports/latest.md`.

## Running locally

Your own Terminal is not behind the proxy, so this works on your Mac directly:

```bash
pip install -r requirements.txt
python -m screener.cli live --level metro --save --report reports
```

The bundled seed markets work anywhere, no network:

```bash
python -m screener.cli seed --top 25
```
