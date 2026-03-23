#!/usr/bin/env python3
"""
Reset all connection failure counts to 0.
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

def reset_all_failures():
    """Reset all connection failure counts to 0."""
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
        
        count_before = cursor.fetchone()[0]
        
        print(f"\n{'='*70}")
        print(f"RESET CONNECTION FAILURES")
        print(f"{'='*70}")
        print(f"Devices with failures > 0: {count_before}")
        
        if count_before == 0:
            print("\nNo devices with connection failures found. Nothing to reset.")
            return
        
        # Reset all connection failures to 0
        cursor.execute("""
            UPDATE devices 
            SET connection_failures = 0 
            WHERE connection_failures > 0
        """)
        
        rows_updated = cursor.rowcount
        
        # Commit changes
        conn.commit()
        
        print(f"\n{'='*70}")
        print(f"RESET COMPLETE")
        print(f"{'='*70}")
        print(f"Devices updated: {rows_updated}")
        print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Failed to reset failures: {e}")
        raise
    
    finally:
        conn.close()

if __name__ == '__main__':
    reset_all_failures()
