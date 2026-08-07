#!/usr/bin/env python3
"""Memory health checker for the memory-optimizer skill.

Scans user-level and project-level memory, and reports:
  - daily logs past the retention window (default 30 days)
  - MEMORY.md files near/over their character limits
  - duplicate candidate lines (within a file and across the two layers)
  - stale markers (临时 / 草稿 / TODO / WIP ...)

Outputs a human-readable report by default, or JSON with --json.

Usage:
  python check_memory_health.py \
      --workspace "C:/path/to/project" \
      --home "C:/Users/xianyu/.workbuddy" \
      --days 30 [--json]
"""
import argparse
import json
import os
import re
from datetime import datetime

USER_MEMORY_LIMIT = 4000
PROJECT_MEMORY_LIMIT = 3000
RETENTION_DAYS = 30
# Lines containing these tokens are flagged as potentially stale (Chinese + ascii).
STALE_MARKERS = ["临时", "草稿", "待确认", "待办", "稍后", "todo", "wip", "temporary", "草稿版", "暂定"]

# Lines shorter than this (after normalization) are ignored for duplicate detection.
MIN_DUP_LEN = 6


def parse_date_from_filename(name):
    m = re.match(r"(\d{4}-\d{2}-\d{2})", name)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None


def normalize(line):
    s = line.strip().lower()
    s = re.sub(r"\s+", " ", s)
    # keep word chars and CJK, drop punctuation
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "", s)
    return s


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception as e:  # pragma: no cover
        return "<ERROR:{}>".format(e)


def collect_lines(text):
    return [ln for ln in text.splitlines() if ln.strip()]


def non_trivial_normalized(lines):
    out = []
    for ln in lines:
        n = normalize(ln)
        if len(n) >= MIN_DUP_LEN:
            out.append((n, ln.strip()))
    return out


def find_daily_logs(memory_dir):
    if not memory_dir or not os.path.isdir(memory_dir):
        return []
    logs = []
    for fn in os.listdir(memory_dir):
        d = parse_date_from_filename(fn)
        if d is None:
            continue
        p = os.path.join(memory_dir, fn)
        if not os.path.isfile(p):
            continue
        logs.append((fn, p, d))
    logs.sort(key=lambda x: x[2])
    return logs


def detect_duplicates(lines):
    """Return list of (normalized, [original_lines]) for lines seen >= 2 times."""
    seen = {}
    for n, orig in non_trivial_normalized(lines):
        seen.setdefault(n, []).append(orig)
    dups = []
    for n, origs in seen.items():
        if len(origs) >= 2:
            # dedupe preserving order
            uniq = []
            for o in origs:
                if o not in uniq:
                    uniq.append(o)
            dups.append((n, uniq))
    return dups


def detect_stale(lines):
    hits = []
    low = [ln.lower() for ln in lines]
    for i, ln in enumerate(lines):
        for tok in STALE_MARKERS:
            if tok in low[i]:
                hits.append(ln.strip())
                break
    return hits


def build_report(home, workspace, days, today):
    home = os.path.expanduser(home)
    user_mem = os.path.join(home, "MEMORY.md")
    proj_mem_dir = os.path.join(workspace, ".workbuddy", "memory") if workspace else None
    proj_mem = os.path.join(proj_mem_dir, "MEMORY.md") if proj_mem_dir else None

    user_text = read_text(user_mem)
    proj_text = read_text(proj_mem) if proj_mem else None

    report = {
        "generated_at": today.isoformat(),
        "retention_days": days,
        "user": {
            "path": user_mem,
            "exists": user_text is not None and not str(user_text).startswith("<ERROR:"),
            "chars": len(user_text) if isinstance(user_text, str) and not user_text.startswith("<ERROR:") else None,
            "limit": USER_MEMORY_LIMIT,
        },
        "project": {
            "path": proj_mem,
            "exists": proj_text is not None and not str(proj_text).startswith("<ERROR:"),
            "chars": len(proj_text) if isinstance(proj_text, str) and not proj_text.startswith("<ERROR:") else None,
            "limit": PROJECT_MEMORY_LIMIT,
        },
        "old_logs": [],
        "duplicates": {"within_user": [], "within_project": [], "cross_layer": []},
        "stale_markers": {"user": [], "project": []},
        "issues": 0,
    }

    if report["user"]["chars"] is not None:
        if report["user"]["chars"] >= 0.9 * USER_MEMORY_LIMIT:
            report["issues"] += 1
    if report["project"]["chars"] is not None:
        if report["project"]["chars"] >= 0.9 * PROJECT_MEMORY_LIMIT:
            report["issues"] += 1

    # daily logs
    if proj_mem_dir:
        for fn, p, d in find_daily_logs(proj_mem_dir):
            age = (today - d).days
            if age > days:
                txt = read_text(p) or ""
                excerpt = txt.strip()[:400].replace("\n", " ")
                report["old_logs"].append({
                    "file": fn,
                    "path": p,
                    "date": d.isoformat(),
                    "age_days": age,
                    "chars": len(txt),
                    "excerpt": excerpt,
                })
                report["issues"] += 1

    # duplicates
    if report["user"]["exists"]:
        report["duplicates"]["within_user"] = [
            {"normalized": n, "lines": origs} for n, origs in detect_duplicates(collect_lines(user_text))
        ]
    if report["project"]["exists"]:
        report["duplicates"]["within_project"] = [
            {"normalized": n, "lines": origs} for n, origs in detect_duplicates(collect_lines(proj_text))
        ]
    # cross-layer
    if report["user"]["exists"] and report["project"]["exists"]:
        user_norm = {n for n, _ in non_trivial_normalized(collect_lines(user_text))}
        for n, origs in detect_duplicates(collect_lines(proj_text)):
            if n in user_norm:
                report["duplicates"]["cross_layer"].append({"normalized": n, "project_lines": origs})
    report["issues"] += (
        len(report["duplicates"]["within_user"])
        + len(report["duplicates"]["within_project"])
        + len(report["duplicates"]["cross_layer"])
    )

    # stale markers
    if report["user"]["exists"]:
        report["stale_markers"]["user"] = detect_stale(collect_lines(user_text))
    if report["project"]["exists"]:
        report["stale_markers"]["project"] = detect_stale(collect_lines(proj_text))
    report["issues"] += len(report["stale_markers"]["user"]) + len(report["stale_markers"]["project"])

    return report


def render_text(report):
    L = []
    L.append("=" * 60)
    L.append("MEMORY HEALTH REPORT  ({})".format(report["generated_at"]))
    L.append("retention window: {} days".format(report["retention_days"]))
    L.append("=" * 60)

    def line_for(layer):
        d = report[layer]
        if not d["exists"]:
            return "  [{}] {} -> NOT FOUND".format(layer, d["path"])
        status = "OK"
        if d["chars"] >= d["limit"]:
            status = "OVER LIMIT"
        elif d["chars"] >= 0.9 * d["limit"]:
            status = "NEAR LIMIT"
        return "  [{}] {} -> {} chars / {} ({}%) [{}]".format(
            layer, d["path"], d["chars"], d["limit"],
            round(100 * d["chars"] / d["limit"]), status)

    L.append("LAYER SIZE:")
    L.append(line_for("user"))
    L.append(line_for("project"))

    L.append("")
    L.append("DAILY LOGS PAST RETENTION (candidates for distillation):")
    if report["old_logs"]:
        for o in report["old_logs"]:
            L.append("  - {} ({} days old, {} chars)".format(o["file"], o["age_days"], o["chars"]))
            if o["excerpt"]:
                L.append("      excerpt: {}".format(o["excerpt"][:120]))
    else:
        L.append("  (none)")

    L.append("")
    L.append("DUPLICATES:")
    if report["duplicates"]["within_user"]:
        L.append("  within user MEMORY.md:")
        for d in report["duplicates"]["within_user"]:
            L.append("    - {}".format(" | ".join(d["lines"][:3])))
    if report["duplicates"]["within_project"]:
        L.append("  within project MEMORY.md:")
        for d in report["duplicates"]["within_project"]:
            L.append("    - {}".format(" | ".join(d["lines"][:3])))
    if report["duplicates"]["cross_layer"]:
        L.append("  cross-layer (same info in BOTH user and project):")
        for d in report["duplicates"]["cross_layer"]:
            L.append("    - {}".format(" | ".join(d["project_lines"][:3])))
    if not (report["duplicates"]["within_user"] or report["duplicates"]["within_project"]
            or report["duplicates"]["cross_layer"]):
        L.append("  (none)")

    L.append("")
    L.append("STALE MARKERS:")
    if report["stale_markers"]["user"]:
        L.append("  user: {}".format(report["stale_markers"]["user"]))
    if report["stale_markers"]["project"]:
        L.append("  project: {}".format(report["stale_markers"]["project"]))
    if not (report["stale_markers"]["user"] or report["stale_markers"]["project"]):
        L.append("  (none)")

    L.append("")
    L.append("TOTAL ISSUES FLAGGED: {}".format(report["issues"]))
    L.append("=" * 60)
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="Memory health checker")
    ap.add_argument("--home", default="~/.workbuddy", help="user-level .workbuddy dir")
    ap.add_argument("--workspace", default=None,
                    help="project workspace root (contains .workbuddy/memory)")
    ap.add_argument("--days", type=int, default=RETENTION_DAYS, help="retention window in days")
    ap.add_argument("--json", action="store_true", help="output JSON instead of text")
    args = ap.parse_args()

    today = datetime.now().date()
    report = build_report(args.home, args.workspace, args.days, today)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_text(report))


if __name__ == "__main__":
    main()
