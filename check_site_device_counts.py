"""Check device counts per site to test scaling"""
import pyodbc

# Database connection
conn_str = (
    "DRIVER={SQL Server};"
    "SERVER=eit-prisqldb01.tgna.tegna.com;"
    "DATABASE=NetWalker;"
    "Trusted_Connection=yes;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Get device counts by site (using first 4 characters of device name)
print("Device counts by site:")
print("-" * 80)
cursor.execute("""
    SELECT LEFT(device_name, 4) as site_code,
           COUNT(*) as device_count
    FROM Devices
    WHERE status = 'active'
    GROUP BY LEFT(device_name, 4)
    HAVING COUNT(*) > 5
    ORDER BY device_count DESC
""")

for row in cursor.fetchall():
    print(f"  {row.site_code}: {row.device_count} devices")

conn.close()
