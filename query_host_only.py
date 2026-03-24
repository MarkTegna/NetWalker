"""Show all devices where capabilities is exactly 'Host'."""
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

cursor.execute("""
    SELECT device_name, platform, hardware_model, capabilities, serial_number, connection_failures
    FROM devices
    WHERE capabilities = 'Host'
    ORDER BY device_name
""")

rows = cursor.fetchall()
print(f"Found {len(rows)} devices with capability = 'Host' only\n")
print(f"{'Device Name':<35} {'Platform':<20} {'Hardware':<20} {'Serial':<20} {'Failures'}")
print("-" * 120)
for r in rows:
    print(f"{r.device_name:<35} {(r.platform or ''):<20} {(r.hardware_model or ''):<20} {(r.serial_number or ''):<20} {r.connection_failures}")

cursor.close()
conn.close()
