#aim is to check the days Octopus Agile rates for negative or zero prices and send an alert via Telegram

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


from common.octopus import get_octopus_agile_rate
from common.telegram_msg import send_telegram_alert

GSP_GROUP_ID = "B" 
# --- Main Logic ---
all_daily_rates = get_octopus_agile_daily_rates(GSP_GROUP_ID)

if all_daily_rates is not None:
    negative_rates = {}
    
    # Check for negative or zero rates
    for time, rate in all_daily_rates.items():
        if rate <= 0:
            negative_rates[time] = rate

    if negative_rates:
        message_parts = ["⚡️ *Negative/Free Price Alert!* ⚡️\n\nThe following time slots have a negative or zero price today:\n"]
        for time_str, rate in sorted(negative_rates.items()):
            # Convert the UTC time to a more readable format
            start_time_utc = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            local_time_str = start_time_utc.astimezone(pytz.timezone('Europe/London')).strftime("%H:%M")
            message_parts.append(f"• From {local_time_str}: {rate:.2f} p/kWh")

        message = "\n".join(message_parts)
        send_telegram_alert(message)
    else:
        print("No negative or zero rates found for the day.")
else:
    print("Could not retrieve daily rates.")