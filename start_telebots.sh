#!/bin/bash

scripts=('holly.py',)

dir_="/home/holly/holly-script-collection/telebots/"
python_env="/home/holly/holly_env/bin/python3"

# Kill all running instances of the scripts at the start
echo "Stopping any existing instances of the scripts..."
for s in "${scripts[@]}"; do
  pids=$(pgrep -f "$s")
  if [ -n "$pids" ]; then
    echo "Killing processes for $s (PIDs: $pids)"
    kill "$pids"
  fi
done
echo "All existing instances stopped."
sleep 5 # Give some time for processes to terminate

# Main loop
while true; do
  for s in "${scripts[@]}"; do
    process_id=$(pgrep -f "$s")

    if [ -n "$process_id" ]; then
      echo "$s is running"
    else
      echo "$s is not running, restarting..."
      nohup "$python_env" "$dir_"$s "command" "arg" &
      sleep 1
    fi
  done
  sleep 120 # Run every 2 minutes
done