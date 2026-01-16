import re

# The exact line from the log
line_461 = "461  FW-RINGCENTRAL                   active    "

# The regex pattern
ios_vlan_pattern = re.compile(
    r'^(\d+)\s+(\S+)\s+\S+\s+(.*)', 
    re.MULTILINE
)

print(f"Testing line: '{line_461}'")
print(f"Line length: {len(line_461)}")
print(f"Line repr: {repr(line_461)}")

match = ios_vlan_pattern.match(line_461)
if match:
    print("\n✅ MATCHED!")
    print(f"Group 1 (VLAN ID): '{match.group(1)}'")
    print(f"Group 2 (VLAN Name): '{match.group(2)}'")
    print(f"Group 3 (Ports): '{match.group(3)}'")
    print(f"Group 3 length: {len(match.group(3))}")
    print(f"Group 3 stripped: '{match.group(3).strip()}'")
    print(f"Group 3 stripped length: {len(match.group(3).strip())}")
else:
    print("\n❌ NO MATCH!")

# Try without the trailing spaces
line_461_no_spaces = "461  FW-RINGCENTRAL                   active"
print(f"\n\nTesting line without trailing spaces: '{line_461_no_spaces}'")
match2 = ios_vlan_pattern.match(line_461_no_spaces)
if match2:
    print("✅ MATCHED!")
else:
    print("❌ NO MATCH!")
