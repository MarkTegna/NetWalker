#!/usr/bin/env python3
"""
Test with actual device patterns from the screenshot
"""

import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from netwalker.discovery.device_collector import DeviceCollector

# Test various Nexus patterns
test_cases = [
    # Case 1: Standard Nexus format
    ("cisco Nexus9000 C9396PX Chassis", "C9396PX"),
    # Case 2: Nexus with different model
    ("cisco Nexus5000 C5548P Chassis", "C5548P"),
    # Case 3: Nexus 7000
    ("cisco Nexus7000 C7009 Chassis", "C7009"),
    # Case 4: Without space before Chassis
    ("cisco Nexus9000 C9396PXChassis", None),  # Should not match
    # Case 5: With extra spaces
    ("cisco  Nexus9000  C9396PX  Chassis", "C9396PX"),
]

collector = DeviceCollector()

print("=" * 70)
print("Testing Nexus Chassis Pattern")
print("=" * 70)

pattern = r'cisco\s+Nexus\d+\s+(C\d+[A-Z]*)\s+Chassis'

for test_input, expected in test_cases:
    match = re.search(pattern, test_input, re.IGNORECASE)
    result = match.group(1).strip() if match else None
    
    status = "✓ PASS" if result == expected else "✗ FAIL"
    print(f"\nInput: {test_input}")
    print(f"Expected: {expected}")
    print(f"Got: {result}")
    print(f"{status}")

print("\n" + "=" * 70)
print("Testing with Full Version Output")
print("=" * 70)

# Simulate a full version output that might be missing the chassis line
partial_nxos = """Cisco Nexus Operating System (NX-OS) Software
Software
  BIOS: version 08.38
 NXOS: version 9.3(9)

Hardware
  cisco Nexus9000 C9396PX
  Processor Board ID FDO2324DFVE
"""

print("\nTest: Partial output without 'Chassis' keyword")
print("-" * 70)
model = collector._extract_hardware_model(partial_nxos)
print(f"Extracted: {model}")
print(f"Expected: C9396PX or Unknown")

# Test with Model Number field
with_model_number = """Cisco Nexus Operating System (NX-OS) Software
Software
  BIOS: version 08.38
 NXOS: version 9.3(9)

Hardware
  Model Number: C9396PX
  cisco Nexus9000 C9396PX Chassis
  Processor Board ID FDO2324DFVE
"""

print("\nTest: With Model Number field")
print("-" * 70)
model = collector._extract_hardware_model(with_model_number)
print(f"Extracted: {model}")
print(f"Expected: C9396PX")
