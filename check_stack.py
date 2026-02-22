import sqlite3

conn = sqlite3.connect('marktests/netwalker_inventory.db')
cursor = conn.cursor()

# Get KARE-CORE devices
cursor.execute("SELECT device_id, device_name, serial_number, hardware_model, platform FROM devices WHERE device_name LIKE '%KARE-CORE%'")
devices = cursor.fetchall()

print("=== KARE-CORE Devices ===")
for row in devices:
    print(f"{row[0]}: {row[1]} | Serial: {row[2]} | Model: {row[3]} | Platform: {row[4]}")

# Get stack members for each device
for device in devices:
    device_id = device[0]
    device_name = device[1]
    
    cursor.execute("""
        SELECT switch_number, role, hardware_model, serial_number, software_version, state 
        FROM device_stack_members 
        WHERE device_id = ?
        ORDER BY switch_number
    """, (device_id,))
    
    members = cursor.fetchall()
    
    if members:
        print(f"\n=== Stack Members for {device_name} (device_id={device_id}) ===")
        for member in members:
            print(f"  Switch {member[0]}: Role={member[1]}, Model={member[2]}, Serial={member[3]}, Version={member[4]}, State={member[5]}")
    else:
        print(f"\n=== No stack members found for {device_name} ===")

conn.close()
