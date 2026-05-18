# Task List - Prioritized

Generated from knowledge base on 2026-04-20.

## Priority Levels
- **High**: Immediate action needed, deadlines approaching, or critical path.
- **Medium**: Important but flexible timing.
- **Low**: Nice-to-have, exploratory, or dependent on other tasks.

---

## 🟦 Parkwood Accord (High)
*Joint venture with wife for glamping/STR in Santa Cruz County. Property search phase.*

**Next Actions** (from Parkwood-Accord.md):
- [ ] Complete regulatory research checklist
- [ ] Identify 3-5 potential properties
- [ ] Run financial projections for top candidates
- [ ] Discuss findings with wife

**Additional Tasks**:
- [ ] Review SOPA regulations summary
- [ ] Check LICA ordinance details
- [ ] Contact local real estate agent familiar with STR regulations
- [ ] Set up property search alerts (Zillow, Redfin)

**Related**: Finances, Real Estate, Santa Cruz County Regulations, Smart Money Tracker.

---

## 🟪 A-Liner Replication (High)
*DIY hard-sided pop-up camper build. Engineering calculators built. Key patents expired.*

**Next Actions** (from A-Liner-Replication.md):
- [ ] Finalize material list
- [ ] Build prototype frame
- [ ] Test lifting mechanism
- [ ] Source insulation and interior materials

**Additional Tasks**:
- [ ] Review engineering calculators for safety factors
- [ ] Order materials for prototype
- [ ] Document build process for future replication
- [ ] Test weather sealing of prototype

**Related**: Homelab workspace, Fabrication, Camper Design References, Pop-up Mechanism Engineering, Smart Money Tracker (budget).

---

## 🟨 CampingSniper (Medium)
*Campsite availability monitor hitting Recreation.gov's internal API. Sends Slack alerts.*

**Inferred Tasks**:
- [ ] Verify current API endpoint and authentication
- [ ] Check Slack alert channel configuration (#futures or #openclaw?)
- [ ] Add logging for failed requests
- [ ] Implement exponential backoff for rate limits
- [ ] Add UI/dashboard for manual checks
- [ ] Expand to other recreation sites (Forest Service, BLM)
- [ ] Deploy updates to VPS/homelab

**Related**: Paper Trading (n8n), futures channel.

---

## 🟩 iOS Apps (Medium)
*Parkwood Accord (couples spending app), pill counting app (pharmacy), CleanStreak (habit tracker at cleanstreak.club).*

**Inferred Tasks**:
- [ ] Parkwood Accord: Design UI for shared expenses
- [ ] Parkwood Accord: Integrate with bank APIs (Plaid?)
- [ ] Pill counting app: Finalize prescription scanning flow
- [ ] Pill counting app: HIPAA compliance review
- [ ] CleanStreak: Add streak restoration feature
- [ ] CleanStreak: Push notifications for habit reminders
- [ ] Test all apps via TestFlight
- [ ] Update App Store metadata and screenshots
- [ ] Set up analytics (Firebase/Amplitude)

**Related**: iOS development certificates, App Store Connect.

---

## 🟧 Paper Trading (Medium)
*Futures paper trading via Tradovate API integration in n8n.*

**Inferred Tasks**:
- [ ] Monitor n8n workflow for errors
- [ ] Review paper trading performance vs. live
- [ ] Adjust risk parameters based on Smart Money Tracker V5.1
- [ ] Add notifications for significant drawdowns
- [ ] Implement auto-scaling of position sizes
- [ ] Backtest new strategies on historical data
- [ ] Document strategy logic for future reference

**Related**: #futures channel, Smart Money Tracker.

---

## 🟥 Smart Money Tracker (Medium)
*Financial risk scoring system (currently V5.1).*

**Inferred Tasks**:
- [ ] Validate V5.1 model against recent market data
- [ ] Incorporate new macro indicators (interest rates, inflation)
- [ ] Update dashboard visualizations
- [ ] Set up automated retraining pipeline
- [ ] Create simulation mode for strategy testing
- [ ] Export risk scores to other projects (Parkwood, A-Liner)
- [ ] Review paper trading integration points
- [ ] Document model assumptions and limitations

**Related**: #money-maker channel.

---

## 🟦 STEM with Roo (Low)
*Children's STEM education content brand.*

**Inferred Tasks**:
- [ ] Brainstorm next video topic (e.g., simple machines)
- [ ] Script and storyboard educational segment
- [ ] Film with Roo (setup lighting/audio)
- [ ] Edit video (add animations, captions)
- [ ] Publish to YouTube/ODYSSEE
- [ ] Create accompanying worksheet/activity PDF
- [ ] Share snippet on #stem-with-roo Slack
- [ ] Plan monthly content calendar

**Related**: Content creation gear, editing software.

---

## 🟨 Self-hosting Course (Low)
*Potential digital product — Proxmox-based self-hosting education.*

**Inferred Tasks**:
- [ ] Outline course syllabus (installation, VMs, backups, security)
- [ ] Record introductory video (What is self-hosting?)
- [ ] Create slide deck for each module
- [ ] Set up practice environment (VM templates)
- [ ] Record hands-on labs (Proxmox CLI, Ceph storage)
- [ ] Edit and host videos on platform (Teachable/Gumroad)
- [ ] Price and launch pre-sale
- [ ] Gather beta tester feedback
- [ ] Update course based on feedback

**Related**: Homelab, Proxmox, Docker, networking.

---

## 🔧 Maintenance & Infrastructure (Ongoing)
*Tasks that support multiple projects.*

- [ ] Monitor homelab resources (CPU, RAM, disk)
- [ ] Update Docker images and containers
- [ ] Backup critical volumes (Nextcloud, Immich, Actual Budget)
- [ ] Review Tailscale/ACL rules for node access
- [ ] Check OpenClaw skills for updates
- [ ] Rotate logs and prune old data
- [ ] Test failover for critical services (HAProxy?)
- [ ] Document any infrastructure changes

**Related**: All projects.

---
*Review and adjust priorities weekly. Move completed tasks to done log or archive.*