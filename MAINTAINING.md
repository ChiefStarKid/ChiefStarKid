# Maintaining this repo

## After any doc change to claude-outlook-bridge, etf-momentum-analytics, or link-pitch

Regenerate `llms-full.txt` for the affected repo(s):

```bash
python "C:\Users\Third Sight\.claude\build_llms_full.py"              # all repos
python "C:\Users\Third Sight\.claude\build_llms_full.py" etf          # single repo
python "C:\Users\Third Sight\.claude\build_llms_full.py" outlook etf  # subset
```

Also update the `> Last updated: YYYY-MM-DD` line in the relevant `llms.txt`.

## Adding a new repo

1. Add an entry to `README.md` and `llms.txt` in this repo.
2. Add a config block to `scripts/build_llms_full.py` under `REPOS`.
3. Run the build script.