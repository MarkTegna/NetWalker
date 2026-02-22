"""Test database query for filtered devices"""
import sys
sys.path.insert(0, '.')

from netwalker.database.database_manager import DatabaseManager
import configparser

# Load config
config = configparser.ConfigParser()
config.read('netwalker.ini')

# Create database manager
db_config = {
    'enabled': config.getboolean('database', 'enabled'),
    'server': config.get('database', 'server'),
    'port': config.getint('database', 'port'),
    'database': config.get('database', 'database'),
    'username': config.get('database', 'username'),
    'password': config.get('database', 'password'),
    'trust_server_certificate': config.getboolean('database', 'trust_server_certificate'),
    'connection_timeout': config.getint('database', 'connection_timeout'),
    'command_timeout': config.getint('database', 'command_timeout')
}

print(f"Database config: enabled={db_config['enabled']}, server={db_config['server']}")

db_manager = DatabaseManager(db_config)

if db_manager.connect():
    print("✓ Connected to database successfully")
    
    # Test query for LUMT-CORE-A
    print("\nQuerying for LUMT-CORE-A...")
    device_info = db_manager.get_device_info_by_host('LUMT-CORE-A')
    
    if device_info:
        print(f"✓ Found device info:")
        print(f"  Hostname: {device_info['hostname']}")
        print(f"  Serial: {device_info['serial_number']}")
        print(f"  Model: {device_info['hardware_model']}")
        print(f"  Platform: {device_info['platform']}")
        print(f"  Software: {device_info['software_version']}")
        print(f"  IP: {device_info['primary_ip']}")
    else:
        print("✗ No device info found for LUMT-CORE-A")
    
    db_manager.disconnect()
else:
    print("✗ Failed to connect to database")
