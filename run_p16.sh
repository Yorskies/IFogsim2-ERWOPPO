#!/usr/bin/env bash
# P16 launcher (see docs/research_v2/P15_P16_IMPLEMENTATION_PLAN.md).
# Runs detached from the terminal and the browser tab; resumable.
#
#   ./run_p16.sh            run every stage (resumes where it stopped; ~3.5 h on 12 workers)
#   ./run_p16.sh status     progress
#   ./run_p16.sh stop       graceful stop (run ./run_p16.sh again later to resume)
#   ./run_p16.sh log        follow the pipeline log
set -euo pipefail
cd "$(dirname "$0")"
DIR=results/research_v2/p15/pipeline
PIDFILE=$DIR/pid_p16
mkdir -p "$DIR"

alive() {  # a live (non-zombie) process with this pid
  [ -f "$PIDFILE" ] || return 1
  local pid; pid=$(cat "$PIDFILE")
  [ -r "/proc/$pid/stat" ] || return 1
  [ "$(awk '{print $3}' "/proc/$pid/stat")" != "Z" ]
}

case "${1:-}" in
  status) PYTHONPATH=. venv/bin/python -m research_v2.p16 status
          if alive; then echo "pipeline running (pid $(cat "$PIDFILE"))"; else echo "pipeline not running"; fi; exit 0 ;;
  stop)   if alive; then kill -TERM "$(cat "$PIDFILE")"; echo "stop requested; running jobs are terminated and redone on resume"; else echo "not running"; fi; exit 0 ;;
  log)    touch "$DIR/pipeline.log"; exec tail -f "$DIR/pipeline.log" ;;
  "")     ;;
  *)      echo "usage: $0 [status|stop|log]"; exit 2 ;;
esac

if alive; then echo "already running (pid $(cat "$PIDFILE")); use: $0 status"; exit 1; fi
PYTHONPATH=. setsid nohup venv/bin/python -u -m research_v2.p16 run >> "$DIR/console.log" 2>&1 < /dev/null &
echo $! > "$PIDFILE"
echo "started pid $(cat "$PIDFILE"): P16"
echo "  progress : $0 status"
echo "  live log : $0 log      (Ctrl-C only stops viewing)"
echo "  stop     : $0 stop     (resume later with $0)"
