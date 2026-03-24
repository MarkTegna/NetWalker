"""Purge all devices with only 'Host' capability."""
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

cursor.execute("SELECT device_id FROM devices WHERE capabilities = 'Host'")
device_ids = [row.device_id for row in cursor.fetchall()]
print(f"Found {len(device_ids)} Host-only devices to purge")

if not device_ids:
    cursor.close()
    conn.close()
    exit()

placeholders = ','.join(['?' for _ in device_ids])

cursor.execute(f"""
    DELETE FROM device_neighbors 
    WHERE source_device_id IN ({placeholders}) 
       OR destination_device_id IN ({placeholders})
""", device_ids + device_ids)
print(f"Deleted {cursor.rowcount} connections")

for table in ['device_interfaces', 'device_versions', 'device_vlans', 'device_stack_members']:
    try:
        cursor.execute(f"DELETE FROM {table} WHERE device_id IN ({placeholders})", device_ids)
        if cursor.rowcount > 0:
            print(f"Deleted {cursor.rowcount} rows from {table}")
    except pyodbc.Error:
        pass

cursor.execute(f"DELETE FROM devices WHERE device_id IN ({placeholders})", device_ids)
print(f"Deleted {cursor.rowcount} devices")

conn.commit()
cursor.close()
conn.close()
print("Purge complete.")
