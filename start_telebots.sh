#!/bin/bash

LOCK_FILE="/tmp/start_telebots.lock"

# Check if lock file exists and process inside is running
if [ -f "$LOCK_FILE" ]; then
  old_pid=$(cat "$LOCK_FILE")
  if ps -p "$old_pid" > /dev/null 2>&1; then
    echo "$(date) - Script already running with PID $old_pid. Killing it..."
    kill "$old_pid"
    sleep 2
  fi
fi

# Store current PID in lock file
echo $$ > "$LOCK_FILE"

# Acquire an exclusive lock on the lock file
flock -n "$LOCK_FILE" -c '
  # Check Ollama status and restart/start accordingly
  if systemctl is-active --quiet ollama; then
    echo "$(date) - Ollama service is running. Restarting..."
    sudo systemctl restart ollama
    if [ $? -eq 0 ]; then
      echo "$(date) - Ollama service restarted successfully."
    else
      echo "$(date) - Failed to restart Ollama service."
    fi
  else
    echo "$(date) - Ollama service is not running. Starting..."
    sudo systemctl start ollama
    if [ $? -eq 0 ]; then
      echo "$(date) - Ollama service started successfully."
    else
      echo "$(date) - Failed to start Ollama service."
    fi
  fi
  sleep 5 # Give Ollama time to (re)start

  scripts=('holly.py' 'reddit_bot.py')
  dir_="/home/holly/holly-script-collection/tele_bots"
  python_env="/home/holly/holly_env/bin/python3"

  # Kill all running instances of the scripts at the start
  echo "Stopping any existing instances of the scripts..."
  for s in "${scripts[@]}"; do
    pids=$(pgrep -f "$s")
    if [ -n "$pids" ]; then
      echo "Killing processes for $s (PIDs: $pids)"
      kill $pids
    fi
  done
  echo "All existing instances stopped."
  sleep 5 # Let them shut down

  # Main loop
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
'