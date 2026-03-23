"""
Test Polycom platform string parsing for both CDP and LLDP formats
"""
import sys
sys.path.insert(0, '.')

from netwalker.discovery.protocol_parser import ProtocolParser

# Create parser instance
parser = ProtocolParser()

# Test platform strings
test_strings = [
    # CDP format (from your example)
    ("Polycom VVX 250|Updater:6.4.6.2681|App:6.4.6.2681", "CDP with Updater and App"),
    ("Polycom VVX 250|App:6.4.6.2656", "CDP with App only"),
    
    # LLDP format (from database)
    ("Polycom;VVX-VVX_401;3111-48400-001,1;SIP/6.4.7.4560/05-Dec-24 00:58;UP/6.4.7.3828/05-Dec-24 01:22;", "LLDP full format"),
    ("Polycom;VVX-VVX_411;3111-48450-001,1;SIP/6.4.7.4560/05-Dec-24 00:58;UP/6.4.7.3828/05-Dec-24 01:22;", "LLDP full format"),
    
    # Simple format
    ("Polycom VVX 150", "Simple format"),
    ("Polycom VVX 250", "Simple format"),
]

print("Testing Polycom Platform String Parsing (CDP and LLDP)")
print("=" * 80)

for i, (platform_str, description) in enumerate(test_strings, 1):
    print(f"\nTest {i}: {description}")
    print(f"Input: {platform_str}")
    print("-" * 80)
    
    result = parser.parse_polycom_platform_string(platform_str)
    
    print(f"  Platform:          {result['platform']}")
    print(f"  Model:             {result['model']}")
    print(f"  Part Number:       {result.get('part_number', 'N/A')}")
    print(f"  Updater Firmware:  {result.get('updater_firmware', 'N/A')}")
    print(f"  App Firmware:      {result.get('app_firmware', 'N/A')}")
    print(f"  SIP Firmware:      {result.get('sip_firmware', 'N/A')}")
    print(f"  UP Firmware:       {result.get('up_firmware', 'N/A')}")

print("\n" + "=" * 80)
print("Testing complete!")
