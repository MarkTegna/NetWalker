#!/usr/bin/env python3
"""
Test KXTV Stack Commands

Manually connect to a KXTV device and test stack commands.

Author: Mark Oldham
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from netwalker.config.config_manager import ConfigurationManager
from netwalker.config.credentials import CredentialManager
from netwalker.connection.connection_manager import ConnectionManager


def main():
    """Main function"""
    
    # Device to test
    device_name = "KXTV-MC-STACK1"
    device_ip = "10.12.203.8"
    
    print(f"\nTesting stack commands on {device_name} ({device_ip})")
    print("=" * 80)
    
    # Load configuration
    config_file = 'netwalker.ini'
    config_manager = ConfigurationManager(config_file)
    parsed_config = config_manager.load_configuration()
    
    # Initialize credentials
    cred_manager = CredentialManager()
    creds = cred_manager.get_credentials()
    username = creds.username
    password = creds.password
    enable_password = creds.enable_password
    
    if not username or not password:
        print("[FAIL] No credentials available")
        return 1
    
    # Initialize connection manager
    conn_manager = ConnectionManager(
        ssh_port=22,
        telnet_port=23,
        timeout=30,
        ssl_verify=False
    )
    
    try:
        print(f"\nConnecting to {device_ip}...")
        
        # Create credentials object
        from netwalker.config.credentials import Credentials
        creds_obj = Credentials(username=username, password=password, enable_password=enable_password)
        
        connection, result = conn_manager.connect_device(device_ip, creds_obj)
        
        if not connection:
            print(f"[FAIL] Could not connect to {device_ip}: {result.error_message}")
            return 1
        
        print(f"[OK] Connected successfully")
        
        # Test show switch
        print(f"\n{'='*80}")
        print("Testing: show switch")
        print(f"{'='*80}")
        output = conn_manager.execute_command(connection, "show switch")
        print(output)
        
        # Test show switch detail
        print(f"\n{'='*80}")
        print("Testing: show switch detail")
        print(f"{'='*80}")
        output = conn_manager.execute_command(connection, "show switch detail")
        print(output)
        
        # Test show inventory
        print(f"\n{'='*80}")
        print("Testing: show inventory")
        print(f"{'='*80}")
        output = conn_manager.execute_command(connection, "show inventory")
        print(output[:2000] if output else "No output")  # Limit output
        
        # Test show version
        print(f"\n{'='*80}")
        print("Testing: show version")
        print(f"{'='*80}")
        output = conn_manager.execute_command(connection, "show version")
        print(output[:2000] if output else "No output")  # Limit output
        
        # Disconnect
        conn_manager.close_connection(device_ip)
        print(f"\n[OK] Disconnected")
        
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
