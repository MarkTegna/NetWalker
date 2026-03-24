"""Purge all *-MAIN-AP* devices and their connections from the database."""
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

# Find matching devices
cursor.execute("SELECT device_id, device_name FROM devices WHERE device_name LIKE '%-MAIN-AP%'")
devices = cursor.fetchall()
print(f"Found {len(devices)} devices matching *-MAIN-AP*:")
for d in devices:
    print(f"  {d.device_name}")

if not devices:
    cursor.close()
    conn.close()
    exit()

device_ids = [d.device_id for d in devices]
placeholders = ','.join(['?' for _ in device_ids])

# Delete connections
cursor.execute(f"""
    DELETE FROM device_neighbors 
    WHERE source_device_id IN ({placeholders}) 
       OR destination_device_id IN ({placeholders})
""", device_ids + device_ids)
print(f"Deleted {cursor.rowcount} connections")

# Delete from related tables
for table in ['device_interfaces', 'device_versions', 'device_vlans', 'device_stack_members']:
    try:
        cursor.execute(f"DELETE FROM {table} WHERE device_id IN ({placeholders})", device_ids)
        if cursor.rowcount > 0:
            print(f"Deleted {cursor.rowcount} rows from {table}")
    except pyodbc.Error:
        pass

# Delete devices
cursor.execute(f"DELETE FROM devices WHERE device_id IN ({placeholders})", device_ids)
print(f"Deleted {cursor.rowcount} devices")

conn.commit()
cursor.close()
conn.close()
print("Purge complete.")
