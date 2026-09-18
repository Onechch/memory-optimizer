# Memory Architecture Reference

This reference documents the three-layer memory system used by WorkBuddy, so the
memory-optimizer skill can make correct layering and retention decisions. It is the
single source of truth for paths, limits, and lifecycle rules.

## Layer 1 — Cloud Memory (read-only)

- Two parts:
  - **(A) Auto-injected profile**: server-generated summary of long-term user profile,
    injected at session start. Managed by the server; cached locally. DO NOT modify locally.
  - **(B) Historical conversation retrieval**: `conversation_search` tool searches past
    conversations server-side. Zero access to the current conversation.
- **Write policy**: NEVER write to Layer 1. It is server-managed and read-only from the
  agent's perspective. Use it only for retrieval and as context.

## Layer 2 — User-level Local Memory (read/write)

- **File**: `~/.workbuddy/MEMORY.md`
- **Scope**: all projects, the user as a person.
- **Limit**: 4000 chars per session of writes.
- **Use for**: personal habits, cross-project conventions/rules, persistent facts about
  the user that apply everywhere (OS, package managers, security rules, working-style
  constraints such as "confirm plan before writing scripts" or "no emoji in code").
- **Trigger**: user explicitly asks to remember something for the long term AND it is
  not tied to a specific project.

## Layer 3 — Workspace (Project) Memory (read/write)

- **Directory**: `<workspace>/.workbuddy/memory/`
- **Files**:
  - `YYYY-MM-DD.md` — daily work log. **Append-only**, never overwrite. Records only
    what has lasting value (built/fixed/refactored something, chose an approach, learned
    a user preference). Skip transient info (search results, temp paths, tool errors).
  - `MEMORY.md` — curated long-term project notes. **Limit**: 3000 chars per session.
- **Scope**: current project only.
- **Use for**: project-specific decisions, architecture, tech choices, project conventions
  that should NOT generalize, lessons tied to this codebase.

## Layering decision rule (core of the skill)

1. Does the information describe the **user as a person** or apply to **all projects**?
   -> Write to **user-level** `~/.workbuddy/MEMORY.md`.
2. Is the information **specific to this project's code/context**?
   -> Write to **project-level** `<workspace>/.workbuddy/memory/MEMORY.md` (or a daily log).
3. **Uncertain?** Ask the user before writing:
   "这个规则/信息只用于当前项目，还是所有项目都用？"
   Do NOT guess when the scope is ambiguous.

## Redundancy / source-pointer rule (report dedup)

Before writing any memory entry, check whether the information already appears in the
report/files the agent produced **this session**.

- **If it is already in the current report** -> do NOT duplicate the content. Store only a
  **source pointer**: the location (absolute path or URL) plus a short index of what it
  contains and 2-4 retrieval keywords.
  Format: `- [来源] <one-line summary> | 位置：<path/url> | 关键词：<kw1, kw2>`
- **If NOT in the current report AND has long-term cross-session value** -> store as an
  independent entry (then apply the layering decision above).
- **If NOT in the current report but one-off / transient** -> do not store.

Rationale: keeps total memory volume bounded and avoids redundant duplication burden.
The `check_memory_health.py` script can flag report-redundant entries when given
`--reports-dir <this-session report dir>` (verbatim substring match).

## Health rules

- Char limits: user 4000, project 3000. Warn at >= 90%; never exceed without condensing.
- Maintain a single canonical copy of each fact. Do NOT store the same fact in both
  layers (cross-layer duplication is a defect).
- Report redundancy is a defect too: an entry that duplicates content already present in a
  current-session report should be replaced by a source pointer (see above). Use
  `check_memory_health.py --reports-dir` to detect.
- Daily logs are supplemental and must NOT replace the normal reply or a user-requested
  deliverable. Prefer a source pointer (location + keywords) over copying report content
  verbatim.

## Retention / distillation policy

- Daily logs are retained for **30 days**.
- A log older than 30 days is a distillation candidate:
  1. Read it; extract reusable "lessons learned" (non-trivial, generalizable insights).
  2. Merge those as short entries into project `MEMORY.md`, respecting the 3000-char limit.
  3. **Confirm with the user that nothing important is lost** before deleting the original log.
  4. Delete only logs older than 30 days. Never delete recent logs. Never delete without confirm.
- Secrets: do not store secrets unless the user explicitly asks.

## Path handling note (Windows)

- The managed Python resolves `/` as `D:\`; Git Bash resolves `/` as `C:\`. Always pass
  **Windows absolute paths with drive letters** (e.g. `C:/Users/yourname/...`) when invoking
  scripts from the agent, to avoid path mismatches between runtimes.
