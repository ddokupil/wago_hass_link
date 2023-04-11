#!/usr/bin/python3

import argparse
import requests
import xml.etree.ElementTree as ET
from ftplib import FTP
import sys
from io import BytesIO
from collections import OrderedDict
import json
import paho.mqtt.publish as publish
import paho.mqtt.client as client
import logging
import logging.handlers
import time

# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

# Define a log format
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Define a rotating file handler with a max size of 10MB
file_handler = logging.handlers.RotatingFileHandler('log.txt', maxBytes=10_000_000, backupCount=1)
file_handler.setFormatter(log_formatter)

# Define a stream handler to print logs to stdout
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

response = ""
prev_response = ""
parser = argparse.ArgumentParser()

iteration = 0

# Define arguments for FTP download
parser.add_argument('-H', '--host', help='Wago address', default='192.168.1.2')
parser.add_argument('-u', '--user', help='FTP server username', default='user')
parser.add_argument('-p', '--password', help='FTP server password', default='user')
parser.add_argument('-f', '--file', help='File path on FTP server', default='/PLC/plc_visu.xml')
parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase output verbosity (e.g., -v, -vv, -vvv)')
parser.add_argument('-s', '--service', action='count', help='Whenn connection problem occurs wait 60 seconds before exiting.', default=0)
args = parser.parse_args()

# Configure logging level based on verbose flag
if args.verbose == 1:
    logging.basicConfig(level=logging.INFO)
elif args.verbose == 2:
    logging.basicConfig(level=logging.DEBUG)
elif args.verbose >= 3:
    logging.basicConfig(level=logging.NOTSET)

endpoint = f"http://{args.host}/PLC/webvisu.htm"

# Define MQTT server parameters
MQTT_SERVER = "192.168.1.4"
MQTT_USERNAME = "user"
MQTT_PASSWORD = "passwd"
MQTT_PORT = 1883
MQTT_PUBL = "wago/bridge"
MQTT_SUBS = 'homeassistant/status'

def on_connect(client, userdata, flags, rc):
    logger.debug(f"Connected with result code {rc}")
    client.subscribe(MQTT_SUBS)

def on_message(client, userdata, msg):
    if msg.payload.decode() == 'online':
        global iteration 
        iteration = 0
        logger.debug(f"Home Assistant has started via MQTT!")

mqtt_client = client.Client()
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(MQTT_SERVER, MQTT_PORT)

mqtt_client.loop_start()

# Fetch the XML file from FTP
ftp = FTP(args.host)
try:
    ftp.login(args.user, args.password)
    with BytesIO() as file_bytes:
        ftp.retrbinary('RETR ' + args.file, file_bytes.write)
        file_content = file_bytes.getvalue()

    ftp.quit()
except Exception as e:
    logger.error("Failed to download file from FTP: %s", e)
    ftp.quit()
    if args.service >= 1:
        logger.debug(f"Will retry from scratch in a minute.")
        time.sleep(60)
    sys.exit()

# Parse XML file
tree = ET.ElementTree(ET.fromstring(file_content.decode('latin-1')))
root = tree.getroot()

# Initialize variables dictionary
variables = OrderedDict()

# Parse variables from XML
for variable in root.findall('variablelist/variable'):
    name = variable.get('name')
    name = name.lstrip(".")
    value = variable.text.strip()
    variables[name] = value

# Print out the variables as they are in xml file
for i in range(len(variables)):
    key, value = list(variables.items())[i]
    logger.debug(f"{key} is {value}")

# Define the payload header
payload = f"|0|{len(variables)}|"

# Iterate over the variables and add them to the payload
counter = 0
for name, value in variables.items():
    address_h, address_l, num_bytes, var_type = value.split(',')
    payload += f"{counter}|{address_h}|{address_l}|{num_bytes}|{var_type}|"
    counter += int(num_bytes)

# And now do it in an endless loop
try:
    while True:
        try:
            # Make the request
            response = requests.post(endpoint, data=payload)
            # Check if the response is different from the previous one
        except Exception as e:
            logger.error(f"An error occurred while making the request: {e}")
            if args.service >= 1:
                logger.debug(f"Will retry from scratch in a minute.")
                time.sleep(60)
            sys.exit()
        # For the first time let's say prev_response is the same as response
        if iteration == 0:
            prev_response = response
        # parse everything if ran for the first time or got different response
        if response.content != prev_response.content or iteration == 0:
            prev_values = [int(value) for value in prev_response.content.decode().split("|")[1:-1]]
            values = [int(value) for value in response.content.decode().split("|")[1:-1]]
            # Check which variables have changed and create a dictionary with their names and new values
            changes = {}
            for i, value in enumerate(values):
                # For the first time do it all
                if value != prev_values[i] or iteration == 0:
                    # if value == 1:
                    #     value = "on"
                    # else: value = "off"
                    name = list(variables.keys())[i]
                    changes[name] = value
                    prev_values[i] = value
            # Convert the dictionary to a JSON string
            json_payload = json.dumps(changes)
            # Publish the JSON payload to the MQTT server
            logger.debug(f"Payload: \n{json_payload}")
            try:
                publish.single(MQTT_PUBL, payload=json_payload, qos=0, retain=False, hostname=MQTT_SERVER, auth={'username':MQTT_USERNAME, 'password':MQTT_PASSWORD})
            except Exception as e:    
                logger.error(f"Error publishing to MQTT: {e}")
                if args.service >= 1:
                    logger.debug(f"Will retry from scratch in a minute.")
                    time.sleep(60)
                sys.exit()
            prev_response = response
        # If hit 10000 iterations reset the counter, if not increment
        if iteration == 10000:
            iteration = 0
        else: iteration = iteration + 1
except KeyboardInterrupt:
    sys.exit()
