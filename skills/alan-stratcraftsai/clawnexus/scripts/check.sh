#!/bin/bash
# Check if clawnexus daemon is available
API_URL="${CLAWNEXUS_API:-http://localhost:17890}"

if curl -sf "${API_URL}/health" > /dev/null 2>&1; then
  echo "ClawNexus daemon is running at ${API_URL}"
  exit 0
else
  echo "ClawNexus daemon is not available at ${API_URL}"
  echo "Start it with: clawnexus start"
  exit 1
fi
