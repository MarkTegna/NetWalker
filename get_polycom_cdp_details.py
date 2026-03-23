"""
Connect to WMAZ-2ND-SW01 and get CDP details for Polycom devices
"""
import sys
sys.path.insert(0, '.')

from netwalker.config.config_manager import ConfigurationManager
from netwalker.connection.connection_manager import ConnectionManager
from netwalker.connection.credential_manager import CredentialManager

# Load config
config_manager = ConfigurationManager('netwalker.ini')
full_config = config_manager.load_configuration()

# Get credentials
cred_manager = CredentialManager()
credentials = cred_manager.get_credentials()

if not credentials or not credentials.username:
    print("No credentials available")
    sys.exit(1)

# Initialize connection manager
conn_config = full_config.get('connection', {})
conn_manager = ConnectionManager(conn_config, credentials)

# Target switch
switch_name = 'WMAZ-2ND-SW01'

print(f"Connecting to {switch_name}...")
print()

try:
    # Connect to the switch
    connection = conn_manager.connect(switch_name, switch_name)
    
    if not connection:
        print(f"Failed to connect to {switch_name}")
        sys.exit(1)
    
    print(f"✓ Connected to {switch_name}")
    print()
    
    # Get CDP neighbors detail
    print("Fetching CDP neighbors detail...")
    cdp_output = conn_manager.send_command(connection, 'show cdp neighbors detail')
    
    # Search for Polycom or Trio in the output
    if 'Polycom' in cdp_output or 'Trio' in cdp_output:
        print("=" * 80)
        print("FOUND POLYCOM/TRIO DEVICES IN CDP OUTPUT")
        print("=" * 80)
        print()
        
        # Split by device separator
        import re
        entries = re.split(r'-{20,}', cdp_output)
        
        for entry in entries:
            if 'Polycom' in entry or 'Trio' in entry:
                print(entry)
                print("-" * 80)
                print()
    else:
        print("No Polycom or Trio devices found in CDP output")
        print()
        print("Trying LLDP...")
        print()
        
        # Try LLDP
        lldp_output = conn_manager.send_command(connection, 'show lldp neighbors detail')
        
        if 'Polycom' in lldp_output or 'Trio' in lldp_output:
            print("=" * 80)
            print("FOUND POLYCOM/TRIO DEVICES IN LLDP OUTPUT")
            print("=" * 80)
            print()
            print(lldp_output)
        else:
            print("No Polycom or Trio devices found in LLDP output either")
    
    # Close connection
    conn_manager.close_connection(connection)
    print()
    print("✓ Connection closed")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    conn_manager.close_all()
