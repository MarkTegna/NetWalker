#!/usr/bin/env python3
"""
Query database for devices with -FW in the name and create seed file
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
        
        # Query for devices with -FW in the name
        query = """
            SELECT 
                d.device_name,
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
                    interface_name) as ip_address,
                d.platform,
                d.last_seen
            FROM devices d
            WHERE d.status = 'active'
              AND d.device_name LIKE '%-FW%'
            ORDER BY d.device_name
        """
        
        cursor.execute(query)
        devices = cursor.fetchall()
        
        if not devices:
            print("\n[INFO] No devices found with -FW in the name")
            return 0
        
        print(f"\n[OK] Found {len(devices)} firewall devices:")
        print("-" * 80)
        
        # Create seed file
        seed_file = "firewall_seed.csv"
        with open(seed_file, 'w') as f:
            for device in devices:
                device_name = device[0]
                ip_address = device[1] or ''
                platform = device[2] or 'Unknown'
                last_seen = device[3]
                
                print(f"  {device_name:30} {ip_address:20} {platform:15} {last_seen}")
                
                # Write IP to seed file if available
                if ip_address:
                    f.write(f"{ip_address}\n")
        
        print("-" * 80)
        print(f"\n[OK] Created seed file: {seed_file}")
        print(f"[OK] Total devices: {len(devices)}")
        print(f"\nTo re-walk these devices, run:")
        print(f"  .\\netwalker.exe --seed-file {seed_file} --depth 0")
        
        cursor.close()
        
    except Exception as e:
        print(f"\n[FAIL] Error querying database: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        db_manager.disconnect()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
