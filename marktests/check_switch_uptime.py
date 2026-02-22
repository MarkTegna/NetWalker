"""
Check what uptime information is available in 'show switch' output for KARE-CORE-A
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scrapli.driver.core import IOSXEDriver
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Device credentials
device = {
    "host": "KARE-CORE-A",
    "auth_username": "netwalker",
    "auth_password": "Netwalker2024!",
    "auth_strict_key": False,
    "transport": "paramiko"
}

try:
    logger.info(f"Connecting to {device['host']}...")
    conn = IOSXEDriver(**device)
    conn.open()
    logger.info("Connected successfully")
    
    # Get show switch output
    logger.info("\n" + "="*80)
    logger.info("SHOW SWITCH OUTPUT:")
    logger.info("="*80)
    response = conn.send_command("show switch")
    print(response.result)
    
    # Get show switch detail output
    logger.info("\n" + "="*80)
    logger.info("SHOW SWITCH DETAIL OUTPUT:")
    logger.info("="*80)
    response = conn.send_command("show switch detail")
    print(response.result)
    
    conn.close()
    logger.info("\nConnection closed")
    
except Exception as e:
    logger.error(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
