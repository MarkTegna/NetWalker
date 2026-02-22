"""Query database for LUMV-CORE-A device information"""
import sys
sys.path.insert(0, '.')

from netwalker.database.database_manager import DatabaseManager
import configparser

# Load config
config = configparser.ConfigParser()
config.read('netwalker.ini')

# Decrypt password if needed
password = config.get('database', 'password')
if password.startswith('ENC:'):
    # For now, use the encrypted value as-is since we can't decrypt without the key
    # The database manager will handle this
    pass

# Create database manager
db_config = {
    'enabled': config.getboolean('database', 'enabled'),
    'server': config.get('database', 'server'),
    'port': config.getint('database', 'port'),
    'database': config.get('database', 'database'),
    'username': config.get('database', 'username'),
    'password': password,
    'trust_server_certificate': config.getboolean('database', 'trust_server_certificate'),
    'connection_timeout': config.getint('database', 'connection_timeout'),
    'command_timeout': config.getint('database', 'command_timeout')
}

db_manager = DatabaseManager(db_config)

if db_manager.connect():
    print("=" * 80)
    print("Connected to database successfully")
    print("=" * 80)
    
    # Query for LUMV-CORE-A
    print("\nQuerying for LUMV-CORE-A...")
    device_info = db_manager.get_device_info_by_host('LUMV-CORE-A')
    
    if device_info:
        print("\n" + "=" * 80)
        print("DEVICE INFORMATION FOR LUMV-CORE-A")
        print("=" * 80)
        print(f"Device ID:        {device_info.get('device_id', 'N/A')}")
        print(f"Hostname:         {device_info.get('hostname', 'N/A')}")
        print(f"Serial Number:    {device_info.get('serial_number', 'N/A')}")
        print(f"Hardware Model:   {device_info.get('hardware_model', 'N/A')}")
        print(f"Platform:         {device_info.get('platform', 'N/A')}")
        print(f"Software Version: {device_info.get('software_version', 'N/A')}")
        print(f"Primary IP:       {device_info.get('primary_ip', 'N/A')}")
        print(f"Status:           {device_info.get('status', 'N/A')}")
        print(f"Last Seen:        {device_info.get('last_seen', 'N/A')}")
        print(f"Capabilities:     {', '.join(device_info.get('capabilities', []))}")
        print("=" * 80)
        
        # Also query raw database for more details
        print("\nQuerying raw database tables...")
        cursor = db_manager.connection.cursor()
        
        # Get device record
        cursor.execute("""
            SELECT 
                device_id,
                device_name,
                serial_number,
                platform,
                hardware_model,
                capabilities,
                connection_failures,
                first_seen,
                last_seen,
                status,
                created_at,
                updated_at
            FROM devices
            WHERE device_name = ?
        """, ('LUMV-CORE-A',))
        
        row = cursor.fetchone()
        if row:
            print("\n" + "-" * 80)
            print("DEVICES TABLE:")
            print("-" * 80)
            print(f"device_id:            {row[0]}")
            print(f"device_name:          {row[1]}")
            print(f"serial_number:        {row[2]}")
            print(f"platform:             {row[3]}")
            print(f"hardware_model:       {row[4]}")
            print(f"capabilities:         {row[5]}")
            print(f"connection_failures:  {row[6]}")
            print(f"first_seen:           {row[7]}")
            print(f"last_seen:            {row[8]}")
            print(f"status:               {row[9]}")
            print(f"created_at:           {row[10]}")
            print(f"updated_at:           {row[11]}")
            
            device_id = row[0]
            
            # Get version info
            cursor.execute("""
                SELECT software_version, first_seen, last_seen
                FROM device_versions
                WHERE device_id = ?
                ORDER BY last_seen DESC
            """, (device_id,))
            
            versions = cursor.fetchall()
            if versions:
                print("\n" + "-" * 80)
                print("DEVICE_VERSIONS TABLE:")
                print("-" * 80)
                for ver in versions:
                    print(f"  Software: {ver[0]}, First: {ver[1]}, Last: {ver[2]}")
            
            # Get interface info
            cursor.execute("""
                SELECT interface_name, ip_address, subnet_mask, interface_type, last_seen
                FROM device_interfaces
                WHERE device_id = ?
                ORDER BY last_seen DESC
            """, (device_id,))
            
            interfaces = cursor.fetchall()
            if interfaces:
                print("\n" + "-" * 80)
                print("DEVICE_INTERFACES TABLE:")
                print("-" * 80)
                for intf in interfaces:
                    print(f"  {intf[0]}: {intf[1]}/{intf[2]} ({intf[3]}) - Last: {intf[4]}")
            
            # Get stack member info
            cursor.execute("""
                SELECT switch_number, role, priority, hardware_model, serial_number, 
                       mac_address, software_version, state, last_seen
                FROM device_stack_members
                WHERE device_id = ?
                ORDER BY switch_number
            """, (device_id,))
            
            stack_members = cursor.fetchall()
            if stack_members:
                print("\n" + "-" * 80)
                print("DEVICE_STACK_MEMBERS TABLE:")
                print("-" * 80)
                for member in stack_members:
                    print(f"  Switch {member[0]}: {member[3]} / {member[4]}")
                    print(f"    Role: {member[1]}, Priority: {member[2]}, State: {member[7]}")
                    print(f"    MAC: {member[5]}, Software: {member[6]}, Last: {member[8]}")
        
        cursor.close()
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("NO DEVICE INFORMATION FOUND FOR LUMV-CORE-A")
        print("=" * 80)
        print("\nSearching for similar hostnames...")
        
        cursor = db_manager.connection.cursor()
        cursor.execute("""
            SELECT device_name, serial_number, platform, hardware_model, last_seen
            FROM devices
            WHERE device_name LIKE '%LUMV%' OR device_name LIKE '%LUM%'
            ORDER BY last_seen DESC
        """)
        
        similar = cursor.fetchall()
        if similar:
            print("\nFound similar devices:")
            for dev in similar:
                print(f"  {dev[0]} - {dev[2]} / {dev[3]} (Serial: {dev[1]}, Last: {dev[4]})")
        else:
            print("No similar devices found")
        
        cursor.close()
    
    db_manager.disconnect()
else:
    print("=" * 80)
    print("FAILED TO CONNECT TO DATABASE")
    print("=" * 80)
    print("\nThis is expected if:")
    print("  - Database credentials need to be decrypted")
    print("  - Network access to database server is restricted")
    print("  - Database is not accessible from this machine")
