#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT=10000
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/uvicorn-10000.log"

PYTHON_BIN="${PYTHON_BIN:-python3}"

UVICORN_CMD="uvicorn main:app --host 0.0.0.0 --port ${PORT} --reload"

mkdir -p "$LOG_DIR"

log() {
  echo "[INFO] $1"
}

warn() {
  echo "[WARN] $1"
}

err() {
  echo "[ERROR] $1" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || err "Missing command: $1"
}

check_deps() {
  require_cmd "$PYTHON_BIN"
  require_cmd lsof
  require_cmd nohup
}

kill_port() {
  log "Checking port ${PORT}..."

  local pids
  pids=$(lsof -ti tcp:"$PORT" || true)

  if [ -z "$pids" ]; then
    log "Port ${PORT} is free"
    return
  fi

  warn "Port ${PORT} is in use by PID(s): $pids"

  for pid in $pids; do
    log "Sending SIGTERM to $pid"
    kill "$pid" || true
  done

  sleep 2

  local still_running
  still_running=$(lsof -ti tcp:"$PORT" || true)

  if [ -n "$still_running" ]; then
    warn "Force killing PID(s): $still_running"
    kill -9 $still_running || true
  fi
}

activate_venv() {
  if [ -d "$PROJECT_ROOT/.venv" ]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.venv/bin/activate"
  else
    warn ".venv not found — running with system python"
  fi
}

start_uvicorn() {
  log "Starting uvicorn on port ${PORT}..."

  nohup bash -c "
    cd '$PROJECT_ROOT' &&
    '$l/venv/bin/python' -m uvicorn main:app \
      --host 0.0.0.0 \
      --port ${PORT} \
      --reload
  " >>"$LOG_FILE" 2>&1 &

  local pid=$!

  echo "$pid" >"$LOG_DIR/uvicorn.pid"

  log "Uvicorn started"
  log "PID: $pid"
  log "Log file: $LOG_FILE"
}

main() {
  check_deps
  activate_venv
  kill_port
  start_uvicorn
}

main "$@"
