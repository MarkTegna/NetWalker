"""Show full details for a device."""
import pyodbc
import base64
import sys

device_name = sys.argv[1] if len(sys.argv) > 1 else 'WCNC-XMIT1-AP01'

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

cursor.execute("SELECT * FROM devices WHERE device_name = ?", (device_name,))
cols = [desc[0] for desc in cursor.description]
row = cursor.fetchone()
if row:
    print(f"=== Device: {device_name} ===")
    for col, val in zip(cols, row):
        print(f"  {col}: {val}")
else:
    print(f"Device '{device_name}' not found.")
    cursor.close()
    conn.close()
    exit()

device_id = row[cols.index('device_id')]

# Neighbors
print(f"\n=== Connections ===")
cursor.execute("""
    SELECT n.*, 
           s.device_name as source_name, 
           d.device_name as dest_name
    FROM device_neighbors n
    JOIN devices s ON n.source_device_id = s.device_id
    JOIN devices d ON n.destination_device_id = d.device_id
    WHERE n.source_device_id = ? OR n.destination_device_id = ?
""", (device_id, device_id))
neighbors = cursor.fetchall()
ncols = [desc[0] for desc in cursor.description]
if neighbors:
    for n in neighbors:
        for col, val in zip(ncols, n):
            print(f"  {col}: {val}")
        print()
else:
    print("  No connections found.")

# Versions
cursor.execute("SELECT * FROM device_versions WHERE device_id = ?", (device_id,))
versions = cursor.fetchall()
if versions:
    vcols = [desc[0] for desc in cursor.description]
    print(f"\n=== Versions ===")
    for v in versions:
        for col, val in zip(vcols, v):
            print(f"  {col}: {val}")

cursor.close()
conn.close()
