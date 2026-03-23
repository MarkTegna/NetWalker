"""
Find the parent switch for PolycomTrio8500 device
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

try:
    cursor = db.connection.cursor()
    
    # Find the Polycom Trio 8500 device
    cursor.execute("""
        SELECT device_id, device_name, platform, hardware_model
        FROM devices
        WHERE device_name LIKE '%Trio%8500%' OR device_name LIKE '%PolycomTrio8500%'
    """)
    
    polycom_row = cursor.fetchone()
    
    if not polycom_row:
        print("PolycomTrio8500 not found in database")
        cursor.close()
        db.disconnect()
        sys.exit(1)
    
    polycom_id = polycom_row[0]
    polycom_name = polycom_row[1]
    
    print(f"Found Polycom device: {polycom_name} (ID: {polycom_id})")
    print(f"  Platform: {polycom_row[2]}")
    print(f"  Hardware Model: {polycom_row[3]}")
    print()
    
    # Find the parent switch (device that discovered this Polycom)
    cursor.execute("""
        SELECT 
            d.device_id,
            d.device_name,
            d.platform,
            d.hardware_model,
            n.source_interface,
            n.destination_interface,
            n.protocol
        FROM device_neighbors n
        INNER JOIN devices d ON n.source_device_id = d.device_id
        WHERE n.destination_device_id = ?
    """, (polycom_id,))
    
    parent_rows = cursor.fetchall()
    
    if parent_rows:
        print(f"Found {len(parent_rows)} parent switch(es):")
        for row in parent_rows:
            print(f"\nParent Switch: {row[1]} (ID: {row[0]})")
            print(f"  Platform: {row[2]}")
            print(f"  Hardware Model: {row[3]}")
            print(f"  Connection: {row[4]} -> {row[5]} ({row[6]})")
            print(f"\n  To see CDP/LLDP details, connect to: {row[1]}")
            print(f"  Command: show cdp neighbors {row[4]} detail")
            print(f"  Or: show lldp neighbors {row[4]} detail")
    else:
        print("No parent switch found (device not discovered via CDP/LLDP)")
    
    cursor.close()
    
except Exception as e:
    print(f"Error querying database: {e}")
finally:
    db.disconnect()
