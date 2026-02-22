"""
Test script to capture show module output from KGW-CORE-A
"""
import sys
sys.path.insert(0, '.')

from netwalker.connection.connection_manager import ConnectionManager
from netwalker.config.credentials import CredentialManager

# Initialize credentials
cred_mgr = CredentialManager()

# Get credentials
creds = cred_mgr.get_credentials()
username = creds.username
password = creds.password
enable_password = creds.enable_password

# Initialize connection manager
conn_mgr = ConnectionManager(username, password, enable_password)

# Connect to device
print("Connecting to KGW-CORE-A (10.176.0.33)...")
connection = conn_mgr.connect('10.176.0.33', 'ssh')

if connection:
    print("Connected successfully!")
    print("\n" + "="*80)
    print("SHOW MODULE OUTPUT:")
    print("="*80)
    
    # Send show module command
    output = connection.send_command('show module')
    print(output)
    
    print("\n" + "="*80)
    
    # Close connection
    conn_mgr.disconnect(connection)
    print("\nConnection closed.")
else:
    print("Failed to connect!")
