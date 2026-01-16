import pyodbc

# Try to connect explicitly to NetWalker database
try:
    conn = pyodbc.connect(
        'DRIVER={SQL Server};'
        'SERVER=eit-prisqldb01.tgna.tegna.com,1433;'
        'DATABASE=NetWalker;'
        'UID=NetWalker;'
        'PWD=FluffyBunnyHitbyaBus;'
        'Connection Timeout=30;'
    )
    
    cursor = conn.cursor()
    
    # Check what database we're connected to
    cursor.execute("SELECT DB_NAME()")
    db_name = cursor.fetchone()[0]
    print(f"✓ Connected to database: {db_name}")
    
    # Try to create the devices table
    try:
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'devices')
            BEGIN
                CREATE TABLE devices (
                    device_id INT IDENTITY(1,1) PRIMARY KEY,
                    device_name NVARCHAR(255) NOT NULL,
                    serial_number NVARCHAR(100) NOT NULL,
                    platform NVARCHAR(100) NULL,
                    hardware_model NVARCHAR(100) NULL,
                    first_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
                    last_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
                    status NVARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
                    updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
                    CONSTRAINT UQ_device_name_serial UNIQUE (device_name, serial_number)
                );
                CREATE INDEX IX_devices_status ON devices(status);
                CREATE INDEX IX_devices_last_seen ON devices(last_seen);
            END
        """)
        conn.commit()
        print("✓ Successfully created devices table (or it already exists)")
        
        # Check if table exists now
        cursor.execute("SELECT name FROM sys.tables WHERE name = 'devices'")
        if cursor.fetchone():
            print("✓ Confirmed: devices table exists")
        else:
            print("✗ Table creation may have failed")
            
    except Exception as e:
        print(f"✗ Error creating table: {e}")
        conn.rollback()
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Error connecting to NetWalker database: {e}")
