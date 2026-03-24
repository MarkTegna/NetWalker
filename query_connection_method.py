"""Show devices with a non-blank connection_method."""
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
    SELECT device_name, connection_method, platform, hardware_model, status
    FROM devices
    WHERE connection_method IS NOT NULL AND connection_method != ''
    ORDER BY connection_method, device_name
""")

rows = cursor.fetchall()
print(f"Devices with connection_method set: {len(rows)}\n")

if rows:
    print(f"{'Device Name':<40} {'Method':<15} {'Platform':<15} {'Hardware':<25} {'Status':<10}")
    print("-" * 105)
    for r in rows:
        print(f"{r.device_name:<40} {r.connection_method:<15} {(r.platform or ''):<15} {(r.hardware_model or ''):<25} {r.status:<10}")
else:
    print("No devices have connection_method populated yet.")
    print("This field will be filled on the next network walk.")

# Also show summary counts
cursor.execute("""
    SELECT 
        COALESCE(connection_method, 'NULL') as method,
        COUNT(*) as cnt
    FROM devices
    GROUP BY connection_method
    ORDER BY connection_method
""")
print("\n--- Connection Method Summary ---")
for r in cursor.fetchall():
    print(f"  {r.method}: {r.cnt}")

cursor.close()
conn.close()
