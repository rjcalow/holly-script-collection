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
current_rate_pkwh = get_octopus_agile_rate(GSP_GROUP_ID)

if current_rate_pkwh is not None:
    print(f"The current Octopus Agile rate is: {current_rate_pkwh:.2f} p/kWh")

    # Check if the price is negative (or zero for simplicity)
    if current_rate_pkwh <= 0:
        message = f"⚡️ *Negative Price Alert!* ⚡️\n\nThe current Octopus Agile rate is {current_rate_pkwh:.2f} p/kWh.\n\nTime to charge up your batteries or run your appliances for free!"
        send_telegram_alert(message)
    else:
        print("The current price is not negative.")
else:
    print("Could not retrieve the current rate.")