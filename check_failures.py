#!/usr/bin/env python3
"""
Check if any devices have connection failures > 0.
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

def check_failures():
    """Check for devices with connection failures > 0."""
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
        # Get count of devices with failures > 0
        cursor.execute("""
            SELECT COUNT(*) 
            FROM devices 
            WHERE connection_failures > 0
        """)
        
        count = cursor.fetchone()[0]
        
        print(f"\n{'='*70}")
        print(f"CONNECTION FAILURES CHECK")
        print(f"{'='*70}")
        print(f"Devices with connection_failures > 0: {count}")
        
        if count > 0:
            # Show the devices
            cursor.execute("""
                SELECT device_name, connection_failures
                FROM devices
                WHERE connection_failures > 0
                ORDER BY connection_failures DESC, device_name
            """)
            
            devices = cursor.fetchall()
            print(f"\n{'Device Name':<40} {'Failures'}")
            print(f"{'-'*40} {'-'*8}")
            for device in devices:
                print(f"{device.device_name:<40} {device.connection_failures}")
        else:
            print("\nAll devices have connection_failures = 0")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to check: {e}")
        raise
    
    finally:
        conn.close()

if __name__ == '__main__':
    check_failures()
