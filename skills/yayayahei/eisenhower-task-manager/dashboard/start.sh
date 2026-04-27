#!/bin/bash
# Eisenhower Task Dashboard Startup Script
# Automatically checks/installs dependencies and remembers the last used port

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT_FILE="$SCRIPT_DIR/port.conf"

# Check and install dependencies if needed
if [ ! -d "$SCRIPT_DIR/node_modules" ]; then
  echo "[Dashboard] First time setup - installing dependencies..."
  bash "$SCRIPT_DIR/check-and-install.sh"
  if [ $? -ne 0 ]; then
    exit 1
  fi
fi

# Read saved port (default: 8080)
if [ -f "$PORT_FILE" ]; then
    SAVED_PORT=$(cat "$PORT_FILE" | tr -d '[:space:]')
fi
SAVED_PORT=${SAVED_PORT:-8080}

# Check if user specified a port via --port argument
USER_PORT=""
for ((i=1; i<=$#; i++)); do
    arg="${!i}"
    if [ "$arg" = "--port" ]; then
        next=$((i+1))
        if [ $next -le $# ]; then
            USER_PORT="${!next}"
        fi
        break
    fi
done

# Determine which port to use
if [ -n "$USER_PORT" ]; then
    # User specified a port, save it for next time
    echo "$USER_PORT" > "$PORT_FILE"
    echo "[Dashboard] Port saved: $USER_PORT"
else
    # No port specified, use saved port
    set -- "$@" --port "$SAVED_PORT"
    echo "[Dashboard] Using saved port: $SAVED_PORT"
fi

cd "$SCRIPT_DIR"

# Check for --daemon flag
DAEMON_MODE=false
for arg in "$@"; do
    if [ "$arg" = "--daemon" ]; then
        DAEMON_MODE=true
        break
    fi
done

# Remove --daemon from args if present
ARGS=()
for arg in "$@"; do
    if [ "$arg" != "--daemon" ]; then
        ARGS+=("$arg")
    fi
done

if [ "$DAEMON_MODE" = true ]; then
    # Daemon mode: run in background with nohup
    LOG_FILE="$SCRIPT_DIR/dashboard.log"
    PID_FILE="$SCRIPT_DIR/dashboard.pid"
    
    # Check if already running
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            echo "[Dashboard] Already running (PID: $OLD_PID)"
            echo "[Dashboard] Visit: http://localhost:$SAVED_PORT"
            exit 0
        fi
    fi
    
    echo "[Dashboard] Starting in daemon mode..."
    echo "[Dashboard] Log file: $LOG_FILE"
    nohup node server.js "${ARGS[@]}" > "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    
    # Wait a moment to check if it started successfully
    sleep 2
    if kill -0 $PID 2>/dev/null; then
        echo "[Dashboard] Started successfully (PID: $PID)"
        echo "[Dashboard] Visit: http://localhost:$SAVED_PORT"
        echo "[Dashboard] Stop with: kill $PID"
    else
        echo "[Dashboard] Failed to start. Check log: $LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi
else
    # Interactive mode: run in foreground
    node server.js "${ARGS[@]}"
fi