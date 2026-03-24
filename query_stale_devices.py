"""Show which devices would be walked with --rewalk-stale 2."""
import pyodbc
import base64
from datetime import datetime

server = "eit-prisqldb01.tgna.tegna.com"
database = "NetWalker"
username = "NetWalker"
password = base64.b64decode("Rmx1ZmZ5QnVubnlIaXRieWFCdXM=").decode()
conn = pyodbc.connect(
    f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};"
    f"UID={username};PWD={password};TrustServerCertificate=yes"
)
cursor = conn.cursor()

days = 2
cursor.execute("""
    SELECT
        d.device_name,
        d.last_seen,
        d.platform,
        d.hardware_model,
        d.connection_method,
        d.connection_failures,
        COALESCE(
            (SELECT TOP 1 ip_address
             FROM device_interfaces
             WHERE device_id = d.device_id
             ORDER BY
                CASE
                    WHEN interface_name LIKE '%Management%' THEN 1
                    WHEN interface_name LIKE '%Loopback%' THEN 2
                    WHEN interface_name LIKE '%Vlan%' THEN 3
                    ELSE 4
                END,
                interface_name
            ),
            ''
        ) AS ip_address
    FROM devices d
    WHERE d.status = 'active'
      AND d.hardware_model != 'Unwalked Neighbor'
      AND d.last_seen < DATEADD(day, -?, GETDATE())
    ORDER BY d.last_seen ASC
""", (days,))

rows = cursor.fetchall()
now = datetime.now()

print(f"Devices that would be walked with --rewalk-stale {days}: {len(rows)}")
print(f"(Criteria: active, not 'Unwalked Neighbor', last_seen > {days} days ago)")
print(f"Current time: {now.strftime('%Y-%m-%d %H:%M')}\n")

if rows:
    print(f"{'Device Name':<40} {'Last Seen':<22} {'Days Ago':<10} {'IP':<18} {'Method':<12} {'Failures':<8} {'Platform':<12}")
    print("-" * 122)
    for r in rows:
        last = r[1]
        if last:
            if isinstance(last, str):
                last = datetime.strptime(last[:19], '%Y-%m-%d %H:%M:%S')
            days_ago = (now - last).days
        else:
            days_ago = '?'
        print(f"{r[0]:<40} {str(last)[:19]:<22} {days_ago:<10} {(r[6] or ''):<18} {(r[4] or 'NULL'):<12} {r[5]:<8} {(r[2] or ''):<12}")

# Also show total counts for context
cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'active'")
total = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'active' AND hardware_model = 'Unwalked Neighbor'")
unwalked = cursor.fetchone()[0]
print(f"\n--- Summary ---")
print(f"Total active devices: {total}")
print(f"Unwalked neighbors (excluded): {unwalked}")
print(f"Would be walked: {len(rows)}")
print(f"Already fresh (walked within {days} days): {total - unwalked - len(rows)}")

cursor.close()
conn.close()
