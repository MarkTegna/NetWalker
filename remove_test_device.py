"""
Remove TEST-DEVICE from the database
Author: Mark Oldham
"""

import pyodbc
import base64

def decode_password(encoded_password):
    """Decode the encrypted password"""
    if encoded_password.startswith("ENC:"):
        encoded_password = encoded_password[4:]
    return base64.b64decode(encoded_password).decode('utf-8')

def connect_to_database():
    """Connect to the NetWalker database"""
    server = "eit-prisqldb01.tgna.tegna.com"
    port = 1433
    database = "NetWalker"
    username = "NetWalker"
    encoded_password = "ENC:Rmx1ZmZ5QnVubnlIaXRieWFCdXM="
    
    password = decode_password(encoded_password)
    
    conn_str = (
        f"DRIVER={{SQL Server}};"
        f"SERVER={server},{port};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"TrustServerCertificate=yes;"
    )
    
    try:
        connection = pyodbc.connect(conn_str, timeout=30)
        print(f"Connected to database: {database}")
        return connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def remove_test_device():
    """Remove TEST-DEVICE from the database"""
    
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Find TEST-DEVICE
        query = """
        SELECT device_id, device_name, serial_number, platform, hardware_model
        FROM devices
        WHERE device_name = 'TEST-DEVICE'
        """
        
        cursor.execute(query)
        devices = cursor.fetchall()
        
        if not devices:
            print("\nNo device found with name 'TEST-DEVICE'")
            return
        
        print(f"\nFound {len(devices)} device(s) named 'TEST-DEVICE':")
        print("=" * 100)
        
        for device in devices:
            device_id, name, serial, platform, hw = device
            print(f"  {name} (ID: {device_id})")
            print(f"    Serial: {serial}, Platform: {platform}, Hardware: {hw}")
        
        print("\n" + "=" * 100)
        
        # Delete devices (CASCADE will handle related records)
        print("\nDeleting TEST-DEVICE...")
        
        deleted_count = 0
        for device in devices:
            device_id, name = device[0], device[1]
            
            cursor.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
            deleted_count += 1
            print(f"  Deleted: {name} (ID: {device_id})")
        
        # Commit changes
        conn.commit()
        
        print("\n" + "=" * 100)
        print(f"\nRemoval Summary:")
        print(f"  Devices deleted: {deleted_count}")
        print(f"  Total devices remaining: {get_device_count(cursor)}")
        
    except Exception as e:
        print(f"Error removing device: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
    finally:
        conn.close()

def get_device_count(cursor):
    """Get total device count"""
    cursor.execute("SELECT COUNT(*) FROM devices")
    return cursor.fetchone()[0]

if __name__ == "__main__":
    print("NetWalker Database - Remove TEST-DEVICE")
    print("=" * 100)
    remove_test_device()
