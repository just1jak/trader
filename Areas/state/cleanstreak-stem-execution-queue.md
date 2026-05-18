# CleanStreak + STEM with Roo: Execution Queue (May 12, 2026)

**Status**: 2-week launch plans drafted. Ready for immediate execution. Both projects P1 (revenue-ready).

## CleanStreak Immediate Actions (Today/This Week)

**Priority order for cron/burndown to follow**:

1. **Submit to App Store** (Day 1, Mon May 12)
   - Build: Use current TestFlight build
   - Screenshots: Ready
   - Metadata: Keywords optimized (habit, streak, tracking, sobriety, wellness)
   - Expected approval: May 15–17
   - Status tracking: Check App Store Connect daily; mark SHIPPED when approved

2. **Set up Facebook/Instagram ads** (Day 2, Tue May 13)
   - Meta Business Manager account
   - 2 campaigns (general wellness + sobriety-focused)
   - Budget: $250/week ($35/day) through May 31
   - Setup: ConvertKit/email platform if not already done
   - Success metric: Campaign live, daily spend tracking active

3. **TikTok content production** (Days 3–5, Wed–Fri May 14–16)
   - 8 scripts written
   - Film 2–3 videos (iPhone + ring light)
   - Post-production in CapCut (overlays, audio)
   - Hold for coordinated launch May 17

4. **Launch day** (Fri May 16 or Sat May 17, conditional on App Store approval)
   - Publish TikTok #1 + #2 + #3
   - Tweet announcement
   - Email waitlist (early-bird offer)
   - Monitor metrics hourly

5. **Ongoing** (Week 2 onwards):
   - Daily ads optimization (pause underperformers, increase winners)
   - 3x/week TikTok posts
   - Reply to comments within 4 hours
   - Weekly metrics review

**Detailed plan**: `/mnt/kb/cleanstreak/LAUNCH_PLAN.md`

---

## STEM with Roo Immediate Actions (Today/This Week)

**Priority order for cron/burndown to follow**:

1. **Finalize Video #1** (Day 1, Mon May 12)
   - Remotion render: Circuit intro (15 sec)
   - Export MP4 (1080p, H.264)
   - Save to: `/mnt/kb/Projects/stem-with-roo-remotion/output/video-1-circuit-intro.mp4`
   - Success metric: File exists, plays without errors

2. **YouTube channel setup** (Days 1–2, Mon–Tue May 12–13)
   - Channel name: "STEM with Roo"
   - Banner: 2560×1440px (Roo character, bright colors)
   - Profile picture: Roo logo
   - Bio: Kids STEM education, ages 6–10
   - Playlists: "Electricity Basics," "Upcoming"
   - Status: Channel ready to publish first video

3. **Patreon account setup** (Days 2–3, Tue–Wed May 13–14)
   - 3 tiers ($2, $5, $15/month)
   - Banner + descriptions
   - Set to "coming soon," switch live May 17
   - Estimated MRR: $20–75 by week 2 end

4. **Book #1 illustrations** (Days 2–4, Tue–Thu May 13–15)
   - Complete all pages (1–11) with kid-friendly art
   - Use Canva templates or hire illustrator ($50–200)
   - Format: 8.5" × 8.5" for KDP
   - Status: Ready for Amazon submission by May 19

5. **Render Videos #2–4** (Day 4, Thu May 15)
   - Video #2: Series vs. parallel (20 sec)
   - Video #3: Conductors vs. insulators (15 sec)
   - Video #4: Switches & safety (15 sec)
   - Parallel render if possible (est. 5 hours total)
   - Save to: `/mnt/kb/Projects/stem-with-roo-remotion/output/`

6. **Social media accounts** (Days 3–4, Wed–Thu May 14–15)
   - TikTok: @stemwithroo
   - Instagram: @stemwithroo
   - Both linked to YouTube channel

7. **Launch day** (Sat May 17)
   - Publish Video #1 to YouTube (10 AM)
   - TikTok upload (10:15 AM)
   - Instagram Reels (10:30 AM)
   - Tweet announcement
   - Patreon goes live
   - Email to newsletter
   - Goal: 50–100 YouTube subs by week 2 end

8. **Week 2: Book to Amazon** (Mon May 19)
   - Compile PDF (all illustrated pages + text)
   - Create KDP cover + back copy
   - Upload to KDP (48-hour approval window)
   - Set pricing: Paperback $8.99, Kindle $2.99
   - Expected live: May 21

9. **Ongoing** (Week 2 onwards):
   - Video #2 launch (Tue May 20)
   - Content batching (3x/week posts)
   - Reply to comments within 4 hours
   - Weekly analytics review
   - Influencer outreach (10 contacts/week)

**Detailed plan**: `/mnt/kb/stem-with-roo/LAUNCH_PLAN.md`

---

## Execution Checkpoints

| Project | Checkpoint | Due | Status |
|---------|------------|-----|--------|
| CleanStreak | App Store submitted | May 12 | |
| CleanStreak | Ads live | May 13 | |
| CleanStreak | Launch day | May 17 | |
| STEM with Roo | Video #1 rendered | May 12 | |
| STEM with Roo | YouTube channel ready | May 13 | |
| STEM with Roo | Launch day | May 17 | |
| STEM with Roo | Book to Amazon | May 19 | |

---

## Next Cron: Pick Up Top P1 Items

The burndown cron (9 AM / 2 PM PT) should:
1. Read OPEN_TASKS.md
2. Filter for `[ready]` + P1 + (cleanstreak OR stem-with-roo)
3. Execute in order: CleanStreak App Store → STEM Video #1 → Ads setup → Channel setup
4. Mark as `[in-progress]` → `[shipped]` as items complete
5. Report daily progress to Slack (#hermes-home)

**For cron automation**: Both projects have detailed daily breakdowns in LAUNCH_PLAN.md files. Cron can reference these for specific do-this-first actions.
