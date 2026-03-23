#!/usr/bin/env python3
"""
Purge Poly CCX 500 device from the database.
"""

import pyodbc
from datetime import datetime
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

def purge_polyccx500():
    """Purge Poly CCX 500 device."""
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
        # Find the Poly CCX 500 device
        cursor.execute("""
            SELECT device_id, device_name, serial_number, platform, status, connection_failures
            FROM devices
            WHERE device_name = 'Poly CCX 500'
        """)
        
        device = cursor.fetchone()
        
        if not device:
            print("Device 'Poly CCX 500' not found in database")
            return
        
        device_id = device.device_id
        device_name = device.device_name
        
        print(f"\n{'='*70}")
        print(f"DEVICE TO PURGE")
        print(f"{'='*70}")
        print(f"Device Name: {device.device_name}")
        print(f"Device ID: {device_id}")
        print(f"Serial: {device.serial_number}")
        print(f"Platform: {device.platform}")
        print(f"Status: {device.status}")
        print(f"Connection Failures: {device.connection_failures}")
        
        # Get connection count
        cursor.execute("""
            SELECT COUNT(*) 
            FROM device_neighbors
            WHERE source_device_id = ? OR destination_device_id = ?
        """, device_id, device_id)
        
        connection_count = cursor.fetchone()[0]
        
        print(f"\n{'='*70}")
        print(f"CONNECTIONS TO DELETE: {connection_count}")
        print(f"{'='*70}")
        
        # Delete connections
        cursor.execute("""
            DELETE FROM device_neighbors
            WHERE source_device_id = ? OR destination_device_id = ?
        """, device_id, device_id)
        
        connections_deleted = cursor.rowcount
        
        # Delete device
        cursor.execute("""
            DELETE FROM devices
            WHERE device_id = ?
        """, device_id)
        
        device_deleted = cursor.rowcount
        
        # Commit changes
        conn.commit()
        
        print(f"\n{'='*70}")
        print(f"PURGE COMPLETE")
        print(f"{'='*70}")
        print(f"Device deleted: {device_name}")
        print(f"Connections deleted: {connections_deleted}")
        print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Failed to purge device: {e}")
        raise
    
    finally:
        conn.close()

if __name__ == '__main__':
    purge_polyccx500()
