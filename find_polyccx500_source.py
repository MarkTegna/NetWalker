#!/usr/bin/env python3
"""
Find which device discovered PolyCCX500 as a neighbor.
"""

import pyodbc
import configparser
import base64

# Read database configuration from netwalker.ini
config = configparser.ConfigParser()
config.read('netwalker.ini')

# Decrypt password (simple base64 encoding)
encrypted_password = config.get('database', 'password').replace('ENC:', '')
password = base64.b64decode(encrypted_password).decode('utf-8')

# Database configuration
DB_SERVER = config.get('database', 'server')
DB_NAME = config.get('database', 'database')
DB_USER = config.get('database', 'username')
DB_PASSWORD = password
DB_PORT = config.get('database', 'port')

def find_polyccx500_source():
    """Find which device discovered PolyCCX500."""
    # Build connection string
    conn_str = (
        f"DRIVER={{SQL Server}};"
        f"SERVER={DB_SERVER},{DB_PORT};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        f"TrustServerCertificate=yes;"
    )
    
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    try:
        # First, find the Poly CCX 500 device
        cursor.execute("""
            SELECT device_id, device_name, serial_number, platform, status, connection_failures
            FROM devices
            WHERE device_name = 'Poly CCX 500'
        """)
        
        polyccx_devices = cursor.fetchall()
        
        if not polyccx_devices:
            print("Device 'Poly CCX 500' not found")
            return
        
        print(f"\n{'='*80}")
        print(f"POLY CCX 500 DEVICE FOUND")
        print(f"{'='*80}")
        
        for device in polyccx_devices:
            device_id = device.device_id
            device_name = device.device_name
            serial = device.serial_number
            platform = device.platform
            status = device.status
            failures = device.connection_failures
            
            print(f"\nDevice: {device_name}")
            print(f"  Device ID: {device_id}")
            print(f"  Serial: {serial}")
            print(f"  Platform: {platform}")
            print(f"  Status: {status}")
            print(f"  Connection Failures: {failures}")
            
            # Get IP address from device_interfaces
            cursor.execute("""
                SELECT ip_address, interface_name
                FROM device_interfaces
                WHERE device_id = ?
            """, device_id)
            
            interfaces = cursor.fetchall()
            if interfaces:
                print(f"  IP Addresses:")
                for iface in interfaces:
                    print(f"    {iface.ip_address} ({iface.interface_name})")
            
            # Find which devices discovered this device as a neighbor
            cursor.execute("""
                SELECT 
                    d.device_name as source_device,
                    dn.source_interface,
                    dn.destination_interface,
                    dn.protocol,
                    dn.first_seen,
                    dn.last_seen
                FROM device_neighbors dn
                INNER JOIN devices d ON dn.source_device_id = d.device_id
                WHERE dn.destination_device_id = ?
                ORDER BY dn.first_seen
            """, device_id)
            
            neighbors = cursor.fetchall()
            
            print(f"\n  DISCOVERED BY ({len(neighbors)} connection(s)):")
            print(f"  {'-'*76}")
            print(f"  {'Source Device':<30} {'Source Port':<20} {'Protocol':<10} {'First Seen'}")
            print(f"  {'-'*76}")
            
            if neighbors:
                for neighbor in neighbors:
                    print(f"  {neighbor.source_device:<30} {neighbor.source_interface:<20} {neighbor.protocol:<10} {neighbor.first_seen}")
            else:
                print(f"  No neighbor connections found (device may have been seed device)")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to query database: {e}")
        raise
    
    finally:
        conn.close()

if __name__ == '__main__':
    find_polyccx500_source()
