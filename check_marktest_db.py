import sqlite3

# Connect to the marktests database
conn = sqlite3.connect('marktests/netwalker_inventory.db')
cursor = conn.cursor()

print("\n=== Tables in marktests database ===\n")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")

print("\n=== Checking for KARE-CORE-A in discovery_queue ===\n")
try:
    cursor.execute("SELECT * FROM discovery_queue WHERE hostname LIKE '%KARE-CORE%'")
    rows = cursor.fetchall()
    print(f"Found {len(rows)} rows")
    for row in rows:
        print(f"  {row}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== Checking for KARE-CORE-A in device_inventory ===\n")
try:
    cursor.execute("SELECT hostname, serial_number, hardware_model, is_stack FROM device_inventory WHERE hostname LIKE '%KARE-CORE%'")
    rows = cursor.fetchall()
    print(f"Found {len(rows)} rows")
    for row in rows:
        print(f"  {row}")
except Exception as e:
    print(f"Error: {e}")

conn.close()
