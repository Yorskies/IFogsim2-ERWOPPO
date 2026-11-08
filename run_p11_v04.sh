#!/usr/bin/env bash
# Protocol v0.4 pipeline launcher: runs detached from the terminal and the browser tab (setsid + nohup).
#
#   ./run_p11_v04.sh                 preparation + lock only (no training, no test)
#   ./run_p11_v04.sh go              + P11 training (your M3 decision: go)
#   ./run_p11_v04.sh go-open-test    + P11 training, then OPEN THE TEST SPLIT, evaluate and analyse (irreversible)
#   ./run_p11_v04.sh status          progress
#   ./run_p11_v04.sh stop            graceful stop (re-run the same mode later to resume)
#   ./run_p11_v04.sh log             follow the pipeline log
set -euo pipefail
cd "$(dirname "$0")"
DIR=results/research_v2/v0.4/pipeline
PIDFILE=$DIR/pid
mkdir -p "$DIR"

alive() {  # a live (non-zombie) process with this pid
  [ -f "$PIDFILE" ] || return 1
  local pid; pid=$(cat "$PIDFILE")
  [ -r "/proc/$pid/stat" ] || return 1
  [ "$(awk '{print $3}' "/proc/$pid/stat")" != "Z" ]
}

case "${1:-}" in
  status) PYTHONPATH=. venv/bin/python -m research_v2.p11_v04 status
          if alive; then echo "pipeline running (pid $(cat "$PIDFILE"))"; else echo "pipeline not running"; fi; exit 0 ;;
  stop)   if alive; then kill -TERM "$(cat "$PIDFILE")"; echo "stop requested; shards finish their current step and exit"; else echo "not running"; fi; exit 0 ;;
  log)    exec tail -f "$DIR/pipeline.log" ;;
  "")     ARGS=(run) ;;
  go)     ARGS=(run --go) ;;
  go-open-test) ARGS=(run --go --open-test) ;;
  *)      echo "usage: $0 [go|go-open-test|status|stop|log]"; exit 2 ;;
esac

if alive; then echo "already running (pid $(cat "$PIDFILE")); use: $0 status"; exit 1; fi
PYTHONPATH=. setsid nohup venv/bin/python -u -m research_v2.p11_v04 "${ARGS[@]}" >> "$DIR/console.log" 2>&1 < /dev/null &
echo $! > "$PIDFILE"
echo "started pid $(cat "$PIDFILE"): ${ARGS[*]}"
echo "  progress : $0 status"
echo "  live log : $0 log      (Ctrl-C only stops viewing)"
echo "  stop     : $0 stop     (resume later with the same command)"
