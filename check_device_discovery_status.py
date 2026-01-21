"""
Check device discovery status and neighbor data in database
"""
import pyodbc
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
conn_str = (
    "DRIVER={SQL Server};"
    "SERVER=eit-prisqldb01.tgna.tegna.com;"
    "DATABASE=NetWalker;"
    "UID=NetWalker;"
    "PWD=FluffyBunnyHitbyaBus"
)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Get all BORO devices with their discovery status
    print("\n=== BORO DEVICES - DISCOVERY STATUS ===")
    cursor.execute("""
        SELECT 
            device_id, 
            device_name, 
            platform, 
            hardware_model,
            first_seen,
            last_seen,
            created_at,
            updated_at
        FROM devices
        WHERE device_name LIKE 'BORO%'
        ORDER BY device_name
    """)
    
    boro_devices = {}
    for row in cursor.fetchall():
        device_id, device_name, platform, hardware_model, first_seen, last_seen, created_at, updated_at = row
        boro_devices[device_id] = device_name
        print(f"\n{device_name} (ID: {device_id})")
        print(f"  Platform: {platform}")
        print(f"  Hardware: {hardware_model}")
        print(f"  First seen: {first_seen}")
        print(f"  Last seen: {last_seen}")
        print(f"  Created: {created_at}")
        print(f"  Updated: {updated_at}")
    
    # Check raw neighbor data for each device
    print("\n\n=== RAW NEIGHBOR DATA BY DEVICE ===")
    for device_id, device_name in boro_devices.items():
        print(f"\n{device_name} (ID: {device_id}):")
        
        # Check as source device
        cursor.execute("""
            SELECT 
                neighbor_id,
                source_interface,
                destination_device_id,
                destination_interface,
                protocol,
                first_seen,
                last_seen
            FROM device_neighbors
            WHERE source_device_id = ?
            ORDER BY neighbor_id
        """, (device_id,))
        
        source_neighbors = cursor.fetchall()
        if source_neighbors:
            print(f"  As SOURCE ({len(source_neighbors)} connections):")
            for row in source_neighbors:
                neighbor_id, src_if, dst_id, dst_if, protocol, first_seen, last_seen = row
                dst_name = boro_devices.get(dst_id, f"Unknown-{dst_id}")
                print(f"    [{neighbor_id}] {src_if} -> {dst_name} ({dst_if}) [{protocol}]")
                print(f"         First: {first_seen}, Last: {last_seen}")
        else:
            print(f"  As SOURCE: NO CONNECTIONS")
        
        # Check as destination device
        cursor.execute("""
            SELECT 
                neighbor_id,
                source_device_id,
                source_interface,
                destination_interface,
                protocol,
                first_seen,
                last_seen
            FROM device_neighbors
            WHERE destination_device_id = ?
            ORDER BY neighbor_id
        """, (device_id,))
        
        dest_neighbors = cursor.fetchall()
        if dest_neighbors:
            print(f"  As DESTINATION ({len(dest_neighbors)} connections):")
            for row in dest_neighbors:
                neighbor_id, src_id, src_if, dst_if, protocol, first_seen, last_seen = row
                src_name = boro_devices.get(src_id, f"Unknown-{src_id}")
                print(f"    [{neighbor_id}] {src_name} ({src_if}) -> {dst_if} [{protocol}]")
                print(f"         First: {first_seen}, Last: {last_seen}")
        else:
            print(f"  As DESTINATION: NO CONNECTIONS")
    
    # Check if devices without connections were actually walked
    print("\n\n=== DEVICES WITHOUT CONNECTIONS - INVESTIGATION ===")
    devices_without_connections = [
        'BORO-IDF-SW01', 'BORO-IDF-SW02', 'BORO-IDF-SW03', 'BORO-IDF-SW04',
        'BORO-LAB-CORE-A', 'BORO-MPR-SW01'
    ]
    
    for device_name in devices_without_connections:
        print(f"\n{device_name}:")
        
        # Check if device exists in devices table
        cursor.execute("""
            SELECT device_id, platform, last_seen
            FROM devices
            WHERE device_name = ?
        """, (device_name,))
        
        row = cursor.fetchone()
        if row:
            device_id, platform, last_seen = row
            print(f"  [OK] Device exists in database (ID: {device_id})")
            print(f"       Platform: {platform}, Last seen: {last_seen}")
            
            # Check if device has any interfaces
            cursor.execute("""
                SELECT COUNT(*) FROM device_interfaces
                WHERE device_id = ?
            """, (device_id,))
            
            interface_count = cursor.fetchone()[0]
            print(f"       Interfaces: {interface_count}")
            
            # Check if device has any VLANs
            cursor.execute("""
                SELECT COUNT(*) FROM device_vlans
                WHERE device_id = ?
            """, (device_id,))
            
            vlan_count = cursor.fetchone()[0]
            print(f"       VLANs: {vlan_count}")
            
            # This suggests the device was discovered but has no neighbor data
            print(f"  [ISSUE] Device was discovered but has NO neighbor connections!")
            print(f"          Possible causes:")
            print(f"          - Device has no CDP/LLDP neighbors")
            print(f"          - CDP/LLDP not enabled on device")
            print(f"          - Neighbor data collection failed")
            print(f"          - Neighbors not in BORO site (filtered out)")
        else:
            print(f"  [ERROR] Device NOT found in database!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
