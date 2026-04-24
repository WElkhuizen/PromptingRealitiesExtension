settings = {
    "ssid": "<your-wifi-name>",           # WiFi network name
    "password": "<your-wifi-password>",   # WiFi password
    "mqtt_clientid": "<unique-device-id>",# Unique name for this device (e.g. "pico-logic-01")
    "broker": "<your-mqtt-broker>",       # MQTT broker host (e.g. "ide-education.cloud.shiftr.io")
    "mqtt_user": "<mqtt-username>",       # MQTT username
    "mqtt_password": "<mqtt-password>",   # MQTT password
    "mqtt_port": 1883,                    # MQTT port (use 8883 for TLS)
    "mqtt_topic": "<your-mqtt-topic>"     # Must match the topic set in the Prompting Realities webapp
}
