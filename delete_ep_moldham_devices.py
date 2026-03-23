#!/usr/bin/env python3
"""
Delete devices containing 'ep-moldham' from the database
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from netwalker.config.config_manager import ConfigurationManager
from netwalker.database import DatabaseManager


def delete_devices(db_manager, search_term):
    """
    Delete devices containing the search term (case insensitive)

    Returns:
        Number of devices deleted
    """
    cursor = db_manager.connection.cursor()

    # First, get the list of devices to delete
    cursor.execute("""
        SELECT device_id, device_name, serial_number
        FROM devices
        WHERE device_name LIKE ? OR serial_number LIKE ?
    """, (f'%{search_term}%', f'%{search_term}%'))

    devices_to_delete = cursor.fetchall()

    if not devices_to_delete:
        print(f"\n[INFO] No devices found containing '{search_term}'")
        cursor.close()
        return 0

    print(f"\n[INFO] Found {len(devices_to_delete)} devices to delete:")
    print("=" * 80)
    for device in devices_to_delete:
        device_id, device_name, serial_number = device
        print(f"  Device ID: {device_id}, Device Name: {device_name}, Serial: {serial_number}")
    print("=" * 80)

    # Delete from devices table (cascading deletes should handle related tables)
    cursor.execute("""
        DELETE FROM devices
        WHERE device_name LIKE ? OR serial_number LIKE ?
    """, (f'%{search_term}%', f'%{search_term}%'))

    deleted_count = cursor.rowcount
    db_manager.connection.commit()

    cursor.close()
    return deleted_count


def main():
    """Main function"""

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
        print("=" * 80)
        print("DELETING DEVICES CONTAINING 'ep-moldham' (case insensitive)")
        print("=" * 80)

        # Delete devices
        deleted_count = delete_devices(db_manager, 'ep-moldham')

        if deleted_count > 0:
            print(f"\n[OK] Successfully deleted {deleted_count} devices")
        else:
            print("\n[INFO] No devices were deleted")

        print("=" * 80)

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        db_manager.connection.rollback()
        return 1

    finally:
        db_manager.disconnect()

    return 0


if __name__ == "__main__":
    sys.exit(main())
