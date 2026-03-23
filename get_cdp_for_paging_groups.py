"""
Get CDP Neighbor Data for Paging Groups

This script connects to KUSA-9300-BASEMENT-01 and retrieves the raw CDP data
for the paging group devices.
"""

from netwalker.config.config_manager import ConfigurationManager
from netwalker.config.credentials import CredentialManager
from netwalker.connection.connection_manager import ConnectionManager
from netwalker.connection.data_models import ConnectionStatus
from netwalker.discovery.protocol_parser import ProtocolParser

def get_cdp_data():
    """Get CDP data from parent device"""
    
    # Load configuration
    config_manager = ConfigurationManager('netwalker.ini')
    config = config_manager.load_configuration()
    
    # Get credentials
    credentials_file = config.get('credentials_file', 'secret_creds.ini')
    credential_manager = CredentialManager(credentials_file, config)
    credentials = credential_manager.get_credentials()
    
    # Create connection manager with proper parameters
    connection_config = config['connection']
    discovery_config = config['discovery']
    conn_manager = ConnectionManager(
        ssh_port=connection_config.ssh_port,
        telnet_port=connection_config.telnet_port,
        timeout=discovery_config.connection_timeout,
        ssl_verify=connection_config.ssl_verify,
        ssl_cert_file=connection_config.ssl_cert_file if connection_config.ssl_cert_file else None,
        ssl_key_file=connection_config.ssl_key_file if connection_config.ssl_key_file else None,
        ssl_ca_bundle=connection_config.ssl_ca_bundle if connection_config.ssl_ca_bundle else None
    )
    
    parent_device = "KUSA-9300-BASEMENT-01"
    parent_ip = "10.120.138.11"  # You may need to adjust this
    
    print(f"Connecting to {parent_device} ({parent_ip})...")
    
    try:
        # Connect to device
        connection, result = conn_manager.connect_device(parent_ip, credentials)
        
        if not connection or result.status != ConnectionStatus.SUCCESS:
            print(f"Failed to connect to {parent_device}: {result.error_message if result else 'Unknown error'}")
            return
        
        print(f"Connected successfully!\n")
        print("=" * 80)
        print("RAW CDP NEIGHBOR OUTPUT:")
        print("=" * 80)
        
        # Get CDP neighbors
        cdp_output = connection.send_command("show cdp neighbors detail")
        print(cdp_output)
        
        print("\n" + "=" * 80)
        print("PARSING CDP DATA:")
        print("=" * 80)
        
        # Parse CDP data
        parser = ProtocolParser()
        neighbors = parser.parse_cdp_neighbors(cdp_output)
        
        # Filter for paging groups
        paging_neighbors = [n for n in neighbors if 'paging' in n.device_id.lower()]
        
        if paging_neighbors:
            print(f"\nFound {len(paging_neighbors)} paging group neighbors:\n")
            for neighbor in paging_neighbors:
                print(f"Hostname: {neighbor.device_id}")
                print(f"IP Address: {neighbor.ip_address}")
                print(f"Platform: {neighbor.platform}")
                print(f"Capabilities: {neighbor.capabilities}")
                print(f"Local Interface: {neighbor.local_interface}")
                print(f"Remote Interface: {neighbor.remote_interface}")
                print("-" * 80)
        else:
            print("\nNo paging group neighbors found in parsed data")
        
        # Close connection
        conn_manager.disconnect_device(parent_ip)
        print("\nConnection closed")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    get_cdp_data()
