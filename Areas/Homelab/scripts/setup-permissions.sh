#!/bin/bash
# Setup filesystem permissions for the outbox security model.
# Run this on the Proxmox host where the knowledge-base is shared.
#
# Assumes:
#   - KB_ROOT is the knowledge-base mount (e.g., /mnt/shared/knowledge-base)
#   - AGENT_USER is the user nemo-claw runs as
#   - OWNER_USER is Justin's user (or root)
#
# Usage: sudo ./setup-permissions.sh <kb-root> <agent-user> <owner-user>

set -euo pipefail

KB_ROOT="${1:-/mnt/shared/knowledge-base}"
AGENT_USER="${2:-nemo-claw}"
OWNER_USER="${3:-justin}"

echo "Setting up outbox permissions model..."
echo "  KB Root:    $KB_ROOT"
echo "  Agent user: $AGENT_USER"
echo "  Owner user: $OWNER_USER"

# Owner owns everything
chown -R "$OWNER_USER":"$OWNER_USER" "$KB_ROOT"

# Remove world/group write from everything
chmod -R go-w "$KB_ROOT"

# Agent gets read access to the whole KB
setfacl -R -m u:"$AGENT_USER":rX "$KB_ROOT"
setfacl -R -d -m u:"$AGENT_USER":rX "$KB_ROOT"

# Agent gets write access ONLY to outbox/
setfacl -R -m u:"$AGENT_USER":rwX "$KB_ROOT/outbox"
setfacl -R -d -m u:"$AGENT_USER":rwX "$KB_ROOT/outbox"

# Gatekeeper script must be owned by owner and not writable by agent
chmod 755 "$KB_ROOT/bin/gatekeeper.sh"
chown "$OWNER_USER":"$OWNER_USER" "$KB_ROOT/bin/gatekeeper.sh"

# Audit log: agent cannot write
chmod 755 "$KB_ROOT/state/audit"
chown -R "$OWNER_USER":"$OWNER_USER" "$KB_ROOT/state/audit"

echo "Done. nemo-claw can now:"
echo "  - READ everything in $KB_ROOT"
echo "  - WRITE only to $KB_ROOT/outbox/"
echo ""
echo "Run gatekeeper on a schedule to process outbox:"
echo "  */5 * * * * $KB_ROOT/bin/gatekeeper.sh"
