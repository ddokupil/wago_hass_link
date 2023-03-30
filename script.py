import argparse
import requests
import xml.etree.ElementTree as ET

url = 'http://192.168.1.2/PLC/webvisu.htm'
response = ""
prev_response = ""
parser = argparse.ArgumentParser()
parser.add_argument('xml_file', help='path to the XML file')
args = parser.parse_args()

# Parse XML file
tree = ET.parse(args.xml_file)
root = tree.getroot()

# Initialize variables dictionary
variables = {}

# Parse variables from XML
for variable in root.findall('variablelist/variable'):
    name = variable.get('name')
    value = variable.text.strip()
    variables[name] = value

# Define the protocol
payload = f"|0|{len(variables)}|"

# Iterate over the variables and add them to the protocol
counter = 0
for name, value in variables.items():
    address_h, address_l, num_bytes, var_type = value.split(',')
    payload += f"{counter}|{address_h}|{address_l}|{num_bytes}|{var_type}|"
    counter += int(num_bytes)

# Do it once to initialize the previous response
prev_response = requests.post(url, data=payload)

while True:
    # Make the request
    response = requests.post(url, data=payload)
    # Check if the response is different from the previous one
    if response.content != prev_response.content:
        print("Raw response: ", response.content)
        prev_response = response

