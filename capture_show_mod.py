"""
Capture raw show module output from KGW-CORE-A
"""
import sys
sys.path.insert(0, '.')

from netwalker.connection.connection_manager import ConnectionManager
from netwalker.config.credentials import CredentialManager

# Initialize credentials
cred_mgr = CredentialManager()
creds = cred_mgr.get_credentials()

# Initialize connection manager
conn_mgr = ConnectionManager()

# Connect to device
print("Connecting to KGW-CORE-A (10.176.0.33)...")
connection, result = conn_mgr.connect_device('10.176.0.33', creds)

if connection:
    print("Connected successfully!")
    print("\n" + "="*80)
    print("RAW SHOW MODULE OUTPUT:")
    print("="*80)
    
    # Send show module command
    output = conn_mgr.execute_command(connection, 'show module')
    
    # Print with line numbers
    lines = output.split('\n')
    for i, line in enumerate(lines, 1):
        print(f"{i:3d}: {line}")
    
    print("\n" + "="*80)
    
    # Close connection
    conn_mgr.close_connection('10.176.0.33')
    print("\nConnection closed.")
else:
    print(f"Failed to connect: {result}")
