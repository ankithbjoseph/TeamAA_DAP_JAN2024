#!/usr/bin/env bash
set -euo pipefail

# Start Dagster webserver and daemon, forward signals, and wait

dagster-webserver -h 0.0.0.0 -w workspace.yaml &
WEB_PID=$!

dagster-daemon run &
DAEMON_PID=$!

# Start Panel dashboard (served from the dashboard/ folder)
# Run from /main/dashboard so relative data files are found
cd /main/dashboard || true
panel serve dashboard.py --address 0.0.0.0 --port 5006 --autoreload &
PANEL_PID=$!
cd - >/dev/null 2>&1 || true

term_handler() {
  echo "Shutting down..."
  kill -TERM "$WEB_PID" 2>/dev/null || true
  kill -TERM "$DAEMON_PID" 2>/dev/null || true
  kill -TERM "$PANEL_PID" 2>/dev/null || true
  wait "$WEB_PID" 2>/dev/null || true
  wait "$DAEMON_PID" 2>/dev/null || true
  wait "$PANEL_PID" 2>/dev/null || true
  exit 0
}

trap 'term_handler' SIGTERM SIGINT

# Wait for any process to exit
if wait -n 2>/dev/null; then
  EXIT_CODE=$?
else
  # Fallback for shells without wait -n: poll processes
  while true; do
    if ! kill -0 "$WEB_PID" 2>/dev/null || ! kill -0 "$DAEMON_PID" 2>/dev/null || ! kill -0 "$PANEL_PID" 2>/dev/null; then
      break
    fi
    sleep 1
  done
  EXIT_CODE=0
fi

echo "One process exited (code $EXIT_CODE), stopping others..."
term_handler
