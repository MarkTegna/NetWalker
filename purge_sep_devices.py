"""Purge all SEP* devices and their connections from the database."""
import pyodbc
import base64

server = "eit-prisqldb01.tgna.tegna.com"
database = "NetWalker"
username = "NetWalker"
password = base64.b64decode("Rmx1ZmZ5QnVubnlIaXRieWFCdXM=").decode()

conn_str = (
    f"DRIVER={{SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    f"TrustServerCertificate=yes"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Count SEP devices
cursor.execute("SELECT COUNT(*) FROM devices WHERE device_name LIKE 'SEP%'")
count = cursor.fetchone()[0]
print(f"Found {count} SEP devices to purge")

# Get device IDs
cursor.execute("SELECT device_id, device_name FROM devices WHERE device_name LIKE 'SEP%'")
sep_devices = cursor.fetchall()
device_ids = [row.device_id for row in sep_devices]

if not device_ids:
    print("No SEP devices found.")
    cursor.close()
    conn.close()
    exit()

placeholders = ','.join(['?' for _ in device_ids])

# Delete connections
cursor.execute(f"""
    DELETE FROM device_neighbors 
    WHERE source_device_id IN ({placeholders}) 
       OR destination_device_id IN ({placeholders})
""", device_ids + device_ids)
conn_deleted = cursor.rowcount
print(f"Deleted {conn_deleted} connections")

# Delete from related tables
for table in ['device_interfaces', 'device_versions', 'device_vlans', 'device_stack_members']:
    try:
        cursor.execute(f"DELETE FROM {table} WHERE device_id IN ({placeholders})", device_ids)
        deleted = cursor.rowcount
        if deleted > 0:
            print(f"Deleted {deleted} rows from {table}")
    except pyodbc.Error:
        pass

# Delete devices
cursor.execute(f"DELETE FROM devices WHERE device_id IN ({placeholders})", device_ids)
devices_deleted = cursor.rowcount
print(f"Deleted {devices_deleted} SEP devices")

conn.commit()
cursor.close()
conn.close()
print("Purge complete.")
