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

# Check KVUE-ntxnd03
cursor.execute("SELECT device_name, capabilities FROM devices WHERE device_name = 'KVUE-ntxnd03'")
row = cursor.fetchone()
if row:
    print(f'Device: {row[0]}')
    print(f'Capabilities: {row[1]}')
else:
    print("KVUE-ntxnd03 not found")
print()

# Check a few other devices
cursor.execute("SELECT TOP 20 device_name, capabilities FROM devices WHERE capabilities IS NOT NULL AND capabilities != '' ORDER BY device_name")
print("Sample devices with capabilities:")
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

conn.close()
