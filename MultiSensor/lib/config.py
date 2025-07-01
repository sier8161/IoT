# Wireless network
WIFI_SSID = 'YOUR_WIFI_SSID' # replace with your WiFi SSID
WIFI_PASS = 'YOUR_WIFI_PASSWORD' # replace with your WiFi password

# MQTT server's configuration
MQTT_SERVER = "YOUR_LOCAL_IP_ADDRESS"  # replace with local IP address of your machine running mosquitto
#MQTT_PORT = 8883
MQTT_PORT = 1883
MQTT_USER = "YOUR_USER" # replace with your mosquitto username
MQTT_KEY = "YOUR_PASSWORD" # replace with your mosquitto password
MQTT_CLIENT_ID = "id-123" # can be set to anything starting with "id-"
MQTT_TEMPERATURE_FEED = "devices/temp"
MQTT_HUMIDITY_FEED = "devices/hum"
MQTT_BRIGHTNESS_FEED = "devices/light"
