"""Purge stale duplicate device records, keeping the most recently seen one."""
import pyodbc
import base64

server = "eit-prisqldb01.tgna.tegna.com"
database = "NetWalker"
username = "NetWalker"
password = base64.b64decode("Rmx1ZmZ5QnVubnlIaXRieWFCdXM=").decode()
conn = pyodbc.connect(
    f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};"
    f"UID={username};PWD={password};TrustServerCertificate=yes"
)
cursor = conn.cursor()

# Find all duplicate device names
cursor.execute("""
    SELECT device_name, COUNT(*) as cnt
    FROM devices
    GROUP BY device_name
    HAVING COUNT(*) > 1
    ORDER BY device_name
""")
dupes = cursor.fetchall()
print(f"Found {len(dupes)} device names with duplicates\n")

total_purged = 0
for d in dupes:
    name = d[0]
    # Get all records for this device, ordered by last_seen desc
    cursor.execute("""
        SELECT device_id, serial_number, last_seen, hardware_model
        FROM devices WHERE device_name = ?
        ORDER BY last_seen DESC
    """, (name,))
    records = cursor.fetchall()
    
    # Keep the first (most recent), delete the rest
    keep = records[0]
    print(f"{name}:")
    print(f"  KEEP: ID {keep[0]}, serial={keep[1]}, last_seen={str(keep[2])[:19]}")
    
    for stale in records[1:]:
        print(f"  DELETE: ID {stale[0]}, serial={stale[1]}, last_seen={str(stale[2])[:19]}")
        stale_id = stale[0]
        
        # Delete neighbor connections referencing this device
        cursor.execute("DELETE FROM device_neighbors WHERE destination_device_id = ?", (stale_id,))
        n1 = cursor.rowcount
        cursor.execute("DELETE FROM device_neighbors WHERE source_device_id = ?", (stale_id,))
        n2 = cursor.rowcount
        
        # Delete the device (CASCADE handles versions, interfaces, vlans, stack_members)
        cursor.execute("DELETE FROM devices WHERE device_id = ?", (stale_id,))
        
        print(f"    Purged device + {n1 + n2} neighbor connections")
        total_purged += 1

conn.commit()
print(f"\nTotal stale duplicates purged: {total_purged}")

# Verify no more duplicates
cursor.execute("""
    SELECT device_name, COUNT(*) as cnt
    FROM devices GROUP BY device_name HAVING COUNT(*) > 1
""")
remaining = cursor.fetchall()
print(f"Remaining duplicates: {len(remaining)}")

cursor.close()
conn.close()
