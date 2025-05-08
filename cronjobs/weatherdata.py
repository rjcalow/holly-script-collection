'''
Downloads weather data from Adafruit IO with common.adafruit_sync
'''
import os
# Get the absolute path to the directory containing holly.py
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
common_dir = os.path.join(base_dir, "cronjobs")
home_dir = os.path.expanduser("~")

# Add paths to sys.path
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
if home_dir not in sys.path:
    sys.path.insert(0, home_dir)

# --- Secrets ---
from _secrets import adafruit_username, adafruit_key

# --- Adafruit backend --- 
from common.adafruit_sync import configure, sync_feeds

# --- Adafruit IO Config ---
configure(
    username=adafruit_username,    
    key=adafruit_key,  
    group="weather",
    limit=1000
)

feeds = ["temperature", "pressure", "humidity"]
sync_feeds(feeds, folder="/home/holly/weatherdata")
