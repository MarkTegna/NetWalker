"""
Connect to WMAZ-2ND-SW01 and get CDP neighbors detail to find Polycom Trio 8500
"""
import sys
sys.path.insert(0, '.')

from netwalker.config.config_manager import ConfigurationManager
from netwalker.config.credentials import CredentialManager
from netwalker.connection.connection_manager import ConnectionManager

# Load config
config_manager = ConfigurationManager('marktests/netwalker.ini')
full_config = config_manager.load_configuration()

# Get credentials
cred_manager = CredentialManager(credentials_file='secret_creds.ini')
credentials = cred_manager.get_credentials()

if not credentials:
    print("Failed to get credentials")
    sys.exit(1)

# Initialize connection manager
conn_config = full_config.get('connection')
conn_manager = ConnectionManager(
    ssh_port=conn_config.ssh_port if conn_config else 22,
    telnet_port=conn_config.telnet_port if conn_config else 23,
    timeout=30
)

# Connect to WMAZ-2ND-SW01
switch_ip = None
switch_name = "WMAZ-2ND-SW01"

# First, find the IP address from database
from netwalker.database.database_manager import DatabaseManager
db_config = full_config.get('database')
db = DatabaseManager(db_config)

if db.connect():
    cursor = db.connection.cursor()
    # Get device_id first
    cursor.execute("SELECT device_id FROM devices WHERE device_name = ?", (switch_name,))
    row = cursor.fetchone()
    if not row:
        print(f"Device {switch_name} not found in database")
        sys.exit(1)
    
    device_id = row[0]
    
    # Get management IP from device_interfaces
    cursor.execute("""
        SELECT ip_address 
        FROM device_interfaces 
        WHERE device_id = ? AND interface_type = 'Management'
        ORDER BY interface_id
    """, (device_id,))
    row = cursor.fetchone()
    if row:
        switch_ip = row[0]
        print(f"Found {switch_name} with IP: {switch_ip}")
    else:
        print(f"Device {switch_name} not found in database")
        sys.exit(1)
    cursor.close()
    db.disconnect()
else:
    print("Failed to connect to database")
    sys.exit(1)

# Connect to the switch
print(f"\nConnecting to {switch_name} ({switch_ip})...")
connection, conn_result = conn_manager.connect_device(switch_ip, credentials)

if not connection or conn_result.status.value != "success":
    print(f"Failed to connect: {conn_result.error_message}")
    sys.exit(1)

print("Connected successfully!")

# Execute "show cdp neighbors detail" command
print("\nExecuting 'show cdp neighbors detail'...")
output = conn_manager.execute_command(connection, "show cdp neighbors detail")

if output:
    print("\n" + "="*80)
    print("CDP NEIGHBORS DETAIL OUTPUT:")
    print("="*80)
    print(output)
    print("="*80)
    
    # Search for Polycom or Trio in the output
    if 'Polycom' in output or 'Trio' in output or 'polycom' in output.lower():
        print("\n*** FOUND POLYCOM/TRIO DEVICE IN OUTPUT ***")
    else:
        print("\nNo Polycom or Trio devices found in CDP output")
else:
    print("No output received from command")

# Close connection
conn_manager.close_connection(switch_ip)
print("\nConnection closed")
