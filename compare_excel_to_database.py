"""Compare Excel devices to database"""
import xml.etree.ElementTree as ET
import pyodbc
import base64
import configparser
from pathlib import Path

# Load config
config = configparser.ConfigParser()
config.read('netwalker.ini')

db_config = {
    'server': config.get('database', 'server'),
    'port': config.get('database', 'port'),
    'database': config.get('database', 'database'),
    'username': config.get('database', 'username'),
    'password': config.get('database', 'password'),
}

if db_config['password'].startswith('ENC:'):
    encoded = db_config['password'][4:]
    db_config['password'] = base64.b64decode(encoded.encode()).decode()

# Connect to database
connection_string = (
    f"DRIVER={{SQL Server}};"
    f"SERVER={db_config['server']},{db_config['port']};"
    f"DATABASE={db_config['database']};"
    f"UID={db_config['username']};"
    f"PWD={db_config['password']};"
    "TrustServerCertificate=yes;"
)

conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

# Get all devices from database
cursor.execute("SELECT DISTINCT device_name FROM devices")
db_devices = {row[0].upper() for row in cursor.fetchall()}
print(f"Database devices: {len(db_devices)}")

# Extract devices from Excel
file_path = r"D:\MJODev\NetWalker\prodtest_files\ChassisInventory.xls"
tree = ET.parse(file_path)
root = tree.getroot()
ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
ws = root.find('.//ss:Worksheet', ns)
table = ws.find('.//ss:Table', ns)
rows = table.findall('.//ss:Row', ns)

excel_devices = []
for row in rows:
    cells = row.findall('.//ss:Cell', ns)
    if len(cells) >= 2:
        label_cell = cells[0]
        label_data = label_cell.find('.//ss:Data', ns)
        if label_data is not None and label_data.text:
            if label_data.text.strip() == "Name:":
                value_cell = cells[1]
                value_data = value_cell.find('.//ss:Data', ns)
                if value_data is not None and value_data.text:
                    excel_devices.append(value_data.text.strip().upper())

unique_excel = set(excel_devices)
print(f"Excel devices (total): {len(excel_devices)}")
print(f"Excel devices (unique): {len(unique_excel)}")

# Find devices in Excel but NOT in database
new_devices = unique_excel - db_devices
print(f"\nDevices in Excel but NOT in database: {len(new_devices)}")

if new_devices:
    print("\nNew devices:")
    for device in sorted(new_devices):
        print(f"  - {device}")

# Find devices in database but NOT in Excel
missing_from_excel = db_devices - unique_excel
print(f"\nDevices in database but NOT in Excel: {len(missing_from_excel)}")
print("(These are devices discovered by NetWalker but not in the chassis inventory)")

conn.close()
