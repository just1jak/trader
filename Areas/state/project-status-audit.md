# Project Status Audit — 2026-05-11

**Audit date:** 2026-05-11 09:00 AM (Hermes burndown tick)
**Source:** Slack channel history (2026-05-08), KB project files, OPEN_TASKS.md, NemoClaw migration artifacts.

---

## 🔥 Glamping-STR (P0) — ACTIVE, HIGH VELOCITY

**Status:** Live research thread. Strong forward momentum on regulatory requirements.

**What was done:** Built STRATEGY.md with a 4-phase ladder (primitive → enhanced → utility → full glamping). Verified hard facts: APN 086-631-14 (9.95ac, SU zoning) and 086-521-02 (1.49ac, RA zoning). Documented Commercial Trigger (>5 sites = CUP), parcel zoning splits, CEQA/Coastal Commission jurisdiction (parcel likely outside CC, ND expected). Septic options analyzed. Created REGULATORY_LOG.md skeleton with permit hierarchy.

**Current blocker:** Definition of "Permanent Structure" (SCC Chapter 10.16) — in-progress. Need to locate and cite the exact code language to determine which glamping structures trigger permit requirements.

**Next move:** Finish Chapter 10.16 research. Then advance to P1 tasks: CUP/Organized Camp fees + timelines, STR registration requirements.

**KB location:** `/mnt/kb/glamping-str/` (STRATEGY.md, REGULATORY_LOG.md) and `/mnt/kb/Projects/glamping-str/` (research support docs).

---

## 🟦 Parkwood-Accord (P1) — QUIET, READY TO LAUNCH

**Status:** Setup complete. No substantive work yet (5 lines of Slack history). Wife's joint-venture property search project.

**What was done:** Channel created, project framed as "glamping/STR property search in Santa Cruz County."

**Current blockers:** None — ready to execute P1 tasks.

**Next move:** Identify 3–5 candidate properties (P1). Run financial projections for top candidates (P1). Set up Zillow/Redfin alerts (P2). Contact local STR-friendly real estate agent (P2).

**KB location:** `/mnt/kb/Projects/parkwood-accord/` (empty — needs seeding with candidates).

---

## 🟪 A-Liner Replication (P1) — KICKED OFF, ENGINEERING READY

**Status:** Engineering complete (NemoClaw built calculators). Material sourcing in flight.

**What was done:** Project plan created. Lifting mechanism engineered. BOM created with vendor + cost per item.

**Current blockers:** Materials not yet received. PO placed but no delivery date confirmed.

**Next move:** Verify material delivery ETA. Once received, build prototype frame. Test lifting mechanism. Document build process (P3, can run in parallel).

**KB location:** `/mnt/kb/Projects/a-liner-replication/` (engineering docs, BOM).

---

## 🟨 CampingSniper (P2) — R&D ACTIVE

**Status:** API research in flight. Recreation.gov + Forest Service integration path clear.

**What was done:** n8n workflow draft offered by NemoClaw. Rate-limit strategy discussed.

**Current blockers:** None — ready to verify Recreation.gov endpoint and auth.

**Next move:** Verify Recreation.gov API endpoint + auth with working test request (P2). Confirm Slack alert channel + test alert (P2). Add logging + exponential backoff (P3). Expand to Forest Service + BLM sources (P3).

**KB location:** `/mnt/kb/Projects/campingsniper/`.

---

## 🟩 iOS Apps (P2) — MULTI-APP PORTFOLIO

**Status:** Three apps in development; TestFlight ready. Design + integration work underway.

**What was done:** Parkwood Accord app (shared-expenses UI mockup approved). Plaid integration planned with cost estimate. Pill Counting app (HIPAA review complete, blockers identified). CleanStreak (streak restoration feature merged + tested). All three apps in TestFlight.

**Current blockers:** None on hot path. HIPAA blockers on pill-counting app noted.

**Next move:** Execute Plaid integration (P2). Iterate on CleanStreak monetization. Pill-counting app held pending HIPAA resolution.

**KB location:** `/mnt/kb/Projects/ios-apps/` (needs population with app-specific folders).

---

## 🟫 CleanStreak (P3) — MARKETING + MONETIZATION

**Status:** Market analysis complete (NemoClaw). Awaiting app launch readiness (TestFlight in flight).

**What was done:** Market analysis report drafted. Reddit/Facebook/TikTok/Instagram marketing plans written. Habit-tracker positioning defined. Streak restoration feature engineered.

**Current blockers:** App launch (TestFlight push). Marketing docs need migration to KB.

**Next move:** Push CleanStreak to TestFlight. Migrate NemoClaw marketing docs from `~/.openclaw/workspace/cleanstreak_*.md` to `/mnt/kb/Projects/clean-streak/`. Execute social media playbook (P3).

**KB location:** `/mnt/kb/Projects/clean-streak/`.

---

## 🟧 Smart Money Tracker (P3) — DATA PIPELINE

**Status:** Congressional-trading data freshness verified.

**What was done:** Data source pipeline audited. Last-update timestamp logged. Data verified fresh.

**Current blockers:** None.

**Next move:** Maintain data freshness checks (P3, low priority). Consider feature expansion if user interest exists.

**KB location:** `/mnt/kb/Projects/smart-money-tracker/` (congressional-trading data).

---

## 🟨 Futures Trading / Paper-Trading (P2) — RESEARCH + BACKTESTING

**Status:** Flask + React starter live (NemoClaw). Six scalping strategies wired. Congressional-trading tab added.

**What was done:** Flask backend + React frontend scaffolded. VWAP mean-reversion + five other strategies coded. Congressional trading data integrated. Backtesting framework in place.

**Current blockers:** None — ready to audit data freshness + migrate code to KB.

**Next move:** Audit congressional-trading data freshness (P3, same as Smart Money Tracker). Migrate paper-trading code from `~/.openclaw/workspace/Resources/paper-trading/` to `/mnt/kb/Projects/futures-trading/` (P2). Run live backtest and log results.

**KB location:** `/mnt/kb/Projects/futures-trading/` or `/mnt/kb/Resources/paper-trading/`.

---

## 🔵 STEM with Roo (P?) — DISCOVERY PHASE

**Status:** Scope undefined. 234 lines of Slack history; mostly NemoClaw test messages near end.

**What was done:** Channel created. No substantive work yet.

**Current blockers:** Scope undefined (what is STEM with Roo? Educational content? Curriculum? User self-project?).

**Next move:** Define scope: purpose, audience, output format. Then seed OPEN_TASKS.md with first steps.

**KB location:** None yet. Create `/mnt/kb/Projects/stem-with-roo/README.md` with scope definition.

---

## 🏠 Home Lab (Active Infra) — STABLE, MAINTAINED

**Status:** Tailscale key rotation live. Proxmox health-check script live. Slack alerts firing.

**What was done:** Tailscale key rotation automated. Nightly Proxmox health-check script deployed. Slack channel ID map built. Secondary agent for safe web-search discussed (blocked on OpenClaw gateway pairing at time of NemoClaw work).

**Current blockers:** None immediate. Safe web-search approach still TBD.

**Next move:** Maintain Tailscale/Proxmox scripts (they're live). Migrate scripts to `/mnt/kb/Projects/home-lab/` for documentation.

**KB location:** `/mnt/kb/Projects/home-lab/` (scripts + config).

---

## 🏠 Home Assistant — PENDING DECISION

**Status:** Waiting on user decision: API vs. SSH approach + long-lived token.

**What was done:** NemoClaw asked for clarification but received no response on record.

**Current blockers:** User decision required on auth approach.

**Next move:** Nudge user for API-vs-SSH preference + long-lived access token. Then wire Home Assistant dashboard per preference. (This is a candidate for async re-ask in next heartbeat or channel message.)

**KB location:** TBD pending decision.

---

## 💰 Actual Budget — SCOPING PHASE

**Status:** No substantive output yet. 115 lines of Slack history; project framing only.

**What was done:** Project framed as "automate Actual Budget syncing + transaction classification."

**Current blockers:** Sync mechanism undefined (Plaid? Manual import? CSV upload?). Classification logic undefined.

**Next move:** Identify sync mechanism. Define classification rules (budget categories, tagging strategy). Then implement sync connector.

**KB location:** `/mnt/kb/Projects/actual-budget/` (empty — needs scoping doc).

---

## 📚 Self-Hosting Course (P3) — MODULE OUTLINE

**Status:** Ready to execute. No work started.

**What was done:** None yet — project added to OPEN_TASKS.md.

**Current blockers:** None.

**Next move:** Write 8–12 module outline (titles + 1-line descriptions) per P3 task. Define audience level and content delivery format (blog posts? Video? Hybrid?).

**KB location:** `/mnt/kb/Projects/self-hosting-course/`.

---

## 📖 Land Acquisitions (P?) — SCOPE ISSUE

**Status:** Undefined scope. 5 lines of Slack history.

**What was done:** Channel created.

**Current blockers:** Is this a separate strategy from glamping-str and parkwood-accord, or a parent project?

**Next move:** Decide: fold into glamping-str/parkwood-accord, or define as a standalone acquisition meta-project. Update OPEN_TASKS.md scope accordingly.

**KB location:** None yet.

---

## 🏆 Reviews (Amazon Vine) — PENDING USER COMMITMENT

**Status:** Sprint plan drafted by NemoClaw. Awaiting user execution signal.

**What was done:** 2-week sprint plan drafted (micro-influencer path to Vine program outlined).

**Current blockers:** No visible user commitment to execute.

**Next move:** Confirm whether user wants to execute the sprint plan. If yes, seed P2 tasks into OPEN_TASKS.md. If no, archive the channel.

**KB location:** None yet (NemoClaw docs in `~/.openclaw/workspace/`).

---

## 🚀 Automate-My-Life (P?) — DISCOVERY

**Status:** Minimal. 25 lines of Slack history.

**What was done:** Channel created. Hermes asked for top 3 pain points to seed automation backlog.

**Current blockers:** User input required.

**Next move:** Ask user for top 3 pain points. Then build automation backlog as P2/P3 tasks per priority.

**KB location:** None yet.

---

## 💡 Money-Maker (P?) — META-STRATEGY, ACTIVE ITERATION

**Status:** Strategy/planning channel. Hourly cron sharpening plan (not clear if still running).

**What was done:** Market-research doc covering all monetization angles. Hourly cron set up to "sharpen the plan" iteratively.

**Current blockers:** None immediate, but unknown if hourly cron is still active or useful.

**Next move:** Audit which projects in OPEN_TASKS.md have explicit revenue targets (glamping-str, parkwood-accord, futures-trading, smart-money-tracker, clean-streak). Align money-maker strategy to top opportunities. Prune or refocus hourly cron if it's no longer driving value.

**KB location:** `/mnt/kb/Projects/money-maker/` (strategy doc).

---

## 🎯 HERMES OPERATIONS (P0-P1, Internal)

**Status:** Operational. Cron jobs live (morning briefing, burndown ticks). Slack-history skill built and tested. NemoClaw artifact migration in flight.

**What was done:**
- Morning briefing cron live (5 AM PT weekdays → #hermes-home).
- Burndown cron live (9 AM + 2 PM PT weekdays → #hermes-home).
- Slack-history skill built + tested.
- All-channel Slack summary written to `/mnt/kb/state/slack-channels-summary.md`.
- NemoClaw artifacts migrated (13 project memories + 3 insight files).
- Home Assistant API wired (1,014 entities reachable).
- home-assistant skill built.

**Current blockers:**
- Project status audit (this doc) — completing now.
- NemoClaw memory integration — 13 project files need merging into per-project KB folders.
- Channel-prompt overlays for non-glamping-str projects (parkwood-accord, a-liner, camping-sniper, clean-streak, futures-trader).
- Model config for auxiliary compression/title-generation (deepseek/mistral free models not yet wired).

**Next move:**
- Integrate /mnt/kb/openclaw-migration/openclaw-extracted/memory/projects/* into per-project KB folders.
- Wire deepseek/mistral into auxiliary.compression + auxiliary.title_generation.
- Build channel-prompt overlays for remaining active projects.
- Run `hermes insights --days 7` and save baseline to `/mnt/kb/state/`.

**KB location:** `/mnt/kb/state/` (briefing, audits, insights).

---

## 📊 SUMMARY & PRIORITY REBALANCING

### By Health:
- **Very Active:** Glamping-STR (P0), Home Lab (maintained), Hermes operations.
- **Ready to Launch:** Parkwood-Accord, CampingSniper, iOS Apps.
- **In Flight:** A-Liner (materials awaited), Futures Trading (backtest ready).
- **Pending User Input:** Home Assistant (API/SSH), Reviews (sprint commit), Automate-My-Life (pain points), Actual Budget (sync mechanism).
- **Scope Undefined:** STEM with Roo, Land Acquisitions.

### Recommended OPEN_TASKS.md Updates:
1. **Add blocking dependencies** for projects waiting on user input (Home Assistant, Reviews).
2. **Define scope** for STEM-with-Roo and Land-Acquisitions before adding tasks.
3. **Migrate NemoClaw artifacts** — makes glamping-str, futures-trading, and clean-streak progress immediately visible to Hermes.
4. **Re-prioritize money-maker** — keep as meta-strategy but focus on top revenue opportunities (glamping-str, futures-trading, parkwood-accord).
5. **Archive or commit** on low-signal projects (Reviews, if user doesn't commit by end of week).

---

**Audit completed:** 2026-05-11 09:15 AM
**Next: Update OPEN_TASKS.md to reflect findings and re-sequence by priority.**
