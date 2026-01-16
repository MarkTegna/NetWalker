#!/usr/bin/env python3
"""
Regression test for hardware model extraction on DFW1-CORE-A
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scrapli import Scrapli
from netwalker.discovery.device_collector import DeviceCollector

# Device connection details
device = {
    "host": "DFW1-CORE-A",
    "auth_username": "ep-moldham",
    "auth_password": "vogon#Zaphod4pizza$",
    "auth_strict_key": False,
    "platform": "cisco_nxos",
    "transport": "paramiko",
}

print("=" * 70)
print("Regression Test: DFW1-CORE-A Hardware Model Extraction")
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
    
    # Show relevant hardware section
    lines = version_output.split('\n')
    in_hardware = False
    for line in lines:
        if 'Hardware' in line:
            in_hardware = True
        if in_hardware:
            print(line)
            if line.strip() == '' and in_hardware:
                break
    
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
    
    # Verify expected values
    print("=" * 70)
    print("Verification")
    print("=" * 70)
    
    expected_platform = "NX-OS"
    expected_version = "9.3(9)"
    expected_model = "C9336C-FX2"  # Actual hardware model for DFW1-CORE-A
    
    results = []
    
    if platform == expected_platform:
        print(f"✓ Platform: {platform} (correct)")
        results.append(True)
    else:
        print(f"✗ Platform: {platform} (expected: {expected_platform})")
        results.append(False)
    
    if version == expected_version:
        print(f"✓ Software Version: {version} (correct)")
        results.append(True)
    else:
        print(f"✗ Software Version: {version} (expected: {expected_version})")
        results.append(False)
    
    if model == expected_model:
        print(f"✓ Hardware Model: {model} (correct)")
        results.append(True)
    else:
        print(f"✗ Hardware Model: {model} (expected: {expected_model})")
        results.append(False)
    
    if serial and serial != "Unknown":
        print(f"✓ Serial Number: {serial} (extracted)")
        results.append(True)
    else:
        print(f"✗ Serial Number: {serial} (failed to extract)")
        results.append(False)
    
    print()
    
    # Close connection
    conn.close()
    print("✓ Connection closed")
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if all(results):
        print("✓ ALL TESTS PASSED - No regression detected")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED - Regression detected!")
        sys.exit(1)
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
