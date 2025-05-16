'''

Dans Weather Station
contect to the MQTT broker and fetch the weather station data

'''
#initialise the path
import path_setup

#keys and secrets
from _secrets import (
    dans_weather_station_address,
    dans_weather_station_username,
    dans_weather_station_password,
    dans_weather_station_topic1,
    dans_weather_station_topic2)

#other imports
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import time
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

    def on_connect(client, userdata, flags, rc):
        logging.info("Connected to MQTT Broker")

    def on_message(client, userdata, msg):
        nonlocal data
        try:
            data = json.loads(msg.payload.decode('utf-8'))
            data_received.set()
        except Exception as e:
            logging.error(f"Error decoding message: {e}")

    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(dans_weather_station_username, dans_weather_station_password)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(dans_weather_station_address, 1883, 60)
        topics = [dans_weather_station_topic1, dans_weather_station_topic2]
        for topic in topics:
            mqtt_client.subscribe(topic)
        
        mqtt_client.loop_start()

        if not data_received.wait(timeout=timeout):
            logging.warning("Timeout: No data received from the weather station.")
            return {}

    except Exception as e:
        logging.error(f"Failed to connect to MQTT broker: {e}")
        return {}

    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

    return data

#for testing
data = fetch_weather_station_data()
print(data)