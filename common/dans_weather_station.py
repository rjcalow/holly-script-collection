"""
Dans Weather Station
Connect to the MQTT broker and fetch the weather station data
"""

# Initialise the path
import path_setup

# Keys and secrets
from _secrets import (
    dans_weather_station_address,
    dans_weather_station_username,
    dans_weather_station_password,
    dans_weather_station_topic1,
    dans_weather_station_topic2)

# Other imports
import paho.mqtt.client as mqtt
import json
import threading
import logging

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
    def on_connect(client, userdata, flags, reasonCode, properties):
        if reasonCode == mqtt.ReasonCodes.SUCCESS:
            logging.info("Connected to MQTT Broker successfully.")
            client.subscribe(dans_weather_station_topic1)
            client.subscribe(dans_weather_station_topic2)
        else:
            logging.error(f"Failed to connect to MQTT broker. Reason code: {reasonCode}")

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
        callback_api_version=5  # <- This silences the deprecation warning
    )
    mqtt_client.username_pw_set(dans_weather_station_username, dans_weather_station_password)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(dans_weather_station_address, port=1883, keepalive=60)
        mqtt_client.loop_start()

        if not data_received.wait(timeout=timeout):
            logging.warning("Timeout waiting for MQTT message.")
            return {}

    except Exception as e:
        logging.error(f"MQTT connection error: {e}")
        return {}

    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

    return data

# --- For testing ---
if __name__ == "__main__":
    result = fetch_weather_station_data()
    print(json.dumps(result, indent=2) if result else "No data received.")
