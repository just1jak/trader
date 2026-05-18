# Home Assistant Area

**Owner**: You (primary), Hermes (monitors via API)  
**Review cadence**: Weekly device checks, monthly automation audit  
**Created**: 2026-05-18

## Overview

Smart home automation: 1,014 entities across smart home devices, automations, and notifications.

## Subdirectories

### device-registry.md
Complete catalog of all Home Assistant entities, device groups, and capabilities.

### automations.md
Active automations (triggers, conditions, actions, notifications).

### alerts.md
Device failure detection rules and escalation paths.

## Standards

- Weekly device online/offline checks
- Monthly automation review (remove dead automations, add new ones)
- Device group health monitored continuously
- Slack alerts on device failures

## Key Automations

- **Daily** (6 AM) — device status check post-night
- **Weekly** (Monday 10 AM) — HA entity audit
- **Real-time** — device failure alerts → Slack

## Next Steps

1. Export current device-registry from HA API
2. Document active automations
3. Define failure notification rules
