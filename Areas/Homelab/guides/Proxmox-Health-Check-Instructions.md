# Proxmox Nightly Health Check Setup

This guide configures a nightly script that checks the health of your Proxmox host, VMs, and LXCs, and sends a Slack notification if any issues are detected.

## Files Provided

- `~/workspace/bin/proxmox-health-check.sh` – the health‑check script (executable)
- Instructions below for creating a systemd timer and configuring notifications.

## Prerequisites

1. **Access to the Proxmox API**  
   The script uses `pvesh` (which talks to the local pveproxy). It must run as a user that can access the API—typically `root` or a user with `Sys.Audit` privileges on `/nodes/<node>`.  
   If you prefer to use an API token, adjust the script’s `API_USER` and `API_TOKEN` variables accordingly.

2. **`jq` installed** (for JSON parsing)  
   ```bash
   apt-get update && apt-get install -y jq   # Debian/Ubuntu
   ```

3. **Slack Incoming Webhook URL** (optional but recommended)  
   Create one in Slack → Settings → Apps → Incoming Webhooks → Add New Webhook → Choose a channel.  
   Copy the URL; you’ll set it as an environment variable.

## Installation Steps

### 1. Copy the script and make it executable

```bash
mkdir -p ~/workspace/bin
cp /path/to/proxmox-health-check.sh ~/workspace/bin/   # if not already there
chmod +x ~/workspace/bin/proxmox-health-check.sh
```

### 2. Create an environment file for the script

The script reads the following variables from `~/.config/proxmox-health-check/env`:

```bash
mkdir -p ~/.config/proxmox-health-check
cat > ~/.config/proxmox-health-check/env <<EOF
# Proxmox node (usually your hostname); can be left empty to auto‑detect
# NODE=

# API user for pvesh – leave as root@pam if running as root, or use a token:
# API_USER="root@pam!tokentitle"
# API_TOKEN="<uuid>"   # only needed if using token auth

# Slack webhook URL (get from Slack Incoming Webhook integration)
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/XXXXX/XXXXX/XXXXXXXX"

# Optional: set to "true" to disable Slack notifications (useful for testing)
# DISABLE_SLACK=true
EOF
chmod 600 ~/.config/proxmox-health-check/env
```

> **Tip:** If you run the script as root on the host, you can leave `API_USER` and `API_TOKEN` blank; `pvesh` will use the local ticket.

### 3. Test the script manually

```bash
# Source the env file so variables are available
export $(grep -v '^#' ~/.config/proxmox-health-check/env | xargs)
~/workspace/bin/proxmox-health-check.sh
```

You should see output like:

```
:white_check_mark: *Proxmox Health Check* – All good on node proxmox01
```

or a list of issues if any are found. Check that a Slack message appears in the configured channel (if `SLACK_WEBHOOK_URL` is set).

### 4. Install the systemd timer (user‑level)

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/proxmox-health-check.service <<EOF
[Unit]
Description=Nightly Proxmox health check
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
EnvironmentFile=%h/.config/proxmox-health-check/env
ExecStart=%h/workspace/bin/proxmox-health-check.sh
EOF

cat > ~/.config/systemd/user/proxmox-health-check.timer <<EOF
[Unit]
Description=Run Proxmox health check each night at 02:30

[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true   # run immediately if machine was off at the scheduled time

[Install]
WantedBy=timers.target
EOF
```

### 5. Enable and start the timer

```bash
systemctl --user daemon-reload
systemctl --user enable --now proxmox-health-check.timer
```

### 6. Verify the timer is active

```bash
systemctl --user list-timers | grep proxmox-health-check
journalctl --user -u proxmox-health-check.service -f   # follow logs when it runs
```

## What the Script Checks

| Entity | Check Performed |
|--------|-----------------|
| **Host** | Subscription status (`active`/`Community`), available package updates (`pveapt list --upgradable`) |
| **VMs (QEMU)** | Current status (`running`, `paused`, `suspended` are OK); HA state if configured |
| **LXCs (Containers)** | Same as VMs |
| **Backups** (optional) | Looks for any `vzdump*.log` from the last 24 h containing `END BACKUP`. If none found, flags an issue. |

You can extend the script by adding more checks (e.g., storage usage, Ceph health, etc.) – just edit the `proxmox-health-check.sh` file.

## Fixing / Ensuring Golden Backups

While this health check verifies that a backup *log* exists and ends successfully, ensuring “golden” (verified, restorable) backups involves:

1. **Backup Validation** – Periodically restore a VM/CT to an isolated network or use `qm restore`/`pct restore` to a temporary ID and verify boot.
2. **Backup Pruning** – Ensure your backup jobs (`vzdump` or storage‑level snapshots) retain the correct retention policy (daily/weekly/monthly).
3. **Storage Health** – Monitor the storage where backups reside (e.g., ZFS pool status, SMART of disks).
4. **Off‑site Copy** – Consider copying backups to another location (Restic, rsync, or another Proxmox node) and checking the copy’s integrity.

You can add a separate script for backup validation and hook it into the same timer or a different cadence (e.g., weekly).

## Customisation

- **Change check time**: Edit `OnCalendar` in the timer file (see `man systemd.time`).
- **Adjust thresholds**: Modify the script’s checks (e.g., only alert if >5 updates, or ignore certain VM IDs).
- **Notification method**: Replace the Slack webhook block with email (`mailx`), Pushover, Telegram, etc., by editing the `notify_slack` function.
- **Run as system service**: If you prefer a system‑wide timer, copy the units to `/etc/systemd/system/` and run `systemctl daemon-reload && systemctl enable --now proxmox-health-check.timer`.

## Security Notes

- The environment file contains your Slack webhook URL (and possibly an API token). Keep it permissions‑restricted (`chmod 600`).
- The script runs with the privileges of the user invoking the timer. If you run it as a non‑root user, ensure that user can access `pvesh` (grant `Sys.Audit` on `/nodes/<node>` or use an API token with appropriate permissions).

---

You’re all set! The health check will run each night and ping Slack if anything looks off. Let me know if you’d like help adding backup validation or tweaking any of the checks.