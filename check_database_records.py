"""
Quick script to check what's actually in the NetWalker database
"""
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

# Check devices table
print("=== DEVICES TABLE ===")
cursor.execute("SELECT COUNT(*) FROM Devices")
device_count = cursor.fetchone()[0]
print(f"Total devices: {device_count}")

cursor.execute("""
    SELECT hostname, ip_address, status, connection_status 
    FROM Devices 
    ORDER BY last_updated DESC
""")
print("\nRecent devices:")
for row in cursor.fetchall()[:25]:
    print(f"  {row.hostname} ({row.ip_address}) - Status: {row.status}, Connection: {row.connection_status}")

# Check neighbors table
print("\n=== NEIGHBORS TABLE ===")
cursor.execute("SELECT COUNT(*) FROM Neighbors")
neighbor_count = cursor.fetchone()[0]
print(f"Total neighbor records: {neighbor_count}")

cursor.execute("""
    SELECT TOP 10 n.neighbor_hostname, n.neighbor_ip, n.local_interface, n.remote_interface
    FROM Neighbors n
    ORDER BY n.last_updated DESC
""")
print("\nRecent neighbors:")
for row in cursor.fetchall():
    print(f"  {row.neighbor_hostname} ({row.neighbor_ip}) - {row.local_interface} <-> {row.remote_interface}")

conn.close()
print("\n✓ Database check complete")
