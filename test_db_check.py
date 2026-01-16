import pyodbc

# Connect to master to check if NetWalker database exists
conn = pyodbc.connect(
    'DRIVER={SQL Server};'
    'SERVER=eit-prisqldb01.tgna.tegna.com,1433;'
    'UID=NetWalker;'
    'PWD=FluffyBunnyHitbyaBus;'
    'Connection Timeout=30;'
)

cursor = conn.cursor()

# Check if NetWalker database exists
cursor.execute("SELECT name FROM sys.databases WHERE name = 'NetWalker'")
result = cursor.fetchone()

if result:
    print(f"✓ NetWalker database exists: {result[0]}")
    
    # Try to connect to NetWalker database
    cursor.close()
    conn.close()
    
    conn2 = pyodbc.connect(
        'DRIVER={SQL Server};'
        'SERVER=eit-prisqldb01.tgna.tegna.com,1433;'
        'DATABASE=NetWalker;'
        'UID=NetWalker;'
        'PWD=FluffyBunnyHitbyaBus;'
        'Connection Timeout=30;'
    )
    
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT DB_NAME()")
    db_name = cursor2.fetchone()[0]
    print(f"✓ Successfully connected to: {db_name}")
    
    # Check if tables exist
    cursor2.execute("SELECT name FROM sys.tables WHERE name = 'devices'")
    if cursor2.fetchone():
        print("✓ Schema already exists (devices table found)")
    else:
        print("✗ Schema does not exist (devices table not found)")
    
    cursor2.close()
    conn2.close()
else:
    print("✗ NetWalker database does NOT exist")
    print("  Default database for NetWalker login is: master")

cursor.close()
conn.close()
