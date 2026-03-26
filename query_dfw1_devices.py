"""List all DFW1 Cisco/Nexus devices."""
import pyodbc
import base64

server = "eit-prisqldb01.tgna.tegna.com"
database = "NetWalker"
username = "NetWalker"
password = base64.b64decode("Rmx1ZmZ5QnVubnlIaXRieWFCdXM=").decode()

conn = pyodbc.connect(
    f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};"
    f"UID={username};PWD={password}"
)
cursor = conn.cursor()

cursor.execute("""
    SELECT device_name, platform, hardware_model, connection_failures,
           connection_method, status, CONVERT(VARCHAR, last_seen, 120) as last_seen
    FROM devices
    WHERE device_name LIKE 'DFW1%'
      AND (platform LIKE '%IOS%' OR platform LIKE '%NX-OS%'
           OR platform LIKE '%cisco%' OR platform LIKE '%N9K%'
           OR platform LIKE '%C9%')
    ORDER BY device_name
""")

rows = cursor.fetchall()
fmt = "{:<40} {:<20} {:<25} {:>5} {:<15} {:<10} {}"
print(fmt.format("Name", "Platform", "HW Model", "Fail", "Method", "Status", "Last Seen"))
print("-" * 140)
for r in rows:
    print(fmt.format(
        r[0] or "", r[1] or "", r[2] or "", r[3] or 0,
        r[4] or "None", r[5] or "", r[6] or ""
    ))
print(f"\nTotal: {len(rows)} devices")

cursor.close()
conn.close()
