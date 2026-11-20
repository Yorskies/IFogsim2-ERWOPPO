#!/usr/bin/env bash
# P13 launcher: RL benchmark (DQN, tabular Q-Learning, DDPG vs PPO-Equal) with tuning, P13 lock, training,
# sealed benchmark_test evaluation, analysis and claims. Runs detached from the terminal and the browser tab.
#
#   ./run_p13.sh            run every stage (resumes where it stopped; ~2 days on 12 workers)
#   ./run_p13.sh status     progress
#   ./run_p13.sh stop       graceful stop (run ./run_p13.sh again later to resume)
#   ./run_p13.sh log        follow the pipeline log
set -euo pipefail
cd "$(dirname "$0")"
DIR=results/research_v2/p13/pipeline
PIDFILE=$DIR/pid
mkdir -p "$DIR"

alive() {  # a live (non-zombie) process with this pid
  [ -f "$PIDFILE" ] || return 1
  local pid; pid=$(cat "$PIDFILE")
  [ -r "/proc/$pid/stat" ] || return 1
  [ "$(awk '{print $3}' "/proc/$pid/stat")" != "Z" ]
}

case "${1:-}" in
  status) PYTHONPATH=. venv/bin/python -m research_v2.p13 status
          if alive; then echo "pipeline running (pid $(cat "$PIDFILE"))"; else echo "pipeline not running"; fi; exit 0 ;;
  stop)   if alive; then kill -TERM "$(cat "$PIDFILE")"; echo "stop requested; running jobs are terminated and redone on resume"; else echo "not running"; fi; exit 0 ;;
  log)    touch "$DIR/pipeline.log"; exec tail -f "$DIR/pipeline.log" ;;
  "")     ;;
  *)      echo "usage: $0 [status|stop|log]"; exit 2 ;;
esac

if alive; then echo "already running (pid $(cat "$PIDFILE")); use: $0 status"; exit 1; fi
PYTHONPATH=. setsid nohup venv/bin/python -u -m research_v2.p13 run >> "$DIR/console.log" 2>&1 < /dev/null &
echo $! > "$PIDFILE"
echo "started pid $(cat "$PIDFILE"): P13 (determinism, tuning, lock, training, benchmark_test evaluation, analysis, claims)"
echo "  progress : $0 status"
echo "  live log : $0 log      (Ctrl-C only stops viewing)"
echo "  stop     : $0 stop     (resume later with $0)"
