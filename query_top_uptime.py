"""Query top 5 devices by uptime from the database."""
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
    SELECT TOP 10 device_name, uptime_raw, uptime_hours
    FROM devices
    WHERE uptime_hours IS NOT NULL AND uptime_hours > 0
    ORDER BY uptime_hours DESC
""")

rows = cursor.fetchall()
if rows:
    print(f"{'Device Name':<35} {'Uptime (Hours)':<16} {'Days':<10} {'Raw Uptime'}")
    print("-" * 120)
    for row in rows:
        hours = row.uptime_hours or 0
        days = hours / 24
        print(f"{row.device_name:<35} {hours:<16.1f} {days:<10.1f} {row.uptime_raw}")
else:
    print("No uptime data found.")

cursor.close()
conn.close()
