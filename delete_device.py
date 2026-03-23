"""
Delete a specific device from NetWalker database
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

# Device to delete
device_name = 'ep-moldhamWMAZ-MAIN-FW02'

try:
    cursor = db.connection.cursor()
    
    # First, check if device exists
    cursor.execute("""
        SELECT device_id, device_name, serial_number, platform 
        FROM devices 
        WHERE device_name = ?
    """, (device_name,))
    
    row = cursor.fetchone()
    
    if row:
        device_id = row[0]
        print(f"Found device:")
        print(f"  ID: {device_id}")
        print(f"  Name: {row[1]}")
        print(f"  Serial: {row[2]}")
        print(f"  Platform: {row[3]}")
        print()
        
        # Delete the device (CASCADE will handle related records)
        cursor.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
        db.connection.commit()
        
        print(f"✓ Successfully deleted device '{device_name}' (ID: {device_id})")
        print("  All related records (interfaces, versions, VLANs, neighbors) were also deleted.")
    else:
        print(f"Device '{device_name}' not found in database")
    
    cursor.close()
    
except Exception as e:
    print(f"Error deleting device: {e}")
    if db.connection:
        db.connection.rollback()
finally:
    db.disconnect()
