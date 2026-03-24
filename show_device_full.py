"""Show all data across all tables for a device."""
import pyodbc
import base64
import sys

device_name = sys.argv[1] if len(sys.argv) > 1 else 'KSDK-SERVER-STACK-2'

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

# Device record
cursor.execute("SELECT * FROM devices WHERE device_name = ?", (device_name,))
cols = [d[0] for d in cursor.description]
row = cursor.fetchone()
if not row:
    print(f"Device '{device_name}' not found.")
    cursor.close()
    conn.close()
    exit()

print(f"=== devices ===")
for c, v in zip(cols, row):
    print(f"  {c}: {v}")
device_id = row[cols.index('device_id')]

# All related tables
tables = {
    'device_neighbors (as source)': f"SELECT n.*, d.device_name as dest_name FROM device_neighbors n JOIN devices d ON n.destination_device_id = d.device_id WHERE n.source_device_id = {device_id}",
    'device_neighbors (as dest)': f"SELECT n.*, d.device_name as source_name FROM device_neighbors n JOIN devices d ON n.source_device_id = d.device_id WHERE n.destination_device_id = {device_id}",
    'device_versions': f"SELECT * FROM device_versions WHERE device_id = {device_id}",
    'device_interfaces': f"SELECT * FROM device_interfaces WHERE device_id = {device_id}",
    'device_vlans': f"SELECT * FROM device_vlans WHERE device_id = {device_id}",
    'device_stack_members': f"SELECT * FROM device_stack_members WHERE device_id = {device_id}",
}

for table_name, query in tables.items():
    try:
        cursor.execute(query)
        tcols = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        if rows:
            print(f"\n=== {table_name} ({len(rows)} rows) ===")
            for r in rows:
                for c, v in zip(tcols, r):
                    print(f"  {c}: {v}")
                print()
    except pyodbc.Error:
        pass

cursor.close()
conn.close()
