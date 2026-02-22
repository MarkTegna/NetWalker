#!/usr/bin/env python3
"""
Check Stack Member Serial Numbers

Query database to see what serial number data exists for stack members.

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
        
        # Query stack members with serial numbers
        query = """
            SELECT
                d.device_name,
                sm.switch_number,
                sm.serial_number,
                sm.hardware_model,
                sm.role,
                sm.state
            FROM device_stack_members sm
            INNER JOIN devices d ON sm.device_id = d.device_id
            WHERE d.status = 'active'
            ORDER BY d.device_name, sm.switch_number
            LIMIT 20
        """
        
        # SQL Server doesn't use LIMIT, use TOP instead
        query = """
            SELECT TOP 20
                d.device_name,
                sm.switch_number,
                sm.serial_number,
                sm.hardware_model,
                sm.role,
                sm.state
            FROM device_stack_members sm
            INNER JOIN devices d ON sm.device_id = d.device_id
            WHERE d.status = 'active'
            ORDER BY d.device_name, sm.switch_number
        """
        
        cursor.execute(query)
        members = cursor.fetchall()
        
        print("\n" + "=" * 120)
        print("SAMPLE STACK MEMBER DATA (First 20 records)")
        print("=" * 120)
        print(f"{'Device Name':<30} {'Switch':<8} {'Serial Number':<20} {'Hardware Model':<25} {'Role':<12} {'State':<10}")
        print("-" * 120)
        
        for member in members:
            device_name = member[0]
            switch_num = member[1]
            serial = member[2] or 'NULL'
            hw_model = member[3] or 'NULL'
            role = member[4] or 'NULL'
            state = member[5] or 'NULL'
            
            print(f"{device_name:<30} {switch_num:<8} {serial:<20} {hw_model:<25} {role:<12} {state:<10}")
        
        print("=" * 120)
        
        # Count how many have serial numbers
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN serial_number IS NOT NULL AND serial_number != '' AND serial_number != 'Unknown' THEN 1 ELSE 0 END) as with_serial,
                SUM(CASE WHEN serial_number IS NULL OR serial_number = '' OR serial_number = 'Unknown' THEN 1 ELSE 0 END) as without_serial
            FROM device_stack_members sm
            INNER JOIN devices d ON sm.device_id = d.device_id
            WHERE d.status = 'active'
        """)
        
        stats = cursor.fetchone()
        total = stats[0]
        with_serial = stats[1]
        without_serial = stats[2]
        
        print(f"\nSTATISTICS:")
        print(f"  Total stack members: {total}")
        print(f"  With serial numbers: {with_serial} ({100*with_serial/total:.1f}%)")
        print(f"  Without serial numbers: {without_serial} ({100*without_serial/total:.1f}%)")
        
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
