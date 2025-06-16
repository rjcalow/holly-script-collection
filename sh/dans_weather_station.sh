#!/bin/bash
#bash attempt at getting dans weather station

# --- Source the secrets file ---
# This loads all variables (MQTT_BROKER, MQTT_USERNAME, etc.) from weather_secrets.sh
SECRETS_FILE="/home/holly/.secrets/secrets.sh"

if [ -f "$SECRETS_FILE" ]; then
    . "$SECRETS_FILE" # The '.' command (or 'source') reads and executes commands from the file.
else
    # If the secrets file is missing, print an error to stdout (for the calling Python script)
    # and also to stderr (for system logs/debugging).
    ERROR_MESSAGE="<i>⚠️ Error: Weather bot setup failed. Secrets file not found at $SECRETS_FILE.</i>"
    echo "$ERROR_MESSAGE"
    echo "$(date): $ERROR_MESSAGE" >&2
    exit 1
fi

# --- Main Logic ---

# Log initiation to stderr, so stdout remains clean for the HTML output.
echo "$(date): Attempting to fetch Dan's weather data from MQTT topic: $MQTT_TOPIC" >&2

# Use mosquitto_sub to get ONE message (-C 1) from the specified topic.
# This will typically be the last RETAINED message.
# '2>/dev/null' suppresses mosquitto_sub's connection messages from stderr.
MQTT_PAYLOAD=$(mosquitto_sub \
    -h "$MQTT_BROKER" \
    -u "$MQTT_USERNAME" \
    -P "$MQTT_PASSWORD" \
    -t "$MQTT_TOPIC" \
    -C 1 \
    2>/dev/null)

# Check if any payload was received.
if [ -z "$MQTT_PAYLOAD" ]; then
    ERROR_MESSAGE="<i>⚠️ No data received from Dan's Weather Station (topic: $MQTT_TOPIC).</i>"
    echo "$ERROR_MESSAGE" # Output error to stdout for the calling Python bot
    echo "$(date): Error: No data received from MQTT broker for Dan's Weather Station (topic: $MQTT_TOPIC)." >&2
    exit 1 # Exit with error code
fi

# Log the raw payload to stderr for debugging.
echo "$(date): Raw MQTT Payload received:" >&2
echo "$MQTT_PAYLOAD" | jq . >&2 # Pretty-print JSON to stderr

# --- Extract data using jq ---
# Using 'jq -r' for raw output (no quotes).
# Using '// "N/A"' to provide a default value if a key is missing.
TEMPERATURE=$(echo "$MQTT_PAYLOAD" | jq -r '.readings.temperature // "N/A"')
HUMIDITY=$(echo "$MQTT_PAYLOAD" | jq -r '.readings.humidity // "N/A"')
PRESSURE=$(echo "$MQTT_PAYLOAD" | jq -r '.readings.pressure // "N/A"')
WIND_SPEED=$(echo "$MQTT_PAYLOAD" | jq -r '.readings.wind_speed // "N/A"')
WIND_DIRECTION=$(echo "$MQTT_PAYLOAD" | jq -r '.readings.wind_direction // "N/A"')
RAINFALL=$(echo "$MQTT_PAYLOAD" | jq -r '.readings.rain // "N/A"')
LUMINANCE=$(echo "$MQTT_PAYLOAD" | jq -r '.readings.luminance // "N/A"')
TIMESTAMP_RAW=$(echo "$MQTT_PAYLOAD" | jq -r '.timestamp // .readings.timestamp // "N/A"')

# --- Format Timestamp ---
FORMATTED_TIMESTAMP="N/A"
if [ "$TIMESTAMP_RAW" != "N/A" ]; then
    # Check for 'Z' (UTC indicator) and format accordingly.
    if [[ "$TIMESTAMP_RAW" == *Z ]]; then
        FORMATTED_TIMESTAMP=$(date -u -d "$TIMESTAMP_RAW" "+%H:%M GMT" 2>/dev/null)
    else
        FORMATTED_TIMESTAMP=$(date -d "$TIMESTAMP_RAW" "+%H:%M GMT" 2>/dev/null)
    fi

    # Fallback if date conversion fails.
    if [ -z "$FORMATTED_TIMESTAMP" ]; then
        FORMATTED_TIMESTAMP="$TIMESTAMP_RAW (parsing error)"
    fi
fi

# --- Construct HTML Message ---
# The 'cat << EOF ... EOF' syntax (HEREDOC) allows for multi-line strings.
# THIS IS THE ONLY THING PRINTED TO STDOUT, so the Python bot can capture it.
cat << EOF
