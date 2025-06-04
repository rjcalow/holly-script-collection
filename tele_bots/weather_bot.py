"""
Telegram Weather Bot
Fetches data from Dans Weather Station and creates a weather report.
"""

# Initialise the path (if path_setup is needed for dans_weather_station import)
import sys
import os
import time # For tracking call timestamps
from datetime import datetime, timedelta
import pytz # For timezone handling in timestamp formatting

# Add the directory containing dans_weather_station.py to sys.path if it's not in the same directory
# This assumes dans_weather_station.py is in the 'common' directory relative to this script's parent.
# Adjust if your structure is different.
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..')) 
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Keys and secrets
from _secrets import weather_bot_token

# Import your weather station data fetcher
# Make sure dans_weather_station.py is accessible via sys.path or in the same folder
try:
    from common.dans_weather_station import fetch_weather_station_data
except ImportError:
    # Fallback if 'common' prefix is not used in your path setup
    from dans_weather_station import fetch_weather_station_data

# Other imports
import telebot
import logging
import json # For pretty printing received data during debug

# --- Logging ---
log_file = "/home/holly/telegram_bot_error.log" # Dedicated log for the bot
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Initialize Bot ---
bot = telebot.TeleBot(weather_bot_token)
logging.info("Telegram Bot initialized.")

# --- Rate Limiting Configuration ---
MAX_CALLS_PER_WINDOW = 5
RESET_INTERVAL_MINUTES = 20
RESET_INTERVAL_SECONDS = RESET_INTERVAL_MINUTES * 60

# Dictionary to store user call timestamps and lockout status
# Structure: {chat_id: {'calls': [timestamp1, timestamp2, ...], 'locked_until': timestamp_datetime_object}}
user_call_tracker = {}
logging.info(f"Rate limiting configured: {MAX_CALLS_PER_WINDOW} calls per {RESET_INTERVAL_MINUTES} minutes.")

# --- Bot Commands ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Handles /start and /help commands."""
    welcome_text = (
        "Hello! I am your weather reporting bot.\n"
        "Send /weather to get the latest weather report from Dans Weather Station."
    )
    bot.reply_to(message, welcome_text)
    logging.info(f"Sent welcome message to {message.chat.id}")

@bot.message_handler(commands=['weather'])
def get_weather_report(message):
    """Handles the /weather command to fetch and report weather data."""
    chat_id = message.chat.id
    current_time = datetime.now() # Using datetime objects for lockout time

    # --- Rate Limiting Logic ---
    if chat_id not in user_call_tracker:
        user_call_tracker[chat_id] = {'calls': [], 'locked_until': None}

    user_data = user_call_tracker[chat_id]

    # 1. Check if currently locked out
    if user_data['locked_until'] and current_time < user_data['locked_until']:
        remaining_time = user_data['locked_until'] - current_time
        minutes, seconds = divmod(int(remaining_time.total_seconds()), 60)
        lockout_message = (
            f"You have made too many requests. Please try again in "
            f"{minutes} minutes and {seconds} seconds."
        )
        bot.send_message(chat_id, lockout_message)
        logging.warning(f"User {chat_id} is rate-limited. Locked until {user_data['locked_until']}")
        return

    # 2. Clean up old timestamps from the call list
    user_data['calls'] = [
        ts for ts in user_data['calls'] 
        if current_time - ts < timedelta(seconds=RESET_INTERVAL_SECONDS)
    ]

    # 3. Add current call timestamp
    user_data['calls'].append(current_time)

    # 4. Check if rate limit is exceeded after this call
    if len(user_data['calls']) > MAX_CALLS_PER_WINDOW:
        user_data['locked_until'] = current_time + timedelta(seconds=RESET_INTERVAL_SECONDS)
        remaining_time = user_data['locked_until'] - current_time
        minutes, seconds = divmod(int(remaining_time.total_seconds()), 60)
        lockout_message = (
            f"You have made too many requests ({MAX_CALLS_PER_WINDOW} calls in {RESET_INTERVAL_MINUTES} minutes). "
            f"You are temporarily locked out. Please try again in "
            f"{minutes} minutes and {seconds} seconds."
        )
        bot.send_message(chat_id, lockout_message)
        logging.warning(f"User {chat_id} hit rate limit. Locked until {user_data['locked_until']}")
        return
    # --- End Rate Limiting Logic ---

    logging.info(f"Received /weather command from {chat_id}. Calls in window: {len(user_data['calls'])}")
    bot.send_message(chat_id, "Fetching the latest weather data... please wait.")

    weather_data = fetch_weather_station_data(timeout=20) # Increased timeout for bot responsiveness

    if weather_data:
        logging.info(f"Successfully fetched weather data for {chat_id}.")
        # Optional: Log the raw data received for debugging purposes
        # logging.debug(f"Raw weather data: {json.dumps(weather_data, indent=2)}")

        report = format_weather_report(weather_data)
        bot.send_message(chat_id, report, parse_mode='Markdown')
    else:
        logging.error(f"Failed to fetch weather data for {chat_id}.")
        bot.send_message(chat_id, 
                         "Sorry, I couldn't retrieve the weather data at this time. "
                         "Please check the weather station's status or try again later.")

def format_weather_report(data):
    """
    Formats the raw weather data dictionary into a human-readable string.
    """
    if not data:
        return "No data available to generate a report."

    report_parts = ["*Dan's Weather Station Report*"]

    # Basic info
    nickname = data.get('nickname', 'N/A')
    model = data.get('model', 'N/A')
    uid = data.get('uid', 'N/A')
    timestamp_str = data.get('timestamp', 'N/A')

    report_parts.append(f"\n*Station:* {nickname} ({model})")
    if timestamp_str != 'N/A':
        try:
            dt_object = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            # Format for Worksop, England (BST/GMT)
            # Find the correct timezone string for your location
            # 'Europe/London' covers BST/GMT transitions
            local_tz = pytz.timezone('Europe/London')
            local_dt = dt_object.astimezone(local_tz)
            report_parts.append(f"*Last Updated:* {local_dt.strftime('%A, %d %B %Y %H:%M:%S %Z%z')}")
        except (ValueError, pytz.UnknownTimeZoneError) as e:
            logging.error(f"Failed to parse or localize timestamp '{timestamp_str}': {e}")
            report_parts.append(f"*Last Updated (UTC):* {timestamp_str}")
    else:
        report_parts.append(f"*Last Updated:* {timestamp_str}")


    # Readings
    readings = data.get('readings', {})
    report_parts.append("\n*Current Conditions:*")

    temp = readings.get('temperature')
    if temp is not None:
        report_parts.append(f"🌡️ Temperature: `{temp:.1f}°C`")

    humidity = readings.get('humidity')
    if humidity is not None:
        report_parts.append(f"💧 Humidity: `{humidity:.1f}%`")

    pressure = readings.get('pressure')
    if pressure is not None:
        report_parts.append(f"🌬️ Pressure: `{pressure:.2f} hPa`")

    wind_speed = readings.get('wind_speed')
    wind_direction = readings.get('wind_direction')
    if wind_speed is not None and wind_direction is not None:
        # Convert wind direction from degrees to cardinal direction
        cardinal_direction = get_cardinal_direction(wind_direction)
        report_parts.append(f"💨 Wind: `{wind_speed:.1f} m/s` from `{cardinal_direction} ({wind_direction}º)`")
    elif wind_speed is not None:
         report_parts.append(f"💨 Wind Speed: `{wind_speed:.1f} m/s`")
    elif wind_direction is not None:
         report_parts.append(f"💨 Wind Direction: `{wind_direction}º`")


    rain = readings.get('rain')
    if rain is not None:
        report_parts.append(f"☔ Total Rain: `{rain:.2f} mm`")

    rain_per_second = readings.get('rain_per_second')
    if rain_per_second is not None:
        report_parts.append(f"💦 Rain Rate: `{rain_per_second:.3f} mm/s`")

    luminance = readings.get('luminance')
    if luminance is not None:
        report_parts.append(f"💡 Luminance: `{luminance:.1f} lux`")

    return "\n".join(report_parts)

def get_cardinal_direction(degrees):
    """Converts degrees to a cardinal direction."""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    # Normalize degrees to 0-360
    degrees = degrees % 360
    # Each direction covers 22.5 degrees (360/16)
    # Add 11.25 to shift the boundaries so N is centered around 0
    index = int((degrees + 11.25) / 22.5) % 16
    return directions[index]

# --- Start the Bot ---
if __name__ == "__main__":
    logging.info("Starting Telegram Bot polling...")
    try:
        bot.polling(non_stop=True, interval=0, timeout=20) # Long polling timeout for better responsiveness
    except Exception as e:
        logging.critical(f"Telegram Bot crashed: {e}")