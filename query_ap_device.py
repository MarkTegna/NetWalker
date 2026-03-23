#!/usr/bin/env python3
"""
Query information about WUSA-MAIN-AP07 from the database
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from netwalker.config.config_manager import ConfigurationManager
from netwalker.database import DatabaseManager


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
        cursor = db_manager.connection.cursor()

        # Query device information
        cursor.execute("""
            SELECT device_id, device_name, serial_number, platform, hardware_model, 
                   capabilities, status, first_seen, last_seen
            FROM devices
            WHERE device_name LIKE '%AP07%'
        """)

        devices = cursor.fetchall()

        if not devices:
            print("\n[INFO] No devices found matching 'AP07'")
        else:
            print("\n[FOUND] Device Information:")
            print("=" * 80)
            for device in devices:
                device_id, device_name, serial, platform, model, caps, status, first, last = device
                print(f"Device ID: {device_id}")
                print(f"Device Name: {device_name}")
                print(f"Serial Number: {serial}")
                print(f"Platform: {platform}")
                print(f"Hardware Model: {model}")
                print(f"Capabilities: {caps}")
                print(f"Status: {status}")
                print(f"First Seen: {first}")
                print(f"Last Seen: {last}")
                print("-" * 80)

                # Get neighbor connections for this device
                cursor.execute("""
                    SELECT dn.source_device_id, d1.device_name as source_name,
                           dn.source_interface, dn.destination_interface,
                           dn.protocol, dn.first_seen, dn.last_seen
                    FROM device_neighbors dn
                    JOIN devices d1 ON dn.source_device_id = d1.device_id
                    WHERE dn.destination_device_id = ?
                    ORDER BY dn.last_seen DESC
                """, (device_id,))

                neighbors = cursor.fetchall()
                if neighbors:
                    print(f"\nConnected From ({len(neighbors)} connections):")
                    for n in neighbors:
                        src_id, src_name, src_if, dst_if, proto, first, last = n
                        print(f"  {src_name} ({src_if}) -> {dst_if} via {proto}")
                        print(f"    Last seen: {last}")

        cursor.close()

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db_manager.disconnect()

    return 0


if __name__ == "__main__":
    sys.exit(main())
