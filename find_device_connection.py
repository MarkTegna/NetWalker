"""
Find device connection information
Author: Mark Oldham
"""

import pyodbc
import base64
import sys

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
        return connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def find_device_connection(device_name):
    """Find where a device is connected"""
    
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Search for device (case-insensitive, partial match)
        query = """
        SELECT device_id, device_name, serial_number, platform, hardware_model, capabilities
        FROM devices
        WHERE device_name LIKE ?
        """
        
        cursor.execute(query, f"%{device_name}%")
        devices = cursor.fetchall()
        
        if not devices:
            print(f"\nNo devices found matching: {device_name}")
            return
        
        print(f"\nFound {len(devices)} device(s) matching '{device_name}':")
        print("=" * 120)
        
        for device in devices:
            device_id, name, serial, platform, hw, cap = device
            print(f"\nDevice: {name} (ID: {device_id})")
            print(f"  Serial: {serial}")
            print(f"  Platform: {platform}")
            print(f"  Hardware: {hw}")
            print(f"  Capabilities: {cap}")
            
            # Get IP addresses
            ip_query = """
            SELECT interface_name, ip_address, interface_type
            FROM device_interfaces
            WHERE device_id = ?
            ORDER BY last_seen DESC
            """
            cursor.execute(ip_query, device_id)
            interfaces = cursor.fetchall()
            
            if interfaces:
                print(f"\n  IP Addresses:")
                for iface_name, ip, iface_type in interfaces:
                    print(f"    {iface_name}: {ip} ({iface_type})")
            
            # Find connections where this device is the destination (what it's connected TO)
            neighbor_query = """
            SELECT 
                d.device_name as source_device,
                dn.source_interface,
                dn.destination_interface,
                dn.protocol,
                dn.last_seen
            FROM device_neighbors dn
            JOIN devices d ON dn.source_device_id = d.device_id
            WHERE dn.destination_device_id = ?
            ORDER BY dn.last_seen DESC
            """
            
            cursor.execute(neighbor_query, device_id)
            connections = cursor.fetchall()
            
            if connections:
                print(f"\n  Connected TO (upstream devices):")
                for src_dev, src_iface, dst_iface, protocol, last_seen in connections:
                    print(f"    {src_dev} [{src_iface}] --{protocol}--> [{dst_iface}] (Last seen: {last_seen})")
            else:
                print(f"\n  No upstream connections found")
            
            # Find connections where this device is the source (what's connected TO IT)
            downstream_query = """
            SELECT 
                d.device_name as dest_device,
                dn.source_interface,
                dn.destination_interface,
                dn.protocol,
                dn.last_seen
            FROM device_neighbors dn
            JOIN devices d ON dn.destination_device_id = d.device_id
            WHERE dn.source_device_id = ?
            ORDER BY dn.last_seen DESC
            """
            
            cursor.execute(downstream_query, device_id)
            downstream = cursor.fetchall()
            
            if downstream:
                print(f"\n  Devices connected TO this device (downstream):")
                for dst_dev, src_iface, dst_iface, protocol, last_seen in downstream:
                    print(f"    [{src_iface}] --{protocol}--> {dst_dev} [{dst_iface}] (Last seen: {last_seen})")
            
            print("\n" + "=" * 120)
        
    except Exception as e:
        print(f"Error finding device: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        device_name = " ".join(sys.argv[1:])
    else:
        device_name = "AXIS T8508 -   ACCC8ECF511A"
    
    print(f"Searching for device: {device_name}")
    print("=" * 120)
    find_device_connection(device_name)
