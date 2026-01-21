"""Check BORO connections in database"""
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
print("BORO Devices:")
cursor.execute("""
    SELECT device_name 
    FROM devices 
    WHERE device_name LIKE 'BORO%' AND status = 'active'
    ORDER BY device_name
""")
boro_devices = [row[0] for row in cursor.fetchall()]
print(f"Found {len(boro_devices)} devices:")
for dev in boro_devices:
    print(f"  - {dev}")

# Get all connections for BORO devices
print("\nAll Connections (including duplicates):")
cursor.execute("""
    SELECT 
        source_device_id,
        source_interface,
        destination_device_id,
        destination_interface,
        protocol
    FROM device_neighbors
    ORDER BY source_device_id, destination_device_id
""")

all_connections = cursor.fetchall()
print(f"Total connections in database: {len(all_connections)}")

# Get device names
device_names = {}
cursor.execute("SELECT device_id, device_name FROM devices")
for row in cursor.fetchall():
    device_names[row[0]] = row[1]

# Filter to BORO connections
boro_device_names = set(boro_devices)
boro_connections = []

for conn_row in all_connections:
    source_id, source_if, dest_id, dest_if, protocol = conn_row
    source_name = device_names.get(source_id, '')
    dest_name = device_names.get(dest_id, '')
    
    if source_name in boro_device_names and dest_name in boro_device_names:
        boro_connections.append((source_name, source_if, dest_name, dest_if, protocol))

print(f"\nBORO Connections: {len(boro_connections)}")
for i, (src, src_if, dst, dst_if, proto) in enumerate(boro_connections, 1):
    print(f"{i:2d}. {src:20s} {src_if:20s} -> {dst:20s} {dst_if:20s} ({proto})")

# Check for bidirectional deduplication
print("\nChecking for bidirectional pairs:")
seen = set()
unique_connections = []
for src, src_if, dst, dst_if, proto in boro_connections:
    # Create a normalized key (alphabetically sorted)
    if src < dst:
        key = (src, src_if, dst, dst_if)
    else:
        key = (dst, dst_if, src, src_if)
    
    if key not in seen:
        seen.add(key)
        unique_connections.append((src, src_if, dst, dst_if, proto))

print(f"\nUnique connections after deduplication: {len(unique_connections)}")
for i, (src, src_if, dst, dst_if, proto) in enumerate(unique_connections, 1):
    print(f"{i:2d}. {src:20s} {src_if:20s} <-> {dst:20s} {dst_if:20s} ({proto})")

cursor.close()
conn.close()
