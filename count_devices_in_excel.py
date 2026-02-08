"""Count all devices in ChassisInventory.xls"""
import xml.etree.ElementTree as ET

file_path = r"D:\MJODev\NetWalker\prodtest_files\ChassisInventory.xls"

tree = ET.parse(file_path)
root = tree.getroot()

ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}

ws = root.find('.//ss:Worksheet', ns)
table = ws.find('.//ss:Table', ns)
rows = table.findall('.//ss:Row', ns)

device_names = []

for row in rows:
    cells = row.findall('.//ss:Cell', ns)
    
    if len(cells) >= 2:
        label_cell = cells[0]
        label_data = label_cell.find('.//ss:Data', ns)
        
        if label_data is not None and label_data.text:
            label = label_data.text.strip()
            
            if label == "Name:":
                value_cell = cells[1]
                value_data = value_cell.find('.//ss:Data', ns)
                
                if value_data is not None and value_data.text:
                    device_name = value_data.text.strip()
                    device_names.append(device_name)

print(f"Total devices found: {len(device_names)}")
print(f"\nFirst 20 devices:")
for i, name in enumerate(device_names[:20], 1):
    print(f"{i}. {name}")

print(f"\nLast 20 devices:")
for i, name in enumerate(device_names[-20:], len(device_names)-19):
    print(f"{i}. {name}")

# Check for unique devices
unique_devices = set(device_names)
print(f"\nUnique devices: {len(unique_devices)}")
print(f"Duplicate entries: {len(device_names) - len(unique_devices)}")
