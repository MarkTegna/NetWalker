"""
Reset connection failure count for a device in NetWalker database
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

# Device to reset
device_name = 'WMAZ-CORE-A'

try:
    cursor = db.connection.cursor()
    
    # Check current failure count
    cursor.execute("""
        SELECT device_id, device_name, connection_failures 
        FROM devices 
        WHERE device_name = ?
    """, (device_name,))
    
    row = cursor.fetchone()
    
    if row:
        device_id = row[0]
        current_failures = row[2]
        print(f"Found device: {row[1]}")
        print(f"  Device ID: {device_id}")
        print(f"  Current connection failures: {current_failures}")
        print()
        
        # Reset connection failures to 0
        cursor.execute("""
            UPDATE devices 
            SET connection_failures = 0, updated_at = GETDATE()
            WHERE device_id = ?
        """, (device_id,))
        db.connection.commit()
        
        print(f"✓ Successfully reset connection failures for '{device_name}'")
        print(f"  Connection failures: {current_failures} → 0")
    else:
        print(f"Device '{device_name}' not found in database")
    
    cursor.close()
    
except Exception as e:
    print(f"Error resetting connection failures: {e}")
    if db.connection:
        db.connection.rollback()
finally:
    db.disconnect()
