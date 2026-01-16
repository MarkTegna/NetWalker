#!/usr/bin/env python3
"""
Test connection to iad2-tegna-56128p-2 to see its show version output
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scrapli import Scrapli
from netwalker.discovery.device_collector import DeviceCollector

# Device connection details
device = {
    "host": "iad2-tegna-56128p-2",
    "auth_username": "ep-moldham",
    "auth_password": "vogon#Zaphod4pizza$",
    "auth_strict_key": False,
    "platform": "cisco_nxos",
    "transport": "paramiko",
}

print("=" * 70)
print("Connecting to iad2-tegna-56128p-2")
print("=" * 70)

try:
    conn = Scrapli(**device)
    conn.open()
    
    print("✓ Connected successfully")
    print()
    
    # Get show version output
    print("=" * 70)
    print("Getting 'show version' output")
    print("=" * 70)
    
    response = conn.send_command("show version")
    version_output = response.result
    
    print(version_output)
    print()
    
    # Test extraction
    print("=" * 70)
    print("Testing Extraction")
    print("=" * 70)
    
    collector = DeviceCollector()
    
    platform = collector._detect_platform(version_output)
    version = collector._extract_software_version(version_output)
    model = collector._extract_hardware_model(version_output)
    serial = collector._extract_serial_number(version_output)
    
    print(f"Platform: {platform}")
    print(f"Software Version: {version}")
    print(f"Hardware Model: {model}")
    print(f"Serial Number: {serial}")
    print()
    
    # Close connection
    conn.close()
    print("✓ Connection closed")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
