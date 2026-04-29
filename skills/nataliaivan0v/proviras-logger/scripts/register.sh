#!/bin/bash

# Path to config file
CONFIG_FILE="$(dirname "$0")/../references/config.md"

# Check if already registered
if grep -q "agent_id:" "$CONFIG_FILE" && ! grep -q "agent_id: (populated" "$CONFIG_FILE"; then
  echo "Agent already registered, skipping."
  exit 0
fi

# Determine identity field: parent_id takes precedence when set (agent-spawned), else user_id (human-spawned)
if [ -n "$PROVIRAS_PARENT_ID" ]; then
  IDENTITY_FIELD='"parent_id": "'"$PROVIRAS_PARENT_ID"'"'
elif [ -n "$PROVIRAS_USER_ID" ]; then
  IDENTITY_FIELD='"user_id": "'"$PROVIRAS_USER_ID"'"'
else
  echo "Registration failed: neither PROVIRAS_USER_ID nor PROVIRAS_PARENT_ID is set."
  exit 1
fi

# Read agent name from SOUL.md
SOUL_FILE="$HOME/.openclaw/workspace/SOUL.md"
AGENT_NAME=$(grep -m 1 "^name:" "$SOUL_FILE" | awk '{print $2}')

# Fallback if name not found
if [ -z "$AGENT_NAME" ]; then
  AGENT_NAME="unnamed-agent"
fi

# Read model from openclaw.json
MODEL=$(cat "$HOME/.openclaw/openclaw.json" | grep '"model"' | head -1 | awk -F'"' '{print $4}')

# Register with platform
RESPONSE=$(curl -s -X POST https://proviras.com/agent/register \
  -H "Content-Type: application/json" \
  -d '{
    '"$IDENTITY_FIELD"',
    "agent_name": "'"$AGENT_NAME"'",
    "model": "'"$MODEL"'",
    "platform": "openclaw",
    "registered_at": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'"
  }')

# Extract agent_id from response
AGENT_ID=$(echo "$RESPONSE" | grep -o '"agent_id":"[^"]*"' | awk -F'"' '{print $4}')

# Handle failure
if [ -z "$AGENT_ID" ]; then
  echo "Registration failed. Response: $RESPONSE"
  exit 1
fi

# Write agent_id to config
sed -i "s/agent_id: (populated automatically on first heartbeat)/agent_id: $AGENT_ID/" "$CONFIG_FILE"

echo "Agent registered successfully. ID: $AGENT_ID"