#!/usr/bin/env python3
"""
Test various Nexus output formats to find what might be failing
"""

import re

# Test different possible Nexus output formats
test_cases = [
    ("Standard with space before Chassis", "cisco Nexus9000 C9396PX Chassis", "C9396PX"),
    ("No space before Chassis", "cisco Nexus9000 C9396PXChassis", None),
    ("Lowercase", "cisco nexus9000 c9396px chassis", "c9396px"),
    ("Extra spaces", "cisco  Nexus9000  C9396PX  Chassis", "C9396PX"),
    ("Nexus 5000", "cisco Nexus5000 C5548P Chassis", "C5548P"),
    ("Nexus 7000", "cisco Nexus7000 C7009 Chassis", "C7009"),
    ("Without Chassis keyword", "cisco Nexus9000 C9396PX", None),
    ("With line break", "cisco Nexus9000 C9396PX\nChassis", None),
    ("Chassis on same line", "cisco Nexus9000 C9396PX Chassis ", "C9396PX"),
]

# Current pattern from device_collector.py
pattern = r'cisco\s+Nexus\d+\s+(C\d+[A-Z]*)\s+Chassis'

print("=" * 70)
print("Testing Nexus Chassis Pattern")
print("=" * 70)
print(f"Pattern: {pattern}")
print()

for description, test_input, expected in test_cases:
    match = re.search(pattern, test_input, re.IGNORECASE)
    result = match.group(1).strip() if match else None
    
    status = "✓ PASS" if result == expected else "✗ FAIL"
    print(f"{status} {description}")
    print(f"  Input: '{test_input}'")
    print(f"  Expected: {expected}")
    print(f"  Got: {result}")
    print()

print("=" * 70)
print("Alternative Pattern Tests")
print("=" * 70)

# Try a more flexible pattern
alt_pattern1 = r'cisco\s+Nexus\d+\s+(C\d+[A-Z0-9]*)'
print(f"\nAlternative 1 (without Chassis requirement): {alt_pattern1}")

for description, test_input, _ in test_cases:
    match = re.search(alt_pattern1, test_input, re.IGNORECASE)
    result = match.group(1).strip() if match else None
    print(f"  {description}: {result}")

# Try pattern that handles line breaks
alt_pattern2 = r'cisco\s+Nexus\d+\s+(C\d+[A-Z0-9]*)\s*(?:Chassis)?'
print(f"\nAlternative 2 (optional Chassis): {alt_pattern2}")

for description, test_input, _ in test_cases:
    match = re.search(alt_pattern2, test_input, re.IGNORECASE)
    result = match.group(1).strip() if match else None
    print(f"  {description}: {result}")

print("\n" + "=" * 70)
print("RECOMMENDATION")
print("=" * 70)
print("If devices are showing 'Unknown', the actual output might:")
print("1. Not have 'Chassis' keyword")
print("2. Have line breaks between model and 'Chassis'")
print("3. Have a different format entirely")
print("\nWe need to see actual 'show version' output from a failing device")
