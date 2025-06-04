"""
Telegram Weather Bot
Fetches data from Dans Weather Station and creates a weather report.
"""

# Initialise the path (if path_setup is needed for dans_weather_station import)
import time # For tracking call timestamps
from datetime import datetime, timedelta
import pytz # For timezone handling in timestamp formatting


import sys
import os

# Get the absolute path to the directory containing holly.py
script_dir = os.path.dirname(os.path.abspath(__file__))
# script_dir will be: /home/holly/holly-script-collection/telebots

# Go up one level to 'holly-script-collection'
base_dir = os.path.dirname(script_dir)
# base_dir will be: /home/holly/holly-script-collection

# Construct the path to the 'common' directory
common_dir = os.path.join(base_dir, "common")

# Get the user's home directory
home_dir = os.path.expanduser("~")

# Add 'holly-script-collection' and the home directory to sys.path
# Adding at the beginning prioritizes these locations
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
if home_dir not in sys.path:"""
Telegram Weather Bot
Fetches data from Dan's Weather Station and sends a weather report.
"""

import sys
from pathlib import Path
import logging
from datetime import datetime, timedelta
import pytz
import json
import re
import argparse
import telebot

# --- Path Setup ---
script_dir = Path(__file__).resolve().parent
base_dir = script_dir.parent
common_dir = base_dir / "common"
home_dir = Path.home()

sys.path.insert(0, str(base_dir))
sys.path.insert(0, str(home_dir))

# --- Imports ---
from _secrets import weather_bot_token
from common.dans_weather_station import fetch_weather_station_data

# --- Logging ---
log_file = str(home_dir / "errorlog.txt")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Bot Initialization ---
bot = telebot.TeleBot(weather_bot_token)
logging.info("Telegram Bot initialized.")

# --- Rate Limiting ---
MAX_CALLS_PER_WINDOW = 5
RESET_INTERVAL_SECONDS = 20 * 60  # 20 minutes
user_call_tracker = {}

def check_rate_limit(chat_id):
    now = datetime.now()
    tracker = user_call_tracker.setdefault(chat_id, {'calls': [], 'locked_until': None})

    if tracker['locked_until'] and now < tracker['locked_until']:
        remaining = tracker['locked_until'] - now
        return False, f"⏳ Too many requests. Try again in {remaining.seconds // 60} min."

    tracker['calls'] = [ts for ts in tracker['calls'] if now - ts < timedelta(seconds=RESET_INTERVAL_SECONDS)]
    tracker['calls'].append(now)

    if len(tracker['calls']) > MAX_CALLS_PER_WINDOW:
        tracker['locked_until'] = now + timedelta(seconds=RESET_INTERVAL_SECONDS)
        return False, "🚫 Rate limit exceeded. Please try again later."

    return True, None

def escape_markdown(text):
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', str(text))

# --- Command Handlers ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message,
        "🌤️ *Welcome to the Weather Bot!*\nSend `/weather` to get the latest report.",
        parse_mode='MarkdownV2'
    )

@bot.message_handler(commands=['weather'])
def get_weather_report(message):
    chat_id = message.chat.id
    allowed, info = check_rate_limit(chat_id)

    if not allowed:
        bot.send_message(chat_id, escape_markdown(info), parse_mode='MarkdownV2')
        logging.warning(f"User {chat_id} is rate-limited: {info}")
        return

    bot.send_message(chat_id, "📡 Fetching weather data... please wait.")
    logging.info(f"Received /weather from {chat_id}")

    weather_data = fetch_weather_station_data(timeout=20)

    if weather_data:
        logging.info(f"Weather data fetched for {chat_id}")
        report = format_weather_report(weather_data)
        bot.send_message(chat_id, escape_markdown(report), parse_mode='MarkdownV2')
    else:
        logging.error(f"No weather data received for {chat_id}")
        bot.send_message(chat_id, escape_markdown(
            "⚠️ Sorry, I couldn't retrieve the weather data. Please try again later."
        ), parse_mode='MarkdownV2')

# --- Helpers ---

def format_weather_report(data):
    if not data:
        return "No data to report."

    report = ["*📋 Dan's Weather Station Report*"]

    nickname = data.get('nickname', 'N/A')
    model = data.get('model', 'N/A')
    uid = data.get('uid', 'N/A')
    timestamp_str = data.get('timestamp', 'N/A')

    report.append(f"\n📡 Station: {nickname} ({model})")
    report.append(f"🆔 UID: {uid}")

    if timestamp_str != 'N/A':
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            local_dt = dt.astimezone(pytz.timezone('Europe/London'))
            report.append(f"🕒 Last Updated: {local_dt.strftime('%A, %d %B %Y %H:%M:%S %Z')}")
        except Exception as e:
            logging.error(f"Timestamp parse failed: {e}")
            report.append(f"🕒 Last Updated (UTC): {timestamp_str}")

    readings = data.get('readings', {})
    report.append("\n🌦️ *Current Conditions:*")

    if (temp := readings.get('temperature')) is not None:
        report.append(f"🌡️ Temperature: `{temp:.1f}°C`")

    if (humidity := readings.get('humidity')) is not None:
        report.append(f"💧 Humidity: `{humidity:.1f}%`")

    if (pressure := readings.get('pressure')) is not None:
        report.append(f"🌬️ Pressure: `{pressure:.2f} hPa`")

    wind_speed = readings.get('wind_speed')
    wind_dir = readings.get('wind_direction')
    if wind_speed is not None and wind_dir is not None:
        dir_cardinal = get_cardinal_direction(wind_dir)
        report.append(f"💨 Wind: `{wind_speed:.1f} m/s` from `{dir_cardinal} ({wind_dir}°)`")
    elif wind_speed is not None:
        report.append(f"💨 Wind Speed: `{wind_speed:.1f} m/s`")

    if (rain := readings.get('rain')) is not None:
        report.append(f"☔ Total Rain: `{rain:.2f} mm`")

    if (rain_rate := readings.get('rain_per_second')) is not None:
        report.append(f"💦 Rain Rate: `{rain_rate:.3f} mm/s`")

    if (lux := readings.get('luminance')) is not None:
        report.append(f"💡 Luminance: `{lux:.1f} lux`")

    return "\n".join(report)

def get_cardinal_direction(degrees):
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    degrees %= 360
    return directions[int((degrees + 11.25) / 22.5) % 16]

# --- Entry Point ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help="Run in test mode (no bot)")
    args = parser.parse_args()

    if args.test:
        data = fetch_weather_station_data()
        print(json.dumps(data, indent=2) if data else "No data received.")
    else:
        logging.info("Bot polling started.")
        try:
            bot.polling(non_stop=True, interval=0, timeout=20)
        except Exception as e:
            logging.critical(f"Bot crashed: {e}")

    sys.path.insert(0, home_dir)

# Keys and secrets
from _secrets import weather_bot_token

# Import your weather station data fetcher
# Make sure dans_weather_station.py is accessible via sys.path or in the same folder

from common.dans_weather_station import fetch_weather_station_data

# Other imports
import telebot
import logging
import json # For pretty printing received data during debug

# --- Logging ---
log_file = "/home/holly/errorlog.txt" # Dedicated log for the bot
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