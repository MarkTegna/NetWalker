#!/usr/bin/env python3
"""
Query database for kgw-core-a device information including stack members
"""

import pyodbc
from netwalker.config.config_manager import ConfigurationManager

# Load configuration
config_manager = ConfigurationManager('netwalker.ini')
config = config_manager.load_configuration()
db_config = config['database']

# Connect to database
# Try different ODBC drivers
drivers = [
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 18 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server"
]

conn = None
for driver in drivers:
    try:
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={db_config['server']};"
            f"DATABASE={db_config['database']};"
            f"Trusted_Connection=yes;"
        )
        conn = pyodbc.connect(conn_str)
        print(f"Connected using driver: {driver}")
        break
    except pyodbc.Error:
        continue

if not conn:
    print("Failed to connect with any available ODBC driver")
    exit(1)

try:
    cursor = conn.cursor()
    
    print("=" * 80)
    print("KGW-CORE-A Device Information")
    print("=" * 80)
    
    # Query device information
    cursor.execute("""
        SELECT 
            device_id,
            device_name,
            serial_number,
            platform,
            hardware_model,
            capabilities,
            status,
            first_seen,
            last_seen
        FROM devices
        WHERE device_name LIKE '%kgw-core-a%'
    """)
    
    device_row = cursor.fetchone()
    
    if not device_row:
        print("Device 'kgw-core-a' not found in database")
        exit(0)
    
    device_id = device_row[0]
    
    print(f"\nDevice ID: {device_row[0]}")
    print(f"Device Name: {device_row[1]}")
    print(f"Serial Number: {device_row[2]}")
    print(f"Platform: {device_row[3]}")
    print(f"Hardware Model: {device_row[4]}")
    print(f"Capabilities: {device_row[5]}")
    print(f"Status: {device_row[6]}")
    print(f"First Seen: {device_row[7]}")
    print(f"Last Seen: {device_row[8]}")
    
    # Query software version
    print("\n" + "-" * 80)
    print("Software Version:")
    print("-" * 80)
    cursor.execute("""
        SELECT software_version, first_seen, last_seen
        FROM device_versions
        WHERE device_id = ?
        ORDER BY last_seen DESC
    """, (device_id,))
    
    for row in cursor.fetchall():
        print(f"  Version: {row[0]}")
        print(f"  First Seen: {row[1]}")
        print(f"  Last Seen: {row[2]}")
    
    # Query interfaces
    print("\n" + "-" * 80)
    print("Interfaces:")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            interface_name,
            ip_address,
            subnet_mask,
            interface_type,
            last_seen
        FROM device_interfaces
        WHERE device_id = ?
        ORDER BY interface_name
    """, (device_id,))
    
    interface_count = 0
    for row in cursor.fetchall():
        interface_count += 1
        print(f"\n  Interface: {row[0]}")
        print(f"    IP Address: {row[1]}")
        print(f"    Subnet Mask: {row[2]}")
        print(f"    Type: {row[3]}")
        print(f"    Last Seen: {row[4]}")
    
    if interface_count == 0:
        print("  No interfaces found")
    
    # Query stack members
    print("\n" + "-" * 80)
    print("Stack Members:")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            switch_number,
            role,
            priority,
            hardware_model,
            serial_number,
            mac_address,
            software_version,
            state,
            first_seen,
            last_seen
        FROM device_stack_members
        WHERE device_id = ?
        ORDER BY switch_number
    """, (device_id,))
    
    stack_members = cursor.fetchall()
    
    if stack_members:
        for row in stack_members:
            print(f"\n  Switch #{row[0]}")
            print(f"    Role: {row[1]}")
            print(f"    Priority: {row[2]}")
            print(f"    Hardware Model: {row[3]}")
            print(f"    Serial Number: {row[4]}")
            print(f"    MAC Address: {row[5]}")
            print(f"    Software Version: {row[6]}")
            print(f"    State: {row[7]}")
            print(f"    First Seen: {row[8]}")
            print(f"    Last Seen: {row[9]}")
    else:
        print("  No stack members found (device is not a stack or hasn't been discovered yet)")
    
    # Query VLANs
    print("\n" + "-" * 80)
    print("VLANs:")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            vlan_number,
            vlan_name,
            port_count,
            last_seen
        FROM device_vlans
        WHERE device_id = ?
        ORDER BY vlan_number
    """, (device_id,))
    
    vlan_count = 0
    for row in cursor.fetchall():
        vlan_count += 1
        if vlan_count <= 10:  # Show first 10 VLANs
            print(f"  VLAN {row[0]}: {row[1]} ({row[2]} ports) - Last seen: {row[3]}")
    
    if vlan_count > 10:
        print(f"  ... and {vlan_count - 10} more VLANs")
    elif vlan_count == 0:
        print("  No VLANs found")
    
    # Query neighbors
    print("\n" + "-" * 80)
    print("Neighbors:")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            d.device_name as neighbor_hostname,
            di.ip_address as neighbor_ip,
            n.source_interface as local_interface,
            n.destination_interface as remote_interface,
            n.protocol,
            n.last_seen
        FROM device_neighbors n
        INNER JOIN devices d ON n.destination_device_id = d.device_id
        LEFT JOIN (
            SELECT device_id, ip_address,
                   ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY last_seen DESC) as rn
            FROM device_interfaces
        ) di ON d.device_id = di.device_id AND di.rn = 1
        WHERE n.source_device_id = ?
        ORDER BY d.device_name
    """, (device_id,))
    
    neighbor_count = 0
    for row in cursor.fetchall():
        neighbor_count += 1
        if neighbor_count <= 10:  # Show first 10 neighbors
            print(f"\n  Neighbor: {row[0]}")
            print(f"    IP: {row[1]}")
            print(f"    Local Interface: {row[2]}")
            print(f"    Remote Interface: {row[3]}")
            print(f"    Protocol: {row[4]}")
            print(f"    Last Seen: {row[5]}")
    
    if neighbor_count > 10:
        print(f"\n  ... and {neighbor_count - 10} more neighbors")
    elif neighbor_count == 0:
        print("  No neighbors found")
    
    print("\n" + "=" * 80)
    
    cursor.close()
    conn.close()
    
except pyodbc.Error as e:
    print(f"Database error: {e}")
except Exception as e:
    print(f"Error: {e}")
