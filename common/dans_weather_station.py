"""
Dans Weather Station
Connect to the MQTT broker and fetch the weather station data
"""

import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
common_dir = os.path.join(base_dir, "common")
home_dir = os.path.expanduser("~")

# Add paths to sys.path
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
if home_dir not in sys.path:
    sys.path.insert(0, home_dir)


# Keys and secrets
from _secrets import (
    dans_weather_station_address,
    dans_weather_station_username,
    dans_weather_station_password,
    dans_weather_station_topic1,
    dans_weather_station_topic2)

# Other imports
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion # Correctly imported now
import json
import threading
import logging
import re
from datetime import datetime

# --- Logging ---
log_file = "/home/holly/errorlog.txt"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def fetch_weather_station_data(timeout=10):
    """
    Fetches weather station data from the MQTT broker.

    Args:
        timeout: The maximum time (in seconds) to wait for data.

    Returns:
        The weather station data as a dictionary, or an empty dictionary if no data is received.
    """
    data = None
    data_received = threading.Event()

    # --- Callback using API v5 ---
    # Note: For CallbackAPIVersion.VERSION2 (or 5), the on_connect signature includes 'properties'
    def on_connect(client, userdata, flags, reasonCode, properties):
        # The reasonCode here is an integer (0 for success when using CallbackAPIVersion.VERSION2)
        if reasonCode == 0: # <-- CORRECTED THIS LINE
            logging.info("Connected to MQTT Broker successfully.")
            client.subscribe(dans_weather_station_topic1)
            client.subscribe(dans_weather_station_topic2)
        else:
            logging.error(f"Failed to connect to MQTT broker. Reason code: {reasonCode}")
            # Ensure the event is set on connection failure too, to unblock wait()
            data_received.set()

    def on_message(client, userdata, msg):
        nonlocal data
        try:
            decoded = msg.payload.decode("utf-8")
            data = json.loads(decoded)
            logging.info(f"Received data from topic {msg.topic}: {decoded}")
            data_received.set()
        except Exception as e:
            logging.error(f"Failed to decode MQTT message: {e}")

    # --- MQTT client setup ---
    mqtt_client = mqtt.Client(
        client_id="",
        protocol=mqtt.MQTTv311,
        transport="tcp",
        callback_api_version=CallbackAPIVersion.VERSION2 # Using the enum member now
    )
    mqtt_client.username_pw_set(dans_weather_station_username, dans_weather_station_password)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        logging.info(f"Attempting to connect to {dans_weather_station_address}")
        mqtt_client.connect(dans_weather_station_address, port=1883, keepalive=60)
        mqtt_client.loop_start()

        logging.info(f"Waiting for data (timeout: {timeout}s)...")
        if not data_received.wait(timeout=timeout):
            logging.warning("Timeout waiting for MQTT message.")
            return {}
        else:
             # If data_received was set, data variable should hold the received data
             if data is None:
                  logging.warning("Data received event set, but no data was assigned.")
                  return {}

    except Exception as e:
        logging.error(f"MQTT connection error: {e}")
        return {}

    finally:
        logging.info("Stopping MQTT loop and disconnecting.")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        logging.info("MQTT client disconnected.")

    return data




def escape_telegram(text):
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', str(text))

def format_dans_weather_report_telegram(data=None, tz="UTC"):
    """
    Formats Dan's Weather Station data into a Telegram MarkdownV2 string.

    Args:
        data (dict, optional): The weather data dictionary. If None, fetches it.
        tz (str): Timezone string for local time formatting (currently unused).

    Returns:
        str: MarkdownV2-formatted weather report string.
    """
    if data is None:
        data = fetch_weather_station_data()

    if not data:
        return escape_telegram("⚠️ No data received from Dan's Weather Station.")

    lines = ["*🌦️ Dan's Weather Station*"]

    # Extract and format values
    temperature = data.get("temperature_c")
    humidity = data.get("humidity")
    pressure = data.get("pressure")
    wind_speed = data.get("wind_speed")
    wind_direction = data.get("wind_direction")
    rainfall = data.get("rainfall")
    timestamp = data.get("timestamp")

    def safe_line(label, value, unit=""):
        if value is not None:
            return f"{label}: `{value} {unit}`".strip()
        return None

    lines.append(safe_line("🌡️ Temperature", temperature, "°C"))
    lines.append(safe_line("💧 Humidity", humidity, "%"))
    lines.append(safe_line("🌬️ Pressure", pressure, "hPa"))
    lines.append(safe_line("🍃 Wind Speed", wind_speed, "m/s"))
    lines.append(safe_line("🧭 Wind Dir", wind_direction, "°"))
    lines.append(safe_line("🌧️ Rainfall", rainfall, "mm"))

    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp)
            lines.append(f"_Last updated at {dt.strftime('%H\\:%M')} UTC_")
        except Exception:
            pass

    return "\n".join(escape_telegram(line) for line in lines if line)




# --- For testing ---
if __name__ == "__main__":
    logging.info("--- Starting weather data fetch test ---")
    result = fetch_weather_station_data()
    print(json.dumps(result, indent=2) if result else "No data received.")
    logging.info("--- Test finished ---")