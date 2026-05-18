# KB Reorganization Plan

## Standing Rule — PARA Structure (enforced 2026-05-15)

All files and folders must live inside one of the four PARA buckets. Nothing goes at the KB root except this file and `OPEN_TASKS.md`.

| Bucket | What goes here |
|---|---|
| `Projects/` | Any active project with a goal and an end — apps, real estate deals, side projects |
| `Areas/` | Ongoing responsibilities with no end date — finance, budget, memory, operational state |
| `Resources/` | Reference material, scripts, guides, research — stuff you might need later |
| `Archives/` | Inactive, completed, or deprecated folders |

When in doubt: if it's a project you're actively working on → `Projects/`. If it's something you maintain indefinitely → `Areas/`. If it's reference material → `Resources/`.

---

## Target Structure

```
/mnt/kb/
├── Projects/                    # PARA: all active projects
│   ├── glamping-str/
│   │   ├── docs/               # planning, strategy, requirements
│   │   │   ├── LAUNCH_PLAN.md
│   │   │   ├── STRATEGY.md
│   │   │   ├── glamping-str-plan.md
│   │   │   ├── land-acquisition-strategy.md
│   │   │   └── ...
│   │   ├── logs/               # LOG.md, REGULATORY_LOG.md, ACCESS.md
│   │   ├── reference/          # septic_faq.md, haul_away_septic_info.md
│   │   ├── scripts/            # contour_grabber.py, find_adjacent_owners.sh
│   │   ├── contours/           # data dir
│   │   └── memory.md           # agent summary (32 lines)
│   │
│   ├── stem-with-roo/
│   │   ├── docs/
│   │   │   ├── LAUNCH_PLAN.md
│   │   │   ├── STRATEGY.md
│   │   │   ├── STEM_plan.md
│   │   │   ├── stem-with-roo-book.md
│   │   │   └── posts_plan.md
│   │   └── memory.md
│   │
│   ├── cleanstreak/
│   │   ├── docs/
│   │   │   ├── LAUNCH_PLAN.md
│   │   │   └── STRATEGY.md
│   │   └── memory.md
│   │
│   ├── paper-trading/          # moved from Resources/
│   │   ├── docs/
│   │   │   ├── paper-trading.md
│   │   │   ├── STRATEGIES.md
│   │   │   └── volume-profile-orderflow.md
│   │   ├── backend/
│   │   ├── frontend/
│   │   ├── docker-compose.yml
│   │   └── memory.md
│   │
│   ├── congressional-trading/
│   │   ├── docs/
│   │   ├── web/
│   │   ├── congress_trades.db
│   │   ├── backtest.py
│   │   └── memory.md
│   │
│   ├── stem-with-roo-remotion/
│   │   ├── src/
│   │   ├── package.json
│   │   └── memory.md
│   │
│   ├── [a-liner-replication, campingsniper, ios-apps, land-sales, parkwood-accord, self-hosting-course, smart-money-tracker]/
│   │   └── Same pattern: docs/ + memory.md
│   │
│   └── Sync-Setup/
│       └── Sync-Setup.md
│
├── Areas/                       # PARA: ongoing responsibilities
│   ├── Finance/
│   │   ├── AREA_PLAN.md        # overview, standards, check-in schedule
│   │   ├── budget/             # moved from top-level
│   │   │   └── LOG.md
│   │   ├── actual-budget/      # moved from top-level
│   │   │   └── LOG.md
│   │   └── parkwood-accord/    # moved from finance/
│   │       └── parkwood-accord.md
│   │
│   ├── Homelab/
│   │   ├── AREA_PLAN.md
│   │   ├── guides/             # moved from Resources/
│   │   │   ├── Proxmox-Health-Check-Instructions.md
│   │   │   ├── Tailscale-Key-Rotation-Instructions.md
│   │   │   └── home-assistant-recovery.md
│   │   └── scripts/            # moved from Resources/
│   │       └── review_money_maker.sh
│   │
│   └── [other areas as needed]/
│
├── Resources/                   # PARA: reference, not projects
│   ├── guides/                 # kept: general learning resources
│   ├── paper-trading/          # reference data (backup)
│   │   └── [read-only historical data]
│   └── knowledge_base.md       # index
│
├── Archives/                    # PARA: completed/inactive
│   └── openclaw-migration/     # moved from top-level
│       ├── AGENTS.md
│       ├── HEARTBEAT.md
│       ├── SOUL.md (archived version)
│       └── ... other docs
│
├── memory/                      # Agent-readable summaries
│   ├── contacts/
│   ├── insights/
│   └── projects/               # one .md per project (13 files)
│
├── concepts/
│   └── soul.md                 # (can be deleted — canonical is /root/.hermes/SOUL.md)
│
└── OPEN_TASKS.md               # loose task file (or move to Projects/?)
```

---

## Migration Steps

### Phase 1: Consolidate Projects (no deletions)

1. **glamping-str** → `/Projects/glamping-str/`
   - Create `Projects/glamping-str/docs/` → move 9 .md files from top-level
   - Create `Projects/glamping-str/logs/` → consolidate LOG.md, REGULATORY_LOG.md, ACCESS.md
   - Create `Projects/glamping-str/reference/` → move septic_faq.md, haul_away_septic_info.md from `Projects/glamping-str/` → reference/
   - Move scripts + contours/ → `Projects/glamping-str/`
   - Verify: all content reachable, no loss

2. **stem-with-roo** → `/Projects/stem-with-roo/`
   - Move top-level LAUNCH_PLAN.md, STRATEGY.md → `docs/`
   - Merge with existing `Projects/stem-with-roo/` content

3. **cleanstreak** → `/Projects/cleanstreak/`
   - Move top-level to `Projects/cleanstreak/docs/`

4. **paper-trading** → `/Projects/paper-trading/`
   - Move `Resources/paper-trading/` to `Projects/`

5. Verify remaining projects (congressional-trading, a-liner-replication, etc.) are complete in `Projects/`

### Phase 2: Create Areas (move ongoing responsibilities)

1. Create `Areas/Finance/`
   - Move `budget/`, `actual-budget/` → `Areas/Finance/`
   - Move `finance/parkwood-accord.md` → `Areas/Finance/parkwood-accord/parkwood-accord.md`
   - Create `AREA_PLAN.md` (template: overview, standards, review cadence)

2. Create `Areas/Homelab/`
   - Move `Resources/guides/` → `Areas/Homelab/guides/`
   - Move `Resources/scripts/` → `Areas/Homelab/scripts/`
   - Create `AREA_PLAN.md`

3. Create other Areas as needed (Health, Relationships, etc.)

### Phase 3: Archive old/inactive

1. Move `openclaw-migration/` → `Archives/openclaw-migration/`

### Phase 4: Clean up

1. Delete/consolidate `concepts/soul.md` (canonical: `/root/.hermes/SOUL.md`)
2. Consolidate lowercase `projects/` into `Projects/`
3. Move `state/` to `/root/.hermes/state/` (runtime data, not KB)
4. Delete `shared-repos/`, `requirements/` (empty)
5. Delete `bin/` (scripts, consider moving gatekeeper.sh + setup-permissions.sh elsewhere if needed)
6. Delete `.DS_Store` (macOS artifact)

### Phase 5: Consolidate memory

**Keep as-is** (currently working well):
- `/mnt/kb/memory/projects/<name>.md` — agent summaries, referenced by notes
- `memory/contacts/`, `memory/insights/` — linked knowledge

**Add**:
- Per-project `memory.md` inside each `Projects/<name>/` (optional detail/scratch space)

---

## File Changes Summary

| Move | From | To |
|------|------|-----|
| cleanstreak | top-level | `Projects/cleanstreak/docs/` |
| glamping-str | top-level (9) + `Projects/` (5) | **consolidate** → `Projects/glamping-str/` |
| stem-with-roo | top-level (2) + `Projects/` (4) | **consolidate** → `Projects/stem-with-roo/` |
| budget, actual-budget, finance | top-level | `Areas/Finance/` |
| guides, scripts | `Resources/` | `Areas/Homelab/` |
| paper-trading | `Resources/paper-trading/` | `Projects/paper-trading/` |
| openclaw-migration | top-level | `Archives/openclaw-migration/` |
| state/ | top-level | → `/root/.hermes/state/` |
| projects/ | top-level | merge into `Projects/` |
| concepts/soul.md | `concepts/` | delete (use `/root/.hermes/SOUL.md`) |
| bin/, shared-repos/, requirements/ | top-level | delete or relocate |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Broken wikilinks (`[[glamping-str]]` → path changes) | Update all `[[...]]` backlinks in notes after moves |
| Syncthing / git conflicts | Commit moves as single batch, verify no stale ignores |
| Agent summaries point to old paths | Backlinks in `memory/projects/` use titles; likely safe if file structure stays under `Projects/` |
| `OPEN_TASKS.md` unanchored | Decide: keep at root, or move into a specific project/area? |

---

## Sign-off Checklist

- [ ] All Projects/ consolidations complete (no loss, all wikilinks updated)
- [ ] Areas/ populated with ongoing responsibilities
- [ ] Archives/ contains openclaw-migration
- [ ] memory/ backlinks verified
- [ ] state/ moved to .hermes
- [ ] Duplicates cleaned (concepts/soul.md, projects/, bin/)
- [ ] OPEN_TASKS.md repositioned
- [ ] Single commit pushed with all moves
