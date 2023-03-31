#!/usr/bin/python3

import argparse
import requests
import xml.etree.ElementTree as ET
from ftplib import FTP
import sys
from io import BytesIO
from collections import OrderedDict

response = ""
prev_response = ""
parser = argparse.ArgumentParser()

# Define arguments for FTP download
parser.add_argument('--host', help='Wago address', default='192.168.1.2')
parser.add_argument('--user', help='FTP server username', default='user')
parser.add_argument('--password', help='FTP server password', default='user')
parser.add_argument('--file', help='File path on FTP server', default='/PLC/plc_visu.xml')
args = parser.parse_args()

endpoint = f"http://{args.host}/PLC/webvisu.htm"

# Fetch the XML file from FTP
ftp = FTP(args.host)
try:
    ftp.login(args.user, args.password)
    with BytesIO() as file_bytes:
        ftp.retrbinary('RETR ' + args.file, file_bytes.write)
        file_content = file_bytes.getvalue()

    ftp.quit()
except Exception as e:
    print("Failed to download file from FTP:", e)
    ftp.quit()

# Parse XML file
tree = ET.ElementTree(ET.fromstring(file_content.decode('latin-1')))
root = tree.getroot()

# Initialize variables dictionary
variables = OrderedDict()

# Parse variables from XML
for variable in root.findall('variablelist/variable'):
    name = variable.get('name')
    value = variable.text.strip()
    variables[name] = value

# Print out the variables as they are in xml file
for i in range(len(variables)):
    key, value = list(variables.items())[i]
    print(f"{key} is {value}")

# Define the payload header
payload = f"|0|{len(variables)}|"

# Iterate over the variables and add them to the payload
counter = 0
for name, value in variables.items():
    address_h, address_l, num_bytes, var_type = value.split(',')
    payload += f"{counter}|{address_h}|{address_l}|{num_bytes}|{var_type}|"
    counter += int(num_bytes)

# Do for the first time to initialize the previous response
prev_response = requests.post(endpoint, data=payload)

# And now do it in an endless loop
try:
    while True:
        # Make the request
        response = requests.post(endpoint, data=payload)
        # Check if the response is different from the previous one
        if response.content != prev_response.content:
            prev_values = [int(value) for value in prev_response.content.decode().split("|")[1:-1]]
            values = [int(value) for value in response.content.decode().split("|")[1:-1]]
            # Check which variables have changed and print their names and new values
            for i, value in enumerate(values):
                if value != prev_values[i]:
                    name = list(variables.keys())[i]
                    print(f"{name} changed to {value}")
                    prev_values[i] = value
            prev_response = response
except KeyboardInterrupt:
    sys.exit()
