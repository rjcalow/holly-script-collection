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
import pytz
import uuid


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

    def on_connect(client, userdata, flags, reasonCode, properties):
        if reasonCode == 0:
            logging.info("Connected to MQTT Broker successfully.")
            client.subscribe(dans_weather_station_topic1)
            client.subscribe(dans_weather_station_topic2)
        else:
            logging.error(f"Failed to connect to MQTT broker. Reason code: {reasonCode}")
            data_received.set()

    def on_message(client, userdata, msg):
        nonlocal data
        try:
            # Ignore retained messages
            if msg.retain:
                logging.info(f"Ignoring retained message from topic {msg.topic}")
                return
            decoded = msg.payload.decode("utf-8")
            data = json.loads(decoded)
            logging.info(f"Received data from topic {msg.topic}: {decoded}")
            data_received.set()
        except Exception as e:
            logging.error(f"Failed to decode MQTT message: {e}")

    # --- MQTT client setup ---
    mqtt_client = mqtt.Client(
        client_id=str(uuid.uuid4()),
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


from datetime import datetime

def dans_weather_station_html():
    """
    Formats Dan's Weather Station data into HTML for Telegram.

    Args:
        data (dict, optional): The weather data dictionary. If None, fetches it.

    Returns:
        str: HTML-formatted weather report string.
    """

    data = fetch_weather_station_data() 

    if not data:
        return "<i>⚠️ No data received from Dan's Weather Station.</i>"

    readings = data.get("readings", {})
    if not readings:
        return "<i>⚠️ No 'readings' data found.</i>"

    lines = ["<b>🌦️ Dan's Weather Station</b>"]

    def safe_line(label, value, unit=""):
        if value is not None:
            return f"{label}: <code>{value} {unit}</code>"
        return None

    # Build lines
    lines.append(safe_line("🌡️ Temperature", readings.get("temperature"), "°C"))
    lines.append(safe_line("💧 Humidity", readings.get("humidity"), "%"))
    lines.append(safe_line("🌬️ Pressure", readings.get("pressure"), "hPa"))
    lines.append(safe_line("🍃 Wind Speed", readings.get("wind_speed"), "m/s"))
    lines.append(safe_line("🧭 Wind Dir", readings.get("wind_direction"), "°"))
    lines.append(safe_line("🌧️ Rainfall", readings.get("rain"), "mm"))
    lines.append(safe_line("💡 Luminance", readings.get("luminance"), "lux"))

    timestamp = data.get("timestamp")
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            gmt_dt = dt.astimezone(pytz.timezone("GMT"))
            lines.append(f"<i>Last updated at {gmt_dt.strftime('%H:%M')} GMT</i>")
        except Exception as e:
            logging.error(f"Failed to parse timestamp: {e}")

    return "\n".join(line for line in lines if line)



# --- For testing ---
if __name__ == "__main__":
    logging.info("--- Starting weather data fetch test ---")
    result = fetch_weather_station_data()
    print(json.dumps(result, indent=2) if result else "No data received.")
    logging.info("--- Test finished ---")