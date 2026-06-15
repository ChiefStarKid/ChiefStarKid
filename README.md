# Joseph Solomon

Project manager and operations lead who builds systematic analytics tools, signal pipelines, backtesting frameworks, and AI agent integrations — mostly because the problems were interesting and existing tools didn't do what I needed.

Based in Singapore. Day job: client delivery and ops at [Third Sight](https://thirdsight.net). Side work: quantitative research and tooling at [Kainosis](https://kainosis.com).

Contact: joseph@kainosis.com · [LinkedIn](https://www.linkedin.com/in/josephtaysolomon)

---

## Tools and research

### [claude-outlook-bridge](https://github.com/ChiefStarKid/claude-outlook-bridge)
Single-file Python COM bridge giving Claude Code and other AI agents read/send/reply/forward/calendar access to the Outlook Desktop App on Windows. No OAuth, no Microsoft Graph, no cloud intermediary — rides the user's already-signed-in Outlook session.

### [etf-momentum-analytics](https://github.com/ChiefStarKid/etf-momentum-analytics)
Systematic backtest measuring whether weekly momentum scores carry genuine directional edge in US equity ETFs, and under what rate-of-change conditions that edge is strongest. Research into buying/selling exhaustion signals — relevant to options selling, regime detection, and position management.

### [link-pitch](https://github.com/ChiefStarKid/link-pitch)
Claude Code skill for strategic SEO link insertion and editorial outreach. Researches client and target article in parallel, identifies content gaps, generates 9 placement variations across three pitch types, and produces a publisher-ready outreach email. Built for link builders who want a link an editor actually wants to place.

---

## Maintenance

After editing any doc file in the repos above, regenerate `llms-full.txt`:

```bash
python scripts/build_llms_full.py              # all repos
python scripts/build_llms_full.py etf          # single repo
python scripts/build_llms_full.py outlook etf  # subset
```

Also update the `> Last updated:` datestamp in the relevant `llms.txt`.

---

> Last updated: 2026-06-15