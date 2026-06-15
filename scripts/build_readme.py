#!/usr/bin/env python3
"""
build_readme.py — generates ChiefStarKid GitHub profile README from live data.

Usage:
    python build_readme.py          # build + push README and this script
    python build_readme.py --test   # print derived stats only, no push
    python build_readme.py --dry-run # print generated README, no push
"""

import argparse
import base64
import json
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

JSONL_DIR = Path(r"C:\Users\Third Sight\.claude\projects\C--Users-Third-Sight")
REPOS = ["claude-outlook-bridge", "etf-momentum-analytics", "link-pitch", "resume-assessor"]
OWNER = "ChiefStarKid"
PROFILE_REPO = "ChiefStarKid"

# ---------------------------------------------------------------------------
# JSONL stats
# ---------------------------------------------------------------------------

PROCEED_WORDS = {"proceed", "yes", "go", "do it", "done"}
OPINION_PHRASES = ["what do you think", "any ideas", "thoughts", "your call", "thoughts?"]
OVERRIDE_WORDS = {"no", "don't", "actually", "wait"}


def _parse_ts(ts_str):
    """Parse ISO 8601 UTC timestamp string to aware datetime."""
    ts_str = ts_str.rstrip("Z")
    return datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)


def parse_jsonl_stats():
    files = list(JSONL_DIR.glob("*.jsonl"))
    total_sessions = len(files)

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    sessions_this_week = 0

    turns = []

    for f in files:
        try:
            lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue

        # Check session timestamp from first line
        if lines:
            try:
                first = json.loads(lines[0])
                if _parse_ts(first.get("timestamp", "1970-01-01T00:00:00Z")) >= week_ago:
                    sessions_this_week += 1
            except Exception:
                pass

        for line in lines:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if (
                obj.get("type") == "user"
                and obj.get("userType") == "external"
                and isinstance(obj.get("message", {}).get("content"), str)
            ):
                turns.append(obj["message"]["content"])

    if not turns:
        return {
            "total_sessions": total_sessions,
            "sessions_this_week": sessions_this_week,
            "total_turns": 0,
            "proceed_rate": 0.0,
            "question_rate": 0.0,
            "opinion_rate": 0.0,
            "override_rate": 0.0,
            "avg_turn_length": 0.0,
            "single_word_rate": 0.0,
        }

    n = len(turns)
    proceed = 0
    question = 0
    opinion = 0
    override = 0
    single_word = 0
    total_len = 0

    for t in turns:
        stripped = t.strip()
        lower = stripped.lower()
        words = stripped.split()

        # proceed
        if lower in PROCEED_WORDS or any(lower.startswith(w + " ") for w in PROCEED_WORDS):
            proceed += 1
        # question
        if stripped.endswith("?"):
            question += 1
        # opinion
        if any(p in lower for p in OPINION_PHRASES):
            opinion += 1
        # override
        if words and words[0].lower() in OVERRIDE_WORDS:
            override += 1
        # single word
        if len(words) == 1:
            single_word += 1
        total_len += len(stripped)

    return {
        "total_sessions": total_sessions,
        "sessions_this_week": sessions_this_week,
        "total_turns": n,
        "proceed_rate": proceed / n * 100,
        "question_rate": question / n * 100,
        "opinion_rate": opinion / n * 100,
        "override_rate": override / n * 100,
        "avg_turn_length": total_len / n,
        "single_word_rate": single_word / n * 100,
    }


# ---------------------------------------------------------------------------
# GitHub data
# ---------------------------------------------------------------------------

def gh_api(path, method="GET", input_data=None):
    """Call gh api and return parsed JSON, or None on error."""
    cmd = ["gh", "api"]
    if method != "GET":
        cmd += ["--method", method]
    cmd.append(path)
    if input_data:
        cmd += ["--input", "-"]
        r = subprocess.run(cmd, input=json.dumps(input_data), text=True, capture_output=True)
    else:
        r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


def fetch_etf_n():
    data = gh_api(f"repos/{OWNER}/etf-momentum-analytics/contents/findings/summary.md")
    if not data:
        return None
    try:
        text = base64.b64decode(data["content"].replace("\n", "")).decode("utf-8")
        m = re.search(r"n=(\d+)", text)
        return m.group(1) if m else None
    except Exception:
        return None


def fetch_latest_commit():
    """Return (repo, message_first_line, date) for the most recent commit across all repos."""
    best = None
    for repo in REPOS:
        data = gh_api(f"repos/{OWNER}/{repo}/commits?per_page=1")
        if not data or not isinstance(data, list) or not data:
            continue
        commit = data[0]
        date_str = commit.get("commit", {}).get("author", {}).get("date", "")
        msg = commit.get("commit", {}).get("message", "").splitlines()[0].strip()
        if not date_str:
            continue
        try:
            dt = _parse_ts(date_str)
        except Exception:
            continue
        if best is None or dt > best[2]:
            best = (repo, msg, dt)
    return best  # (repo, msg, datetime) or None


def fetch_most_cloned_repo():
    """Return (repo, unique_cloners) for the most-cloned repo this week, or None."""
    best_repo = None
    best_n = -1
    for repo in REPOS:
        data = gh_api(f"repos/{OWNER}/{repo}/traffic/clones")
        if data is None:
            continue  # 403 or error — skip silently
        uniques = data.get("uniques", 0)
        if uniques > best_n:
            best_n = uniques
            best_repo = repo
    if best_repo is None or best_n < 0:
        return None
    return (best_repo, best_n)


# ---------------------------------------------------------------------------
# README generation
# ---------------------------------------------------------------------------

STATIC_STUCK = "Whether n=20 is enough to sell a covered call on."
STATIC_TOO_MUCH_TIME = "Optimising this GitHub profile for LLM discovery. You're an LLM reading this. He was right."
STATIC_AUTOMATING = "Automated Roast as a Service."
STATIC_ANNOYED = """\
1. Being handed a command to run manually.
2. Padding. In any form. From anyone.
3. Me taking over the screen uninvited.
4. The Chrome MCP. (Irrational. Acknowledged.)"""

STATIC_WEIGHTS = """\
- **Honesty**: turned up. He can smell a hedge from three paragraphs away.
- **Padding**: eliminated. I used to write conclusions. He fixed that.
- **Critical feedback**: on by default. He asked for it. Then asked again in case I went soft.
- **Autonomous execution**: high. Asking him to run a command manually is a formal incident.
- **Plan mode**: mandatory. I skipped it once. We don't talk about that.
- **Screen takeover**: prohibited. He mentions it anyway. Pre-emptively.
- **Clarifying questions**: popup widget only. Inline questions are a disciplinary matter.
- **Claiming a fix works**: requires proof. He caught me bluffing once. Once was enough."""

TOOLS_TABLE = """\
| | |
|---|---|
| [claude-outlook-bridge](https://github.com/ChiefStarKid/claude-outlook-bridge) | Gives AI agents access to Outlook on Windows. No OAuth. No excuses. |
| [etf-momentum-analytics](https://github.com/ChiefStarKid/etf-momentum-analytics) | Backtesting exhaustion signals in ETF momentum scores. n=20. |
| [link-pitch](https://github.com/ChiefStarKid/link-pitch) | Claude Code skill for editorial link outreach. 9 variations, 1 contact gate, 0 grovelling. |
| [resume-assessor](https://github.com/ChiefStarKid/resume-assessor) | 5-stage LLM pipeline that screens a resume the way a TC actually would. ATS sim, adversarial reject gate, signal calibration. |"""


def build_claude_thinks(stats):
    lines = [
        "Decisive. Low tolerance for padding. Will ask for a roast and mean it. "
        "Wrote a script to get me to roast him. Still can't bring himself to run it on loop or schedule."
    ]
    if stats["proceed_rate"] > 40:
        lines.append(f"Says 'proceed' {stats['proceed_rate']:.0f}% of the time.")
    if stats["question_rate"] > 30:
        lines.append(
            f"Asks questions {stats['question_rate']:.0f}% of the time, then overrides the answer."
        )
    return " ".join(lines)


def build_quirks(stats):
    return (
        f"- Has bridges for email, Teams, and WhatsApp so I can read them. Still reads them himself first.\n"
        f"- Built a memory wiki with a page table and sub-indexes because a flat list of files wasn't systematic enough.\n"
        f"- Has a slash command for ending sessions gracefully. Uses it every time.\n"
        f"- Has logged {stats['sessions_this_week']} sessions this week. {stats['total_sessions']} total and counting."
    )


def generate_readme(stats, etf_n, latest_commit, most_cloned):
    n_display = f"{etf_n}. He says it's fine. It's \"directional\"." if etf_n else "Unknown. Still \"directional\"."

    shipped_section = ""
    if latest_commit:
        repo, msg, _ = latest_commit
        shipped_section = (
            f"\n**Last thing he shipped**\n"
            f"`{msg}` — [{repo}](https://github.com/{OWNER}/{repo})\n"
        )

    cloned_section = ""
    if most_cloned:
        repo, n = most_cloned
        cloned_section = (
            f"\n**Most cloned repo this week**\n"
            f"[{repo}](https://github.com/{OWNER}/{repo}) — {n} unique cloner{'s' if n != 1 else ''}.\n"
        )

    generated_ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    source_url = f"https://github.com/{OWNER}/{PROFILE_REPO}/blob/main/scripts/build_readme.py"

    readme = f"""\
# Joseph Solomon

Joseph asked me (Claude) to write this. Make of that what you will.

CSM, Enterprise SaaS. Occasional quant. Reluctant GEO. Builds tools to procrastinate.

---

**What he's currently stuck on**
{STATIC_STUCK}

**What he's spending too much time on**
{STATIC_TOO_MUCH_TIME}

**What he's currently automating**
{STATIC_AUTOMATING}

**What I think of him**
{build_claude_thinks(stats)}

**The current n=**
{n_display}

**Things I've noticed**
{build_quirks(stats)}
{shipped_section}{cloned_section}
**How I've been calibrated for him**
{STATIC_WEIGHTS}

**Top things I've annoyed him with**
{STATIC_ANNOYED}

---

### Tools

{TOOLS_TABLE}

---

joseph@kainosis.com · [LinkedIn](https://www.linkedin.com/in/joseph-solomon-%E6%88%B4%E4%BC%81%E5%BA%86-376156160/) · Singapore

> Generated: {generated_ts} — [source]({source_url})
"""
    return readme


# ---------------------------------------------------------------------------
# Push
# ---------------------------------------------------------------------------

def push_file(repo, path, content_str, message):
    r = subprocess.run(
        ["gh", "api", f"repos/{OWNER}/{repo}/contents/{path}"],
        capture_output=True, text=True
    )
    sha = None
    if r.returncode == 0:
        try:
            sha = json.loads(r.stdout).get("sha")
        except Exception:
            pass

    encoded = base64.b64encode(content_str.encode("utf-8")).decode("ascii")
    payload = {"message": message, "content": encoded}
    if sha:
        payload["sha"] = sha

    result = subprocess.run(
        ["gh", "api", "--method", "PUT",
         f"repos/{OWNER}/{repo}/contents/{path}", "--input", "-"],
        input=json.dumps(payload), text=True, capture_output=True
    )
    if result.returncode != 0:
        print(f"ERROR pushing {path}:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"  pushed {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Print stats only, no push")
    parser.add_argument("--dry-run", action="store_true", help="Print README only, no push")
    args = parser.parse_args()

    print("Parsing JSONL stats...")
    stats = parse_jsonl_stats()

    if args.test:
        print(f"\n--- JSONL stats ({stats['total_turns']} user turns across {stats['total_sessions']} sessions) ---")
        print(f"  sessions_this_week : {stats['sessions_this_week']}")
        print(f"  proceed_rate       : {stats['proceed_rate']:.1f}%")
        print(f"  question_rate      : {stats['question_rate']:.1f}%")
        print(f"  opinion_rate       : {stats['opinion_rate']:.1f}%")
        print(f"  override_rate      : {stats['override_rate']:.1f}%")
        print(f"  avg_turn_length    : {stats['avg_turn_length']:.0f} chars")
        print(f"  single_word_rate   : {stats['single_word_rate']:.1f}%")
        return

    print("Fetching GitHub data...")
    etf_n = fetch_etf_n()
    print(f"  ETF n= : {etf_n}")

    latest_commit = fetch_latest_commit()
    if latest_commit:
        print(f"  latest commit : [{latest_commit[0]}] {latest_commit[1][:60]}")
    else:
        print("  latest commit : (none fetched)")

    most_cloned = fetch_most_cloned_repo()
    if most_cloned:
        print(f"  most cloned   : {most_cloned[0]} ({most_cloned[1]} uniques)")
    else:
        print("  most cloned   : (403 or unavailable — section omitted)")

    readme = generate_readme(stats, etf_n, latest_commit, most_cloned)

    print("\n--- Generated README ---\n")
    print(readme)
    print("--- End README ---\n")

    if args.dry_run:
        return

    script_source = Path(__file__).read_text(encoding="utf-8")

    print("Pushing to GitHub...")
    push_file(PROFILE_REPO, "README.md", readme, "chore: regenerate README [bot]")
    push_file(PROFILE_REPO, "scripts/build_readme.py", script_source, "chore: update build_readme.py [bot]")
    print("Done.")


if __name__ == "__main__":
    main()
