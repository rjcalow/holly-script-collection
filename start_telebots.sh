#!/bin/bash

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