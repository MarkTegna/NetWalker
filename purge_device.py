#!/usr/bin/env python3
"""
Purge Device from NetWalker Database

Deletes a specific device and all related records from the database.

Author: Mark Oldham
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from netwalker.config.config_manager import ConfigurationManager
from netwalker.database import DatabaseManager


def main():
    """Main function to purge a device"""
    
    if len(sys.argv) < 2:
        print("Usage: python purge_device.py <device_name>")
        print("Example: python purge_device.py KGW-CORE-A")
        return 1
    
    device_name = sys.argv[1]
    
    # Load configuration
    config_file = 'netwalker.ini'
    config_manager = ConfigurationManager(config_file)
    parsed_config = config_manager.load_configuration()
    db_config = parsed_config.get('database', {})
    
    # Initialize database manager
    db_manager = DatabaseManager(db_config)
    
    if not db_manager.connect():
        print("[FAIL] Could not connect to database")
        return 1
    
    try:
        cursor = db_manager.connection.cursor()
        
        # First, check if device exists
        cursor.execute("SELECT device_id, device_name, platform, hardware_model FROM devices WHERE device_name = ?", (device_name,))
        device = cursor.fetchone()
        
        if not device:
            print(f"\n[FAIL] Device '{device_name}' not found in database")
            return 1
        
        device_id = device[0]
        platform = device[2] or 'Unknown'
        hardware_model = device[3] or 'Unknown'
        
        print(f"\nFound device: {device_name}")
        print(f"  Platform: {platform}")
        print(f"  Hardware Model: {hardware_model}")
        
        # Get counts of related records
        cursor.execute("SELECT COUNT(*) FROM device_stack_members WHERE device_id = ?", (device_id,))
        stack_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM device_interfaces WHERE device_id = ?", (device_id,))
        interface_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM device_versions WHERE device_id = ?", (device_id,))
        version_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM device_vlans WHERE device_id = ?", (device_id,))
        vlan_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM device_neighbors WHERE source_device_id = ? OR destination_device_id = ?", (device_id, device_id))
        neighbor_count = cursor.fetchone()[0]
        
        print(f"\nRelated records to be deleted:")
        print(f"  Stack members: {stack_count}")
        print(f"  Interfaces: {interface_count}")
        print(f"  Versions: {version_count}")
        print(f"  VLANs: {vlan_count}")
        print(f"  Neighbor connections: {neighbor_count}")
        
        # Confirm deletion
        print(f"\nWARNING: This will permanently delete '{device_name}' and all related records!")
        response = input("Type 'YES' to confirm: ")
        
        if response != 'YES':
            print("\nPurge cancelled")
            return 0
        
        # Delete neighbor connections first (both source and destination)
        print(f"\nDeleting neighbor connections...")
        cursor.execute("DELETE FROM device_neighbors WHERE source_device_id = ? OR destination_device_id = ?", (device_id, device_id))
        
        # Delete the device (CASCADE will handle remaining related records)
        print(f"Deleting device '{device_name}'...")
        cursor.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
        
        db_manager.connection.commit()
        
        print(f"\n[OK] Device '{device_name}' purged successfully")
        print(f"  Deleted 1 device record")
        print(f"  Deleted {stack_count} stack member records")
        print(f"  Deleted {interface_count} interface records")
        print(f"  Deleted {version_count} version records")
        print(f"  Deleted {vlan_count} VLAN records")
        print(f"  Deleted {neighbor_count} neighbor connection records")
        
        cursor.close()
        
    except Exception as e:
        print(f"\n[FAIL] Error purging device: {e}")
        import traceback
        traceback.print_exc()
        if db_manager.connection:
            db_manager.connection.rollback()
        return 1
    
    finally:
        db_manager.disconnect()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
