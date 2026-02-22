#!/usr/bin/env python3
"""
Test script to see actual PAN-OS command output
"""

import sys
from pathlib import Path
from netmiko import ConnectHandler

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from netwalker.config.credentials import CredentialManager

def main():
    # Get credentials
    cred_manager = CredentialManager('secret_creds.ini', {})
    creds = cred_manager.get_credentials()
    
    if not creds:
        print("Failed to get credentials")
        return 1
    
    # Connect to firewall
    device = {
        'device_type': 'paloalto_panos',
        'host': '192.168.205.173',
        'username': creds.username,
        'password': creds.password,
        'timeout': 30,
    }
    
    print(f"Connecting to {device['host']}...")
    
    try:
        connection = ConnectHandler(**device)
        print("Connected successfully!\n")
        
        # Test commands
        commands = [
            "set cli pager off",
            "show system info",
            "show arp all",
            "show routing route"
        ]
        
        for cmd in commands:
            print("=" * 80)
            print(f"Command: {cmd}")
            print("=" * 80)
            output = connection.send_command(cmd)
            print(output)
            print("\n")
        
        connection.disconnect()
        print("Disconnected")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
