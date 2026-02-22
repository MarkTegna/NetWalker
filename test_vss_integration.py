"""
Integration test for VSS stack detection
Tests the full stack collection flow with simulated connection
"""

import sys
sys.path.insert(0, '.')

from netwalker.discovery.stack_collector import StackCollector

# Mock connection class
class MockConnection:
    def __init__(self, show_switch_output=None, show_mod_output=None):
        self.show_switch_output = show_switch_output
        self.show_mod_output = show_mod_output
        self.transport = True  # Indicates scrapli connection
    
    def send_command(self, command):
        class Response:
            def __init__(self, result):
                self.result = result
        
        if command == "show switch":
            return Response(self.show_switch_output)
        elif command == "show mod":
            return Response(self.show_mod_output)
        else:
            return Response("")

# KGW-CORE-A show mod output
kgw_show_mod = """
Mod Ports Card Type                              Model              Serial No.
--- ----- -------------------------------------- ------------------ -----------
  1   52  Sup 7-E, 48 GE (SFP+), 4 XGMII Fabric WS-C4500X-32       JAE240213DA
  2   52  Sup 7-E, 48 GE (SFP+), 4 XGMII Fabric WS-C4500X-32       JAE171504NJ

Mod MAC addresses                       Hw    Fw           Sw           Status
--- ---------------------------------- ------ ------------ ------------ -------
  1 0062.ec9d.7800 to 0062.ec9d.7833   1.1   15.1(1r)SG8  03.11.03.E   Ok
  2 0062.ec9d.6000 to 0062.ec9d.6033   1.1   15.1(1r)SG8  03.11.03.E   Ok

Mod  Sub-Module                  Model              Serial       Hw     Status
---- --------------------------- ------------------ ----------- ------- -------
  1 Centralized Forwarding Card WS-C4500X-32       JAE240213DA  1.1    Ok
  2 Centralized Forwarding Card WS-C4500X-32       JAE171504NJ  1.1    Ok
"""

print("=" * 80)
print("VSS Stack Detection Integration Test")
print("=" * 80)

# Test 1: Device with no show switch support (VSS fallback)
print("\nTest 1: VSS device (show switch not supported)")
print("-" * 80)

collector = StackCollector()
connection = MockConnection(
    show_switch_output="% Invalid input detected at '^' marker.",
    show_mod_output=kgw_show_mod
)

members = collector.collect_stack_members(connection, "IOS-XE")

if members:
    print(f"✓ Found {len(members)} VSS members:")
    for member in members:
        print(f"  - Switch {member.switch_number}: {member.role}, {member.hardware_model}, {member.serial_number}")
    
    # Validate
    assert len(members) == 2, f"Expected 2 members, got {len(members)}"
    assert members[0].switch_number == 1, "Switch 1 number incorrect"
    assert members[0].hardware_model == "WS-C4500X-32", f"Switch 1 model incorrect: {members[0].hardware_model}"
    assert members[0].serial_number == "JAE240213DA", f"Switch 1 serial incorrect: {members[0].serial_number}"
    assert members[0].role == "Active", f"Switch 1 role incorrect: {members[0].role}"
    
    assert members[1].switch_number == 2, "Switch 2 number incorrect"
    assert members[1].hardware_model == "WS-C4500X-32", f"Switch 2 model incorrect: {members[1].hardware_model}"
    assert members[1].serial_number == "JAE171504NJ", f"Switch 2 serial incorrect: {members[1].serial_number}"
    assert members[1].role == "Standby", f"Switch 2 role incorrect: {members[1].role}"
    
    print("\n✓ All validations passed!")
else:
    print("✗ FAILED: No VSS members found")
    sys.exit(1)

# Test 2: Device with no stack (standalone switch)
print("\n\nTest 2: Standalone switch (no stack)")
print("-" * 80)

connection = MockConnection(
    show_switch_output="% Invalid input detected at '^' marker.",
    show_mod_output="Mod Ports Card Type                              Model              Serial No.\n--- ----- -------------------------------------- ------------------ -----------\n  1   48  48 port 10/100/1000 mb RJ45              WS-X4748-RJ45-V    JAE123456AB"
)

members = collector.collect_stack_members(connection, "IOS-XE")

if not members:
    print("✓ Correctly identified as non-stack (single module)")
else:
    print(f"✗ FAILED: Found {len(members)} members, expected 0 for standalone switch")
    sys.exit(1)

# Test 3: Traditional stack (show switch works)
print("\n\nTest 3: Traditional StackWise stack")
print("-" * 80)

show_switch_output = """
Switch/Stack Mac Address : 0123.4567.89ab - Local Mac Address
Mac persistency wait time: Indefinite
                                             H/W   Current
Switch#   Role    Mac Address     Priority Version  State 
---------------------------------------------------------------------------
*1       Master   0123.4567.89ab     15     V01     Ready               
 2       Member   0123.4567.89cd     1      V01     Ready
"""

connection = MockConnection(
    show_switch_output=show_switch_output,
    show_mod_output=kgw_show_mod
)

members = collector.collect_stack_members(connection, "IOS-XE")

if members:
    print(f"✓ Found {len(members)} StackWise members:")
    for member in members:
        print(f"  - Switch {member.switch_number}: {member.role}, MAC {member.mac_address}")
    
    assert len(members) == 2, f"Expected 2 members, got {len(members)}"
    print("\n✓ Traditional stack detection works!")
else:
    print("✗ FAILED: No stack members found")
    sys.exit(1)

print("\n" + "=" * 80)
print("ALL TESTS PASSED!")
print("=" * 80)
print("\nVSS detection is working correctly:")
print("  ✓ VSS stacks detected via 'show mod' fallback")
print("  ✓ Standalone switches correctly identified")
print("  ✓ Traditional StackWise stacks still work")
print("  ✓ Serial numbers and models extracted correctly")
