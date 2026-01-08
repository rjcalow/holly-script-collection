#!/bin/bash

LOCK_FILE="/tmp/start_telebots.lock"
THIS_PID=$$

# === Kill previous instance if running ===
if [ -f "$LOCK_FILE" ]; then
  OLD_PID=$(cat "$LOCK_FILE")
  if ps -p "$OLD_PID" > /dev/null 2>&1; then
    echo "$(date) - Previous instance detected (PID: $OLD_PID). Killing it..."
    kill "$OLD_PID"
    sleep 2
  else
    echo "$(date) - Found stale lock file. Proceeding."
  fi
fi

# === Save current PID to lock file ===
echo "$THIS_PID" > "$LOCK_FILE"

# === Cleanup on exit ===
cleanup() {
  echo "$(date) - Cleaning up lock file."
  rm -f "$LOCK_FILE"
}
trap cleanup EXIT

# === this needs work ===
# # === Restart/start Ollama ===
# if systemctl is-active --quiet ollama; then
#   echo "$(date) - Ollama service is running. Restarting..."
#   sudo systemctl restart ollama && echo "$(date) - Ollama restarted." || echo "$(date) - Failed to restart Ollama."
# else
#   echo "$(date) - Ollama service is not running. Starting..."
#   sudo systemctl start ollama && echo "$(date) - Ollama started." || echo "$(date) - Failed to start Ollama."
# fi

# sleep 1 # Give Ollama time to (re)start

# === Script config ===
scripts=('holly.py' 'reddit_bot.py' 'weather_bot.py' '/filmsim_bot/filmsim_bot.py') #in bash lists are speparated by spaces
dir_="/home/holly/holly-script-collection/tele_bots"
python_env="/home/holly/holly_env/bin/python3"

# === Kill existing bot scripts ===
echo "$(date) - Stopping any existing instances of the scripts..."
for s in "${scripts[@]}"; do
  pids=$(pgrep -f "$s")
  if [ -n "$pids" ]; then
    echo "Killing $s (PIDs: $pids)"
    kill $pids
  fi
done
sleep 5

# === Main loop: keep scripts alive ===
while true; do
  for s in "${scripts[@]}"; do
    process_id=$(pgrep -f "$s")
    if [ -n "$process_id" ]; then
      echo "$(date) - $s is running (PID: $process_id)"
    else
      echo "$(date) - $s is not running, starting it..."
      nohup "$python_env" "$dir_/$s" > "$dir_/${s}.log" 2>&1 &
      echo "$(date) - $s started, check ${s}.log for output"
      sleep 1
    fi
  done
  sleep 120
done
