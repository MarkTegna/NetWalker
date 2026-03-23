"""
Check what CDP/LLDP data we have for Polycom devices
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
    
    # Search for Polycom devices
    cursor.execute("""
        SELECT device_id, device_name, serial_number, platform, hardware_model, capabilities
        FROM devices
        WHERE device_name LIKE '%Polycom%' OR platform LIKE '%Polycom%'
        ORDER BY device_name
    """)
    
    rows = cursor.fetchall()
    
    if rows:
        print(f"Found {len(rows)} Polycom device(s):\n")
        for row in rows:
            print(f"Device: {row[1]}")
            print(f"  ID: {row[0]}")
            print(f"  Serial: {row[2]}")
            print(f"  Platform: {row[3]}")
            print(f"  Hardware Model: {row[4]}")
            print(f"  Capabilities: {row[5]}")
            print()
    else:
        print("No Polycom devices found in database")
    
    cursor.close()
    
except Exception as e:
    print(f"Error querying database: {e}")
finally:
    db.disconnect()
