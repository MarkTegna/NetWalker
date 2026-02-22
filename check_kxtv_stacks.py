#!/usr/bin/env python3
"""
Check KXTV Stack Data

Query database to see what stack data exists for KXTV devices.

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
        
        # Query KXTV devices with stack members
        query = """
            SELECT
                d.device_name,
                d.platform,
                d.hardware_model,
                COUNT(sm.stack_member_id) as member_count
            FROM devices d
            LEFT JOIN device_stack_members sm ON d.device_id = sm.device_id
            WHERE d.status = 'active'
              AND d.device_name LIKE 'KXTV%'
            GROUP BY d.device_name, d.platform, d.hardware_model
            HAVING COUNT(sm.stack_member_id) > 0
            ORDER BY d.device_name
        """
        
        cursor.execute(query)
        devices = cursor.fetchall()
        
        if not devices:
            print("\nNo KXTV devices with stack members found in database")
            return 0
        
        print(f"\n{'='*100}")
        print(f"KXTV DEVICES WITH STACK MEMBERS")
        print(f"{'='*100}")
        print(f"{'Device Name':<30} {'Platform':<15} {'Hardware Model':<30} {'Members':<10}")
        print(f"{'-'*100}")
        
        for device in devices:
            device_name = device[0]
            platform = device[1] or 'Unknown'
            hardware_model = device[2] or 'Unknown'
            member_count = device[3]
            
            print(f"{device_name:<30} {platform:<15} {hardware_model:<30} {member_count:<10}")
        
        print(f"{'-'*100}")
        print(f"Total: {len(devices)} devices")
        print(f"{'='*100}")
        
        # Show detailed info for first device
        if devices:
            first_device = devices[0][0]
            print(f"\nDetailed stack member info for {first_device}:")
            print(f"{'-'*120}")
            
            detail_query = """
                SELECT
                    sm.switch_number,
                    sm.role,
                    sm.priority,
                    sm.hardware_model,
                    sm.serial_number,
                    sm.mac_address,
                    sm.software_version,
                    sm.state
                FROM device_stack_members sm
                INNER JOIN devices d ON sm.device_id = d.device_id
                WHERE d.device_name = ?
                ORDER BY sm.switch_number
            """
            
            cursor.execute(detail_query, (first_device,))
            members = cursor.fetchall()
            
            print(f"{'Switch':<8} {'Role':<12} {'Priority':<10} {'Hardware Model':<25} {'Serial':<20} {'State':<10}")
            print(f"{'-'*120}")
            
            for member in members:
                switch_num = member[0]
                role = member[1] or 'NULL'
                priority = member[2] if member[2] is not None else 'NULL'
                hw_model = member[3] or 'NULL'
                serial = member[4] or 'NULL'
                state = member[7] or 'NULL'
                
                print(f"{switch_num:<8} {role:<12} {str(priority):<10} {hw_model:<25} {serial:<20} {state:<10}")
        
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
