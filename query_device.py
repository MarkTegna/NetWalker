"""
Query device information from NetWalker database
"""
import sys
sys.path.insert(0, '.')

from netwalker.config.config_manager import ConfigurationManager
from netwalker.database.database_manager import DatabaseManager

# Load config
config_manager = ConfigurationManager('netwalker.ini')
full_config = config_manager.load_configuration()
db_config = full_config.get('database', {})

# Connect to database
db = DatabaseManager(db_config)
if not db.connect():
    print("Failed to connect to database")
    sys.exit(1)

# Query device
device_name = 'WPMT-STUDIO-SW01'
cursor = db.connection.cursor()

cursor.execute("""
    SELECT d.device_id, d.device_name, d.serial_number, d.platform, d.hardware_model, 
           d.capabilities, d.status, d.last_seen
    FROM devices d
    WHERE d.device_name = ?
""", (device_name,))

row = cursor.fetchone()
if row:
    print(f'Device ID: {row[0]}')
    print(f'Device Name: {row[1]}')
    print(f'Serial Number: {row[2]}')
    print(f'Platform: {row[3]}')
    print(f'Hardware Model: {row[4]}')
    print(f'Capabilities: {row[5]}')
    print(f'Status: {row[6]}')
    print(f'Last Seen: {row[7]}')
    print()
    
    device_id = row[0]
    
    # Query neighbors where this device is the destination
    cursor.execute("""
        SELECT n.neighbor_id, d1.device_name AS source_name, n.source_interface, 
               n.destination_interface, n.protocol, n.last_seen
        FROM device_neighbors n
        INNER JOIN devices d1 ON n.source_device_id = d1.device_id
        WHERE n.destination_device_id = ?
        ORDER BY n.last_seen DESC
    """, (device_id,))
    
    print('Discovered from (CDP/LLDP neighbors):')
    neighbors = cursor.fetchall()
    if neighbors:
        for neighbor_row in neighbors:
            print(f'  - From: {neighbor_row[1]} via {neighbor_row[2]} -> {neighbor_row[3]} ({neighbor_row[4]}) at {neighbor_row[5]}')
    else:
        print('  - No neighbor records found')
else:
    print(f'Device {device_name} not found in database')

cursor.close()
db.disconnect()
