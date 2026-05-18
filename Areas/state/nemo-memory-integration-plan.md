# NemoClaw Memory Integration Plan — 2026-05-11

**Task:** Integrate 13 NemoClaw project memory files into Hermes KB project folders.

**Status:** NemoClaw artifact migration blocked due to file permissions (cron job runs as 'nobody' user with read-only access to /mnt/kb/Projects/).

**Files to integrate:**

| Project | NemoClaw File | Target KB Location | Integration Notes |
|---------|---|---|---|
| **glamping-str** | glamping-str.md | /mnt/kb/Projects/glamping-str/ | Tax-defaulted parcel strategy (3692 petition, owner clusters: Gamble/Fredrickson/Barret). Revenue target: >60% occupancy, 18mo payback. Merge with STRATEGY.md's 4-phase ladder. |
| **a-liner-replication** | a-liner-replication.md | /mnt/kb/Projects/a-liner-replication/ | Engineering calculator status. Merge with BOM and build plan. |
| **parkwood-accord** | parkwood-accord.md | /mnt/kb/Projects/parkwood-accord/ | iOS app architecture (SwiftUI). Plaid API integration planned. MVP scope needed. Merge with candidate property research. |
| **campingsniper** | campingsniper.md | /mnt/kb/Projects/campingsniper/ | API architecture, rate-limit strategy. Merge with Recreation.gov endpoint verification work. |
| **cleanstreak** | cleanstreak.md | /mnt/kb/Projects/clean-streak/ | Marketing docs exist (market_analysis, social_marketing_plan, ad_guide). DryStreak codebase rebranded. Move docs to KB. |
| **congressional-trading** | congressional-trading.md | /mnt/kb/Projects/congressional-trading/ | Scrapers + backtester built. SQLite schema ready, DB not initialized. House/Senate STOP Act endpoints documented. Create project folder + wire up DB. |
| **land-sales** | land-sales.md | /mnt/kb/Projects/land-sales/ | Tax auction scraper (GovEase platform). CSV/JSON output. Supports glamping-str acquisition. Create folder + document scraper. |
| **smart-money-tracker** | smart-money-tracker.md | /mnt/kb/Projects/smart-money-tracker/ | Congressional-trading feed integration. Merge with data-freshness audit. |
| **paper-trading** | paper-trading.md | /mnt/kb/Projects/futures-trading/ | Flask + React starter, 6 scalping strategies. Merge with VWAP mean-reversion backtest. |
| **self-hosting-course** | self-hosting-course.md | /mnt/kb/Projects/self-hosting-course/ | Module outline draft exists. Merge NemoClaw notes with P3 task (8–12 modules). |
| **stem-with-roo** | stem-with-roo.md | /mnt/kb/Projects/stem-with-roo/ | **KEY DISCOVERY**: Children's STEM YouTube content. Remotion video pipeline live (test outputs: out.mp4, test.mp4). Content plans: STEM_plan.md, posts_plan.md, stem-with-roo-book.md. Channel setup + content calendar TBD. Create project folder + seed with NemoClaw docs. |
| **path-to-1m** | path-to-1m.md | /mnt/kb/Projects/path-to-1m/ | Meta-strategy project (turning $500 into $1M in 8 months). Create folder + document monetization ladder. |

---

## Blockers

1. **File permissions:** Cron job user (nobody) cannot write to /mnt/kb/Projects/. 
   - **Solution:** Run integration as a separate task with elevated privileges, or request user to execute manually.

2. **Missing project folders:** Some projects have no KB folder yet (stem-with-roo, land-sales, congressional-trading, path-to-1m).
   - **Solution:** Create folders with elevated privileges.

3. **~/.openclaw/workspace/ artifact migration:** NemoClaw also wrote working code (paper-trading Flask app, congressional-trading scrapers, land-sales scraper) to `~/.openclaw/workspace/`. Need to migrate those too.

---

## Recommended Next Steps (for next burndown tick or user action)

1. **User or elevated-privilege task:** Copy/merge NemoClaw memory files into project KB folders using the table above as a guide.
2. **User or elevated-privilege task:** Migrate live code artifacts from `~/.openclaw/workspace/Resources/` and `~/.openclaw/workspace/` subfolders into `/mnt/kb/Projects/` (paper-trading, congressional-trading, land-sales code).
3. **Next Hermes burndown tick:** Once folders created and NemoClaw docs backfilled, execute P1/P2 tasks that depend on this context (e.g., congressional-trading DB initialization, STEM-with-Roo channel setup + content calendar).

---

**Prepared by:** Hermes (2026-05-11 09:30 AM)
**Status:** Ready for implementation. Awaiting elevated privileges or user action.
