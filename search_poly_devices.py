#!/usr/bin/env python3
"""
Search for Poly devices in the database.
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

def search_poly_devices():
    """Search for Poly devices."""
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
        # Search for devices with 'Poly' or 'CCX' in the name
        cursor.execute("""
            SELECT device_id, device_name, serial_number, platform, status
            FROM devices
            WHERE device_name LIKE '%Poly%' 
               OR device_name LIKE '%CCX%'
               OR platform LIKE '%Poly%'
               OR platform LIKE '%CCX%'
            ORDER BY device_name
        """)
        
        devices = cursor.fetchall()
        
        print(f"\n{'='*80}")
        print(f"POLY/CCX DEVICES FOUND: {len(devices)}")
        print(f"{'='*80}")
        print(f"{'Device Name':<40} {'Platform':<30} {'Status'}")
        print(f"{'-'*40} {'-'*30} {'-'*10}")
        
        for device in devices:
            print(f"{device.device_name:<40} {device.platform or 'N/A':<30} {device.status}")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to query database: {e}")
        raise
    
    finally:
        conn.close()

if __name__ == '__main__':
    search_poly_devices()
