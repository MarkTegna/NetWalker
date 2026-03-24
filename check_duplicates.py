"""Check for duplicate device records for WPMT-NETWORK-SW01."""
import pyodbc
import base64

server = "eit-prisqldb01.tgna.tegna.com"
database = "NetWalker"
username = "NetWalker"
password = base64.b64decode("Rmx1ZmZ5QnVubnlIaXRieWFCdXM=").decode()
conn = pyodbc.connect(
    f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};"
    f"UID={username};PWD={password};TrustServerCertificate=yes"
)
cursor = conn.cursor()

cursor.execute("""
    SELECT device_id, device_name, serial_number, platform, hardware_model,
           last_seen, status, connection_method, connection_failures
    FROM devices
    WHERE device_name = 'WPMT-NETWORK-SW01'
    ORDER BY device_id
""")

rows = cursor.fetchall()
cols = [d[0] for d in cursor.description]
print(f"Found {len(rows)} record(s) for WPMT-NETWORK-SW01:\n")
for r in rows:
    for c, v in zip(cols, r):
        print(f"  {c}: {v}")
    print()

# Also check for any devices with device_id 2340
cursor.execute("""
    SELECT device_id, device_name, serial_number, last_seen, status
    FROM devices WHERE device_id = 2340
""")
row = cursor.fetchone()
if row:
    print(f"Device ID 2340: {row.device_name} (serial: {row.serial_number}, last_seen: {row.last_seen})")

# Check how many duplicates exist in general
cursor.execute("""
    SELECT device_name, COUNT(*) as cnt
    FROM devices
    GROUP BY device_name
    HAVING COUNT(*) > 1
    ORDER BY cnt DESC
""")
dupes = cursor.fetchall()
if dupes:
    print(f"\n--- Duplicate device names ({len(dupes)} names) ---")
    for d in dupes:
        print(f"  {d.device_name}: {d.cnt} records")

cursor.close()
conn.close()
