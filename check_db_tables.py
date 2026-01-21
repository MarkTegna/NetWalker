"""Check NetWalker database tables"""
import pyodbc

try:
    conn = pyodbc.connect(
        'DRIVER={SQL Server};'
        'SERVER=eit-prisqldb01.tgna.tegna.com,1433;'
        'DATABASE=NetWalker;'
        'UID=NetWalker;'
        'PWD=FluffyBunnyHitbyaBus;'
        'TrustServerCertificate=yes'
    )
    
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables in NetWalker database: {len(tables)}")
    for table in tables:
        print(f"  - {table}")
    
    # Check if we have a neighbors/connections table
    print("\nChecking for connection/neighbor data...")
    
    for table in tables:
        if 'neighbor' in table.lower() or 'connection' in table.lower() or 'link' in table.lower():
            print(f"\nFound potential connection table: {table}")
            cursor.execute(f"SELECT TOP 5 * FROM {table}")
            rows = cursor.fetchall()
            if rows:
                print(f"  Sample data: {len(rows)} rows")
                for row in rows:
                    print(f"    {row}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
