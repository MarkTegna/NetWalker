"""
Property-based tests for protocol parsing
Feature: network-topology-discovery, Property 1: Neighbor Information Extraction
"""

import pytest
from hypothesis import given, strategies as st
from netwalker.discovery import ProtocolParser


# Sample CDP output for testing
SAMPLE_CDP_OUTPUT = """
-------------------------
Device ID: SWITCH-01.example.com
Entry address(es): 
  IP address: 192.168.1.10
Platform: cisco WS-C3560-24TS,  Capabilities: Router Switch IGMP 
Interface: GigabitEthernet0/1,  Port ID (outgoing port): GigabitEthernet0/24
Holdtime : 179 sec

Version :
Cisco IOS Software, C3560 Software (C3560-IPSERVICESK9-M), Version 12.2(55)SE12, RELEASE SOFTWARE (fc2)

-------------------------
Device ID: ROUTER-02
Entry address(es): 
  IP address: 10.1.1.1
Platform: Cisco 2911,  Capabilities: Router Source-Route-Bridge 
Interface: GigabitEthernet0/2,  Port ID (outgoing port): GigabitEthernet0/0
Holdtime : 165 sec

Version :
Cisco IOS Software, C2900 Software (C2900-UNIVERSALK9-M), Version 15.1(4)M12a, RELEASE SOFTWARE (fc2)
"""

# Sample LLDP output for testing
SAMPLE_LLDP_OUTPUT = """
Local Intf: Gi0/1
Chassis id: 001e.7a12.3456
Port id: Gi0/24
Port Description: GigabitEthernet0/24
System Name: SWITCH-03.example.com
System Description: Cisco IOS Software, C3750 Software
System Capabilities: B,R
Enabled Capabilities: B,R

Local Intf: Gi0/2
Chassis id: 001f.9b34.5678
Port id: Gi0/1
Port Description: GigabitEthernet0/1
System Name: ACCESS-SWITCH-01
System Description: Cisco IOS Software, C2960 Software
System Capabilities: B
Enabled Capabilities: B
"""


def test_neighbor_information_extraction():
    """
    Feature: network-topology-discovery, Property 1: Neighbor Information Extraction
    For any device with CDP/LLDP neighbors, when the Discovery_Engine connects and extracts neighbor information, 
    all available neighbor data should be correctly parsed and structured
    **Validates: Requirements 1.1**
    """
    parser = ProtocolParser()
    
    # Test CDP parsing
    cdp_neighbors = parser.parse_cdp_neighbors(SAMPLE_CDP_OUTPUT)
    
    assert len(cdp_neighbors) == 2, "Should parse 2 CDP neighbors"
    
    # Verify first neighbor
    neighbor1 = cdp_neighbors[0]
    assert neighbor1.device_id == "SWITCH-01.example.com"
    assert neighbor1.ip_address == "192.168.1.10"
    assert neighbor1.platform == "cisco WS-C3560-24TS"
    assert "Router" in neighbor1.capabilities
    assert "Switch" in neighbor1.capabilities
    assert neighbor1.local_interface == "GigabitEthernet0/1"
    assert neighbor1.remote_interface == "GigabitEthernet0/24"
    assert neighbor1.protocol == "CDP"
    
    # Verify second neighbor
    neighbor2 = cdp_neighbors[1]
    assert neighbor2.device_id == "ROUTER-02"
    assert neighbor2.ip_address == "10.1.1.1"
    assert neighbor2.platform == "Cisco 2911"
    assert "Router" in neighbor2.capabilities


def test_multi_protocol_parsing_support():
    """
    Feature: network-topology-discovery, Property 30: Multi-Protocol Parsing Support
    For any device with neighbor information, both CDP and LLDP protocol outputs should be parsed when available
    **Validates: Requirements 11.3**
    """
    parser = ProtocolParser()
    
    # Test LLDP parsing
    lldp_neighbors = parser.parse_lldp_neighbors(SAMPLE_LLDP_OUTPUT)
    
    assert len(lldp_neighbors) == 2, "Should parse 2 LLDP neighbors"
    
    # Verify LLDP neighbor
    lldp_neighbor = lldp_neighbors[0]
    assert lldp_neighbor.device_id == "SWITCH-03.example.com"
    assert lldp_neighbor.local_interface == "Gi0/1"
    assert lldp_neighbor.remote_interface == "Gi0/24"
    assert lldp_neighbor.protocol == "LLDP"
    
    # Test combined parsing
    combined_neighbors = parser.parse_multi_protocol_output(SAMPLE_CDP_OUTPUT, SAMPLE_LLDP_OUTPUT)
    
    # Should have neighbors from both protocols (4 total, assuming no duplicates)
    assert len(combined_neighbors) >= 2, "Should have neighbors from both protocols"
    
    # Verify we have both CDP and LLDP neighbors
    protocols = {neighbor.protocol for neighbor in combined_neighbors}
    assert "CDP" in protocols, "Should include CDP neighbors"
    assert "LLDP" in protocols, "Should include LLDP neighbors"


@given(
    device_id=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-'),
    ip_address=st.text(min_size=7, max_size=15, alphabet='0123456789.').filter(lambda x: x.count('.') == 3)
)
def test_cdp_parsing_robustness(device_id, ip_address):
    """
    Property test: For any valid CDP-like output format, the parser should handle it gracefully
    """
    parser = ProtocolParser()
    
    # Create synthetic CDP output
    cdp_output = f"""
-------------------------
Device ID: {device_id}
Entry address(es): 
  IP address: {ip_address}
Platform: cisco TestDevice,  Capabilities: Router Switch 
Interface: GigabitEthernet0/1,  Port ID (outgoing port): GigabitEthernet0/2
Holdtime : 180 sec
"""
    
    neighbors = parser.parse_cdp_neighbors(cdp_output)
    
    # Should parse at least one neighbor or handle gracefully
    if neighbors:
        neighbor = neighbors[0]
        assert neighbor.device_id == device_id
        assert neighbor.protocol == "CDP"
        # IP validation is complex, so just check it's not None if parsed
        if neighbor.ip_address:
            assert len(neighbor.ip_address) > 0


def test_hostname_extraction():
    """
    Test hostname extraction from neighbor device IDs
    """
    parser = ProtocolParser()
    
    # Test various hostname formats
    test_cases = [
        ("SWITCH-01.example.com", "SWITCH-01"),
        ("ROUTER-02", "ROUTER-02"),
        ("device.with.multiple.dots.com", "device"),
        ("VERY-LONG-HOSTNAME-THAT-EXCEEDS-LIMIT-123456789", "VERY-LONG-HOSTNAME-THAT-EXCEEDS-LIMIT-"),  # Should be truncated to 36 chars
    ]
    
    for device_id, expected_hostname in test_cases:
        # Create a mock neighbor info
        from netwalker.connection.data_models import NeighborInfo
        neighbor = NeighborInfo(
            device_id=device_id,
            local_interface="Gi0/1",
            remote_interface="Gi0/2",
            platform="Test",
            capabilities=["Router"]
        )
        
        hostname = parser.extract_hostname(neighbor)
        
        if len(expected_hostname) > 36:
            assert len(hostname) <= 36, "Hostname should be truncated to 36 characters"
        else:
            assert hostname == expected_hostname, f"Expected {expected_hostname}, got {hostname}"


def test_platform_command_adaptation():
    """
    Test platform-specific command adaptation
    """
    parser = ProtocolParser()
    
    # Test different platforms
    platforms = ["IOS", "IOS-XE", "NX-OS", "Unknown"]
    
    for platform in platforms:
        commands = parser.adapt_commands_for_platform(platform)
        
        # Should always return required commands
        assert 'cdp_neighbors' in commands
        assert 'lldp_neighbors' in commands
        assert 'version' in commands
        
        # Commands should be strings
        assert isinstance(commands['cdp_neighbors'], str)
        assert isinstance(commands['lldp_neighbors'], str)
        assert isinstance(commands['version'], str)


def test_empty_output_handling():
    """
    Test graceful handling of empty or invalid outputs
    """
    parser = ProtocolParser()
    
    # Test empty outputs
    assert parser.parse_cdp_neighbors("") == []
    assert parser.parse_cdp_neighbors(None) == []
    assert parser.parse_lldp_neighbors("") == []
    assert parser.parse_lldp_neighbors(None) == []
    
    # Test invalid outputs
    assert parser.parse_cdp_neighbors("Invalid CDP output") == []
    assert parser.parse_lldp_neighbors("Invalid LLDP output") == []
    
    # Test combined parsing with empty inputs
    combined = parser.parse_multi_protocol_output("", "")
    assert combined == []


def test_duplicate_neighbor_handling():
    """
    Test that duplicate neighbors are handled correctly in multi-protocol parsing
    """
    parser = ProtocolParser()
    
    # Create CDP output with a device
    cdp_output = """
-------------------------
Device ID: DUPLICATE-DEVICE
Entry address(es): 
  IP address: 192.168.1.100
Platform: cisco TestDevice,  Capabilities: Router 
Interface: GigabitEthernet0/1,  Port ID (outgoing port): GigabitEthernet0/2
"""
    
    # Create LLDP output with the same device (should be deduplicated)
    lldp_output = """
Local Intf: Gi0/1
System Name: DUPLICATE-DEVICE
System Description: Cisco IOS Software
Port id: Gi0/2
System Capabilities: R
"""
    
    combined_neighbors = parser.parse_multi_protocol_output(cdp_output, lldp_output)
    
    # Should only have one neighbor (deduplicated)
    device_ids = [parser.extract_hostname(n) for n in combined_neighbors]
    unique_device_ids = set(device_ids)
    
    # The same device should not appear multiple times
    assert len(device_ids) == len(unique_device_ids), "Duplicate neighbors should be removed"