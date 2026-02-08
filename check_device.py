"""Check if specific device is in database"""
import pyodbc
import base64
import configparser

# Load config
config = configparser.ConfigParser()
config.read('netwalker.ini')

db_config = {
    'server': config.get('database', 'server'),
    'port': config.get('database', 'port'),
    'database': config.get('database', 'database'),
    'username': config.get('database', 'username'),
    'password': config.get('database', 'password'),
}

if db_config['password'].startswith('ENC:'):
    encoded = db_config['password'][4:]
    db_config['password'] = base64.b64decode(encoded.encode()).decode()

# Connect
connection_string = (
    f"DRIVER={{SQL Server}};"
    f"SERVER={db_config['server']},{db_config['port']};"
    f"DATABASE={db_config['database']};"
    f"UID={db_config['username']};"
    f"PWD={db_config['password']};"
    "TrustServerCertificate=yes;"
)

conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

# Check for KENS-2NDFLOOR-01
device_name = "KENS-2NDFLOOR-01"
cursor.execute("SELECT device_name FROM devices WHERE device_name = ?", device_name)
result = cursor.fetchone()

if result:
    print(f"✓ {device_name} IS in the database")
else:
    print(f"✗ {device_name} is NOT in the database")

# Also check for similar names
cursor.execute("SELECT device_name FROM devices WHERE device_name LIKE ?", f"%{device_name}%")
similar = cursor.fetchall()

if similar:
    print(f"\nSimilar devices found:")
    for row in similar:
        print(f"  - {row[0]}")

conn.close()
