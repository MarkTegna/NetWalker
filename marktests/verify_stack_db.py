"""Verify stack member data in production SQL Server database."""
import pyodbc
import sys

def verify_stack_members():
    """Query and display stack member data from SQL Server."""
    try:
        # Connection string for SQL Server
        conn_str = (
            "DRIVER={SQL Server};"
            "SERVER=eit-prisqldb01.tgna.tegna.com,1433;"
            "DATABASE=NetWalker;"
            "UID=NetWalker;"
            "PWD=FluffyBunnyHitbyaBus;"
        )
        
        conn = pyodbc.connect(conn_str, timeout=30)
        cursor = conn.cursor()
        
        # Query stack members for KARE-CORE-A
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
        
        print(f"\n{'='*100}")
        print(f"Stack Members for KARE-CORE-A (Production SQL Server)")
        print(f"{'='*100}")
        print(f"Found {len(results)} stack members\n")
        
        if results:
            print(f"{'Switch':<8} {'Serial Number':<20} {'Model':<30} {'Role':<10} {'Priority':<10} {'State':<10}")
            print(f"{'-'*8} {'-'*20} {'-'*30} {'-'*10} {'-'*10} {'-'*10}")
            for row in results:
                device_name, switch_num, serial, model, role, priority, state, last_seen = row
                print(f"{switch_num:<8} {serial:<20} {model or 'Unknown':<30} {role or 'N/A':<10} {str(priority) if priority else 'N/A':<10} {state or 'N/A':<10}")
            print(f"\nLast seen: {results[0][7]}")
        else:
            print("No stack members found for KARE-CORE-A")
        
        print(f"\n{'='*100}\n")
        
        conn.close()
        return len(results) > 0
        
    except Exception as e:
        print(f"Error querying database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_stack_members()
    sys.exit(0 if success else 1)
