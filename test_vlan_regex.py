import re

# The regex pattern from the code
ios_vlan_pattern = re.compile(
    r'^(\d+)\s+(\S+)\s+\S+\s+(.*)', 
    re.MULTILINE
)

# Test cases
test_lines = [
    "216  RingCentral-Test                 active    Gi2/0/6, Gi2/0/31, Tw4/0/6, Tw4/0/23, Tw4/0/31",
    "461  FW-RINGCENTRAL                   active    ",
    "461  FW-RINGCENTRAL                   active",
    "469  AI                               active    ",
]

print("Testing VLAN regex pattern:")
print("=" * 80)

for line in test_lines:
    print(f"\nLine: '{line}'")
    match = ios_vlan_pattern.match(line)
    if match:
        vlan_id = match.group(1)
        vlan_name = match.group(2)
        ports_str = match.group(3)
        print(f"  ✅ MATCHED")
        print(f"  VLAN ID: {vlan_id}")
        print(f"  VLAN Name: {vlan_name}")
        print(f"  Ports: '{ports_str}' (length: {len(ports_str)})")
    else:
        print(f"  ❌ NO MATCH")
