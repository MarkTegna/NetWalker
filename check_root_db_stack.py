import sqlite3

# Connect to the root database
conn = sqlite3.connect('netwalker_inventory.db')
cursor = conn.cursor()

print("\n=== Checking KARE-CORE-A in root database ===\n")

# Check if tables exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f"Tables: {tables}\n")

if 'device_inventory' in tables:
    cursor.execute("""
        SELECT hostname, serial_number, hardware_model, is_stack, platform
        FROM device_inventory 
        WHERE hostname = 'KARE-CORE-A'
    """)
    device = cursor.fetchone()
    if device:
        hostname, serial, model, is_stack, platform = device
        print(f"Device: {hostname}")
        print(f"  Serial: {serial}")
        print(f"  Model: {model}")
        print(f"  Is Stack: {is_stack}")
        print(f"  Platform: {platform}")
    else:
        print("KARE-CORE-A not found in device_inventory")

if 'stack_members' in tables:
    cursor.execute("""
        SELECT sm.member_number, sm.serial_number, sm.hardware_model, sm.role, sm.priority, sm.state
        FROM stack_members sm
        JOIN device_inventory di ON sm.device_id = di.device_id
        WHERE di.hostname = 'KARE-CORE-A'
        ORDER BY sm.member_number
    """)
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
    print("\nstack_members table does not exist")

conn.close()
