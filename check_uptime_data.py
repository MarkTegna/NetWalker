#!/usr/bin/env python3
"""
Check if uptime data exists in the database.
"""

import pyodbc
import configparser
import base64

# Read database configuration from netwalker.ini
config = configparser.ConfigParser()
config.read('netwalker.ini')

encrypted_password = config.get('database', 'password').replace('ENC:', '')
password = base64.b64decode(encrypted_password).decode('utf-8')

DB_SERVER = config.get('database', 'server')
DB_NAME = config.get('database', 'database')
DB_USER = config.get('database', 'username')
DB_PASSWORD = password
DB_PORT = config.get('database', 'port')

def check_uptime():
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
        # Check all columns in devices table
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'devices' ORDER BY ORDINAL_POSITION")
        print("Columns in 'devices' table:")
        for row in cursor.fetchall():
            print(f"  - {row.COLUMN_NAME}")
        
        # Check if there's an uptime column anywhere
        cursor.execute("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME LIKE '%uptime%'")
        results = cursor.fetchall()
        if results:
            print(f"\nTables with 'uptime' columns:")
            for row in results:
                print(f"  - {row.TABLE_NAME}.{row.COLUMN_NAME}")
        else:
            print(f"\nNo 'uptime' columns found in any table")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    check_uptime()
