# Slack Channel History Summary

Generated: 2026-05-08 (Hermes)
Source: pulled last 50 messages of each channel via `slack-history` skill on 2026-05-08 13:18 UTC.

## Key context
- All channels were created in mid-April 2026.
- The prior agent was **NemoClaw** (an OpenClaw replica). Most past work happened in NemoClaw's workspace at `~/.openclaw/workspace/` and may not have been migrated to `/mnt/kb`. Where NemoClaw saved files, those files are likely still there.
- **Hermes** (the current agent, user `U0B0F0XDML7`) joined every channel on 2026-05-08 between 12:53 and 13:14 UTC.
- 6 channels return `not_in_channel` for history (bot needs to be invited): `openclaw-replica`, `open-claw`, `nemo-claw`, `new-channel`, `all-kay-inc`, `social`.

---

## Active project channels (in OPEN_TASKS.md)

### `#glamping-str` (C0ASF1XRETH) — ⭐ very active
**Purpose**: Santa Cruz mountains land purchase (APN 086-631-14) for a short-term-rental glamping operation. Father will live on-site as caretaker.
**Status**: 705 lines of history; active research thread.
**Key threads**:
- Land acquisition strategy, neighbor-APN outreach, auction sourcing
- Septic constraints (`WSW-SLW` designations), perc test requirements, slope limits
- Consumer-grade GPS recommendations (~$100, foot accuracy)
- Channel-prompt overlay already wired ✓
**Files referenced**: `Projects/glamping-str/land-acquisition-strategy.md` (NemoClaw-saved)
**Pick up at**: regulatory unknowns from `OPEN_TASKS.md` glamping-str P0 entries.

### `#parkwood-accord` (C0AST2ZB1S8) — quiet
**Purpose**: Joint venture with wife — glamping/STR property search in Santa Cruz County.
**Status**: 5 lines, just setup. No substantive work yet.
**Pick up at**: identify 3–5 candidate properties (P1 in OPEN_TASKS.md).

### `#a-liner` (C0ASMDCUSQN) — minimal but kicked off
**Purpose**: DIY hard-sided pop-up camper build (a-liner replication).
**Status**: 151 lines. Project kickoff in April; NemoClaw built engineering calculators. Recent message asks Hermes to summarize history into KB (still pending).
**Pick up at**: finalize material list / BOM (P1 in OPEN_TASKS.md).

### `#camping-sniper` (C0ASPFDAZ1Q) — active R&D
**Purpose**: Campsite availability monitor for Recreation.gov (and similar). Sends Slack alerts on openings.
**Status**: 117 lines. Discussion of API endpoints, rate limits, attribution. Last NemoClaw msg offered to draft an n8n workflow that respects rate limits.
**Pick up at**: verify Recreation.gov API endpoint + auth (P2 in OPEN_TASKS.md).

### `#land-acquisitions` (C0AV80C4TS8) — quiet
**Purpose**: Broader land-acquisition workflow (separate from but adjacent to glamping-str).
**Status**: 5 lines, just setup.
**Pick up at**: undefined; consider folding into glamping-str / parkwood-accord or define scope.

### `#clean-streak` (C0AS81UA7KR) — substantive R&D
**Purpose**: Habit-tracker iOS app at cleanstreak.club. Marketing/monetization research.
**Status**: 257 lines. NemoClaw produced market analysis + Reddit/Facebook/TikTok/Instagram marketing plans (saved to `~/.openclaw/workspace/cleanstreak_*.md`).
**Pick up at**: TestFlight push + streak restoration feature (P3 in OPEN_TASKS.md). Migrate the marketing docs to `/mnt/kb/Projects/clean-streak/` first.

### `#stem-with-roo` (C0A6E9RLZBL) — discovery
**Purpose**: STEM-with-Roo project (educational content for child? unclear).
**Status**: 234 lines. Discussion only; mostly NemoClaw test/health-check messages near end of period.
**Pick up at**: define what "STEM with Roo" actually is — purpose/audience/output unclear from history alone.

---

## Hermes operations

### `#hermes-home` (C0B1R3GMQ0Y) — active control channel
**Purpose**: Hermes default channel; receives morning briefing + burndown ticks.
**Status**: 611 lines. Live config tuning, model swaps, cron debugging — the meta-channel for managing Hermes itself.
**Pick up at**: ongoing — first burndown tick fires today at 9 AM PT.

---

## Active monetization / experiment channels

### `#futures-trader` (C0AGSK349J5) — substantive work
**Purpose**: Paper-trading + backtesting for futures (ES, NQ, CL, GC). Includes congressional-trading scraper (House/Senate disclosures correlated with futures).
**Status**: 565 lines. NemoClaw built a Flask + React starter saved to `~/.openclaw/workspace/Resources/paper-trading/`. Six scalping strategies wired in (incl. VWAP mean-reversion). Congressional-trading tab added.
**Pick up at**: migrate paper-trading code to `/mnt/kb/Resources/paper-trading/` (or verify it's already there). Audit data freshness on the congressional feed (P3 in OPEN_TASKS.md).

### `#money-maker` (C0AGSMY3GAD) — strategy / planning channel
**Purpose**: Ideation channel for monetization across all projects. Original prompt: "turn $500 into $1M in 8 months."
**Status**: 481 lines. NemoClaw built a market-research doc covering all monetization angles. Hourly cron was set up to "sharpen the plan" iteratively.
**Pick up at**: review what's still active vs. abandoned. Lots of tests + heartbeats clog later messages — actual work is in the first half of history.

### `#reviews` (C0A6K7A1SQY) — ongoing strategy
**Purpose**: Get into Amazon Vine (Reviewer Program) and similar review platforms. Some require micro-influencer status.
**Status**: 136 lines. NemoClaw drafted a 2-week sprint plan (no commit on user follow-through visible in history).
**Pick up at**: confirm whether user wants to execute the sprint plan, or close this thread.

### `#automate-my-life` (C0AUPV1LRQU) — kicked off, not deep
**Purpose**: Find pain points + automate them.
**Status**: 25 lines, mostly setup. Hermes asked today to summarize history into KB (this doc satisfies it).
**Pick up at**: ask user for top 3 pain points to seed automation backlog.

---

## Infra / personal

### `#home-lab-it` (C0ASMDKFFRC) — active infra
**Purpose**: Homelab + Proxmox + Tailscale.
**Status**: 764 lines. NemoClaw set up Tailscale key rotation, nightly Proxmox health-check script + Slack alerts, and provided a complete Slack channel ID map. Discussion of safe web-search via secondary agent (was blocked by OpenClaw gateway not being paired).
**Pick up at**: migrate Tailscale-rotation + Proxmox-health-check scripts to `/mnt/kb/Projects/home-lab/` if not already.

### `#home-assistant` (C0ATG04HQVC) — pending decision
**Purpose**: Spruce up Home Assistant dashboard.
**Status**: 103 lines. NemoClaw asked which approach the user prefers (API vs. SSH) and for a long-lived access token. **No user response on record.**
**Pick up at**: nudge user for the API-vs-SSH decision + token.

### `#actual-budget` (C0AULBCJ98S) — kicked off, no execution
**Purpose**: Automate Actual Budget syncing + transaction classification.
**Status**: 115 lines. Project kicked off but no substantive output visible. Recent user msg asks Hermes to review chat + add to KB (this doc).
**Pick up at**: identify the actual sync mechanism (Plaid? Manual import?) and what classification logic is needed.

### `#self-hostin` (C0AS822C6QP) — empty
**Purpose**: Self-hosting course (per OPEN_TASKS.md).
**Status**: 3 lines, just setup. No content.
**Pick up at**: 8–12 module outline (P3 in OPEN_TASKS.md).

---

## Inaccessible (bot not invited)

| Channel | ID | Action |
|---|---|---|
| `openclaw-replica` | C0AG7A1P0LT | Invite `@Hermes` to read history |
| `open-claw` | C0B194SJ2KA | Invite `@Hermes` |
| `nemo-claw` | C0AT2H7LQBS | Invite `@Hermes` |
| `new-channel` | C0A4S7X8F0C | Likely can be archived |
| `all-kay-inc` | C0A4K74P1PF | Workspace #general — invite if you want briefings here |
| `social` | C0A4S7UBUA0 | Probably skip |

---

## Recommended next moves (added to OPEN_TASKS.md)

1. **Migrate NemoClaw artifacts** — sweep `~/.openclaw/workspace/` for project files referenced above and copy/symlink into `/mnt/kb/Projects/<project>/`. Big bang of context the agent can't currently see.
2. **Decide on `#land-acquisitions`** scope — fold into glamping-str/parkwood-accord, or define separately.
3. **Resolve pending decisions**: `#home-assistant` API-vs-SSH question, `#reviews` sprint-plan commit.
4. **Build channel-prompt overlays** for the active project channels: parkwood-accord, a-liner, camping-sniper, clean-streak, futures-trader. Each gets a focused prompt like glamping-str already has.