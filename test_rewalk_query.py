"""Test script to check what devices get_stale_devices returns"""
from netwalker.database.database_manager import DatabaseManager
from netwalker.config.config_manager import ConfigurationManager

# Load configuration
cm = ConfigurationManager('netwalker.ini')
config = cm.load_configuration()

# Initialize database
db = DatabaseManager(config.get('database', {}))
db.connect()

# Query stale devices with days=0 (should return ALL devices)
print("Querying stale devices with days=0...")
devices = db.get_stale_devices(0)

print(f"\nFound {len(devices)} devices:")
for d in devices:
    ip_display = d['ip_address'] if d['ip_address'] else 'No IP'
    print(f"  {d['device_name']} - IP: {ip_display} - Last seen: {d['last_seen']}")

db.disconnect()
