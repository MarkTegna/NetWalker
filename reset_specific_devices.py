"""
Reset connection failure count to 0 for specific devices
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

# List of devices to reset
devices_to_reset = [
    'WZZM-MC-SW03',
    'WZZM-MC-SW02',
    'WZZM-MC-SW01',
    'WZDX-CORE-A',
    'WUSA-STACK-SW02',
    'WUSA-STACK-SW01',
    'WTHR-TEMP-SW01',
    'WTHR-SHOP36',
    'WPMT-WITF-2',
    'WPMT-NEWSCTRL01-SW3750',
    'WOI-CORE-A',
    'WFAA-AJA-MRR-R129',
    'WBNS-TXMT-TENET-AS-163',
    'WATN-TRANSMITTER-SW01',
    'TEST-UW02',
    'Switch',
    'Pooky-CoreSwitch',
    'ORAD_RM105_WNET',
    'KXTV-TRIANGLE-SW-A',
    'KXTV-2960-WC-SW-C',
    'KXTV-2960-EC-SW-D',
    'KWES-MGMT-SW01',
    'KWES-DR1-SW01',
    'KVUE-CORE-A',
    'KUSA-2960-TRANSMITTER-SW-A',
    'KSDK-1F-CONTENTHUB1',
    'kpnx-oobmanage',
    'KPNX-7FLR-SW02',
    'KPNX-7FLR-SW01',
    'kpnx-10thfloorwhitetanks',
    'KING-CER-706-SW02',
    'KIII-CORE-A',
    'KGW-SHOP-SW01',
    'KGW-CORE-A',
    'KGW-038-R02-SW02',
    'KGW-000-R71-SW02',
    'KGW-000-R71-SW01',
    'KGW-000-R61-SW02',
    'KGW-000-R61-SW01',
    'KFMB-VIZRT-SW01',
    'KFMB-SOLEDAD-SW01',
    'KCEN-SW09',
    'KBMT-CORE-A'
]

try:
    cursor = db.connection.cursor()
    
    print("Resetting connection failure count for specified devices...")
    print("=" * 80)
    
    reset_count = 0
    not_found = []
    
    for device_name in devices_to_reset:
        # Check if device exists and get current failure count
        cursor.execute("""
            SELECT device_id, connection_failures 
            FROM devices 
            WHERE device_name = ?
        """, (device_name,))
        
        row = cursor.fetchone()
        
        if row:
            device_id = row[0]
            old_failures = row[1]
            
            # Reset connection failures to 0
            cursor.execute("""
                UPDATE devices 
                SET connection_failures = 0, updated_at = GETDATE()
                WHERE device_id = ?
            """, (device_id,))
            
            print(f"[OK] {device_name}: {old_failures} -> 0")
            reset_count += 1
        else:
            print(f"[NOT FOUND] {device_name}")
            not_found.append(device_name)
    
    # Commit changes
    db.connection.commit()
    
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  Devices reset: {reset_count}")
    print(f"  Devices not found: {len(not_found)}")
    
    if not_found:
        print(f"\nDevices not found in database:")
        for device in not_found:
            print(f"  - {device}")
    
    cursor.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    if db.connection:
        db.connection.rollback()
finally:
    db.disconnect()
