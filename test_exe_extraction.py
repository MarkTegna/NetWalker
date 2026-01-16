#!/usr/bin/env python3
"""
Test if the built executable has the correct extraction methods
This script should be run AFTER building to verify the exe
"""

import subprocess
import sys

# Test script that will be passed to the executable
test_script = """
import sys
sys.path.insert(0, '.')

from netwalker.discovery.device_collector import DeviceCollector

nxos_output = '''Cisco Nexus Operating System (NX-OS) Software
Software
  BIOS: version 08.38
 NXOS: version 9.3(9)

Hardware
  cisco Nexus9000 C9396PX Chassis 
  Processor Board ID FDO2324DFVE
'''

collector = DeviceCollector()
version = collector._extract_software_version(nxos_output)
model = collector._extract_hardware_model(nxos_output)

print(f"Version: {version}")
print(f"Model: {model}")

if version == "9.3(9)" and model == "C9396PX":
    print("PASS")
    sys.exit(0)
else:
    print("FAIL")
    sys.exit(1)
"""

# Write test script to temp file
with open('_temp_test.py', 'w') as f:
    f.write(test_script)

print("Testing if built executable has correct extraction methods...")
print("=" * 70)

try:
    # Run the test with Python directly first
    print("\n1. Testing with Python source:")
    result = subprocess.run([sys.executable, '_temp_test.py'], 
                          capture_output=True, text=True, timeout=10)
    print(result.stdout)
    if result.returncode != 0:
        print("FAILED with Python source!")
        print(result.stderr)
    
    # Now test with the executable (if it exists)
    import os
    exe_path = 'dist/netwalker.exe'
    if os.path.exists(exe_path):
        print("\n2. Testing with built executable:")
        print("(This test cannot directly import from exe, checking version instead)")
        result = subprocess.run([exe_path, '--version'], 
                              capture_output=True, text=True, timeout=10)
        print(result.stdout)
    else:
        print(f"\n2. Executable not found at {exe_path}")
        print("   Build the executable first with: python build_executable.py")
        
finally:
    # Clean up
    import os
    if os.path.exists('_temp_test.py'):
        os.remove('_temp_test.py')

print("\n" + "=" * 70)
print("NOTE: The executable packages the Python code internally.")
print("The real test is running actual discovery and checking the reports.")
