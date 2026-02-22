"""Test script to simulate the rewalk-stale flow"""
from netwalker.database.database_manager import DatabaseManager
from netwalker.config.config_manager import ConfigurationManager
import tempfile

# Load configuration
cm = ConfigurationManager('netwalker.ini')
config = cm.load_configuration()

# Initialize database
db = DatabaseManager(config.get('database', {}))
db.connect()

# Query stale devices with days=0 (should return ALL devices)
print("Querying stale devices with days=0...")
stale_devices = db.get_stale_devices(0)

print(f"\nFound {len(stale_devices)} devices")
print(f"First 5 devices:")
for i, device in enumerate(stale_devices[:5]):
    ip_display = device['ip_address'] if device['ip_address'] else 'No IP'
    print(f"  {device['device_name']} - IP: {ip_display}")

# Simulate creating the temporary seed file
seed_devices = []
for device in stale_devices:
    seed_devices.append({
        'hostname': device['device_name'],
        'ip_address': device['ip_address']
    })

print(f"\nCreated seed_devices list with {len(seed_devices)} entries")

# Create temporary seed file (like the code does)
with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as temp_seed:
    temp_seed.write("hostname,ip_address,status,error_details\n")
    for device in seed_devices:
        hostname = device['hostname']
        ip_address = device['ip_address'] if device['ip_address'] else ''
        temp_seed.write(f"{hostname},{ip_address},,\n")
    temp_seed_path = temp_seed.name

print(f"\nCreated temporary seed file: {temp_seed_path}")
print(f"Reading it back to verify...")

# Read it back to verify
with open(temp_seed_path, 'r') as f:
    lines = f.readlines()
    print(f"Seed file has {len(lines)} lines (including header)")
    print(f"First 5 lines:")
    for line in lines[:5]:
        print(f"  {line.strip()}")

# Clean up
import os
os.unlink(temp_seed_path)

db.disconnect()
