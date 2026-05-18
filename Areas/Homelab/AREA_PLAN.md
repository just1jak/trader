# Homelab Area

**Owner**: You (primary), Hermes (monitors via Home Assistant API)
**Review cadence**: As-needed + quarterly health check
**Created**: 2026-05-18

## Overview

Self-hosted infrastructure: Proxmox cluster, Home Assistant, Tailscale VPN, container orchestration.

## Standards

- **Health checks**: Run Proxmox health script quarterly
- **Key rotation**: Annual Tailscale key rotation
- **Recovery docs**: Keep updated for HA, VPN, DNS failures
- **Permissions**: Run setup-permissions.sh + gatekeeper.sh after OS updates

## Subdirectories

### guides/
- Proxmox health checks, Tailscale key rotation, HA recovery

### scripts/
- setup-permissions.sh — fix ownership + perms after OS updates
- gatekeeper.sh — security scanning

### monitoring/
- Backup verification (rsync logs, ZFS snapshots)
- Drive health checks (SMART data)
- LXC/VM audits (resource usage, uptime)
- Home Assistant entity status

## Automations

- **Weekly** (Sunday 6 PM) — backup verification
- **Quarterly** (1st of month) — full health check + key rotation reminders
- **Monthly** — HA device status audit

## Next Steps

1. Document current Proxmox + HA state (VMs, entities, automation)
2. Set up monitoring crons in Hermes
3. Create backup checklist + verification protocol
