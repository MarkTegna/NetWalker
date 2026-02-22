"""
Check stack member data in database for KGW-CORE-A
"""
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

# Query for KGW-CORE-A stack members
query = """
SELECT 
    d.device_id,
    d.device_name,
    di.ip_address,
    sm.switch_number,
    sm.role,
    sm.hardware_model,
    sm.serial_number,
    sm.mac_address,
    sm.software_version,
    sm.state
FROM devices d
LEFT JOIN device_interfaces di ON d.device_id = di.device_id
LEFT JOIN device_stack_members sm ON d.device_id = sm.device_id
WHERE d.device_name LIKE 'KGW-CORE-A%'
ORDER BY d.device_name, sm.switch_number
"""

cursor.execute(query)
rows = cursor.fetchall()

print("\nStack Member Data from Database:")
print("="*120)
print(f"{'DeviceID':<10} {'Hostname':<20} {'IP':<15} {'SW#':<5} {'Role':<10} {'Model':<20} {'Serial':<15} {'MAC':<20} {'SW Ver':<15} {'State':<10}")
print("="*120)

for row in rows:
    device_id = row[0]
    hostname = row[1] or ''
    ip = row[2] or ''
    sw_num = row[3] if row[3] is not None else ''
    role = row[4] or ''
    model = row[5] or ''
    serial = row[6] or ''
    mac = row[7] or ''
    sw_ver = row[8] or ''
    state = row[9] or ''
    
    print(f"{device_id:<10} {hostname:<20} {ip:<15} {str(sw_num):<5} {role:<10} {model:<20} {serial:<15} {mac:<20} {sw_ver:<15} {state:<10}")

cursor.close()
conn.close()
