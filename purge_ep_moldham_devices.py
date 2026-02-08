"""
Purge all devices starting with 'ep-moldham' from the database
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

def purge_ep_moldham_devices():
    """Purge all devices starting with 'ep-moldham'"""
    
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # First, find all devices starting with 'ep-moldham'
        query = """
        SELECT device_id, device_name, serial_number, platform, hardware_model
        FROM devices
        WHERE device_name LIKE 'ep-moldham%'
        ORDER BY device_name
        """
        
        cursor.execute(query)
        devices = cursor.fetchall()
        
        if not devices:
            print("\nNo devices found starting with 'ep-moldham'")
            return
        
        print(f"\nFound {len(devices)} devices starting with 'ep-moldham':")
        print("=" * 100)
        
        for device in devices:
            device_id, name, serial, platform, hw = device
            print(f"  {name} (ID: {device_id})")
            print(f"    Serial: {serial}, Platform: {platform}, Hardware: {hw}")
        
        print("\n" + "=" * 100)
        print(f"\nThis will DELETE {len(devices)} devices and all their related records.")
        print("Related records include: interfaces, versions, VLANs, and neighbor connections.")
        
        response = input("\nAre you sure you want to proceed? (yes/no): ")
        
        if response.lower() not in ['yes', 'y']:
            print("Purge cancelled")
            return
        
        # Delete devices (CASCADE will handle related records)
        print("\nDeleting devices...")
        
        deleted_count = 0
        for device in devices:
            device_id, name = device[0], device[1]
            
            # Delete the device (CASCADE will handle related records)
            cursor.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
            deleted_count += 1
            print(f"  Deleted: {name} (ID: {device_id})")
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "=" * 100)
        print(f"\nPurge Summary:")
        print(f"  Devices deleted: {deleted_count}")
        print(f"  Total devices remaining: {get_device_count(cursor)}")
        
    except Exception as e:
        print(f"Error purging devices: {e}")
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
    print("NetWalker Database - Purge ep-moldham Devices")
    print("=" * 100)
    purge_ep_moldham_devices()
