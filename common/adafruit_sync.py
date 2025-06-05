'''
adafruit_sync.py

========
Downloads data from Adafruit IO feeds and appends it to CSV files.

Also provides a string report for Telegram with the latest feed data.
========

'''
import requests
import csv
import os
from datetime import datetime, timezone, timedelta

# Globals (set via configure)
HEADERS = {}
ADAFRUIT_IO_USERNAME = ""
GROUP_NAME = ""
LIMIT = 1000

def configure(username, key, group, limit=1000):
    global HEADERS, ADAFRUIT_IO_USERNAME, GROUP_NAME, LIMIT
    ADAFRUIT_IO_USERNAME = username
    GROUP_NAME = group
    LIMIT = limit
    HEADERS = {
        "X-AIO-Key": key,
        "Content-Type": "application/json"
    }

def get_last_timestamp_from_csv(filename):
    if not os.path.exists(filename):
        return None
    with open(filename, "r") as file:
        rows = list(csv.reader(file))
        if len(rows) < 2:
            return None
        return rows[-1][0]

def fetch_feed_data(feed_key):
    url = f"https://io.adafruit.com/api/v2/{ADAFRUIT_IO_USERNAME}/feeds/{GROUP_NAME}.{feed_key}/data?limit={LIMIT}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Error fetching {feed_key}: {response.status_code} {response.text}")
        return []
    return response.json()

def append_new_data_to_csv(feed_key, data, folder="feeds"):
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, f"{feed_key}.csv")
    last_timestamp = get_last_timestamp_from_csv(filename)

    data.sort(key=lambda x: x["created_at"])

    new_entries = [
        (entry["created_at"], entry["value"])
        for entry in data
        if last_timestamp is None or entry["created_at"] > last_timestamp
    ]

    if not new_entries:
        print(f"No new data for {feed_key}")
        return

    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        if os.stat(filename).st_size == 0:
            writer.writerow(["timestamp", "value"])
        writer.writerows(new_entries)

    print(f"Added {len(new_entries)} new entries to {filename}")

def sync_feeds(feed_list, folder="feeds"):
    for feed in feed_list:
        print(f"\nSyncing feed: {feed}")
        data = fetch_feed_data(feed)
        append_new_data_to_csv(feed, data, folder=folder)


# --- for checking feed health ---
def check_feed_freshness(feed_key, folder="feeds", max_age_hours=2):
    filepath = os.path.join(folder, f"{feed_key}.csv")
    if not os.path.exists(filepath):
        print(f"⚠️ No data file for {feed_key}")
        return False

    with open(filepath, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
        if not lines:
            print(f"⚠️ Empty file for {feed_key}")
            return False
        last_line = lines[-1]
        timestamp_str = last_line.split(",")[0]  # ← Fix 

    try:
        dt = datetime.fromisoformat(timestamp_str)
        now = datetime.now(timezone.utc)
        delta = now - dt
        print(f"{feed_key} last updated {delta} ago")
        return delta <= timedelta(hours=max_age_hours)
    except Exception as e:
        print(f"⚠️ Failed to parse timestamp for {feed_key}: {e}")
        return False


def format_feed_report_telegram(feeds=None, tz_name="Europe/London"):
    """
    Drop in function for Telegram bot integration.
    Returns a MarkdownV2-formatted report of specified Adafruit IO feeds.

    Args:
        feeds (list[str]): List of feed names to include. Defaults to common weather feeds.
        tz_name (str): Timezone name for formatting timestamps.

    Returns:
        str: Telegram-safe MarkdownV2 weather report string.
    """
    import pytz
    import re
    from datetime import datetime

    def escape(text):
        return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', str(text))

    def fmt_time(iso_string):
        try:
            dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
            return dt.astimezone(pytz.timezone(tz_name)).strftime('%H\\:%M')
        except Exception:
            return "unknown"

    configure()
    feeds = feeds or ["temperature", "humidity", "pressure", "water-level"]
    symbols = {
        "temperature": "🌡️",
        "humidity": "💧",
        "pressure": "🌬️",
        "water-level": "🌊"
    }

    lines = ["*📡 Adafruit Weather Station*"]
    success = False

    for feed in feeds:
        try:
            data = fetch_feed_data(feed)
            if not data:
                lines.append(f"{symbols.get(feed, '❓')} `{feed}`: no data")
                continue
            v = float(data[0]["value"])
            t = fmt_time(data[0].get("created_at", ""))
            if feed == "temperature":
                lines.append(f"{symbols[feed]} Temperature: `{v:.1f}°C` _(at {t})_")
            elif feed == "humidity":
                lines.append(f"{symbols[feed]} Humidity: `{v:.1f}%`")
            elif feed == "pressure":
                lines.append(f"{symbols[feed]} Pressure: `{v:.2f} hPa`")
            elif feed == "water-level":
                lines.append(f"{symbols[feed]} Water Level: `{v:.2f} cm`")
            else:
                lines.append(f"{symbols.get(feed, '🔹')} {feed}: `{v}`")
            success = True
        except Exception as e:
            lines.append(f"{symbols.get(feed, '❓')} `{feed}`: error reading data")
    
    if not success:
        return escape("⚠️ No data available from Adafruit IO at this time.")

    return "\n".join(escape(line) for line in lines)

