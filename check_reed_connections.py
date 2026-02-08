"""Check REED site connection data to understand label reversal"""
import pyodbc

# Database connection
conn_str = (
    "DRIVER={SQL Server};"
    "SERVER=eit-prisqldb01.tgna.tegna.com;"
    "DATABASE=NetWalker;"
    "Trusted_Connection=yes;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Get REED devices
print("REED Devices:")
print("-" * 80)
cursor.execute("""
    SELECT device_id, device_name
    FROM Devices
    WHERE device_name LIKE 'REED%'
    ORDER BY device_name
""")
for row in cursor.fetchall():
    print(f"  {row.device_id}: {row.device_name}")

print("\nREED Connections:")
print("-" * 80)
cursor.execute("""
    SELECT 
        n.neighbor_id,
        d1.device_name as source_device,
        n.source_interface,
        d2.device_name as dest_device,
        n.destination_interface,
        n.protocol
    FROM device_neighbors n
    JOIN Devices d1 ON n.source_device_id = d1.device_id
    JOIN Devices d2 ON n.destination_device_id = d2.device_id
    WHERE d1.device_name LIKE 'REED%' OR d2.device_name LIKE 'REED%'
    ORDER BY n.neighbor_id
""")

for row in cursor.fetchall():
    print(f"\nConnection {row.neighbor_id}:")
    print(f"  Source: {row.source_device} ({row.source_interface})")
    print(f"  Dest:   {row.dest_device} ({row.destination_interface})")
    print(f"  Protocol: {row.protocol}")

conn.close()
