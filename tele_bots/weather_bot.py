import os
import sys
import logging
import time
from telebot import TeleBot

# --- Path setup ---
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
common_dir = os.path.join(base_dir, "common")

for path in (base_dir, common_dir):
    if path not in sys.path:
        sys.path.insert(0, path)

# --- Secrets ---
from _secrets import telegram_token

# --- Weather modules ---
from dans_weather_station import format_dans_weather_report_telegram
from adafruit_sync import format_adafruit_weather_report_telegram

# --- Logging ---
log_file = "/home/holly/weather_bot_log.txt"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Initialize bot ---
bot = TeleBot(telegram_token)

# --- Cache system ---
CACHE_TTL_SECONDS = 30 * 60  # 30 minutes
weather_cache = {
    "dans": {"timestamp": 0, "data": None},
    "adafruit": {"timestamp": 0, "data": None}
}

def get_cached_weather(source: str):
    """Return cached weather string or refresh if cache expired."""
    now = time.time()

    if source == "dans":
        cached = weather_cache["dans"]
        if now - cached["timestamp"] < CACHE_TTL_SECONDS:
            logging.info("Using cached Dan's weather report.")
            return cached["data"]
        else:
            logging.info("Refreshing Dan's weather report.")
            report = format_dans_weather_report_telegram()
            weather_cache["dans"] = {"timestamp": now, "data": report}
            return report

    elif source == "adafruit":
        cached = weather_cache["adafruit"]
        if now - cached["timestamp"] < CACHE_TTL_SECONDS:
            logging.info("Using cached Adafruit weather report.")
            return cached["data"]
        else:
            logging.info("Refreshing Adafruit weather report.")
            report = format_adafruit_weather_report_telegram()
            weather_cache["adafruit"] = {"timestamp": now, "data": report}
            return report

    else:
        logging.warning(f"Unknown weather source requested: {source}")
        return "_Weather source not recognized._"

# --- Handlers ---
@bot.message_handler(commands=["start", "help"])
def handle_help(message):
    bot.send_message(
        message.chat.id,
        "🌤️ Weather Bot Commands:\n"
        "/dans_weather \\- Dan’s MQTT Station\n"
        "/adafruit_weather \\- Adafruit IO Station\n"
        "/weather \\- Both Stations",
        parse_mode="MarkdownV2"
    )

@bot.message_handler(commands=["dans_weather"])
def handle_dans_weather(message):
    chat_id = message.chat.id
    report = get_cached_weather("dans")
    bot.send_message(chat_id, report, parse_mode="MarkdownV2")

@bot.message_handler(commands=["adafruit_weather"])
def handle_adafruit_weather(message):
    chat_id = message.chat.id
    report = get_cached_weather("adafruit")
    bot.send_message(chat_id, report, parse_mode="MarkdownV2")

@bot.message_handler(commands=["weather"])
def handle_weather(message):
    chat_id = message.chat.id
    report1 = get_cached_weather("dans")
    report2 = get_cached_weather("adafruit")
    full_report = f"{report1}\n\n{report2}"
    bot.send_message(chat_id, full_report, parse_mode="MarkdownV2")

# --- Run bot ---
if __name__ == "__main__":
    logging.info("🌐 Weather bot started")
    bot.infinity_polling()
