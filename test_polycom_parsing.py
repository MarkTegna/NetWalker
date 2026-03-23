"""
Test Polycom platform string parsing
"""
import sys
sys.path.insert(0, '.')

from netwalker.discovery.protocol_parser import ProtocolParser

# Create parser instance
parser = ProtocolParser()

# Test platform strings from the database
test_strings = [
    "Polycom;VVX-VVX_401;3111-48400-001,1;SIP/6.4.7.4560/05-Dec-24 00:58;UP/6.4.7.3828/05-Dec-24 01:22;",
    "Polycom;VVX-VVX_411;3111-48450-001,1;SIP/6.4.7.4560/05-Dec-24 00:58;UP/6.4.7.3828/05-Dec-24 01:22;",
    "Polycom;VVX-VVX_450;3111-48450-025,1;SIP/6.4.7.4560/05-Dec-24 00:58;UP/6.4.7.3828/05-Dec-24 01:22;",
    "Polycom;VVX-VVX_350;3111-48350-025,1;SIP/6.4.7.4560/05-Dec-24 00:58;UP/6.4.7.3828/05-Dec-24 01:22;",
    "Polycom VVX 150",  # Simple format (from CDP without detailed info)
    "Polycom VVX 250",  # Simple format
]

print("Testing Polycom Platform String Parsing")
print("=" * 80)

for i, platform_str in enumerate(test_strings, 1):
    print(f"\nTest {i}: {platform_str}")
    print("-" * 80)
    
    result = parser.parse_polycom_platform_string(platform_str)
    
    print(f"  Platform:      {result['platform']}")
    print(f"  Model:         {result['model']}")
    print(f"  Part Number:   {result['part_number']}")
    print(f"  SIP Firmware:  {result['sip_firmware']}")
    print(f"  UP Firmware:   {result['up_firmware']}")

print("\n" + "=" * 80)
print("Testing complete!")
