"""
Clean up duplicate device records in the database
Merges "unwalked neighbor" records with their walked counterparts
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

def cleanup_duplicates():
    """Clean up duplicate device records"""
    
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Find all device names that have duplicates
        query = """
        SELECT device_name, COUNT(*) as count
        FROM devices
        GROUP BY device_name
        HAVING COUNT(*) > 1
        ORDER BY device_name
        """
        
        cursor.execute(query)
        duplicates = cursor.fetchall()
        
        print(f"\nFound {len(duplicates)} device names with duplicates")
        print("=" * 100)
        
        merged_count = 0
        deleted_count = 0
        
        for device_name, count in duplicates:
            # Get all records for this device
            cursor.execute("""
                SELECT device_id, serial_number, platform, hardware_model, capabilities, first_seen, last_seen
                FROM devices
                WHERE device_name = ?
                ORDER BY first_seen
            """, (device_name,))
            
            records = cursor.fetchall()
            
            # Find unwalked neighbor (serial='unknown') and walked version (serial != 'unknown')
            unwalked = None
            walked = None
            
            for record in records:
                device_id, serial, platform, hw, cap, first, last = record
                if serial == 'unknown':
                    unwalked = record
                else:
                    walked = record
                    break  # Use the first walked version found
            
            if unwalked and walked:
                unwalked_id = unwalked[0]
                walked_id = walked[0]
                walked_serial = walked[1]
                walked_platform = walked[2]
                walked_hw = walked[3]
                walked_cap = walked[4]
                unwalked_first_seen = unwalked[5]
                walked_last_seen = walked[6]
                
                print(f"\nMerging: {device_name}")
                print(f"  Unwalked ID: {unwalked_id} (first_seen: {unwalked_first_seen})")
                print(f"  Walked ID: {walked_id} (serial: {walked_serial})")
                
                # Update walked record to use earlier first_seen date if unwalked was seen first
                cursor.execute("""
                    UPDATE devices
                    SET first_seen = ?
                    WHERE device_id = ? AND first_seen > ?
                """, (unwalked_first_seen, walked_id, unwalked_first_seen))
                
                # Move any related records from unwalked to walked device
                # Update device_versions
                cursor.execute("""
                    UPDATE device_versions
                    SET device_id = ?
                    WHERE device_id = ?
                    AND NOT EXISTS (
                        SELECT 1 FROM device_versions dv2
                        WHERE dv2.device_id = ? AND dv2.software_version = device_versions.software_version
                    )
                """, (walked_id, unwalked_id, walked_id))
                
                # Update device_interfaces
                cursor.execute("""
                    UPDATE device_interfaces
                    SET device_id = ?
                    WHERE device_id = ?
                    AND NOT EXISTS (
                        SELECT 1 FROM device_interfaces di2
                        WHERE di2.device_id = ? AND di2.interface_name = device_interfaces.interface_name
                        AND di2.ip_address = device_interfaces.ip_address
                    )
                """, (walked_id, unwalked_id, walked_id))
                
                # Update device_vlans
                cursor.execute("""
                    UPDATE device_vlans
                    SET device_id = ?
                    WHERE device_id = ?
                    AND NOT EXISTS (
                        SELECT 1 FROM device_vlans dv2
                        WHERE dv2.device_id = ? AND dv2.vlan_id = device_vlans.vlan_id
                    )
                """, (walked_id, unwalked_id, walked_id))
                
                # Update device_neighbors (as source device)
                cursor.execute("""
                    UPDATE device_neighbors
                    SET source_device_id = ?
                    WHERE source_device_id = ?
                    AND NOT EXISTS (
                        SELECT 1 FROM device_neighbors dn2
                        WHERE dn2.source_device_id = ? 
                        AND dn2.destination_device_id = device_neighbors.destination_device_id
                        AND dn2.source_interface = device_neighbors.source_interface
                    )
                """, (walked_id, unwalked_id, walked_id))
                
                # Update device_neighbors (as destination device)
                cursor.execute("""
                    UPDATE device_neighbors
                    SET destination_device_id = ?
                    WHERE destination_device_id = ?
                    AND NOT EXISTS (
                        SELECT 1 FROM device_neighbors dn2
                        WHERE dn2.source_device_id = device_neighbors.source_device_id
                        AND dn2.destination_device_id = ?
                        AND dn2.source_interface = device_neighbors.source_interface
                    )
                """, (walked_id, unwalked_id, walked_id))
                
                # Delete any remaining related records for unwalked device
                cursor.execute("DELETE FROM device_neighbors WHERE source_device_id = ? OR destination_device_id = ?", 
                             (unwalked_id, unwalked_id))
                cursor.execute("DELETE FROM device_vlans WHERE device_id = ?", (unwalked_id,))
                cursor.execute("DELETE FROM device_interfaces WHERE device_id = ?", (unwalked_id,))
                cursor.execute("DELETE FROM device_versions WHERE device_id = ?", (unwalked_id,))
                
                # Delete the unwalked neighbor record
                cursor.execute("DELETE FROM devices WHERE device_id = ?", (unwalked_id,))
                
                print(f"  Deleted unwalked neighbor record (ID: {unwalked_id})")
                
                merged_count += 1
                deleted_count += 1
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "=" * 100)
        print(f"\nCleanup Summary:")
        print(f"  Devices merged: {merged_count}")
        print(f"  Duplicate records deleted: {deleted_count}")
        print(f"  Total devices remaining: {get_device_count(cursor)}")
        
    except Exception as e:
        print(f"Error cleaning up duplicates: {e}")
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
    print("NetWalker Database Duplicate Cleanup")
    print("=" * 100)
    print("\nThis script will merge 'unwalked neighbor' records with their walked counterparts")
    print("and delete the duplicate unwalked neighbor records.\n")
    
    response = input("Do you want to proceed? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        cleanup_duplicates()
    else:
        print("Cleanup cancelled")
