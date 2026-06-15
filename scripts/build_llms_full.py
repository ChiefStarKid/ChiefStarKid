#!/usr/bin/env python3
"""
build_llms_full.py — regenerate llms-full.txt for ChiefStarKid repos

Usage:
  python build_llms_full.py                         # all repos
  python build_llms_full.py outlook                 # claude-outlook-bridge only
  python build_llms_full.py etf                     # etf-momentum-analytics only
  python build_llms_full.py link-pitch              # link-pitch only
  python build_llms_full.py outlook etf link-pitch  # multiple

  python build_llms_full.py resume                   # resume-assessor only
"""

import subprocess, sys, base64, json

REPOS = {
    "outlook": {
        "full_name": "ChiefStarKid/claude-outlook-bridge",
        "branch": "main",
        "canonical": "https://github.com/ChiefStarKid/claude-outlook-bridge",
        "title": "claude-outlook-bridge — full documentation",
        "files": [
            "llms.txt",
            "AGENTS.md",
            "CLAUDE_INTEGRATION.md",
            "EXAMPLES.md",
            "README.md",
        ],
    },
    "etf": {
        "full_name": "ChiefStarKid/etf-momentum-analytics",
        "branch": "master",
        "canonical": "https://github.com/ChiefStarKid/etf-momentum-analytics",
        "title": "etf-momentum-analytics — full documentation",
        "files": [
            "llms.txt",
            "AGENTS.md",
            "methodology/signal-design.md",
            "methodology/backtest-design.md",
            "methodology/regime-detection.md",
            "findings/summary.md",
            "CHANGELOG.md",
            "ABOUT.md",
        ],
    },
    "link-pitch": {
        "full_name": "ChiefStarKid/link-pitch",
        "branch": "master",
        "canonical": "https://github.com/ChiefStarKid/link-pitch",
        "title": "link-pitch — full documentation",
        "files": [
            "llms.txt",
            "AGENTS.md",
            "SKILL.md",
            "EVALUATION.md",
            "references/steps.md",
            "references/templates.md",
            "styles/internal.md",
            "styles/outreach.md",
        ],
    },
    "resume": {
        "full_name": "ChiefStarKid/resume-assessor",
        "branch": "master",
        "canonical": "https://github.com/ChiefStarKid/resume-assessor",
        "title": "resume-assessor — full documentation",
        "files": [
            "README.md",
            "assessor_prompt.md",
        ],
    },
}

ALIASES = {
    "outlook": "outlook",
    "claude-outlook-bridge": "outlook",
    "etf": "etf",
    "etf-momentum-analytics": "etf",
    "link-pitch": "link-pitch",
    "linkpitch": "link-pitch",
    "resume": "resume",
    "resume-assessor": "resume",
}


def gh_get(path):
    result = subprocess.run(
        ["gh", "api", path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh api {path} failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def fetch_file(repo_full, path):
    data = gh_get(f"repos/{repo_full}/contents/{path}")
    return base64.b64decode(data["content"]).decode("utf-8")


def get_file_sha(repo_full, path):
    try:
        data = gh_get(f"repos/{repo_full}/contents/{path}")
        return data["sha"]
    except Exception:
        return None


def push_file(repo_full, path, content, sha, message):
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    payload = {"message": message, "content": encoded}
    if sha:
        payload["sha"] = sha

    payload_json = json.dumps(payload)
    result = subprocess.run(
        ["gh", "api", f"repos/{repo_full}/contents/{path}",
         "--method", "PUT", "--input", "-"],
        input=payload_json, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Push failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def build(key):
    cfg = REPOS[key]
    repo = cfg["full_name"]
    print(f"\n{'='*60}")
    print(f"Building {repo}")
    print(f"{'='*60}")

    sections = [
        f"# {cfg['title']}\n\nThis file concatenates all documentation for LLM ingestion.\nCanonical source: {cfg['canonical']}\n"
    ]

    for path in cfg["files"]:
        print(f"  Fetching {path}...")
        try:
            content = fetch_file(repo, path)
            sections.append(f"---\n\n## {path}\n\n{content.strip()}\n")
        except Exception as e:
            print(f"  WARNING: skipping {path} — {e}")

    full_content = "\n".join(sections) + "\n"

    sha = get_file_sha(repo, "llms-full.txt")
    action = "update" if sha else "create"
    print(f"  Pushing llms-full.txt ({action})...")

    push_file(
        repo, "llms-full.txt", full_content, sha,
        f"docs: regenerate llms-full.txt from source files"
    )
    print(f"  Done. {len(full_content):,} chars written.")
    return len(full_content)


def main():
    args = sys.argv[1:]
    if not args:
        targets = list(REPOS.keys())
    else:
        targets = []
        for a in args:
            key = ALIASES.get(a.lower())
            if not key:
                print(f"Unknown repo alias: {a}. Valid: {', '.join(ALIASES)}")
                sys.exit(1)
            targets.append(key)

    for key in targets:
        build(key)

    print(f"\nDone — {len(targets)} repo(s) updated.")


if __name__ == "__main__":
    main()
