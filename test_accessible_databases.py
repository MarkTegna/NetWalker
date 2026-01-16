import pyodbc

# Connect to default database
conn = pyodbc.connect(
    'DRIVER={SQL Server};'
    'SERVER=eit-prisqldb01.tgna.tegna.com,1433;'
    'UID=NetWalker;'
    'PWD=FluffyBunnyHitbyaBus;'
    'Connection Timeout=30;'
)

cursor = conn.cursor()

# Check what database we're connected to
cursor.execute("SELECT DB_NAME()")
db_name = cursor.fetchone()[0]
print(f"Default database: {db_name}")

# Try to list databases we have access to
try:
    cursor.execute("""
        SELECT name 
        FROM sys.databases 
        WHERE HAS_DBACCESS(name) = 1
        ORDER BY name
    """)
    
    print("\nDatabases accessible to NetWalker login:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}")
        
except Exception as e:
    print(f"\nCannot list databases (may lack VIEW ANY DATABASE permission): {e}")
    print("\nTrying alternative method...")
    
    # Try to check specific databases
    test_dbs = ['master', 'NetWalker', 'tempdb', 'model', 'msdb']
    print("\nTesting access to common databases:")
    for db in test_dbs:
        try:
            cursor.execute(f"SELECT HAS_DBACCESS('{db}')")
            has_access = cursor.fetchone()[0]
            if has_access == 1:
                print(f"  ✓ {db} - accessible")
            else:
                print(f"  ✗ {db} - not accessible")
        except Exception as e2:
            print(f"  ? {db} - error checking: {e2}")

cursor.close()
conn.close()
