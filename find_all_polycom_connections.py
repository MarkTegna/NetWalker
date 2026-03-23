"""
Find all Polycom devices and their parent switches
"""
import sys
sys.path.insert(0, '.')

from netwalker.config.config_manager import ConfigurationManager
from netwalker.database.database_manager import DatabaseManager

# Load config
config_manager = ConfigurationManager('netwalker.ini')
full_config = config_manager.load_configuration()
db_config = full_config.get('database')

# Connect to database
db = DatabaseManager(db_config)
if not db.connect():
    print("Failed to connect to database")
    sys.exit(1)

try:
    cursor = db.connection.cursor()
    
    # Find all Polycom devices
    cursor.execute("""
        SELECT device_id, device_name, serial_number, platform
        FROM devices
        WHERE device_name LIKE '%Polycom%' OR platform LIKE '%Polycom%'
        ORDER BY device_name
    """)
    
    polycom_devices = cursor.fetchall()
    
    if not polycom_devices:
        print("No Polycom devices found in database")
        sys.exit(0)
    
    print(f"Found {len(polycom_devices)} Polycom device(s):\n")
    
    for polycom in polycom_devices:
        device_id = polycom[0]
        device_name = polycom[1]
        serial_number = polycom[2]
        platform = polycom[3]
        
        print(f"Device: {device_name}")
        print(f"  Device ID: {device_id}")
        print(f"  Serial: {serial_number}")
        print(f"  Platform: {platform}")
        
        # Find parent switch(es) - devices that have this Polycom as a neighbor
        cursor.execute("""
            SELECT d.device_name, d.device_id, n.source_interface, n.destination_interface, n.protocol
            FROM device_neighbors n
            INNER JOIN devices d ON n.source_device_id = d.device_id
            WHERE n.destination_device_id = ?
        """, (device_id,))
        
        parents = cursor.fetchall()
        
        if parents:
            print(f"  Connected to {len(parents)} parent switch(es):")
            for parent in parents:
                print(f"    - {parent[0]} (ID: {parent[1]})")
                print(f"      Switch Port: {parent[2]} -> Polycom Port: {parent[3]} ({parent[4]})")
        else:
            print("  No parent switches found (not discovered via CDP/LLDP yet)")
        
        print()
    
    cursor.close()
    
except Exception as e:
    print(f"Error querying database: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.disconnect()
