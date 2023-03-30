import argparse
import requests
import xml.etree.ElementTree as ET
from ftplib import FTP

response = ""
prev_response = ""
parser = argparse.ArgumentParser()

# Remove the argument for the XML file path

# Define arguments for FTP download
parser.add_argument('--host', help='Wago address', default='192.168.1.2')
parser.add_argument('--user', help='FTP server username', default='user')
parser.add_argument('--password', help='FTP server password', default='user')
parser.add_argument('--file', help='File path on FTP server', default='/PLC/plc_visu.xml')
args = parser.parse_args()

endpoint = f"http://{args.host}/PLC/webvisu.htm"

# Download the XML file from FTP
ftp = FTP(args.host)
ftp.login(args.user, args.password)

try:
    with open('plc_visu.xml', 'wb') as f:
        ftp.retrbinary('RETR ' + args.file, f.write)
    ftp.quit()
    print("File downloaded from FTP successfully")
except Exception as e:
    print("Failed to download file from FTP:", e)
    ftp.quit()

# Parse XML file
tree = ET.parse('plc_visu.xml')  # Use the downloaded file instead of the argument
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
prev_response = requests.post(endpoint, data=payload)

while True:
    # Make the request
    response = requests.post(endpoint, data=payload)
    # Check if the response is different from the previous one
    if response.content != prev_response.content:
        print("Raw response: ", response.content)
        prev_response = response
