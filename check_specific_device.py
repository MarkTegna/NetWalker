#!/usr/bin/env python3
"""
Check Specific Device Stack Data

Query database for KXTV-MC-STACK1 stack member details.

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
    
    device_name = "KXTV-MC-STACK1"
    
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
        
        # Query stack members for this device
        query = """
            SELECT
                sm.switch_number,
                sm.role,
                sm.priority,
                sm.hardware_model,
                sm.serial_number,
                sm.mac_address,
                sm.software_version,
                sm.state,
                sm.last_seen
            FROM device_stack_members sm
            INNER JOIN devices d ON sm.device_id = d.device_id
            WHERE d.device_name = ?
            ORDER BY sm.switch_number
        """
        
        cursor.execute(query, (device_name,))
        members = cursor.fetchall()
        
        if not members:
            print(f"\nNo stack members found for {device_name}")
            return 0
        
        print(f"\n{'='*120}")
        print(f"STACK MEMBERS FOR {device_name}")
        print(f"{'='*120}")
        print(f"{'Switch':<8} {'Role':<12} {'Priority':<10} {'Hardware Model':<25} {'Serial':<20} {'State':<10} {'Last Seen':<20}")
        print(f"{'-'*120}")
        
        for member in members:
            switch_num = member[0]
            role = member[1] or 'NULL'
            priority = member[2] if member[2] is not None else 'NULL'
            hw_model = member[3] or 'NULL'
            serial = member[4] or 'NULL'
            state = member[7] or 'NULL'
            last_seen = str(member[8]) if member[8] else 'NULL'
            
            print(f"{switch_num:<8} {role:<12} {str(priority):<10} {hw_model:<25} {serial:<20} {state:<10} {last_seen:<20}")
        
        print(f"{'='*120}")
        
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
