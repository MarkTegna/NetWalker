"""
Quick verification test for prefix normalizer implementation.

This test verifies that Task 9.1 (Create normalizer.py) is complete and functional.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from netwalker.ipv4_prefix.normalizer import PrefixNormalizer, PrefixDeduplicator
from netwalker.ipv4_prefix.data_models import ParsedPrefix, CollectionException
from datetime import datetime


def test_mask_to_cidr_conversion():
    """Test conversion from mask format to CIDR notation."""
    normalizer = PrefixNormalizer()
    
    # Test cases: (ip, mask, expected_cidr)
    test_cases = [
        ("192.168.1.0", "255.255.255.0", "192.168.1.0/24"),
        ("10.0.0.0", "255.0.0.0", "10.0.0.0/8"),
        ("172.16.0.0", "255.255.0.0", "172.16.0.0/16"),
        ("192.168.1.1", "255.255.255.255", "192.168.1.1/32"),
        ("0.0.0.0", "0.0.0.0", "0.0.0.0/0"),
    ]
    
    print("Testing mask to CIDR conversion...")
    for ip, mask, expected in test_cases:
        result = normalizer.mask_to_cidr(ip, mask)
        assert result == expected, f"Expected {expected}, got {result}"
        print(f"  ✓ {ip} {mask} -> {result}")
    
    print("✓ All mask to CIDR conversions passed")


def test_cidr_validation():
    """Test CIDR format validation."""
    normalizer = PrefixNormalizer()
    
    # Valid CIDR formats
    valid_cases = [
        "192.168.1.0/24",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "10.0.0.1/32",
        "0.0.0.0/0",
    ]
    
    print("\nTesting CIDR validation (valid cases)...")
    for cidr in valid_cases:
        result = normalizer.validate_cidr(cidr)
        assert result is not None, f"Expected valid CIDR, got None for {cidr}"
        print(f"  ✓ {cidr} -> {result}")
    
    # Invalid CIDR formats
    invalid_cases = [
        "999.999.999.999/32",
        "10.0.0.0/33",
        "192.168.1.0/",
        "not_an_ip/24",
    ]
    
    print("\nTesting CIDR validation (invalid cases)...")
    for cidr in invalid_cases:
        result = normalizer.validate_cidr(cidr)
        assert result is None, f"Expected None for invalid CIDR {cidr}, got {result}"
        print(f"  ✓ {cidr} -> None (correctly rejected)")
    
    print("✓ All CIDR validations passed")


def test_normalize_function():
    """Test the main normalize function."""
    normalizer = PrefixNormalizer()
    
    # Test cases: (input, expected_output)
    test_cases = [
        # CIDR format (should validate and preserve)
        ("192.168.1.0/24", "192.168.1.0/24"),
        ("10.0.0.0/8", "10.0.0.0/8"),
        
        # Mask format (should convert to CIDR)
        ("192.168.1.0 255.255.255.0", "192.168.1.0/24"),
        ("10.0.0.0 255.0.0.0", "10.0.0.0/8"),
        
        # Host routes
        ("10.0.0.1/32", "10.0.0.1/32"),
        ("192.168.1.1 255.255.255.255", "192.168.1.1/32"),
        
        # Default route
        ("0.0.0.0/0", "0.0.0.0/0"),
    ]
    
    print("\nTesting normalize function...")
    for input_str, expected in test_cases:
        result = normalizer.normalize(input_str)
        assert result == expected, f"Expected {expected}, got {result} for input {input_str}"
        print(f"  ✓ {input_str} -> {result}")
    
    # Test invalid formats (should return None)
    invalid_cases = [
        "999.999.999.999/32",
        "10.0.0.0/33",
        "",
        "   ",
    ]
    
    print("\nTesting normalize function (invalid cases)...")
    for input_str in invalid_cases:
        result = normalizer.normalize(input_str)
        assert result is None, f"Expected None for invalid input {input_str}, got {result}"
        print(f"  ✓ '{input_str}' -> None (correctly rejected)")
    
    print("✓ All normalize function tests passed")


def test_normalize_parsed_prefix():
    """Test normalization of ParsedPrefix objects."""
    normalizer = PrefixNormalizer()
    exceptions = []
    
    # Create a valid ParsedPrefix
    parsed = ParsedPrefix(
        device="test-device",
        platform="ios",
        vrf="global",
        prefix_str="192.168.1.0 255.255.255.0",
        source="rib",
        protocol="C",
        raw_line="C    192.168.1.0 255.255.255.0 is directly connected, GigabitEthernet0/0",
        is_ambiguous=False,
        timestamp=datetime.now(),
        vlan=None,
        interface="GigabitEthernet0/0"
    )
    
    print("\nTesting normalize_parsed_prefix (valid case)...")
    result = normalizer.normalize_parsed_prefix(parsed, exceptions)
    assert result is not None, "Expected NormalizedPrefix, got None"
    assert result.prefix == "192.168.1.0/24", f"Expected 192.168.1.0/24, got {result.prefix}"
    assert result.device == "test-device"
    assert result.vrf == "global"
    assert len(exceptions) == 0, f"Expected no exceptions, got {len(exceptions)}"
    print(f"  ✓ Normalized to {result.prefix}")
    
    # Create an invalid ParsedPrefix
    invalid_parsed = ParsedPrefix(
        device="test-device",
        platform="ios",
        vrf="global",
        prefix_str="999.999.999.999/32",
        source="rib",
        protocol="C",
        raw_line="C    999.999.999.999/32 is directly connected, GigabitEthernet0/0",
        is_ambiguous=False,
        timestamp=datetime.now(),
        vlan=None,
        interface="GigabitEthernet0/0"
    )
    
    print("\nTesting normalize_parsed_prefix (invalid case)...")
    exceptions.clear()
    result = normalizer.normalize_parsed_prefix(invalid_parsed, exceptions)
    assert result is None, f"Expected None for invalid prefix, got {result}"
    assert len(exceptions) == 1, f"Expected 1 exception, got {len(exceptions)}"
    assert exceptions[0].error_type == "normalization_failed"
    print(f"  ✓ Correctly rejected invalid prefix and added exception")
    
    print("✓ All normalize_parsed_prefix tests passed")


def test_deduplication():
    """Test prefix deduplication."""
    from netwalker.ipv4_prefix.data_models import NormalizedPrefix
    
    deduplicator = PrefixDeduplicator()
    
    # Create test prefixes with duplicates
    prefixes = [
        NormalizedPrefix(
            device="device1", platform="ios", vrf="global", prefix="192.168.1.0/24",
            source="rib", protocol="C", raw_line="", timestamp=datetime.now(),
            vlan=None, interface="Gi0/0"
        ),
        NormalizedPrefix(
            device="device1", platform="ios", vrf="global", prefix="192.168.1.0/24",
            source="rib", protocol="C", raw_line="", timestamp=datetime.now(),
            vlan=None, interface="Gi0/0"
        ),  # Duplicate
        NormalizedPrefix(
            device="device1", platform="ios", vrf="global", prefix="10.0.0.0/8",
            source="rib", protocol="B", raw_line="", timestamp=datetime.now(),
            vlan=None, interface=None
        ),
        NormalizedPrefix(
            device="device2", platform="ios", vrf="global", prefix="192.168.1.0/24",
            source="rib", protocol="C", raw_line="", timestamp=datetime.now(),
            vlan=None, interface="Gi0/1"
        ),  # Same prefix, different device
    ]
    
    print("\nTesting deduplication by device...")
    result = deduplicator.deduplicate_by_device(prefixes)
    assert len(result) == 3, f"Expected 3 unique prefixes, got {len(result)}"
    print(f"  ✓ Removed {len(prefixes) - len(result)} duplicates")
    
    print("\nTesting deduplication by VRF...")
    dedup_result = deduplicator.deduplicate_by_vrf(result)
    assert len(dedup_result) == 2, f"Expected 2 unique (vrf, prefix) pairs, got {len(dedup_result)}"
    
    # Find the 192.168.1.0/24 entry
    entry = next(d for d in dedup_result if d.prefix == "192.168.1.0/24")
    assert entry.device_count == 2, f"Expected 2 devices, got {entry.device_count}"
    assert set(entry.device_list) == {"device1", "device2"}
    print(f"  ✓ Created {len(dedup_result)} unique (vrf, prefix) pairs")
    print(f"  ✓ 192.168.1.0/24 appears on {entry.device_count} devices: {entry.device_list}")
    
    print("✓ All deduplication tests passed")


def main():
    """Run all verification tests."""
    print("=" * 70)
    print("IPv4 Prefix Normalizer Verification Tests")
    print("=" * 70)
    
    try:
        test_mask_to_cidr_conversion()
        test_cidr_validation()
        test_normalize_function()
        test_normalize_parsed_prefix()
        test_deduplication()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED - Task 9.1 is complete and functional!")
        print("=" * 70)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
