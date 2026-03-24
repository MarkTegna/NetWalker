"""Check stack members for duplicate devices to understand serial tracking."""
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

# Check all duplicates and their stack members
dupes = [
    'HIHQ-CORE-A', 'KFMB-MDF-SW03', 'WATL-XMIT1-SW01', 'WATL-XMIT1-UW01',
    'WPMT-NETWORK-SW01', 'WWL-CORE-B', 'wwl-sw-rem-txc-twr300', 'wwl-sw-rem-txc-twr500'
]

for name in dupes:
    # Get device records
    cursor.execute("""
        SELECT device_id, serial_number, last_seen, hardware_model
        FROM devices WHERE device_name = ?
        ORDER BY device_id
    """, (name,))
    devices = cursor.fetchall()
    
    print(f"\n=== {name} ({len(devices)} device records) ===")
    for d in devices:
        print(f"  ID {d[0]}: serial={d[1]}, last_seen={str(d[2])[:19]}, hw={d[3]}")
        
        # Get stack members for this device_id
        cursor.execute("""
            SELECT switch_number, role, serial_number, hardware_model
            FROM device_stack_members WHERE device_id = ?
            ORDER BY switch_number
        """, (d[0],))
        members = cursor.fetchall()
        if members:
            for m in members:
                print(f"    Stack #{m[0]}: role={m[1]}, serial={m[2]}, hw={m[3]}")
        else:
            print(f"    (no stack members)")

cursor.close()
conn.close()
