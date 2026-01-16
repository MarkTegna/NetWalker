"""Check BORO-UW01 device information in database"""
import pyodbc

# Connect to database
conn = pyodbc.connect(
    'DRIVER={SQL Server};'
    'SERVER=eit-prisqldb01.tgna.tegna.com,1433;'
    'DATABASE=NetWalker;'
    'UID=NetWalker;'
    'PWD=FluffyBunnyHitbyaBus;'
    'Connection Timeout=30;'
)

cursor = conn.cursor()

# Query BORO-UW01 device
cursor.execute("""
    SELECT 
        d.device_name,
        d.serial_number,
        d.platform,
        d.hardware_model,
        dv.software_version,
        d.last_seen
    FROM devices d
    LEFT JOIN device_versions dv ON d.device_id = dv.device_id
    WHERE d.device_name LIKE '%BORO-UW01%'
    ORDER BY d.device_name, dv.last_seen DESC
""")

print("BORO-UW01 Device Information:")
print("-" * 80)
for row in cursor.fetchall():
    print(f"Device Name: {row[0]}")
    print(f"Serial Number: {row[1]}")
    print(f"Platform: {row[2]}")
    print(f"Hardware Model: {row[3]}")
    print(f"Software Version: {row[4]}")
    print(f"Last Seen: {row[5]}")
    print("-" * 80)

cursor.close()
conn.close()
