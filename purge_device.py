"""Purge a device by name from all tables."""
import pyodbc
import base64
import sys

device_name = sys.argv[1] if len(sys.argv) > 1 else None
if not device_name:
    print("Usage: python purge_device.py <device_name>")
    sys.exit(1)

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

# Find the device
cursor.execute("SELECT device_id, device_name, platform, hardware_model FROM devices WHERE device_name = ?", (device_name,))
row = cursor.fetchone()
if not row:
    print(f"Device '{device_name}' not found.")
    cursor.close()
    conn.close()
    sys.exit(1)

device_id = row.device_id
print(f"Found: {row.device_name} (ID: {device_id}, Platform: {row.platform}, HW: {row.hardware_model})")

# Delete from related tables (CASCADE handles most, but neighbors as dest need manual)
cursor.execute("DELETE FROM device_neighbors WHERE destination_device_id = ?", (device_id,))
dest_neighbors = cursor.rowcount
cursor.execute("DELETE FROM device_neighbors WHERE source_device_id = ?", (device_id,))
src_neighbors = cursor.rowcount
cursor.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
devices_deleted = cursor.rowcount

conn.commit()
print(f"Purged: {devices_deleted} device, {src_neighbors + dest_neighbors} neighbor connections")
cursor.close()
conn.close()
