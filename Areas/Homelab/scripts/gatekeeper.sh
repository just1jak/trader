#!/bin/bash
# Gatekeeper — processes agent outbox submissions
# Validates against rules, applies approved changes, logs everything.
# Run this on a schedule (every 5 min) or trigger after each heartbeat.
#
# Usage: ./bin/gatekeeper.sh
# Requires: jq, node/python for JSON schema validation (optional)

set -euo pipefail

KB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTBOX="$KB_ROOT/outbox"
AUDIT_LOG="$KB_ROOT/state/audit/audit.log"
RULES="$KB_ROOT/state/audit/gatekeeper-rules.json"

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" >> "$AUDIT_LOG"
}

reject() {
    local file="$1" reason="$2"
    log "REJECTED: $(basename "$file") — $reason"
    mv "$file" "$OUTBOX/rejected_$(basename "$file")"
}

# Find all pending submissions (JSON files, not README or schema)
shopt -s nullglob
submissions=("$OUTBOX"/*.json)
shopt -u nullglob

# Skip schema file
submissions=("${submissions[@]/$OUTBOX\/outbox-schema.json/}")

if [ ${#submissions[@]} -eq 0 ]; then
    exit 0
fi

log "Processing ${#submissions[@]} submission(s)"

for submission in "${submissions[@]}"; do
    [ -z "$submission" ] && continue
    [ ! -f "$submission" ] && continue

    filename=$(basename "$submission")

    # Basic validation: is it valid JSON?
    if ! jq empty "$submission" 2>/dev/null; then
        reject "$submission" "Invalid JSON"
        continue
    fi

    # Check agent_id is in allowed list
    agent_id=$(jq -r '.agent_id' "$submission")
    if ! jq -e --arg id "$agent_id" '.rules.allowed_agents | index($id)' "$RULES" >/dev/null 2>&1; then
        reject "$submission" "Unknown agent: $agent_id"
        continue
    fi

    # Check number of actions
    action_count=$(jq '.actions | length' "$submission")
    max_actions=$(jq '.rules.max_actions_per_submission' "$RULES")
    if [ "$action_count" -gt "$max_actions" ]; then
        reject "$submission" "Too many actions: $action_count > $max_actions"
        continue
    fi

    # Process each action
    log "PROCESSING: $filename ($action_count actions from $agent_id)"

    for i in $(seq 0 $((action_count - 1))); do
        action_type=$(jq -r ".actions[$i].type" "$submission")
        target=$(jq -r ".actions[$i].target" "$submission")
        content=$(jq -r ".actions[$i].content" "$submission")
        operation=$(jq -r ".actions[$i].operation // \"append\"" "$submission")
        section=$(jq -r ".actions[$i].section // \"\"" "$submission")

        # Check target against forbidden list
        forbidden=false
        while IFS= read -r pattern; do
            pattern=$(echo "$pattern" | tr -d '"')
            if [[ "$target" == $pattern ]]; then
                forbidden=true
                break
            fi
        done < <(jq -r '.rules.forbidden_targets[]' "$RULES")

        if [ "$forbidden" = true ]; then
            log "  BLOCKED action $i: forbidden target '$target'"
            continue
        fi

        # Check content length
        content_len=${#content}
        max_len=$(jq '.rules.max_content_length_per_action' "$RULES")
        if [ "$content_len" -gt "$max_len" ]; then
            log "  BLOCKED action $i: content too long ($content_len > $max_len)"
            continue
        fi

        # Check for forbidden patterns in content
        blocked_pattern=""
        while IFS= read -r pattern; do
            pattern=$(echo "$pattern" | tr -d '"')
            if echo "$content" | grep -qE "$pattern"; then
                blocked_pattern="$pattern"
                break
            fi
        done < <(jq -r '.rules.forbidden_patterns_in_content[]' "$RULES")

        if [ -n "$blocked_pattern" ]; then
            log "  BLOCKED action $i: forbidden pattern '$blocked_pattern' in content"
            continue
        fi

        # Apply the action
        target_path="$KB_ROOT/$target"

        case "$action_type" in
            update_state|update_status)
                if [ "$operation" = "replace_field" ]; then
                    # For JSON state files — use jq to update
                    if [[ "$target" == *.json ]]; then
                        echo "$content" > "$target_path.tmp"
                        mv "$target_path.tmp" "$target_path"
                        log "  APPLIED action $i: replaced $target"
                    fi
                fi
                ;;
            append_memory|add_insight|add_contact)
                if [ -f "$target_path" ]; then
                    if [ -n "$section" ]; then
                        # Append after the section header
                        # Find the line with "## $section" and append after it
                        if grep -q "## $section" "$target_path"; then
                            sed -i '' "/## $section/a\\
$content" "$target_path" 2>/dev/null || \
                            sed -i "/## $section/a\\$content" "$target_path"
                        else
                            echo -e "\n$content" >> "$target_path"
                        fi
                    else
                        echo -e "\n$content" >> "$target_path"
                    fi
                    log "  APPLIED action $i: appended to $target"
                else
                    log "  BLOCKED action $i: target file does not exist '$target'"
                fi
                ;;
            log_daily)
                # Create daily log file if it doesn't exist
                echo "$content" >> "$target_path"
                log "  APPLIED action $i: logged to $target"
                ;;
            send_slack)
                slack_channel=$(jq -r ".actions[$i].slack_channel" "$submission")
                # Validate channel is allowed
                if jq -e --arg ch "$slack_channel" '.slack_rules.allowed_channels | index($ch)' "$RULES" >/dev/null 2>&1; then
                    log "  QUEUED action $i: slack message to $slack_channel ($(echo "$content" | wc -c) bytes)"
                    # Write to a slack outbox for the Slack gateway to pick up
                    mkdir -p "$KB_ROOT/outbox/slack"
                    echo "{\"channel\":\"$slack_channel\",\"text\":$(echo "$content" | jq -Rs .)}" > "$KB_ROOT/outbox/slack/${filename%.json}_msg${i}.json"
                else
                    log "  BLOCKED action $i: unauthorized slack channel '$slack_channel'"
                fi
                ;;
            *)
                log "  BLOCKED action $i: unknown action type '$action_type'"
                ;;
        esac
    done

    # Archive processed submission
    summary=$(jq -r '.summary // "no summary"' "$submission")
    log "COMPLETED: $filename — $summary"
    mkdir -p "$OUTBOX/processed"
    mv "$submission" "$OUTBOX/processed/$filename"
done

log "Gatekeeper run complete"
