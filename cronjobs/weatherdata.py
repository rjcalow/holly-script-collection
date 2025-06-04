'''
Downloads weather data from Adafruit IO with common.adafruit_sync
'''
# --- secrets ---
import os
import sys

# Get the absolute path to the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
common_dir = os.path.join(base_dir, "cronjobs")
home_dir = os.path.expanduser("~")

# Add paths to sys.path
for path in (base_dir, home_dir):
    if path not in sys.path:
        sys.path.insert(0, path)

# --- Secrets ---
from _secrets import adafruit_username, adafruit_key
# --- Adafruit backend --- 
from common.adafruit_sync import configure, sync_feeds, check_feed_freshness
from common.telegram_msg import send_telegram_alert

# --- Adafruit IO Config ---
configure(
    username=adafruit_username,    
    key=adafruit_key,  
    group="weather",
    limit=1000
)

feeds = ["temperature", "pressure", "humidity", "water-level"]
folder = "/home/holly/weatherdata"
max_age_hours = 2

# --- Sync feeds ---
sync_feeds(feeds, folder=folder)

# --- Check freshness ---
any_stale = False
for feed in feeds:
    fresh = check_feed_freshness(feed, folder=folder, max_age_hours=max_age_hours)
    if not fresh:
        any_stale = True

if any_stale:
    send_telegram_alert("⚠️ Weather feeds have not been updated recently. Battery may be dead or device offline."
    )
