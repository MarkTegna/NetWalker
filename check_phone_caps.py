"""Check capabilities of devices flagged as phones that are actually switches/routers."""
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

# Check the false positives
devices = [
    'DFW1-ACCESS-SW01', 'DFW1-ACCESS-SW02', 'DFW1-HUB-SW02', 'DFW1-HUB-SW04',
    'iad2-tegna-56128p-1', 'iad2-tegna-56128p-2',
    'KPNX-NEXUS-CORE-SW01', 'KPNX-NEXUS-CORE-SW02',
    'WTHR_Core-Media-A', 'WTHR_Core-Media-B'
]

print(f"{'Device Name':<30} {'Platform':<25} {'Capabilities'}")
print("-" * 100)
for dev in devices:
    cursor.execute("SELECT device_name, platform, capabilities FROM devices WHERE device_name = ?", (dev,))
    row = cursor.fetchone()
    if row:
        print(f"{row.device_name:<30} {(row.platform or ''):<25} {row.capabilities or ''}")

# Also check what real phones look like
print("\n\nSample ACTUAL phones (SEP devices):")
print("-" * 100)
cursor.execute("""
    SELECT TOP 10 device_name, platform, capabilities 
    FROM devices 
    WHERE device_name LIKE 'SEP%'
    ORDER BY device_name
""")
for row in cursor.fetchall():
    print(f"{row.device_name:<30} {(row.platform or ''):<25} {row.capabilities or ''}")

# Check devices where phone is the ONLY capability
print("\n\nDevices where 'phone' is the ONLY capability:")
print("-" * 100)
cursor.execute("""
    SELECT TOP 10 device_name, platform, capabilities 
    FROM devices 
    WHERE capabilities = 'Phone'
    ORDER BY device_name
""")
for row in cursor.fetchall():
    print(f"{row.device_name:<30} {(row.platform or ''):<25} {row.capabilities or ''}")

cursor.close()
conn.close()
