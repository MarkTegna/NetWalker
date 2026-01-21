"""
Diagnostic script to check BORO devices and connections for Visio diagram
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
    
    # Get all BORO devices
    print("\n=== BORO DEVICES ===")
    cursor.execute("""
        SELECT device_id, device_name, platform, hardware_model
        FROM devices
        WHERE device_name LIKE 'BORO%'
        ORDER BY device_name
    """)
    
    boro_devices = []
    for row in cursor.fetchall():
        device_id, device_name, platform, hardware_model = row
        boro_devices.append(device_name)
        print(f"  {device_id}: {device_name} ({platform}, {hardware_model})")
    
    print(f"\nTotal BORO devices: {len(boro_devices)}")
    
    # Get all connections from database
    print("\n=== ALL CONNECTIONS IN DATABASE ===")
    cursor.execute("""
        SELECT 
            n.neighbor_id,
            n.source_device_id,
            d1.device_name AS source_name,
            n.source_interface,
            n.destination_device_id,
            d2.device_name AS dest_name,
            n.destination_interface,
            n.protocol
        FROM device_neighbors n
        INNER JOIN devices d1 ON n.source_device_id = d1.device_id
        INNER JOIN devices d2 ON n.destination_device_id = d2.device_id
        ORDER BY d1.device_name, d2.device_name
    """)
    
    all_connections = []
    for row in cursor.fetchall():
        neighbor_id, src_id, src_name, src_if, dst_id, dst_name, dst_if, protocol = row
        all_connections.append((src_name, src_if, dst_name, dst_if))
        print(f"  {neighbor_id}: {src_name} ({src_if}) -> {dst_name} ({dst_if}) [{protocol}]")
    
    print(f"\nTotal connections in database: {len(all_connections)}")
    
    # Filter connections for BORO-to-BORO only
    print("\n=== BORO-TO-BORO CONNECTIONS (FILTERED) ===")
    boro_device_set = set(boro_devices)
    filtered_connections = []
    
    for src_name, src_if, dst_name, dst_if in all_connections:
        if src_name in boro_device_set and dst_name in boro_device_set:
            filtered_connections.append((src_name, src_if, dst_name, dst_if))
            print(f"  {src_name} ({src_if}) -> {dst_name} ({dst_if})")
        else:
            if src_name.startswith('BORO') or dst_name.startswith('BORO'):
                print(f"  FILTERED OUT: {src_name} -> {dst_name} (one device not in BORO set)")
    
    print(f"\nTotal BORO-to-BORO connections: {len(filtered_connections)}")
    
    # Check which BORO devices have NO connections
    print("\n=== BORO DEVICES WITH NO CONNECTIONS ===")
    devices_with_connections = set()
    for src_name, _, dst_name, _ in filtered_connections:
        devices_with_connections.add(src_name)
        devices_with_connections.add(dst_name)
    
    devices_without_connections = boro_device_set - devices_with_connections
    if devices_without_connections:
        for device in sorted(devices_without_connections):
            print(f"  {device}")
    else:
        print("  All BORO devices have connections!")
    
    print(f"\nDevices with connections: {len(devices_with_connections)}")
    print(f"Devices without connections: {len(devices_without_connections)}")
    
    # Check connection count per device
    print("\n=== CONNECTION COUNT PER DEVICE ===")
    connection_counts = {}
    for src_name, _, dst_name, _ in filtered_connections:
        connection_counts[src_name] = connection_counts.get(src_name, 0) + 1
        connection_counts[dst_name] = connection_counts.get(dst_name, 0) + 1
    
    for device in sorted(boro_devices):
        count = connection_counts.get(device, 0)
        print(f"  {device}: {count} connections")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
