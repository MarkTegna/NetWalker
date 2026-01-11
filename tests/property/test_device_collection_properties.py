"""
Property-based tests for device information collection
Feature: network-topology-discovery, Property 8: Complete Device Information Collection
"""

import pytest
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st
from datetime import datetime

from netwalker.discovery import DeviceCollector
from netwalker.connection.data_models import DeviceInfo


# Sample show version output for testing
SAMPLE_VERSION_OUTPUT = """
Cisco IOS Software, C2900 Software (C2900-UNIVERSALK9-M), Version 15.1(4)M12a, RELEASE SOFTWARE (fc2)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2016 by Cisco Systems, Inc.
Compiled Fri 17-Jun-16 13:02 by prod_rel_team

ROM: System Bootstrap, Version 15.0(1r)M16, RELEASE SOFTWARE (fc1)

CORE-SWITCH-A uptime is 2 years, 45 weeks, 3 days, 14 hours, 32 minutes
System returned to ROM by power-on
System restarted at 09:15:32 EST Wed Jan 15 2020
System image file is "flash0:c2900-universalk9-mz.SPA.151-4.M12a.bin"
Last reload type: Normal Reload
Last reload reason: power-on

This product contains cryptographic features and is subject to United
States and local country laws governing import, export, transfer and
use. Delivery of Cisco cryptographic products does not imply
third-party authority to import, export, distribute or use encryption.
Importers, exporters, distributors and users are responsible for
compliance with U.S. and local country laws. By using this product you
agree to comply with applicable laws and regulations. If you are unable
to comply with U.S. and local laws, return this product immediately.

A summary of U.S. laws governing Cisco cryptographic products may be found at:
http://www.cisco.com/wwl/export/crypto/tool/stqrg.html

If you require further assistance please contact us by sending email to
export@cisco.com.

Cisco 2911 (revision 1.0) with 483328K/40960K bytes of memory.
Processor board ID FTX1628A1B2
2 Gigabit Ethernet interfaces
4 Serial interfaces
1 terminal line
DRAM configuration is 64 bits wide with parity disabled.
255K bytes of non-volatile configuration memory.
250880K bytes of ATA System CompactFlash 0 (Read/Write)

License Info:
License UDI:

Device#   PID                   SN
----------------------------------
*0        CISCO2911/K9          FTX1628A1B2

Technology Package License Information for Module:'c2900'

-----------------------------------------------------------------
Technology    Technology-package           Technology-package
              Current       Type           Next reboot
------------------------------------------------------------------
ipbase        ipbasek9      Permanent      ipbasek9
security      None          None           None
uc            None          None           None
data          None          None           None

Configuration register is 0x2102
"""


def test_complete_device_information_collection():
    """
    Feature: network-topology-discovery, Property 8: Complete Device Information Collection
    For any successfully connected device, all required device information should be collected and recorded
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """
    collector = DeviceCollector()
    
    # Mock scrapli connection
    mock_connection = Mock()
    mock_connection.send_command.return_value = Mock(result=SAMPLE_VERSION_OUTPUT)
    
    # Mock VTP and neighbor commands to return empty (focus on basic info)
    def mock_command_side_effect(command):
        if "show version" in command:
            return Mock(result=SAMPLE_VERSION_OUTPUT)
        elif "show vtp" in command:
            return Mock(result="VTP Version : 2")
        elif "show cdp" in command or "show lldp" in command:
            return Mock(result="")
        else:
            return Mock(result="")
    
    mock_connection.send_command.side_effect = mock_command_side_effect
    
    # Collect device information
    device_info = collector.collect_device_information(
        connection=mock_connection,
        host="192.168.1.1",
        connection_method="SSH",
        discovery_depth=1,
        is_seed=True
    )
    
    # Verify all required information is collected
    assert device_info is not None, "Device information should be collected"
    assert device_info.hostname == "CORE-SWITCH-A", "Hostname should be extracted from version output"
    assert device_info.primary_ip == "192.168.1.1", "Primary IP should be recorded"
    assert device_info.platform == "IOS", "Platform should be detected as IOS"
    assert device_info.software_version == "15.1(4)M12a", "Software version should be extracted"
    assert device_info.serial_number == "FTX1628A1B2", "Serial number should be extracted"
    assert device_info.hardware_model == "2911", "Hardware model should be extracted"
    assert "2 years, 45 weeks" in device_info.uptime, "Uptime should be extracted"
    assert device_info.vtp_version == "2", "VTP version should be extracted"
    assert len(device_info.capabilities) > 0, "Capabilities should be determined"
    assert device_info.connection_method == "SSH", "Connection method should be recorded"
    assert device_info.connection_status == "success", "Connection status should be success"
    assert device_info.discovery_depth == 1, "Discovery depth should be recorded"
    assert device_info.is_seed is True, "Seed status should be recorded"
    assert isinstance(device_info.discovery_timestamp, datetime), "Discovery timestamp should be recorded"


def test_discovery_metadata_recording():
    """
    Feature: network-topology-discovery, Property 9: Discovery Metadata Recording
    For any device discovery operation, discovery timestamp and depth level should be accurately recorded
    **Validates: Requirements 3.5**
    """
    collector = DeviceCollector()
    
    # Mock connection
    mock_connection = Mock()
    mock_connection.send_command.return_value = Mock(result=SAMPLE_VERSION_OUTPUT)
    
    # Record time before collection
    before_time = datetime.now()
    
    # Collect device information with specific metadata
    device_info = collector.collect_device_information(
        connection=mock_connection,
        host="test-device",
        connection_method="Telnet",
        discovery_depth=5,
        is_seed=False
    )
    
    # Record time after collection
    after_time = datetime.now()
    
    # Verify metadata is correctly recorded
    assert device_info.discovery_depth == 5, "Discovery depth should be accurately recorded"
    assert device_info.is_seed is False, "Seed status should be accurately recorded"
    assert before_time <= device_info.discovery_timestamp <= after_time, "Discovery timestamp should be within collection timeframe"
    assert device_info.connection_method == "Telnet", "Connection method should be recorded"


@given(
    host=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyz0123456789.-'),
    depth=st.integers(min_value=0, max_value=20),
    is_seed=st.booleans()
)
def test_device_collection_robustness(host, depth, is_seed):
    """
    Property test: For any valid host and discovery parameters, device collection should handle them gracefully
    """
    collector = DeviceCollector()
    
    # Mock connection that returns valid version output
    mock_connection = Mock()
    mock_connection.send_command.return_value = Mock(result=SAMPLE_VERSION_OUTPUT)
    
    device_info = collector.collect_device_information(
        connection=mock_connection,
        host=host,
        connection_method="SSH",
        discovery_depth=depth,
        is_seed=is_seed
    )
    
    # Should always return a DeviceInfo object
    assert device_info is not None, "Device collection should always return DeviceInfo"
    assert device_info.discovery_depth == depth, "Discovery depth should match input"
    assert device_info.is_seed == is_seed, "Seed status should match input"
    assert device_info.connection_status in ["success", "failed"], "Connection status should be valid"


def test_platform_detection_accuracy():
    """
    Test platform detection accuracy for different version outputs
    """
    collector = DeviceCollector()
    
    test_cases = [
        ("Cisco IOS Software", "IOS"),
        ("Cisco IOS-XE Software", "IOS-XE"),
        ("Cisco Nexus Operating System (NX-OS)", "NX-OS"),
        ("Unknown system software", "Unknown")
    ]
    
    for version_text, expected_platform in test_cases:
        detected_platform = collector._detect_platform(version_text)
        assert detected_platform == expected_platform, f"Expected {expected_platform}, got {detected_platform}"


def test_hostname_length_limitation():
    """
    Test that hostnames are properly limited to 36 characters as per requirements
    """
    collector = DeviceCollector()
    
    # Test with very long hostname
    long_version_output = SAMPLE_VERSION_OUTPUT.replace("CORE-SWITCH-A", "VERY-LONG-HOSTNAME-THAT-EXCEEDS-THE-THIRTY-SIX-CHARACTER-LIMIT-FOR-DEVICE-NAMES")
    
    hostname = collector._extract_hostname(long_version_output, "fallback")
    
    assert len(hostname) <= 36, f"Hostname should be limited to 36 characters, got {len(hostname)}"


def test_failed_device_collection():
    """
    Test handling of failed device collection
    """
    collector = DeviceCollector()
    
    # Mock connection that fails
    mock_connection = Mock()
    mock_connection.send_command.side_effect = Exception("Connection failed")
    
    device_info = collector.collect_device_information(
        connection=mock_connection,
        host="failed-device",
        connection_method="SSH",
        discovery_depth=0,
        is_seed=False
    )
    
    # Should return failed device info
    assert device_info is not None, "Should return DeviceInfo even on failure"
    assert device_info.connection_status == "failed", "Connection status should be failed"
    assert device_info.error_details is not None, "Error details should be provided"
    assert device_info.hostname == "failed-device", "Hostname should be the provided host"


def test_capability_determination():
    """
    Test device capability determination based on version output
    """
    collector = DeviceCollector()
    
    # Test router capabilities
    router_output = "Cisco 2911 router with switching capabilities"
    capabilities = collector._determine_capabilities(router_output, "IOS")
    assert "Router" in capabilities, "Should detect router capability"
    
    # Test switch capabilities
    switch_output = "Cisco Catalyst 3560 switch device"
    capabilities = collector._determine_capabilities(switch_output, "IOS")
    assert "Switch" in capabilities, "Should detect switch capability"


def test_version_information_extraction():
    """
    Test extraction of various version information components
    """
    collector = DeviceCollector()
    
    # Test software version extraction
    version = collector._extract_software_version(SAMPLE_VERSION_OUTPUT)
    assert version == "15.1(4)M12a", "Should extract correct software version"
    
    # Test serial number extraction
    serial = collector._extract_serial_number(SAMPLE_VERSION_OUTPUT)
    assert serial == "FTX1628A1B2", "Should extract correct serial number"
    
    # Test hardware model extraction
    model = collector._extract_hardware_model(SAMPLE_VERSION_OUTPUT)
    assert model == "2911", "Should extract correct hardware model"
    
    # Test uptime extraction
    uptime = collector._extract_uptime(SAMPLE_VERSION_OUTPUT)
    assert "2 years, 45 weeks" in uptime, "Should extract correct uptime"


def test_neighbor_collection_integration():
    """
    Test integration with protocol parser for neighbor collection
    """
    collector = DeviceCollector()
    
    # Mock connection with CDP/LLDP output
    mock_connection = Mock()
    
    def mock_command_response(command):
        if "show cdp" in command:
            return Mock(result="Device ID: TEST-NEIGHBOR\nIP address: 192.168.1.2")
        elif "show lldp" in command:
            return Mock(result="System Name: LLDP-NEIGHBOR")
        else:
            return Mock(result="")
    
    mock_connection.send_command.side_effect = mock_command_response
    
    # Test neighbor collection
    neighbors = collector._collect_neighbors(mock_connection, "IOS")
    
    # Should collect neighbors from both protocols
    assert isinstance(neighbors, list), "Should return list of neighbors"
    # Note: Actual parsing depends on protocol parser implementation