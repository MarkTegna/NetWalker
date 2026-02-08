import pyodbc

conn = pyodbc.connect(
    'DRIVER={SQL Server};'
    'SERVER=eit-prisqldb01.tgna.tegna.com;'
    'DATABASE=NetWalker;'
    'UID=NetWalker;'
    'PWD=FluffyBunnyHitbyaBus;'
    'TrustServerCertificate=yes'
)

cursor = conn.cursor()
cursor.execute("""
    SELECT device_name 
    FROM devices 
    WHERE status='active' 
    AND (
        device_name LIKE '%camera%' 
        OR device_name LIKE '%phone%' 
        OR device_name LIKE '%printer%' 
        OR device_name LIKE '%Linux%' 
        OR device_name LIKE 'Algo%' 
        OR device_name LIKE 'Polycom%'
    )
    ORDER BY device_name
""")

rows = cursor.fetchall()
print(f'Found {len(rows)} devices matching exclusion patterns:')
for row in rows:
    device_name = row[0]
    # Extract site code (first 4 characters)
    site_code = device_name[:4] if len(device_name) >= 4 else 'UNKNOWN'
    print(f'  {device_name} (Site: {site_code})')

conn.close()
