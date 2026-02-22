import sqlite3
import sys

# Connect to the marktests database
conn = sqlite3.connect('marktests/netwalker_inventory.db')
cursor = conn.cursor()

device_name = sys.argv[1] if len(sys.argv) > 1 else 'KARE-CORE-A'

print(f"\n=== Checking stack information for {device_name} ===\n")

# Get the main device
cursor.execute("""
    SELECT device_id, hostname, serial_number, hardware_model, platform, is_stack
    FROM devices 
    WHERE hostname = ?
""", (device_name,))

device = cursor.fetchone()
if device:
    device_id, hostname, serial, model, platform, is_stack = device
    print(f"Main Device: {hostname}")
    print(f"  Device ID: {device_id}")
    print(f"  Serial: {serial}")
    print(f"  Model: {model}")
    print(f"  Platform: {platform}")
    print(f"  Is Stack: {is_stack}")
    
    # Get stack members
    cursor.execute("""
        SELECT member_number, serial_number, hardware_model, role, priority, state
        FROM stack_members
        WHERE device_id = ?
        ORDER BY member_number
    """, (device_id,))
    
    members = cursor.fetchall()
    print(f"\n  Stack Members ({len(members)} found):")
    for member in members:
        member_num, serial, model, role, priority, state = member
        print(f"    Member {member_num}:")
        print(f"      Serial: {serial}")
        print(f"      Model: {model}")
        print(f"      Role: {role}")
        print(f"      Priority: {priority}")
        print(f"      State: {state}")
else:
    print(f"Device {device_name} not found in database")

conn.close()
