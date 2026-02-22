"""
Check 'show version' output to see if it contains per-stack-member uptime
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netwalker.connection.connection_manager import ConnectionManager
from netwalker.config.credentials import CredentialManager
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load credentials
cred_manager = CredentialManager()
cred_manager.load_credentials()

# Get credentials for the device
device_host = "KARE-CORE-A"
credentials = cred_manager.get_credentials(device_host)

if not credentials:
    logger.error(f"No credentials found for {device_host}")
    sys.exit(1)

logger.info(f"Using credentials: username={credentials.username}")

# Create connection manager
conn_manager = ConnectionManager(
    ssh_port=22,
    telnet_port=23,
    connection_timeout=30,
    preferred_method='ssh'
)

try:
    logger.info(f"Connecting to {device_host}...")
    connection = conn_manager.connect(device_host, credentials)
    
    if not connection:
        logger.error("Failed to connect")
        sys.exit(1)
    
    logger.info("Connected successfully")
    
    # Get show version output
    logger.info("\n" + "="*80)
    logger.info("SHOW VERSION OUTPUT:")
    logger.info("="*80)
    
    if hasattr(connection, 'send_command'):
        response = connection.send_command("show version")
        if hasattr(response, 'result'):
            output = response.result
        else:
            output = response
        print(output)
    
    # Get show switch output
    logger.info("\n" + "="*80)
    logger.info("SHOW SWITCH OUTPUT:")
    logger.info("="*80)
    
    if hasattr(connection, 'send_command'):
        response = connection.send_command("show switch")
        if hasattr(response, 'result'):
            output = response.result
        else:
            output = response
        print(output)
    
    # Close connection
    conn_manager.disconnect(connection)
    logger.info("\nConnection closed")
    
except Exception as e:
    logger.error(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
