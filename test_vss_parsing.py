"""
Test VSS parsing with actual KGW-CORE-A output
"""

import sys
import re
from typing import List, Optional

# Mock StackMemberInfo for testing
class StackMemberInfo:
    def __init__(self, switch_number, role, priority, hardware_model, 
                 serial_number, mac_address, software_version, state):
        self.switch_number = switch_number
        self.role = role
        self.priority = priority
        self.hardware_model = hardware_model
        self.serial_number = serial_number
        self.mac_address = mac_address
        self.software_version = software_version
        self.state = state
    
    def __repr__(self):
        return (f"StackMemberInfo(switch={self.switch_number}, role={self.role}, "
                f"model={self.hardware_model}, serial={self.serial_number})")


def parse_vss_output(output: str) -> List[StackMemberInfo]:
    """
    Parse 'show mod' output from VSS devices (Catalyst 4500-X, 6500).
    """
    stack_members = []
    lines = output.split('\n')
    
    # Find the first data section (before MAC addresses section)
    in_data_section = False
    found_first_section = False
    
    for line in lines:
        line_stripped = line.strip()
        
        # Skip empty lines
        if not line_stripped:
            continue
        
        # Look for the first header line
        if 'mod' in line_stripped.lower() and 'ports' in line_stripped.lower() and 'card type' in line_stripped.lower():
            continue
        
        # Look for the separator line (dashes)
        if '---' in line_stripped or '------' in line_stripped:
            if not found_first_section:
                in_data_section = True
                found_first_section = True
            else:
                # Stop at second separator (MAC addresses section)
                break
            continue
        
        # Parse data lines only in first section
        if in_data_section:
            # VSS lines start with switch number (1 or 2) followed by spaces and port count
            if re.match(r'^\s*[12]\s+\d+\s+', line):
                member = parse_vss_line(line_stripped)
                if member:
                    stack_members.append(member)
    
    # Only return stack members if we found multiple switches (VSS requires 2)
    if len(stack_members) >= 2:
        return stack_members
    else:
        print(f"Found {len(stack_members)} switch(es), not a VSS configuration (requires 2)")
        return []


def parse_vss_line(line: str) -> Optional[StackMemberInfo]:
    """
    Parse a single line from 'show mod' VSS output.
    Expected format: "  1   52  Sup 7-E, 48 GE (SFP+), 4 XGMII Fabric WS-C4500X-32       JAE240213DA"
    """
    try:
        # Extract switch number (first field)
        switch_match = re.match(r'^\s*([12])\s+', line)
        if not switch_match:
            return None
        
        switch_number = int(switch_match.group(1))
        
        # Extract model - look for WS-C pattern
        model_match = re.search(r'(WS-C[\w-]+)', line, re.IGNORECASE)
        model = model_match.group(1) if model_match else "Unknown"
        
        # Extract serial number - Cisco serial format is typically:
        # 3 letters + 6 digits + 2 letters (e.g., JAE240213DA)
        # or 3 letters + 9 digits (e.g., FOC123456789)
        serial_match = re.search(r'\b([A-Z]{3}\d{6}[A-Z]{2})\b', line)
        if not serial_match:
            # Try alternate pattern: 3 letters + 9 digits
            serial_match = re.search(r'\b([A-Z]{3}\d{9})\b', line)
        
        serial = serial_match.group(1) if serial_match else "Unknown"
        
        # Determine role - for VSS, switch 1 is typically Active, switch 2 is Standby
        role = "Active" if switch_number == 1 else "Standby"
        
        # Check if there's a status indicator in the line
        if 'active' in line.lower():
            role = "Active"
        elif 'standby' in line.lower():
            role = "Standby"
        
        return StackMemberInfo(
            switch_number=switch_number,
            role=role,
            priority=None,
            hardware_model=model,
            serial_number=serial,
            mac_address=None,
            software_version=None,
            state="Ok"
        )
        
    except (ValueError, IndexError) as e:
        print(f"Failed to parse VSS line: {line} - {str(e)}")
        return None


# Test with actual KGW-CORE-A output (using real serial numbers from database)
kgw_core_a_output = """
Mod Ports Card Type                              Model              Serial No.
--- ----- -------------------------------------- ------------------ -----------
  1   52  Sup 7-E, 48 GE (SFP+), 4 XGMII Fabric WS-C4500X-32       JAE240213DA
  2   52  Sup 7-E, 48 GE (SFP+), 4 XGMII Fabric WS-C4500X-32       JAE242325EK

Mod MAC addresses                       Hw    Fw           Sw           Status
--- ---------------------------------- ------ ------------ ------------ -------
  1 0062.ec9d.7800 to 0062.ec9d.7833   1.1   15.1(1r)SG8  03.11.03.E   Ok
  2 0062.ec9d.6000 to 0062.ec9d.6033   1.1   15.1(1r)SG8  03.11.03.E   Ok

Mod  Sub-Module                  Model              Serial       Hw     Status
---- --------------------------- ------------------ ----------- ------- -------
  1 Centralized Forwarding Card WS-C4500X-32       JAE240213DA  1.1    Ok
  2 Centralized Forwarding Card WS-C4500X-32       JAE242325EK  1.1    Ok
"""

print("Testing VSS parsing with KGW-CORE-A output:")
print("=" * 70)

members = parse_vss_output(kgw_core_a_output)

if members:
    print(f"\nSuccessfully parsed {len(members)} VSS members:")
    for member in members:
        print(f"  {member}")
    print("\nExpected results:")
    print("  - Switch 1: Active, WS-C4500X-32, JAE240213DA")
    print("  - Switch 2: Standby, WS-C4500X-32, JAE242325EK")
    
    # Validate results
    success = True
    if len(members) != 2:
        print(f"\n[FAIL] Expected 2 members, got {len(members)}")
        success = False
    
    if members[0].switch_number != 1 or members[0].serial_number != "JAE240213DA":
        print(f"\n[FAIL] Switch 1 data incorrect")
        success = False
    
    if members[0].hardware_model != "WS-C4500X-32":
        print(f"\n[FAIL] Switch 1 model incorrect: {members[0].hardware_model}")
        success = False
    
    if members[1].switch_number != 2 or members[1].serial_number != "JAE242325EK":
        print(f"\n[FAIL] Switch 2 data incorrect: got serial {members[1].serial_number}")
        success = False
    
    if members[1].hardware_model != "WS-C4500X-32":
        print(f"\n[FAIL] Switch 2 model incorrect: {members[1].hardware_model}")
        success = False
    
    if success:
        print("\n[PASS] All validations passed!")
else:
    print("\n[FAIL] No VSS members found")
