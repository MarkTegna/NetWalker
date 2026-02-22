"""Quick script to check stack member data in the database."""
import sqlite3
import sys

def check_stack_members():
    """Query and display stack member data from the database."""
    db_path = "netwalker.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query stack members for KARE-CORE-A
        query = """
        SELECT 
            d.hostname,
            sm.switch_number,
            sm.serial_number,
            sm.model,
            sm.role,
            sm.priority,
            sm.state,
            sm.last_seen
        FROM stack_members sm
        JOIN devices d ON sm.device_id = d.id
        WHERE d.hostname = 'KARE-CORE-A'
        ORDER BY sm.switch_number
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print(f"\n{'='*80}")
        print(f"Stack Members for KARE-CORE-A")
        print(f"{'='*80}")
        print(f"Found {len(results)} stack members\n")
        
        if results:
            print(f"{'Switch':<8} {'Serial Number':<20} {'Model':<25} {'Role':<10} {'Priority':<10} {'State':<10}")
            print(f"{'-'*8} {'-'*20} {'-'*25} {'-'*10} {'-'*10} {'-'*10}")
            for row in results:
                hostname, switch_num, serial, model, role, priority, state, last_seen = row
                print(f"{switch_num:<8} {serial:<20} {model:<25} {role or 'N/A':<10} {priority or 'N/A':<10} {state or 'N/A':<10}")
        else:
            print("No stack members found for KARE-CORE-A")
        
        print(f"\n{'='*80}\n")
        
        conn.close()
        return len(results) > 0
        
    except Exception as e:
        print(f"Error querying database: {e}")
        return False

if __name__ == "__main__":
    success = check_stack_members()
    sys.exit(0 if success else 1)
