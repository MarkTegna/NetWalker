#!/usr/bin/env python3
"""
Walk KXTV Devices

Query database for KXTV devices and create a seed file to walk them.

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
        
        # Query KXTV devices
        query = """
            SELECT
                d.device_name,
                COALESCE(
                    (SELECT TOP 1 ip_address
                     FROM device_interfaces
                     WHERE device_id = d.device_id
                     ORDER BY
                        CASE
                            WHEN interface_name LIKE '%Management%' THEN 1
                            WHEN interface_name LIKE '%Loopback%' THEN 2
                            WHEN interface_name LIKE '%Vlan%' THEN 3
                            ELSE 4
                        END,
                        interface_name
                    ),
                    ''
                ) AS ip_address
            FROM devices d
            WHERE d.status = 'active'
              AND d.device_name LIKE 'KXTV%'
            ORDER BY d.device_name
        """
        
        cursor.execute(query)
        devices = cursor.fetchall()
        
        if not devices:
            print("\nNo KXTV devices found in database")
            return 0
        
        print(f"\nFound {len(devices)} KXTV devices:")
        for device in devices:
            device_name = device[0]
            ip_address = device[1] or 'No IP'
            print(f"  {device_name} - {ip_address}")
        
        # Create seed file
        seed_file = 'kxtv_seed.csv'
        with open(seed_file, 'w') as f:
            f.write("hostname,ip_address,status,error_details\n")
            for device in devices:
                device_name = device[0]
                ip_address = device[1] or ''
                f.write(f"{device_name},{ip_address},,\n")
        
        print(f"\nCreated seed file: {seed_file}")
        print(f"\nTo walk these devices, run:")
        print(f"  .\\netwalker.exe --config netwalker.ini --max-depth 0")
        print(f"\nMake sure to update netwalker.ini to use seed_file = {seed_file}")
        
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
