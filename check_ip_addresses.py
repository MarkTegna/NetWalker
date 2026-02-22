"""Check how many devices have IP addresses"""
from netwalker.database.database_manager import DatabaseManager
from netwalker.config.config_manager import ConfigurationManager

cm = ConfigurationManager('netwalker.ini')
config = cm.load_configuration()
db = DatabaseManager(config.get('database', {}))
db.connect()

devices = db.get_stale_devices(0)
with_ip = [d for d in devices if d['ip_address']]

print(f'Total devices: {len(devices)}')
print(f'Devices with IP: {len(with_ip)}')
print(f'Devices without IP: {len(devices) - len(with_ip)}')
print(f'\nFirst 10 devices WITH IP:')
for d in with_ip[:10]:
    print(f"  {d['device_name']} - {d['ip_address']}")

db.disconnect()
