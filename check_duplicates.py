"""
Check for duplicate device records in the database
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

def check_duplicates():
    """Check for duplicate device records"""
    
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Find devices with duplicate names
        query = """
        SELECT 
            device_name,
            COUNT(*) as count
        FROM devices
        GROUP BY device_name
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC, device_name
        """
        
        cursor.execute(query)
        duplicates = cursor.fetchall()
        
        print(f"\nFound {len(duplicates)} device names with duplicates:")
        print("=" * 120)
        
        for row in duplicates:
            device_name, count = row
            print(f"\nDevice: {device_name}")
            print(f"  Count: {count}")
            
            # Get detailed info for each duplicate
            detail_query = """
            SELECT 
                device_id,
                device_name,
                serial_number,
                platform,
                hardware_model,
                capabilities,
                first_seen,
                last_seen,
                status
            FROM devices
            WHERE device_name = ?
            ORDER BY first_seen
            """
            
            cursor.execute(detail_query, device_name)
            details = cursor.fetchall()
            
            print(f"  Details:")
            for detail in details:
                device_id, name, serial, plat, hw, cap, first, last, stat = detail
                print(f"    ID {device_id}: Serial={serial}, Platform={plat}, HW={hw}")
                print(f"             Capabilities={cap}")
                print(f"             First={first}, Last={last}, Status={stat}")
        
        # Check for "unwalked neighbor" pattern
        print("\n" + "=" * 120)
        print("\nChecking for 'unwalked neighbor' serial numbers:")
        
        unwalked_query = """
        SELECT 
            device_id,
            device_name,
            serial_number,
            platform,
            hardware_model,
            capabilities,
            first_seen,
            last_seen
        FROM devices
        WHERE serial_number LIKE '%unwalked neighbor%'
        ORDER BY device_name
        """
        
        cursor.execute(unwalked_query)
        unwalked = cursor.fetchall()
        
        print(f"Found {len(unwalked)} devices with 'unwalked neighbor' serial numbers")
        
        for row in unwalked:
            device_id, name, serial, plat, hw, cap, first, last = row
            print(f"\n  Device: {name} (ID: {device_id})")
            print(f"    Serial: {serial}")
            print(f"    Platform: {plat}")
            print(f"    Hardware: {hw}")
            print(f"    First seen: {first}")
            print(f"    Last seen: {last}")
            
            # Check if there's a walked version
            walked_query = """
            SELECT device_id, serial_number, platform, hardware_model, last_seen
            FROM devices
            WHERE device_name = ? AND serial_number NOT LIKE '%unwalked neighbor%'
            """
            cursor.execute(walked_query, name)
            walked_versions = cursor.fetchall()
            
            if walked_versions:
                print(f"    ** DUPLICATE: Found {len(walked_versions)} walked version(s):")
                for wv in walked_versions:
                    wv_id, wv_serial, wv_plat, wv_hw, wv_last = wv
                    print(f"       ID {wv_id}: Serial={wv_serial}, Platform={wv_plat}, HW={wv_hw}, Last={wv_last}")
        
    except Exception as e:
        print(f"Error checking duplicates: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    print("NetWalker Database Duplicate Check")
    print("=" * 120)
    check_duplicates()
