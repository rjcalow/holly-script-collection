''' 

for quick messaging via holly for cronjobs ect

'''
import os
import sys
# Get the absolute path to the directory containing holly.py
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
common_dir = os.path.join(base_dir, "common")
home_dir = os.path.expanduser("~")

# Add paths to sys.path
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
if home_dir not in sys.path:
    sys.path.insert(0, home_dir)

# --- Secrets ---
from _secrets import hollytoken, alertsid

import requests

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{hollytoken}/sendMessage"
    payload = {
        "chat_id": alertsid,
        "text": message
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Telegram error: {response.text}")