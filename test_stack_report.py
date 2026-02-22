"""Test stack members in report generation"""
import pyodbc

# Connect to database
conn_str = (
    "DRIVER={SQL Server};"
    "SERVER=eit-prisqldb01.tgna.tegna.com;"
    "DATABASE=NetWalker;"
    "Trusted_Connection=yes;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Check KGW-CORE-A
print("=== Checking KGW-CORE-A in database ===")
cursor.execute("""
    SELECT device_id, device_name, serial_number, hardware_model
    FROM devices 
    WHERE device_name = 'KGW-CORE-A'
""")
device = cursor.fetchone()
if device:
    print(f"Device ID: {device[0]}")
    print(f"Device Name: {device[1]}")
    print(f"Serial: {device[2]}")
    print(f"Model: {device[3]}")
    
    # Check stack members
    print("\n=== Stack Members ===")
    cursor.execute("""
        SELECT switch_number, role, hardware_model, serial_number
        FROM device_stack_members
        WHERE device_id = ?
        ORDER BY switch_number
    """, device[0])
    
    members = cursor.fetchall()
    if members:
        for member in members:
            print(f"  Switch {member[0]}: {member[1]} - {member[2]} ({member[3]})")
    else:
        print("  No stack members found")
else:
    print("Device not found")

conn.close()
