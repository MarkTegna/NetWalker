"""Check database schema."""
import sqlite3

def check_schema():
    """Display database schema."""
    db_path = "netwalker.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"\n{'='*80}")
        print(f"Database Tables")
        print(f"{'='*80}")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check if stack_members table exists
        if ('stack_members',) in tables:
            print("\n✓ stack_members table EXISTS")
            
            # Get schema
            cursor.execute("PRAGMA table_info(stack_members)")
            columns = cursor.fetchall()
            print("\nColumns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
        else:
            print("\n✗ stack_members table DOES NOT EXIST")
        
        print(f"{'='*80}\n")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
