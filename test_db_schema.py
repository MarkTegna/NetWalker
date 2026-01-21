"""Quick test to check NetWalker database schema"""
import pyodbc

connection_string = (
    "DRIVER={SQL Server};"
    "SERVER=eit-prisqldb01.tgna.tegna.com,1433;"
    "DATABASE=NetWalker;"
    "UID=NetWalker;"
    "PWD=FluffyBunnyHitbyaBus;"
    "TrustServerCertificate=yes;"
    "Connection Timeout=30;"
)

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    print("Connected to database successfully!\n")
    
    # Get list of tables
    print("Tables in NetWalker database:")
    print("-" * 50)
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """)
    
    tables = []
    for row in cursor.fetchall():
        table_name = row[0]
        tables.append(table_name)
        print(f"  - {table_name}")
    
    print("\n" + "=" * 50)
    
    # Check devices table
    if 'devices' in tables:
        print("\nDevices table sample:")
        print("-" * 50)
        cursor.execute("SELECT TOP 5 device_name, platform, hardware_model FROM devices WHERE status = 'active'")
        for row in cursor.fetchall():
            print(f"  {row[0]} | {row[1]} | {row[2]}")
        
        cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'active'")
        count = cursor.fetchone()[0]
        print(f"\nTotal active devices: {count}")
    
    # Check for neighbor/connection tables
    print("\n" + "=" * 50)
    print("\nLooking for connection/neighbor tables...")
    connection_tables = [t for t in tables if 'neighbor' in t.lower() or 'connection' in t.lower() or 'link' in t.lower()]
    
    if connection_tables:
        print("Found potential connection tables:")
        for table in connection_tables:
            print(f"  - {table}")
            
            # Show columns
            cursor.execute(f"""
                SELECT COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table}'
                ORDER BY ORDINAL_POSITION
            """)
            print("    Columns:")
            for col_row in cursor.fetchall():
                print(f"      - {col_row[0]} ({col_row[1]})")
    else:
        print("No obvious connection/neighbor tables found")
        print("\nAll tables:")
        for table in tables:
            print(f"  - {table}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
