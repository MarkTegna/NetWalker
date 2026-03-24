"""Find devices matching a search term across name, IP, serial."""
import pyodbc
import base64
import sys

search = sys.argv[1] if len(sys.argv) > 1 else ''
server = "eit-prisqldb01.tgna.tegna.com"
database = "NetWalker"
username = "NetWalker"
password = base64.b64decode("Rmx1ZmZ5QnVubnlIaXRieWFCdXM=").decode()
conn = pyodbc.connect(f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes")
cursor = conn.cursor()

cursor.execute("""
    SELECT d.device_id, d.device_name, d.platform, d.hardware_model, i.ip_address
    FROM devices d
    LEFT JOIN device_interfaces i ON d.device_id = i.device_id
    WHERE d.device_name LIKE ? OR i.ip_address LIKE ?
    ORDER BY d.device_name
""", (f"%{search}%", f"%{search}%"))

rows = cursor.fetchall()
print(f"Found {len(rows)} match(es) for '{search}':\n")
for r in rows:
    print(f"  ID: {r.device_id}  Name: {r.device_name}  IP: {r.ip_address}  Platform: {r.platform}  HW: {r.hardware_model}")

cursor.close()
conn.close()
