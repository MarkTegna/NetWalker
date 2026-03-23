#!/usr/bin/env python3
"""
Purge BORO devices and their orphaned neighbors from the database.

This script:
1. Deletes specified BORO devices
2. Finds devices that were only discovered through BORO devices (never walked)
3. Deletes those orphaned devices
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

# Devices to purge
BORO_DEVICES = [
    'BORO-UW02',
    'BORO-UW01',
    'BORO-MPR-SW01',
    'BORO-MDF-SW05',
    'BORO-MDF-SW04',
    'BORO-MDF-SW03',
    'BORO-MDF-SW02',
    'BORO-MDF-SW01',
    'BORO-LAB-CORE-A',
    'BORO-IDF-SW04',
    'BORO-IDF-SW03',
    'BORO-IDF-SW02',
    'BORO-IDF-SW01',
    'BORO-CORE-A'
]

def purge_devices():
    """Purge BORO devices and their orphaned neighbors."""
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
        # Step 1: Get IDs of BORO devices
        placeholders = ','.join('?' * len(BORO_DEVICES))
        cursor.execute(f"""
            SELECT device_id, device_name 
            FROM devices 
            WHERE device_name IN ({placeholders})
        """, BORO_DEVICES)
        
        boro_device_ids = []
        boro_found = []
        for row in cursor.fetchall():
            boro_device_ids.append(row.device_id)
            boro_found.append(row.device_name)
        
        print(f"\n{'='*70}")
        print(f"BORO DEVICES FOUND: {len(boro_found)}")
        print(f"{'='*70}")
        for name in boro_found:
            print(f"  - {name}")
        
        boro_not_found = set(BORO_DEVICES) - set(boro_found)
        if boro_not_found:
            print(f"\nBORO DEVICES NOT FOUND: {len(boro_not_found)}")
            for name in boro_not_found:
                print(f"  - {name}")
        
        if not boro_device_ids:
            print("\nNo BORO devices found in database. Nothing to purge.")
            return
        
        # Step 2: Find orphaned devices (discovered through BORO but never walked)
        id_placeholders = ','.join('?' * len(boro_device_ids))
        cursor.execute(f"""
            SELECT DISTINCT d.device_id, d.device_name, 
                   (SELECT TOP 1 ip_address FROM device_interfaces WHERE device_id = d.device_id) as ip_address,
                   d.status, d.connection_failures
            FROM devices d
            INNER JOIN device_neighbors dn ON d.device_id = dn.destination_device_id
            WHERE dn.source_device_id IN ({id_placeholders})
            AND d.status = 'discovered'
            AND d.device_id NOT IN ({id_placeholders})
        """, boro_device_ids + boro_device_ids)
        
        orphaned_devices = []
        for row in cursor.fetchall():
            orphaned_devices.append((row.device_id, row.device_name, row.ip_address, row.status, row.connection_failures))
        
        print(f"\n{'='*70}")
        print(f"ORPHANED DEVICES (discovered through BORO, never walked): {len(orphaned_devices)}")
        print(f"{'='*70}")
        if orphaned_devices:
            print(f"{'Device Name':<30} {'IP Address':<15} {'Status':<12} {'Failures'}")
            print(f"{'-'*30} {'-'*15} {'-'*12} {'-'*8}")
            for dev_id, name, ip, status, failures in orphaned_devices:
                print(f"{name:<30} {ip or 'N/A':<15} {status:<12} {failures}")
        
        # Step 3: Delete connections involving BORO devices
        cursor.execute(f"""
            DELETE FROM device_neighbors 
            WHERE source_device_id IN ({id_placeholders})
            OR destination_device_id IN ({id_placeholders})
        """, boro_device_ids + boro_device_ids)
        
        connections_deleted = cursor.rowcount
        print(f"\n{'='*70}")
        print(f"CONNECTIONS DELETED: {connections_deleted}")
        print(f"{'='*70}")
        
        # Step 4: Delete orphaned devices
        if orphaned_devices:
            orphaned_ids = [dev[0] for dev in orphaned_devices]
            orphan_placeholders = ','.join('?' * len(orphaned_ids))
            
            # Delete connections for orphaned devices
            cursor.execute(f"""
                DELETE FROM device_neighbors 
                WHERE source_device_id IN ({orphan_placeholders})
                OR destination_device_id IN ({orphan_placeholders})
            """, orphaned_ids + orphaned_ids)
            
            # Delete orphaned devices
            cursor.execute(f"""
                DELETE FROM devices 
                WHERE device_id IN ({orphan_placeholders})
            """, orphaned_ids)
            
            orphans_deleted = cursor.rowcount
            print(f"ORPHANED DEVICES DELETED: {orphans_deleted}")
        
        # Step 5: Delete BORO devices
        cursor.execute(f"""
            DELETE FROM devices 
            WHERE device_id IN ({id_placeholders})
        """, boro_device_ids)
        
        boro_deleted = cursor.rowcount
        print(f"BORO DEVICES DELETED: {boro_deleted}")
        
        # Commit all changes
        conn.commit()
        
        print(f"\n{'='*70}")
        print(f"PURGE COMPLETE")
        print(f"{'='*70}")
        print(f"Total BORO devices deleted: {boro_deleted}")
        print(f"Total orphaned devices deleted: {len(orphaned_devices) if orphaned_devices else 0}")
        print(f"Total connections deleted: {connections_deleted}")
        print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Failed to purge devices: {e}")
        raise
    
    finally:
        conn.close()

if __name__ == '__main__':
    purge_devices()
