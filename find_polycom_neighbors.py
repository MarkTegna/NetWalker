"""
Find all Polycom devices that are neighbors of WMAZ-2ND-SW01
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
    
    # Get device_id for WMAZ-2ND-SW01
    cursor.execute("SELECT device_id FROM devices WHERE device_name = ?", ("WMAZ-2ND-SW01",))
    row = cursor.fetchone()
    if not row:
        print("WMAZ-2ND-SW01 not found in database")
        sys.exit(1)
    
    switch_device_id = row[0]
    print(f"WMAZ-2ND-SW01 device_id: {switch_device_id}\n")
    
    # Find all neighbors of this switch
    cursor.execute("""
        SELECT n.neighbor_id, n.destination_device_id, n.source_interface, n.destination_interface,
               n.protocol, d.device_name, d.serial_number, d.platform
        FROM device_neighbors n
        INNER JOIN devices d ON n.destination_device_id = d.device_id
        WHERE n.source_device_id = ?
        ORDER BY d.device_name
    """, (switch_device_id,))
    
    rows = cursor.fetchall()
    
    if rows:
        print(f"Found {len(rows)} neighbor(s) of WMAZ-2ND-SW01:\n")
        polycom_count = 0
        for row in rows:
            device_name = row[5]
            platform = row[7]
            
            # Check if this is a Polycom device
            is_polycom = False
            if device_name and 'polycom' in device_name.lower():
                is_polycom = True
            if platform and 'polycom' in platform.lower():
                is_polycom = True
            
            if is_polycom:
                polycom_count += 1
                print(f"*** POLYCOM DEVICE #{polycom_count} ***")
                print(f"  Device Name: {device_name}")
                print(f"  Platform (from CDP/LLDP): {platform}")
                print(f"  Serial Number: {row[6]}")
                print(f"  Local Interface (on WMAZ-2ND-SW01): {row[2]}")
                print(f"  Remote Interface (on Polycom): {row[3]}")
                print(f"  Protocol: {row[4]}")
                print()
        
        if polycom_count == 0:
            print("No Polycom devices found among neighbors")
    else:
        print("No neighbors found for WMAZ-2ND-SW01")
    
    cursor.close()
    
except Exception as e:
    print(f"Error querying database: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.disconnect()
