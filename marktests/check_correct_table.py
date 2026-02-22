"""Check stack member data using the correct table name."""
import sqlite3
import sys

def check_stack_members():
    """Query and display stack member data from the database."""
    db_path = "netwalker.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # First check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        print(f"\nAvailable tables: {[t[0] for t in tables]}\n")
        
        # Query stack members for KARE-CORE-A using correct table name
        query = """
        SELECT 
            d.device_name,
            sm.switch_number,
            sm.serial_number,
            sm.hardware_model,
            sm.role,
            sm.priority,
            sm.state,
            sm.last_seen
        FROM device_stack_members sm
        JOIN devices d ON sm.device_id = d.device_id
        WHERE d.device_name = 'KARE-CORE-A'
        ORDER BY sm.switch_number
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print(f"{'='*100}")
        print(f"Stack Members for KARE-CORE-A")
        print(f"{'='*100}")
        print(f"Found {len(results)} stack members\n")
        
        if results:
            print(f"{'Switch':<8} {'Serial Number':<20} {'Model':<30} {'Role':<10} {'Priority':<10} {'State':<10}")
            print(f"{'-'*8} {'-'*20} {'-'*30} {'-'*10} {'-'*10} {'-'*10}")
            for row in results:
                device_name, switch_num, serial, model, role, priority, state, last_seen = row
                print(f"{switch_num:<8} {serial:<20} {model or 'Unknown':<30} {role or 'N/A':<10} {str(priority) if priority else 'N/A':<10} {state or 'N/A':<10}")
        else:
            print("No stack members found for KARE-CORE-A")
        
        print(f"\n{'='*100}\n")
        
        # Also check all devices to see if KARE-CORE-A exists
        cursor.execute("SELECT device_name, serial_number, platform FROM devices WHERE device_name LIKE '%CORE%'")
        core_devices = cursor.fetchall()
        if core_devices:
            print("Core devices in database:")
            for dev in core_devices:
                print(f"  - {dev[0]} (Serial: {dev[1]}, Platform: {dev[2]})")
        
        conn.close()
        return len(results) > 0
        
    except Exception as e:
        print(f"Error querying database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_stack_members()
    sys.exit(0 if success else 1)
