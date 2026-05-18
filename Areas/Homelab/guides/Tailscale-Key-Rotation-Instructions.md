# Automated Tailscale Key Rotation

This guide sets up a monthly automated rotation of your Tailscale auth key using a script and systemd timer.

## Files Provided

- `~/workspace/bin/rotate-tailscale-key.sh` – rotation script (executable)
- `~/workspace/etc/systemd/user/tailscale-key-rotate.service` – systemd service unit
- `~/workspace/etc/systemd/user/tailscale-key-rotate.timer` – systemd timer unit (monthly)

## Setup Steps

### 1. Install the units

```bash
mkdir -p ~/.config/systemd/user
cp ~/workspace/etc/systemd/user/tailscale-key-rotate.* ~/.config/systemd/user/
```

### 2. Create environment file

```bash
mkdir -p ~/.config/tailscale-key-rotate
cat > ~/.config/tailscale-key-rotate/env <<EOF
# Tailscale API token (must have "key:write" permission)
TS_API_KEY=your_api_token_here

# Your tailnet name (e.g., example.com)
TS_TAILNET=your_tailnet_here

# Optional: adjust expiry (default 720h = 30 days)
# TS_KEY_EXPIRY=720h

# Optional: make key reusable (default false)
# TS_KEY_REUSABLE=false

# Optional: tags (comma-separated, e.g., tag:server,tag:router)
# TS_KEY_TAGS=tag:server
EOF
chmod 600 ~/.config/tailscale-key-rotate/env
```

### 3. Reload systemd, enable and start the timer

```bash
systemctl --user daemon-reload
systemctl --user enable --now tailscale-key-rotate.timer
```

### 4. Verify activation

```bash
systemctl --user list-timers | grep tailscale-key-rotate
journalctl --user -u tailscale-key-rotate.service -f   # view logs when it runs
```

## How It Works

- On the scheduled day (monthly), the timer triggers the service.
- The service runs `rotate-tailscale-key.sh`.
- The script:
  1. Calls the Tailscale API to create a new auth key (using your API token).
  2. Optionally applies the key immediately with `tailscale up`.
  3. Saves the new key (chmod 600) to `~/.tailscale/active-key.txt` for reference.
- Your node stays connected because the script runs `tailscale up` with the new key.

## Customisation

- Edit `~/.config/tailscale-key-rotate/env` to change:
  - `TS_KEY_EXPIRY` (e.g., `240h` for 10 days)
  - `TS_KEY_REUSABLE=true` if you need a reusable key
  - `TS_KEY_TAGS` to add tags like `tag:server,tag:router`
- To change the cadence, modify `OnCalendar` in the timer file (see `man systemd.time`).
- If you run a rootless Tailscale setup, remove `sudo` from the `tailscale up` line in the script.

## Manual Test

Run the script directly to verify it works:

```bash
~/workspace/bin/rotate-tailscale-key.sh
```

Make sure the environment file is sourced (the script reads it automatically).

## Security Note

- Treat `TS_API_KEY` like a password: it grants `key:write` access to your tailnet.
- Store it only in the restricted `env` file (chmod 600) and never commit it to version control.