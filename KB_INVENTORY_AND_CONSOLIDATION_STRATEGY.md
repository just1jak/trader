# KB Inventory & Consolidation Strategy

**Status**: Draft planning doc for Hermes ownership  
**Created**: 2026-05-18  
**Owner**: Hermes (maintains via cron tasks)  

---

## Executive Summary

Your KB structure is ~300MB (mostly stem-with-roo-remotion node_modules). It's organized per PARA but has:
- **Duplicates** at Projects root (A-Liner-Replication.md, Parkwood-Accord.md, README.md)
- **Build artifacts** (node_modules, package-lock.json) that shouldn't be in KB
- **Archived memories** (from NemoClaw) waiting to integrate
- **Permission issues** blocking Hermes from auto-maintaining OPEN_TASKS.md

**Good news**: The KB_REORGANIZATION_PLAN.md already exists and is well-designed. We just need to execute it and fix Hermes' write perms.

---

## Current Inventory

### Active Projects (by priority from OPEN_TASKS.md)

| Project | Status | Lines | Key Docs | Notes |
|---------|--------|-------|----------|-------|
| **glamping-str** | P0 active | 2.5K | REGULATORY_LOG, STR_REQUIREMENTS, FIRE_SANITATION_CHECKLIST, PERMIT_ROADMAP | Most active; site visit pending; 7.1M (GIS contours) |
| **cleanstreak** | P1 ready | 550 | LAUNCH_PLAN, STRATEGY, MARKET_ANALYSIS | Revenue-ready; app submission + ads/social ready |
| **stem-with-roo** | P1 active | 950 | LAUNCH_PLAN, STRATEGY, stem-with-roo-book, posts_plan | Video series; Patreon setup; content calendar |
| **a-liner-replication** | P1 active | 157 | a-liner-replication.md | Material list researched; prototype blocked on materials |
| **75-hard** | P1 pipeline | minimal | STRATEGY.md | Market analysis shared with cleanstreak |
| **luna** | P1 pipeline | minimal | OPEN_QUESTIONS.md, STRATEGY.md | Period tracking app; MVP undefined |
| **parkwood-accord** | P2 ready | 134 | parkwood-accord.md | Spending rules + wireframe ready; Plaid integration pending |
| **campingsniper** | P2 ready | 163 | campingsniper.md | Rec.gov API working; ready to expand to Forest Service/BLM |
| **ios-apps** | P2 active | 240 | ios-apps.md | Parkwood Accord + pill-counter app; HIPAA review done |
| **congressional-trading** | P1 active | 900 | NEXT_STEPS.md, README.md | Python/web project; database + backtest code |
| **stem-with-roo-remotion** | P2 active | 900 | package.json | **267M disk (node_modules bloat) — ready for cleanup** |
| **land-sales** | P2 | 150 | land-sales.md | Minimal activity |
| **smart-money-tracker** | P3 | 119 | smart-money-tracker.md | Paper-trading data freshness; low priority |
| **self-hosting-course** | P3 | 277 | self-hosting-course.md | Module outline draft |
| **ios-apps** | P2 | 240 | ios-apps.md | Shared expense + pill-counter apps |
| **Sync-Setup** | utility | 48 | Sync-Setup.md | Setup docs |

### Ongoing Areas

| Area | Location | Content | Status |
|------|----------|---------|--------|
| **Finance** | Areas/finance | parkwood-accord.md | Archived |
| **Budget** | Areas/budget | LOG.md | Archived |
| **Actual-Budget** | Areas/actual-budget | LOG.md | Archived |
| **Memory** | Areas/memory | (empty directory) | Artifact? |
| **State** | Areas/state | (empty directory) | Artifact? |

### Reference / Resources

| Item | Location | Notes |
|------|----------|-------|
| Homelab guides | Resources/guides/ | Proxmox, Home Assistant, Tailscale — use per-area |
| Scripts | Resources/scripts/ | gatekeeper.sh, setup-permissions.sh, review_money_maker.sh |
| Paper-trading | Resources/paper-trading/ | Reference material (backup) |
| Money-maker plan | Resources/plans/ | Strategic plan |
| Progress tracker | Resources/progress-tracker/ | pain-points.md |
| Skills | Resources/skills/ | web-scrape-python (1 skill, not core) |
| Concepts | Resources/concepts/ | soul.md (duplicate; canonical is /root/.hermes/SOUL.md) |

### Archives

| Folder | Content | Notes |
|--------|---------|-------|
| Archives/openclaw-migration | NemoClaw agent backups | 13 project memories + 3 insight files; **awaiting integration** |
| Archives/projects | Old TASK_LIST.md, safe-web-search.md | Historical |

### Build Artifacts (Remove)

| Item | Size | Action |
|------|------|--------|
| stem-with-roo-remotion/node_modules | 267M | Delete; keep package.json + package-lock.json |
| `.DS_Store` | 12K | Delete (macOS artifact) |

---

## What to Keep

**Definitely keep:**
1. ✅ All active project folders (glamping-str, cleanstreak, stem-with-roo, etc.)
2. ✅ OPEN_TASKS.md (burndown queue, actively maintained)
3. ✅ memory.md files inside projects (agent decision summaries)
4. ✅ Areas/ structure (budgets, state)
5. ✅ Resources/guides/ (operational procedures)
6. ✅ Archives/openclaw-migration/ (historical context from prior agent)

**Conditionally keep:**
- Sync-Setup/ — if it's a utility project you're still using
- Self-hosting-course/ — if you're actively developing it; otherwise → Archives
- Land-sales/ — minimal activity; consider archiving if not current

**Delete:**
- .DS_Store (macOS temp file)
- Resources/concepts/soul.md (canonical is /root/.hermes/SOUL.md)
- stem-with-roo-remotion/node_modules (but keep src/, package.json, package-lock.json)

---

## What to Consolidate

### 1. Remove Duplicate Files at `/mnt/kb/Projects/` Root

**Problem**: These files are at `Projects/` root AND have directories:
```
/mnt/kb/Projects/A-Liner-Replication.md      ← delete (dir exists)
/mnt/kb/Projects/Parkwood-Accord.md          ← delete (dir exists)
/mnt/kb/Projects/README.md                    ← delete (confusing; keep dir READMEs)
```

**Action**: Delete the 3 root .md files. Their canonical content lives in the directories.

### 2. Move Finance/Budget to Areas

**Current**: 
```
Areas/finance/parkwood-accord.md
Areas/budget/LOG.md
Areas/actual-budget/LOG.md
```

**Target** (from KB_REORGANIZATION_PLAN):
```
Areas/Finance/
  ├── AREA_PLAN.md              # NEW: overview + check-in schedule
  ├── budget/
  │   └── LOG.md
  ├── actual-budget/
  │   └── LOG.md
  └── parkwood-accord/
      └── parkwood-accord.md
```

**Action**: Create Areas/Finance/, reorganize, add AREA_PLAN.md.

### 3. Move Homelab Resources to Area

**Current**:
```
Resources/guides/Proxmox-Health-Check-Instructions.md
Resources/guides/home-assistant-recovery.md
Resources/guides/Tailscale-Key-Rotation-Instructions.md
Resources/scripts/setup-permissions.sh
Resources/scripts/gatekeeper.sh
```

**Target**:
```
Areas/Homelab/
  ├── AREA_PLAN.md              # NEW
  ├── guides/
  │   ├── Proxmox-Health-Check-Instructions.md
  │   ├── home-assistant-recovery.md
  │   └── Tailscale-Key-Rotation-Instructions.md
  └── scripts/
      ├── setup-permissions.sh
      └── gatekeeper.sh
```

**Action**: Create Areas/Homelab/, move guides + scripts, add AREA_PLAN.md.

### 4. Archive Low-Activity Projects (optional)

**Candidates** (if you're not actively working on them):
- `land-sales/` — minimal activity in OPEN_TASKS.md
- `self-hosting-course/` — stalled at "module outline draft"

**Action**: Move to Archives/ if you're confident they won't resume soon. Otherwise leave in Projects.

### 5. Integrate Archived Memories

**Current**: `/mnt/kb/Archives/openclaw-migration/openclaw-extracted/memory/projects/`
- Contains 13 project memories from NemoClaw (cleanstreak, stem-with-roo, land-sales, etc.)
- Already documented in OPEN_TASKS.md as a **blocked task**

**Target**: Merge into per-project `memory.md` files.

**Action**: 
- Manual merge for ~5 projects (glamping-str, a-liner, etc.)
- Compare NemoClaw insights with current Hermes-written memory.md
- Keep newer/better version; avoid overwriting
- **BLOCKED on cron user permissions** (see below)

---

## Hermes Maintenance Workflow

### Current State

**OPEN_TASKS.md schema** (already defined):
- `[status] (project) priority — description :: done-when`
- Status: ready | in-progress | blocked | shipped
- Priority: P0 | P1 | P2 | P3
- Sort: P0 first, ready before blocked, oldest within tier

**Currently maintained**: Manually by user + Hermes cron burndown (2x/day)

### Proposed Hermes Workflow

#### Daily Tasks (Hermes-owned)

1. **9 AM burndown** (already live)
   - Post current P0 + in-progress tasks to Slack
   - Flag any tasks 7+ days in-progress (escalate to user)

2. **2 PM status check** (already live)
   - Count completed tasks since morning
   - Summarize progress by project

3. **Weekly (Friday 5 PM)** *(new)*
   - Prune shipped entries from OPEN_TASKS.md (move to "Shipped" section)
   - Identify stale in-progress tasks (in-progress + 14+ days → blocked or escalate)
   - Recount open tasks per project
   - Write summary: "This week: X shipped, Y ready, Z blocked"

#### Monthly Tasks (User input + Hermes assist)

1. **Priority audit** (1st of month)
   - Review P0/P1 projects; confirm still critical path
   - Ask: "Any projects to archive?" / "New P0 work?"
   - Update KB_REORGANIZATION_PLAN.md

2. **Memory refresh** (mid-month)
   - Hermes reads all `memory.md` files
   - Cross-check against current OPEN_TASKS.md
   - Flag any outdated decisions or split memories
   - Suggest consolidations

#### Escalation Rules

| Scenario | Action |
|----------|--------|
| Task in-progress > 7 days | Slack alert: "Still in-progress, needs update?" |
| Task blocked > 14 days | Slack escalation: "Blocker unresolved — user input needed?" |
| P0 + no progress 3+ days | Slack: "P0 stalled, escalating" |
| New project added | Confirm PARA bucket; add memory.md stub |
| Project completed | Move to Archives/, mark shipped |

#### Cron Jobs (config.yaml)

```yaml
cron:
  tasks:
    - name: "burndown-morning"
      schedule: "0 9 * * 1-5"      # 9 AM PT weekdays
      command: "hermes post-burndown"
      channel: "#hermes-home"
    
    - name: "burndown-afternoon"
      schedule: "0 14 * * 1-5"     # 2 PM PT weekdays
      command: "hermes status-check"
      channel: "#hermes-home"
    
    - name: "weekly-prune"         # *(new)*
      schedule: "0 17 * * 5"       # 5 PM PT Friday
      command: "hermes prune-tasks"
      channel: "#hermes-home"
```

---

## Permission Fixes Required

### Problem

`cron user (nobody:nobody)` lacks write access to `/mnt/kb/Projects/`:
- Cannot add task entries to memory.md files
- Cannot prune shipped tasks from OPEN_TASKS.md
- Cannot integrate archived memories (NemoClaw backups)

**Blocked tasks in OPEN_TASKS.md**:
- Line 46: "Finalize material list (a-liner) — blocked on write perms"
- Line 114: "Integrate NemoClaw memories — blocked on cron user write access"

### Solution

**Option A: Fix chown (recommended)**
```bash
# Make /mnt/kb writable by Hermes cron (nobody:999)
sudo chown -R 10010:999 /mnt/kb/
sudo chmod -R 775 /mnt/kb/

# Verify
ls -la /mnt/kb/ | head
```

**Option B: Run Hermes cron as your user**
- Edit docker-compose.yml to specify Hermes cron user
- Less secure; not recommended for multi-user systems

**Option C: Elevate file writes via Hermes task runner**
- Use `docker exec` with elevated perms for write operations
- More complex; only if Option A is not feasible

**Recommendation**: Option A. Then test by having Hermes write a test task to OPEN_TASKS.md.

---

## Execution Roadmap

### Phase 1: Quick Wins (no deletions, no perms needed)

1. Delete `/mnt/kb/Projects/A-Liner-Replication.md`, `Parkwood-Accord.md`, `README.md` (3 files)
2. Delete `/mnt/kb/.DS_Store`
3. Create `Areas/Finance/AREA_PLAN.md` (stub)
4. Create `Areas/Homelab/AREA_PLAN.md` (stub)

**Effort**: 15 min | **Risk**: minimal

### Phase 2: Reorganize (medium effort)

1. Move `Areas/finance/`, `budget/`, `actual-budget/` → `Areas/Finance/`
2. Move `Resources/guides/`, `Resources/scripts/` → `Areas/Homelab/`
3. Delete `Resources/concepts/soul.md`
4. Delete `stem-with-roo-remotion/node_modules/` (saves 267M)

**Effort**: 30 min | **Risk**: wikilinks may break (mitigate: git log + git blame)

### Phase 3: Permissions + Integration (requires elevation)

1. Fix cron user perms: `chown -R 10010:999 /mnt/kb/`
2. Integrate NemoClaw memories into project memory.md files
3. Wire up Hermes prune-tasks cron job
4. Test: have Hermes add a shipped task entry

**Effort**: 20 min (once perms fixed) | **Risk**: permission errors if chown fails

### Phase 4: Optional Archiving

1. Move `land-sales/`, `self-hosting-course/` to Archives/ (if confirmed inactive)
2. Update memory.md files to reflect archived status

**Effort**: 10 min | **Risk**: low (reversible)

---

## Hermes Long-Term Maintenance

### Weekly Cadence

- **Monday 9 AM**: Burndown (post open tasks)
- **Friday 5 PM**: Prune (ship completed tasks, flag stale blockers)
- **Monthly (1st)**: Priority audit (user + Hermes)
- **Quarterly (1st of quarter)**: KB health check (structure, duplicates, archives)

### Signals to Escalate

1. > 3 tasks in-progress simultaneously (likely overcommitted)
2. P0 task in-progress > 10 days (needs clarification or break into smaller tasks)
3. Blocked > 14 days (escalation needed)
4. New project without memory.md (add stub)
5. Project completed but not archived (move to Archives/)

### Memory Hygiene

- **Per-project memory.md**: 32 lines max (agent decision summary)
- **Keep**: decisions, blockers, key research findings, state
- **Remove**: completed subtasks, outdated dates, "just did X" entries
- **Monthly refresh**: Read all memory.md files, flag outdated content

---

## Summary of Changes

### Files to Delete
- `/mnt/kb/Projects/A-Liner-Replication.md`
- `/mnt/kb/Projects/Parkwood-Accord.md`
- `/mnt/kb/Projects/README.md`
- `/mnt/kb/.DS_Store`
- `/mnt/kb/Resources/concepts/soul.md`
- `/mnt/kb/Projects/stem-with-roo-remotion/node_modules/` (saves 267M)

### Directories to Create
- `/mnt/kb/Areas/Finance/` (with AREA_PLAN.md)
- `/mnt/kb/Areas/Homelab/` (with AREA_PLAN.md)

### Directories to Move
- `Areas/finance/` → `Areas/Finance/finance/` (rename + nest)
- `Areas/budget/`, `actual-budget/` → `Areas/Finance/budget/`, `Finance/actual-budget/`
- `Resources/guides/` → `Areas/Homelab/guides/`
- `Resources/scripts/` → `Areas/Homelab/scripts/`

### Permissions to Fix
- `chown -R 10010:999 /mnt/kb/` (enable Hermes cron writes)

### Total Size Saved
- ~267M (node_modules) + ~50K (duplicates, .DS_Store)

---

## Sign-Off Checklist

- [ ] Duplicates deleted (3 files at Projects root)
- [ ] Finance area created + populated
- [ ] Homelab area created + populated
- [ ] node_modules removed, src/ preserved
- [ ] Cron perms fixed (chown)
- [ ] NemoClaw memories integrated (5-10 project files)
- [ ] OPEN_TASKS.md pruned (shipped entries moved)
- [ ] Hermes prune-tasks cron wired + tested
- [ ] Single git commit with all moves
- [ ] KB health verified (no broken wikilinks)

