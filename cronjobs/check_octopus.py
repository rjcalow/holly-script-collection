import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo  # Python 3.9+

# --- paths setup ---
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
common_dir = os.path.join(base_dir, "cronjobs")
home_dir = os.path.expanduser("~")

for path in (base_dir, home_dir):
    if path not in sys.path:
        sys.path.insert(0, path)

# --- imports ---
from common.octopus import get_octopus_agile_daily_rates
from common.telegram_msg import send_telegram_alert

# --- settings ---
GSP_GROUP_ID = "B"
LOCAL_TZ = ZoneInfo("Europe/London")
ALERT_THRESHOLD = 0.0   # change to e.g. 1.0 if you want ≤1p alerts

# --- main logic ---
all_daily_rates = get_octopus_agile_daily_rates(GSP_GROUP_ID)

if all_daily_rates is not None and all_daily_rates:
    negative_rates = []

    # Convert to local times + filter
    for time_str, rate in all_daily_rates.items():
        start_time_utc = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        local_time = start_time_utc.astimezone(LOCAL_TZ)
        if rate <= ALERT_THRESHOLD:
            negative_rates.append((local_time, rate))

    if negative_rates:
        # Sort by local datetime
        negative_rates.sort(key=lambda x: x[0])

        today_str = datetime.now(LOCAL_TZ).strftime("%A %d %B %Y")
        message_lines = [
            f"⚡️ *Negative/Free Price Alert!* ⚡️",
            f"📅 {today_str}\n",
            f"The following time slots are ≤ {ALERT_THRESHOLD:.2f}p/kWh:\n"
        ]

        for local_time, rate in negative_rates:
            message_lines.append(f"• {local_time.strftime('%H:%M')} → {rate:.2f} p/kWh")

        message = "\n".join(message_lines)
        send_telegram_alert(message)
    else:
        print("✅ No negative/zero rates today.")
else:
    print("❌ Could not retrieve Agile daily rates.")
