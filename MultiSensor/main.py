import micropython            # Needed to run any MicroPython code
import sys                    # Using sys to print Exception reasons
import time                   # Allows use of time.sleep() for delays
import math                   # Using math for calculations
import config                 # Contain all keys used here
import wifiConnection         # Contains functions to connect/disconnect from WiFi 
import ujson                  # Creating JSON object for MQTT & Telegraf
import gc                     # Garbage collector to free up memory
from mqtt import MQTTClient   # For use of MQTT protocol to talk to Adafruit IO
from machine import I2C, Pin, ADC # Interfaces with hardware components
from dht11 import DHT11       # Importing DHT11 sensor library
from I2C_LCD import I2CLcd    # Importing I2C LCD library

photoresistor_adc = ADC(27)
thermistor_adc = ADC(26)
dht11_pin = Pin(5, Pin.OUT, Pin.PULL_DOWN)  # Pin for DHT11 sensor
dht11_sensor = DHT11(dht11_pin)  # Initialize DHT11 sensor

i2c = I2C(1,  sda=Pin(14), scl=Pin(15), freq=400000)  # Initialize I2C for LCD display
devices = i2c.scan()  # Scan for I2C devices
lcd = I2CLcd(i2c, devices[0], 2, 16)  # Initialize LCD display
time.sleep(1) # Wait for LCD to initialize

humidity = 0  # Initialize humidity variable
temp = 0  # Initialize temperature variable
light = 0  # Initialize light variable

# Build json format for MQTT 
def build_json(variable_1, value_1):
    try:
        data = {variable_1: value_1}
        retValue = ujson.dumps(data)
        return retValue
    except:
        return None

# Send message to MQTT server
def send_topic(topicObject, topicName):
    print(topicObject)
    try:
        client.publish(topic=topicName, msg=topicObject)
        print("DONE")
    except Exception as e:
        print("FAILED")
        # We must add error hadling here if WiFi being unavailable here

def exceptionHandler(e):
    if e is KeyboardInterrupt:
        print("Keyboard interrupt")
    else:
        print("MQTT Broker does not work or WiFi issues")
        print("Exception: ", e)

def calc_temp(temp_adc):
    # Convert ADC value to temperature in Celsius
    adc_value = temp_adc.read_u16()  # Read the ADC value (0-65535)
    volt = (adc_value / 65535) * 3.3 # Convert ADC value to voltage (0-3.3V)
    Rt = 10 * volt / (3.3 - volt) # Calculate resistance of thermistor
    # Calculate temperature in Kelvin using Steinhart-Hart equation
    tempK = (1 / (1 / (273.15+25) + (math.log(Rt/10)/3950))) 
    tempC = tempK - 273.15 # Convert Kelvin to Celsius
    tempC = round(tempC, 1)  # Round to 1 decimal place
    return tempC

def calc_light(light_adc):
    # Convert ADC value to light level (0-65535)
    adc_value = light_adc.read_u16()  # Read the ADC value (0-65535)
    light_percent = 100 - (adc_value / 65535) * 100  # Convert to percentage (0-100%)
    light_percent = round(light_percent, 1)  # Round to 1 decimal place
    return light_percent

def lcd_display(temp, light, humidity):
    # Display temperature, light, and humidity on the LCD
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("T:{}C".format(temp))
    lcd.move_to(0, 1)
    lcd.putstr("L:{}%".format(light))
    lcd.move_to(8, 1)
    lcd.putstr("H:{}%".format(humidity))

lastMQTTSend = time.time()  # Initialize last send time
lastLCDUpdate = time.time()  # Initialize last LCD update time
lastDHT11Measure = time.time()  # Initialize last DHT11 measure time
lastGC = time.time()  # Initialize last garbage collection time

# WiFi Connection
try:
    ip = wifiConnection.connect()
except KeyboardInterrupt:
    print("Keyboard interrupt")

# Connecting to MQTT server
try:
    client = MQTTClient(client_id=config.MQTT_CLIENT_ID, server=config.MQTT_SERVER, port=config.MQTT_PORT, user=config.MQTT_USER, password=config.MQTT_KEY)
    time.sleep(0.1)
    client.connect()
    print("Connected to %s" % (config.MQTT_SERVER))
except Exception as error:
    sys.print_exception(error, sys.stderr)
    print("Could not establish MQTT connection.")
    wifiConnection.disconnect()
    print("Disconnected from WiFi.")

while True:
    try:
        currentTime = time.time()
        
        light = calc_light(photoresistor_adc)
        temp = calc_temp(thermistor_adc)
        
        # Measure DHT11 sensor every 3 seconds to be safe
        if currentTime - lastDHT11Measure >= 3:
            try:
                dht11_sensor.measure()  # Trigger DHT11 measurement
                new_humidity = dht11_sensor.humidity
            except Exception as e:
                new_humidity = humidity  # Keep the last known humidity value
                print("DHT11 measurement failed:", e)
            humidity = new_humidity
            lastDHT11Measure = currentTime
        
        if currentTime - lastMQTTSend >= 10:
            # Send data on MQTT every 10 seconds
            tempObj = build_json("temperature", temp)
            lightObj = build_json("light", light)
            humidityObj = build_json("humidity", humidity)
        
            send_topic(tempObj, config.MQTT_TEMPERATURE_FEED)
            send_topic(lightObj, config.MQTT_BRIGHTNESS_FEED)
            send_topic(humidityObj, config.MQTT_HUMIDITY_FEED)
            lastMQTTSend = currentTime
        # Update LCD display every 1 second
        if currentTime - lastLCDUpdate >= 1:
            lcd_display(temp, light, humidity)
            lastLCDUpdate = currentTime
        # Run garbage collection every 60 seconds to avoid memory leaks
        if currentTime - lastGC >= 60:
            gc.collect()
            lastGC = currentTime
        time.sleep(0.2)  # Sleep for 200 milliseconds to avoid busy-waiting
    except Exception as e:
        exceptionHandler(e)