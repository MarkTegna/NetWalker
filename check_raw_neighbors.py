"""Check raw device_neighbors table"""
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

# Get device ID mapping
print("Device ID Mapping:")
cursor.execute("SELECT device_id, device_name FROM devices WHERE device_name LIKE 'BORO%' ORDER BY device_id")
device_map = {}
for row in cursor.fetchall():
    device_map[row[0]] = row[1]
    print(f"  {row[0]:3d} = {row[1]}")

print("\n" + "=" * 100)
print("Raw device_neighbors table (all rows):")
print("=" * 100)

cursor.execute("""
    SELECT 
        neighbor_id,
        source_device_id,
        source_interface,
        destination_device_id,
        destination_interface,
        protocol
    FROM device_neighbors
    ORDER BY neighbor_id
""")

for row in cursor.fetchall():
    neighbor_id, src_id, src_if, dest_id, dest_if, protocol = row
    src_name = device_map.get(src_id, f"ID:{src_id}")
    dest_name = device_map.get(dest_id, f"ID:{dest_id}")
    
    print(f"{neighbor_id:3d}: {src_id:3d} ({src_name:20s}) {src_if:25s} -> {dest_id:3d} ({dest_name:20s}) {dest_if:25s} [{protocol}]")

# Check specifically for BORO-MDF-SW01 (device_id 9)
print("\n" + "=" * 100)
print("Connections for BORO-MDF-SW01 (device_id 9):")
print("=" * 100)

cursor.execute("""
    SELECT 
        neighbor_id,
        source_device_id,
        source_interface,
        destination_device_id,
        destination_interface,
        protocol
    FROM device_neighbors
    WHERE source_device_id = 9 OR destination_device_id = 9
    ORDER BY neighbor_id
""")

rows = cursor.fetchall()
if rows:
    for row in rows:
        neighbor_id, src_id, src_if, dest_id, dest_if, protocol = row
        src_name = device_map.get(src_id, f"ID:{src_id}")
        dest_name = device_map.get(dest_id, f"ID:{dest_id}")
        print(f"{neighbor_id:3d}: {src_id:3d} ({src_name:20s}) {src_if:25s} -> {dest_id:3d} ({dest_name:20s}) {dest_if:25s} [{protocol}]")
else:
    print("  NO CONNECTIONS FOUND")

cursor.close()
conn.close()
