#!/usr/bin/env python3
"""Update README.md contributions section with latest stats from GitHub API.

Fetches:
- Merged PRs per repo (via gh search prs)
- Kernel upstream commits (via config)
- Project descriptions (via config)

Updates README between <!--START_SECTION:contributions--> and
<!--END_SECTION:contributions--> markers.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

AUTHOR = "HouMinXi"
README = "README.md"

# Projects with descriptions (order matters for display)
PROJECTS = [
    {
        "name": "linux (net-next)",
        "repo": None,  # kernel — tracked via git log, not GitHub PRs
        "icon": "🐧",
        "desc": "Linux kernel networking subsystem — OVS selftest, YNL spec/infra, ALSA quirks",
        "commits": 10,  # fallback if git log unavailable
    },
    {
        "name": "OmniRoute",
        "repo": "diegosouzapw/OmniRoute",
        "icon": "🔀",
        "desc": "Open-source AI proxy framework — streaming, fallback chain, DNS guard, model config",
    },
    {
        "name": "code-forge",
        "repo": "tirth8205/code-review-graph",
        "icon": "🔨",
        "desc": "AI code review engine — 25+ phases, MCP integration, graph-based analysis",
    },
    {
        "name": "harness",
        "repo": None,  # private repo
        "icon": "🤖",
        "desc": "AI agent orchestration — WeChat iLink → dispatcher → 10 handlers, 335 tests",
    },
    {
        "name": "surflare-watchdog",
        "repo": None,  # private repo
        "icon": "🛡️",
        "desc": "VPN watchdog on N100 router — sing-box tproxy, nftables, SmartDNS, BPF keepalive",
    },
    {
        "name": "ashare-lab",
        "repo": None,  # private repo
        "icon": "📈",
        "desc": "A-share paper trading lab — qlib signal pipeline, 700+ tests, QMT integration",
    },
]


def run(cmd: list[str]) -> str | None:
    """Run a command and return stdout, or None on failure."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return None


def fetch_pr_stats(repo: str) -> dict[str, int]:
    """Fetch PR counts for a repo using gh search prs."""
    out = run(["gh", "search", "prs", "--author", AUTHOR, "--repo", repo,
               "--limit", "200", "--json", "state"])
    if not out:
        return {"merged": 0, "open": 0, "closed": 0}
    prs = json.loads(out)
    merged = sum(1 for p in prs if p["state"].upper() == "MERGED")
    open_n = sum(1 for p in prs if p["state"].upper() == "OPEN")
    closed = sum(1 for p in prs if p["state"].upper() == "CLOSED")
    return {"merged": merged, "open": open_n, "closed": closed}


def fetch_kernel_commits() -> int:
    """Try to get kernel commit count from local repo."""
    for path in ["~/code/linux-net-next", "~/code/kernel"]:
        expanded = os.path.expanduser(path)
        if os.path.isdir(expanded):
            out = run(["git", "-C", expanded, "log", "--oneline",
                       "--author=houminxi@gmail.com", "origin/main"])
            if out:
                return len(out.strip().split("\n"))
    return 10  # fallback


def format_project(proj: dict, stats: dict | None) -> str:
    """Format a single project entry as markdown."""
    icon = proj["icon"]
    name = proj["name"]
    desc = proj["desc"]

    if stats and stats["merged"] > 0:
        badge = f" `{stats['merged']} merged`"
        if stats["open"] > 0:
            badge += f" `{stats['open']} open`"
    elif proj.get("commits"):
        badge = f" `{proj['commits']} commits`"
    else:
        badge = ""

    if proj.get("repo"):
        link = f"[{name}](https://github.com/{proj['repo']})"
    else:
        link = f"**{name}**"

    return f"- {icon} {link}{badge} — {desc}"


def generate_contributions() -> str:
    """Generate the full contributions markdown."""
    lines = []

    for proj in PROJECTS:
        stats = None
        if proj.get("repo"):
            stats = fetch_pr_stats(proj["repo"])
        lines.append(format_project(proj, stats))

    # Add kernel commit count
    kernel_commits = fetch_kernel_commits()
    lines.append("")
    lines.append(f"> Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    return "\n".join(lines)


def update_readme(content: str) -> bool:
    """Update README between markers. Returns True if changed."""
    if not os.path.exists(README):
        print(f"ERROR: {README} not found")
        return False

    with open(README, "r") as f:
        readme = f.read()

    start = "<!--START_SECTION:contributions-->"
    end = "<!--END_SECTION:contributions-->"

    if start not in readme or end not in readme:
        print(f"ERROR: markers not found in {README}")
        return False

    pattern = re.compile(
        re.escape(start) + r".*?" + re.escape(end),
        re.DOTALL,
    )
    new_block = f"{start}\n{content}\n{end}"
    new_readme = pattern.sub(new_block, readme)

    if new_readme == readme:
        print("No changes detected")
        return False

    with open(README, "w") as f:
        f.write(new_readme)
    print("README updated successfully")
    return True


if __name__ == "__main__":
    content = generate_contributions()
    update_readme(content)
