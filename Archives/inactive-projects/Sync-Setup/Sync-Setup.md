# Sync Setup for OpenClaw Knowledge Base

## Current Setup (Host Bind-Mount)

To keep your PARA knowledge base private and synchronized between your OpenCloud and OpenClaw containers **without any data leaving your server**, use a host bind-mount.

### How It Works
- A directory on the Proxmox host is bind-mounted into both containers
- Both containers read/write the exact same files on disk
- **Zero network traffic** — data never leaves your server
- Instant consistency between containers

### Steps Already Completed
1. Host directory created: `/mnt/shared/knowledge-base`
2. Bind-mounted into:
   - OpenCloud container at `/mnt/knowledge-base`
   - OpenClaw container at `/mnt/knowledge-base`
3. Knowledge base symlinked to the mount:
   ```bash
   ln -s /mnt/knowledge-base /home/nemo-claw/.openclaw/workspace/knowledge-base
   ```

### Verification
- Create a test file in one container → see it appear instantly in the other
- Check that no extra ports are opened or sync services running
- Confirm backups of `/mnt/shared` include your knowledge base

### Security Notes
- All data remains on your Proxmox host
- No encryption needed for the share itself (data never traverses network)
- Ensure host directory permissions are restricted to the container UIDs/GIDs
- Your existing OpenCloud encryption (if enabled) still protects data at rest

### To Modify or Replicate
If you need to adjust the setup:
1. Edit the container/VM configs to change the mount point
2. Restart containers to apply changes
3. Update the symlink if the mount path changes

### Alternatives Considered
- **Syncthing**: Great for off-server sync, but unnecessary overhead for host-only sharing
- **Nextcloud built-in sync**: Would work but adds complexity when host mount is simpler
- **Git**: Good for versioning but not real-time collaboration

### Maintenance
- Periodically check that the mount is active (`df -h | grep knowledge-base`)
- Ensure your host backup strategy includes `/mnt/shared`
- Monitor container logs for any mount-related errors
