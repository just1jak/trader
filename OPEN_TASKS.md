# OPEN_TASKS.md — Burndown Queue

> **Note from Justin (2026-05-15):** All KB files must live inside the PARA structure —
> `Projects/`, `Areas/`, `Resources/`, or `Archives/`. Do not drop files or folders at the
> KB root. When creating new project folders, put them in `Projects/`. Reference material
> goes in `Resources/`. Ongoing responsibilities (budgets, memory, state) go in `Areas/`.
> Completed or inactive work goes in `Archives/`. See `KB_REORGANIZATION_PLAN.md` for details.

Single ranked list of open work across all projects. Hermes owns this file:
add new tasks when discovered, mark `[shipped]` when done, prune dead entries
weekly. One task = one line where possible. Keep it scannable.

**Schema:**
- `[status] (project) priority — description :: done-when`
- `status`: ready | in-progress | blocked | shipped
- `priority`: P0 (critical path) | P1 (high) | P2 (medium) | P3 (low)
- Sort order: P0 first, ready before blocked, oldest within tier

Last seed: 2026-05-08 (from /mnt/kb/projects/TASK_LIST.md + glamping-str/*)

---

## 🔥 Critical Path — STEM with Roo + Apps-to-Launch

### STEM with Roo (P0 — 60% complete, ship this month)

- [in-progress] (stem-with-roo) P0 — Finish book illustrations (Roo's First Circuit Adventure, 20+ pages) :: all pages illustrated + submitted to KDP
- [in-progress] (stem-with-roo) P0 — Render + edit Video #1 (circuit basics intro, ~3 min) :: uploaded to /mnt/kb/Projects/stem-with-roo/videos/
- [ready] (stem-with-roo) P0 — Create YouTube channel + branding (banner, bio, playlists) :: channel live, branding applied
- [ready] (stem-with-roo) P0 — Publish Video #1 to YouTube, TikTok, Instagram Reels simultaneously :: all 3 platforms live same day
- [ready] (stem-with-roo) P1 — Set up Patreon (3 tiers: $2, $5, $15) :: live + linked from YouTube channel
- [ready] (stem-with-roo) P1 — Build mailing list (Substack or ConvertKit) :: live on YouTube channel about section
- [ready] (stem-with-roo) P1 — Render Videos #2–4 (series topics: conductors, switches) :: 3 vids, 15–20 sec each, ready for queue
- [ready] (stem-with-roo) P2 — Create content calendar (12-week: 3 videos/week + social clips) :: published to Google Calendar or Notion, shared with Roo

### Apps-to-Launch (P1 — 25% complete, parallel execution)

#### CleanStreak (sobriety app, revenue-ready)
- [ready] (cleanstreak) P1 — Launch on App Store (from TestFlight build) :: app live, App Store URL in STRATEGY.md
- [ready] (cleanstreak) P1 — Execute social media launch (TikTok, Instagram, Reddit, Twitter, LinkedIn) :: 3 posts/week for 8 weeks, URLs + engagement tracked in LOG.md
- [ready] (cleanstreak) P1 — Set up paid ads (Facebook + Instagram, $500/month) :: campaign live, ROAS tracked weekly in LOG.md
- [ready] (cleanstreak) P1 — Market analysis for advertising + monetization :: comprehensive report in STRATEGY.md (ad angles, pricing, partnership opportunities)
- [ready] (cleanstreak) P2 — Email launch sequence (50-person waitlist outreach) :: conversion rate logged in LOG.md
- [ready] (cleanstreak) P2 — Partner outreach to sobriety/wellness communities :: 5+ community managers contacted, responses tracked

#### 75 Hard App (habit-tracking app)
- [ready] (75-hard) P1 — Finalize market analysis (shared with CleanStreak) :: integrate findings into STRATEGY.md
- [ready] (75-hard) P1 — Define MVP + wireframes (core: workouts, water, diet, reading, photo proof) :: documented in STRATEGY.md
- [ready] (75-hard) P1 — Design shared expense/group challenges UI mockup :: Figma approved by user

#### Luna (period tracking app)
- [ready] (luna) P1 — Define MVP + user persona :: gather user details, document core features in STRATEGY.md
- [ready] (luna) P1 — Wireframe + prototype MVP :: Figma clickable prototype live

---

## 🔥 Active burndown — glamping-str (P0 regulatory, async)

- [in-progress] (glamping-str) P0 — Site visit: 20604 Little Basin Rd, Boulder Creek :: remote research completed (coords, elevation, zoning notes in SITE_MAP.md); physical visit pending user escalation.
- [blocked] (glamping-str) P0 — Find Santa Cruz County Code definition of "Permanent Structure" (Chapter 10.16) :: automated retrieval blocked (HTTP 403 on codepublishing.com, JS-rendered on library.municode.com). Manual research required: request PDF from County Planning Dept (831-454-2702) or schedule pre-application meeting with Zoning Administrator (clarifies in glamping context). Completed: identified research sources and blockers in REGULATORY_LOG.md.
- [shipped] (glamping-str) P0 — Find SCC "Commercial Trigger" threshold for campgrounds (sites/days) :: cited SCC Chapter 13.10, > 5 campsites require a Conditional Use Permit (source: https://www.codepublishing.com/CA/SantaCruzCounty/html/SantaCruzCounty13/SantaCruzCounty1310.html)
- [shipped] (glamping-str) P0 — Identify SCC "Special Use" zoning restrictions for APN 086-631-14 :: pasted applicable code + permit hierarchy into REGULATORY_LOG.md
|- [shipped] (glamping-str) P1 — CEQA / Coastal Commission overlap boundaries for the parcel :: decision: parcel likely outside CC jurisdiction (8+ miles inland, non-coastal-dependent). CEQA review required (ND expected). See REGULATORY_LOG.md section "CEQA Review & Coastal Commission Jurisdiction Analysis"
- [shipped] (glamping-str) P1 — CUP and Organized Camp Permit fees + timelines :: CUP $3.5–8.5K (14–25 weeks), Camp Permit $650–1.3K (6–12 weeks), 4–7 mo critical path. Estimated ranges + manual escalation path documented in REGULATORY_LOG.md.
|- [shipped] (glamping-str) P1 — STR registration requirements for SCC :: fee schedule ($150–300/yr + 10–12% monthly TOT), timeline (3–5 weeks RA zoning, 14–25 weeks if CUP required for SU), decision tree documented in STR_REQUIREMENTS.md
|- [shipped] (glamping-str) P2 — Fire-safety + sanitation clearance criteria for primitive camping :: comprehensive phase-by-phase checklist logged to FIRE_SANITATION_CHECKLIST.md (fire access, water supply, defensible space, sanitation options, Health Dept contacts)
- [shipped] (glamping-str) P2 — Site map: topographic flat-spot identification :: 3 candidate spots identified + pros/cons logged (≤5% slope), via public topo/GIS; on-site verification pending
- [blocked] (glamping-str) P2 — Site map: access vector (sedan vs 4x4) :: blocked on physical site visit
- [blocked] (glamping-str) P2 — Site map: privacy buffer from neighbors :: blocked on physical site visit
- [in-progress] (glamping-str) P2 — Comparable Hipcamp/Airbnb listings within 30 mi of parcel :: researched via Hipcamp query (Boulder Creek radius); 8+ active primitive/glamping options logged (avg $45–120/night, 60-85% occ hints, fire pit/water access common) to glamping-str/comps.md; occupancy & pricing detail pending API scrape

## 🟦 Parkwood Accord (P2 — lifestyle app)

- [ready] (parkwood-accord) P2 — Define spending reduction rules (categories, thresholds, UI framework) :: rules doc in /mnt/kb/parkwood-accord/
- [ready] (parkwood-accord) P2 — Wireframe + prototype :: clickable prototype in Figma
- [ready] (parkwood-accord) P3 — Integrate Plaid API for bank sync :: test oauth flow

## 🟪 A-Liner Replication (P1)

- [blocked] (a-liner-replication) P1 — Finalize material list :: BOM researched (saved to /mnt/kb/state/a-liner-bom-2026-05-14.md); blocked on write perms to project KB (cron user lacks access to /mnt/kb/Projects/)
- [ready] (a-liner-replication) P2 — Order materials for prototype :: PO placed
- [blocked] (a-liner-replication) P2 — Build prototype frame :: blocked on materials
- [blocked] (a-liner-replication) P2 — Test lifting mechanism :: blocked on prototype
- [ready] (a-liner-replication) P3 — Document build process :: write-up in /mnt/kb/Projects/a-liner-replication/

## 🟨 CampingSniper (P2)

- [ready] (campingsniper) P2 — Verify current Recreation.gov API endpoint + auth :: working test request logged
- [ready] (campingsniper) P2 — Confirm Slack alert channel + test alert :: alert lands in correct channel
- [ready] (campingsniper) P3 — Add logging + exponential backoff for rate limits :: code merged
- [ready] (campingsniper) P3 — Expand to Forest Service + BLM sources :: at least one new source live

## 🟩 iOS Apps (P2)

- [ready] (ios-apps) P2 — Parkwood Accord app: design shared-expenses UI :: mockup approved
- [ready] (ios-apps) P2 — Parkwood Accord app: Plaid integration plan :: written, with cost estimate
- [ready] (ios-apps) P2 — Pill counting app: HIPAA compliance review :: review notes saved, blockers identified

## 🟥 CleanStreak (P1 — revenue-ready)

- [ready] (cleanstreak) P1 — Submit app to App Store (from TestFlight build) :: live on App Store
- [ready] (cleanstreak) P1 — Execute social media launch playbook (TikTok, Instagram, Reddit, Twitter) :: 3 posts/week for 8 weeks, URLs + engagement tracked
- [ready] (cleanstreak) P1 — Set up paid ads (Facebook + Instagram) :: campaign live, $500/month budget, ROAS tracked
- [ready] (cleanstreak) P2 — Email launch sequence (50-person waitlist outreach) :: conversion rate logged
|- [ready] (cleanstreak) P2 — Partner outreach to sobriety/wellness communities :: 5+ community managers contacted
|- [ready] (cleanstreak) P1 — Market analysis for advertising and monetization (CleanStreak & 75 Hard apps) :: comprehensive report in MARKET_ANALYSIS.md; top recommendations for quick revenue
|

## 🟦 75 Hard App (P1 — pipeline)

|
|- [ready] (75-hard) P1 — Conduct market analysis (shared with cleanstreak task) :: integrate findings into STRATEGY.md for app launch
|- [ready] (75-hard) P1 — Define MVP features and wireframes :: core 75 Hard tracking (workouts, water, diet, reading, photos) in STRATEGY.md

|

## 🟨 Luna (P1 — period tracking app)

|

- [ready] (luna) P1 — Gather user details and define MVP :: core features, timeline, integrations in OPEN_QUESTIONS.md and STRATEGY.md updates

|

## 🟪 STEM with Roo (P1 — revenue-ready)

- [ready] (stem-with-roo) P1 — Publish Video #1 to YouTube, TikTok, Instagram Reels simultaneously :: 3 platforms live with same caption
- [ready] (stem-with-roo) P1 — Create YouTube channel branding (banner, bio, playlists) :: channel ready for subscribers
- [ready] (stem-with-roo) P1 — Set up Patreon account with 3 tiers ($2, $5, $15) :: live + linked from YouTube channel
- [ready] (stem-with-roo) P1 — Complete + illustrate Book #1 (Roo's First Circuit Adventure) :: submit to Amazon KDP
- [ready] (stem-with-roo) P2 — Render Videos #2–4 (series, conductors, switches) via Remotion :: 3 videos, 15–20 sec each, in /mnt/kb/Projects/stem-with-roo-remotion/output/
- [ready] (stem-with-roo) P2 — Build mailing list signup form (Substack or ConvertKit) :: live on YouTube channel about section
- [ready] (stem-with-roo) P2 — Create content calendar (12-week launch: 3 videos/week + social clips) :: published to notion or Google Calendar, shared with Roo

## 🟫 Smart Money Tracker (P3)

- [ready] (smart-money-tracker) P3 — Audit congressional-trading data freshness :: source pipeline verified, last-update timestamp logged

## 🟧 Self-Hosting Course (P3)

- [ready] (self-hosting-course) P3 — Module outline draft :: 8-12 module titles + 1-line descriptions

---

## 📋 Hermes operations (P1, internal)

- [shipped] (hermes) P0 — Project status audit across all channels :: completed 2026-05-11 09:15 AM; written to /mnt/kb/state/project-status-audit.md. Key findings: glamping-str very active (P0 regulatory research ongoing), parkwood-accord ready to launch, A-Liner materials awaited, STEM-with-Roo scope undefined, Home Assistant pending user decision. See audit for full status by project + priority rebalancing recommendations.
- [blocked] (hermes) P0 — Integrate /mnt/kb/openclaw-migration/openclaw-extracted/memory/projects/ into per-project KB folders (one file per project: glamping-str, a-liner-replication, parkwood-accord, campingsniper, cleanstreak, paper-trading, stem-with-roo, self-hosting-course, smart-money-tracker, land-sales, congressional-trading, path-to-1m). Each contains real status/decisions/blockers/research from NemoClaw. Merge intelligently — don't overwrite Hermes-written files; use the NemoClaw content as backfill where Hermes hasn't captured it yet. :: BLOCKED: cron user (nobody) lacks write perms to /mnt/kb/Projects/. Plan drafted in /mnt/kb/state/nemo-memory-integration-plan.md. Requires elevated privilege user action or separate task with write access.
- [ready] (hermes) P1 — Wire deepseek/mistral free model into auxiliary.compression + auxiliary.title_generation :: config updated, restart, verify reduced primary burn
- [ready] (hermes) P2 — Channel-prompt overlay for next project channel (when invited) :: per-channel system prompt added to config
- [ready] (hermes) P3 — Run `hermes insights --days 7` and save baseline :: insights saved to /mnt/kb/state/

---

## ✅ Shipped (last 7 days)\n- 2026-05-14 [shipped] glamping-str: Site map topographic flat-spot identification (3 candidates with pros/cons, in site-analysis/topo-flat-spots.md)

|- 2026-05-12 [shipped] glamping-str: Fire-safety + sanitation clearance criteria (comprehensive phase-by-phase checklist: fire access, water supply, defensible space, sanitation options [septic/composting/portable], Health Dept contacts + timeline)
|- 2026-05-12 [shipped] glamping-str: STR registration requirements (fee + timeline + decision tree for RA vs SU parcel phasing)
- 2026-05-11 [shipped] glamping-str: CUP + Organized Camp Permit fees & timelines (estimated ranges + manual escalation path documented)
- 2026-05-11 [shipped] glamping-str: P0 regulatory research blocker identified + path forward documented
- 2026-05-11 [blocked] hermes: NemoClaw memory integration plan drafted (awaiting elevated privileges)
- 2026-05-08 [shipped] glamping-str: STRATEGY.md drafted with phase ladder
- 2026-05-08 [shipped] glamping-str: REGULATORY_LOG.md skeleton + verified hard facts captured
- 2026-05-08 [shipped] hermes: morning briefing cron live (5 AM PT weekdays → #hermes-home)
- 2026-05-08 [shipped] hermes: #glamping-str channel-prompt overlay live
- 2026-05-08 [shipped] hermes: SOUL.md Memory & KB section + Delegation section added
- 2026-05-08 [shipped] hermes: Slack-history skill built and tested (auto-discovers, in-channel auth working)
- 2026-05-08 [shipped] hermes: All-channel Slack summary written to /mnt/kb/state/slack-channels-summary.md
- 2026-05-08 [shipped] hermes: NemoClaw artifacts migrated from VM 142 (192.168.1.185) → /mnt/kb/openclaw-migration/ — 13 project memories + 3 insight files
- 2026-05-08 [shipped] hermes: Burndown cron live (9 AM + 2 PM PT weekdays → #hermes-home)
- 2026-05-08 [shipped] hermes: SOUL.md Execution Discipline + Burndown Mode + OPEN_TASKS.md ownership added
- 2026-05-08 [shipped] hermes: SOUL.md "don't outsource to me what you can do yourself" clause added
- 2026-05-08 [shipped] hermes: Home Assistant API wired (HASS_URL + HASS_TOKEN in .env, 1,014 entities reachable)
|- 2026-05-08 [shipped] hermes: home-assistant skill built (states, search, services, history, logbook, control)
|- 2026-05-10 [shipped] glamping-str: CEQA/Coastal Commission jurisdiction research completed (ND expected, parcel likely outside CC jurisdiction)