"""Check which BORO devices have no connections"""
import pyodbc

# Database connection
conn_str = (
    "DRIVER={SQL Server};"
    "SERVER=eit-prisqldb01.tgna.tegna.com;"
    "DATABASE=NetWalker;"
    "UID=NetWalker;"
    "PWD=FluffyBunnyHitbyaBus"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Get BORO devices
cursor.execute("""
    SELECT device_name 
    FROM devices 
    WHERE device_name LIKE 'BORO%' AND status = 'active'
    ORDER BY device_name
""")
boro_devices = [row[0] for row in cursor.fetchall()]

# Get device IDs
device_ids = {}
cursor.execute("SELECT device_id, device_name FROM devices WHERE device_name LIKE 'BORO%'")
for row in cursor.fetchall():
    device_ids[row[1]] = row[0]

# Check connections for each device
print("BORO Devices and their connections:")
print("=" * 80)

for device_name in boro_devices:
    device_id = device_ids.get(device_name)
    if not device_id:
        continue
    
    # Get connections where this device is source
    cursor.execute("""
        SELECT 
            dn.source_interface,
            d.device_name as dest_name,
            dn.destination_interface,
            dn.protocol
        FROM device_neighbors dn
        JOIN devices d ON dn.destination_device_id = d.device_id
        WHERE dn.source_device_id = ?
    """, device_id)
    
    source_connections = cursor.fetchall()
    
    # Get connections where this device is destination
    cursor.execute("""
        SELECT 
            d.device_name as source_name,
            dn.source_interface,
            dn.destination_interface,
            dn.protocol
        FROM device_neighbors dn
        JOIN devices d ON dn.source_device_id = d.device_id
        WHERE dn.destination_device_id = ?
    """, device_id)
    
    dest_connections = cursor.fetchall()
    
    total_connections = len(source_connections) + len(dest_connections)
    
    print(f"\n{device_name}: {total_connections} connections")
    
    if source_connections:
        print(f"  As source ({len(source_connections)}):")
        for src_if, dest_name, dest_if, proto in source_connections:
            print(f"    {src_if:25s} -> {dest_name:20s} {dest_if:25s} ({proto})")
    
    if dest_connections:
        print(f"  As destination ({len(dest_connections)}):")
        for src_name, src_if, dest_if, proto in dest_connections:
            print(f"    {src_name:20s} {src_if:25s} -> {dest_if:25s} ({proto})")
    
    if total_connections == 0:
        print(f"  *** NO CONNECTIONS FOUND ***")

cursor.close()
conn.close()
