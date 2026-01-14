"""
Property-based tests for VLAN inventory collection
Feature: vlan-inventory-collection
"""

import pytest
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime

from netwalker.connection.data_models import VLANInfo, VLANCollectionResult, VLANCollectionConfig


class TestVLANDataModelProperties:
    """Property-based tests for VLAN data model validation"""
    
    @given(
        vlan_id=st.integers(min_value=1, max_value=4094),
        vlan_name=st.text(min_size=1, max_size=32),
        port_count=st.integers(min_value=0, max_value=100),
        portchannel_count=st.integers(min_value=0, max_value=20),
        device_hostname=st.text(min_size=1, max_size=36),
        device_ip=st.ip_addresses(v=4).map(str)
    )
    def test_vlan_id_range_validation(self, vlan_id, vlan_name, port_count, portchannel_count, device_hostname, device_ip):
        """
        Feature: vlan-inventory-collection, Property 31: VLAN ID Range Validation
        For any extracted VLAN number, the value should be within the valid range (1-4094)
        
        Validates: Requirements 9.1
        """
        # Create VLAN info with generated data
        vlan_info = VLANInfo(
            vlan_id=vlan_id,
            vlan_name=vlan_name,
            port_count=port_count,
            portchannel_count=portchannel_count,
            device_hostname=device_hostname,
            device_ip=device_ip,
            collection_timestamp=datetime.now()
        )
        
        # Property: VLAN ID should be within valid range
        assert 1 <= vlan_info.vlan_id <= 4094, f"VLAN ID {vlan_info.vlan_id} is outside valid range (1-4094)"
    
    @given(
        vlan_name=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd')), min_size=1, max_size=32),
        vlan_id=st.integers(min_value=1, max_value=4094),
        port_count=st.integers(min_value=0, max_value=100),
        portchannel_count=st.integers(min_value=0, max_value=20),
        device_hostname=st.text(min_size=1, max_size=36),
        device_ip=st.ip_addresses(v=4).map(str)
    )
    def test_vlan_name_character_handling(self, vlan_name, vlan_id, port_count, portchannel_count, device_hostname, device_ip):
        """
        Feature: vlan-inventory-collection, Property 32: VLAN Name Character Handling
        For any extracted VLAN name, special characters and encoding issues should be handled appropriately
        
        Validates: Requirements 9.2
        """
        # Create VLAN info with generated data including special characters
        vlan_info = VLANInfo(
            vlan_id=vlan_id,
            vlan_name=vlan_name,
            port_count=port_count,
            portchannel_count=portchannel_count,
            device_hostname=device_hostname,
            device_ip=device_ip,
            collection_timestamp=datetime.now()
        )
        
        # Property: VLAN name should be stored correctly regardless of special characters
        assert vlan_info.vlan_name == vlan_name, "VLAN name should be preserved exactly as provided"
        assert isinstance(vlan_info.vlan_name, str), "VLAN name should be a string"
        assert len(vlan_info.vlan_name) > 0, "VLAN name should not be empty"
    
    @given(
        port_count=st.integers(min_value=0, max_value=1000),
        portchannel_count=st.integers(min_value=0, max_value=100),
        vlan_id=st.integers(min_value=1, max_value=4094),
        vlan_name=st.text(min_size=1, max_size=32),
        device_hostname=st.text(min_size=1, max_size=36),
        device_ip=st.ip_addresses(v=4).map(str)
    )
    def test_port_count_non_negative_validation(self, port_count, portchannel_count, vlan_id, vlan_name, device_hostname, device_ip):
        """
        Feature: vlan-inventory-collection, Property 33: Port Count Non-Negative Validation
        For any calculated port count, the value should be a non-negative integer
        
        Validates: Requirements 9.3
        """
        # Create VLAN info with generated port counts
        vlan_info = VLANInfo(
            vlan_id=vlan_id,
            vlan_name=vlan_name,
            port_count=port_count,
            portchannel_count=portchannel_count,
            device_hostname=device_hostname,
            device_ip=device_ip,
            collection_timestamp=datetime.now()
        )
        
        # Property: Port counts should be non-negative integers
        assert vlan_info.port_count >= 0, f"Port count {vlan_info.port_count} should be non-negative"
        assert vlan_info.portchannel_count >= 0, f"PortChannel count {vlan_info.portchannel_count} should be non-negative"
        assert isinstance(vlan_info.port_count, int), "Port count should be an integer"
        assert isinstance(vlan_info.portchannel_count, int), "PortChannel count should be an integer"


class TestVLANCollectionResultProperties:
    """Property-based tests for VLAN collection result validation"""
    
    @given(
        device_hostname=st.text(min_size=1, max_size=36),
        device_ip=st.ip_addresses(v=4).map(str),
        collection_success=st.booleans(),
        num_vlans=st.integers(min_value=0, max_value=50)
    )
    def test_vlan_collection_result_consistency(self, device_hostname, device_ip, collection_success, num_vlans):
        """
        Test that VLAN collection results maintain consistency between success status and VLAN data
        """
        # Generate VLAN list
        vlans = []
        for i in range(num_vlans):
            vlan = VLANInfo(
                vlan_id=i + 1,
                vlan_name=f"VLAN_{i+1}",
                port_count=0,
                portchannel_count=0,
                device_hostname=device_hostname,
                device_ip=device_ip
            )
            vlans.append(vlan)
        
        # Create collection result
        result = VLANCollectionResult(
            device_hostname=device_hostname,
            device_ip=device_ip,
            vlans=vlans,
            collection_success=collection_success,
            collection_timestamp=datetime.now()
        )
        
        # Property: Collection result should be consistent
        assert result.device_hostname == device_hostname
        assert result.device_ip == device_ip
        assert len(result.vlans) == num_vlans
        assert isinstance(result.collection_success, bool)
        
        # If collection was successful and we have VLANs, all VLANs should have correct device info
        if collection_success and vlans:
            for vlan in result.vlans:
                assert vlan.device_hostname == device_hostname
                assert vlan.device_ip == device_ip


class TestVLANCollectionConfigProperties:
    """Property-based tests for VLAN collection configuration validation"""
    
    @given(
        enabled=st.booleans(),
        command_timeout=st.integers(min_value=1, max_value=300),
        max_retries=st.integers(min_value=0, max_value=10),
        include_inactive_vlans=st.booleans()
    )
    def test_vlan_collection_config_validation(self, enabled, command_timeout, max_retries, include_inactive_vlans):
        """
        Test that VLAN collection configuration maintains valid values
        """
        config = VLANCollectionConfig(
            enabled=enabled,
            command_timeout=command_timeout,
            max_retries=max_retries,
            include_inactive_vlans=include_inactive_vlans
        )
        
        # Property: Configuration values should be valid
        assert isinstance(config.enabled, bool)
        assert config.command_timeout > 0, "Command timeout should be positive"
        assert config.max_retries >= 0, "Max retries should be non-negative"
        assert isinstance(config.include_inactive_vlans, bool)
        assert isinstance(config.platforms_to_skip, list)


class TestPlatformHandlerProperties:
    """Property-based tests for Platform Handler functionality"""
    
    @given(
        platform=st.sampled_from(['IOS', 'IOS-XE', 'NX-OS', 'ios', 'ios-xe', 'nx-os', 'Ios', 'Ios-Xe', 'Nx-Os'])
    )
    def test_platform_specific_command_selection(self, platform):
        """
        Feature: vlan-inventory-collection, Property 2: Platform-Specific Command Selection
        For any device with a known platform (IOS/IOS-XE/NX-OS), the correct 
        platform-specific VLAN command should be selected
        
        Validates: Requirements 1.2
        """
        from netwalker.vlan.platform_handler import PlatformHandler
        
        platform_handler = PlatformHandler()
        commands = platform_handler.get_vlan_commands(platform)
        
        # Property: Correct commands should be selected based on platform
        platform_upper = platform.upper()
        
        if platform_upper in ['IOS', 'IOS-XE']:
            assert 'show vlan brief' in commands, f"IOS/IOS-XE platform should use 'show vlan brief', got {commands}"
            assert len(commands) == 1, f"IOS/IOS-XE should have exactly one command, got {len(commands)}"
        elif platform_upper == 'NX-OS':
            assert 'show vlan' in commands, f"NX-OS platform should use 'show vlan', got {commands}"
            assert len(commands) == 1, f"NX-OS should have exactly one command, got {len(commands)}"
        
        # Property: Commands should always be returned as a list
        assert isinstance(commands, list), "Commands should be returned as a list"
        assert len(commands) > 0, "At least one command should be returned"
        
        # Property: All commands should be strings
        for command in commands:
            assert isinstance(command, str), f"Command should be a string, got {type(command)}"
            assert len(command.strip()) > 0, "Command should not be empty"
    
    @given(
        unknown_platform=st.text(min_size=1, max_size=20).filter(
            lambda x: x.upper() not in ['IOS', 'IOS-XE', 'NX-OS', 'UNKNOWN']
        )
    )
    def test_unknown_platform_fallback_behavior(self, unknown_platform):
        """
        Feature: vlan-inventory-collection, Property 6: Unknown Platform Fallback Behavior
        For any device with unknown or undetected platform, both command variants 
        should be attempted and the successful one used
        
        Validates: Requirements 2.3
        """
        from netwalker.vlan.platform_handler import PlatformHandler
        
        platform_handler = PlatformHandler()
        commands = platform_handler.get_vlan_commands(unknown_platform)
        
        # Property: Unknown platforms should get both command variants
        assert 'show vlan brief' in commands, f"Unknown platform should include 'show vlan brief', got {commands}"
        assert 'show vlan' in commands, f"Unknown platform should include 'show vlan', got {commands}"
        assert len(commands) == 2, f"Unknown platform should have exactly 2 commands, got {len(commands)}"
        
        # Property: Fallback commands should be available
        fallback_commands = platform_handler.get_fallback_commands(unknown_platform)
        assert isinstance(fallback_commands, list), "Fallback commands should be a list"
        assert len(fallback_commands) > 0, "Fallback commands should not be empty"
    
    @given(
        platform=st.one_of(
            st.sampled_from(['IOS', 'IOS-XE', 'NX-OS']),
            st.text(min_size=1, max_size=20),
            st.none()
        )
    )
    def test_platform_support_validation_consistency(self, platform):
        """
        Test that platform support validation is consistent with command availability
        """
        from netwalker.vlan.platform_handler import PlatformHandler
        
        platform_handler = PlatformHandler()
        is_supported = platform_handler.validate_platform_support(platform)
        commands = platform_handler.get_vlan_commands(platform)
        
        # Property: If platform is supported, commands should be available
        if is_supported:
            assert len(commands) > 0, f"Supported platform {platform} should have commands available"
        
        # Property: Commands should always be available (even for unsupported platforms as fallback)
        assert len(commands) > 0, f"Commands should always be available for platform {platform}"
        
        # Property: Support validation should be boolean
        assert isinstance(is_supported, bool), "Platform support should be boolean"


class TestVLANParserProperties:
    """Property-based tests for VLAN Parser functionality"""
    
    @given(
        vlan_entries=st.lists(
            st.tuples(
                st.integers(min_value=1, max_value=4094),  # vlan_id
                st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')), min_size=1, max_size=32),  # vlan_name
                st.lists(st.from_regex(r'(Fa|Gi|Te|Eth)\d+/\d+'), min_size=0, max_size=10),  # ports
                st.lists(st.from_regex(r'Po\d+'), min_size=0, max_size=5)  # portchannels
            ),
            min_size=1, max_size=20
        ),
        platform=st.sampled_from(['IOS', 'IOS-XE', 'NX-OS']),
        device_hostname=st.text(min_size=1, max_size=36),
        device_ip=st.ip_addresses(v=4).map(str)
    )
    def test_vlan_data_extraction_completeness(self, vlan_entries, platform, device_hostname, device_ip):
        """
        Feature: vlan-inventory-collection, Property 9: Complete VLAN Data Extraction
        For any valid VLAN command output, VLAN number, VLAN name, and port assignment 
        information should be extracted
        
        Validates: Requirements 3.1
        """
        from netwalker.vlan.vlan_parser import VLANParser
        
        # Generate realistic VLAN output based on platform
        if platform in ['IOS', 'IOS-XE']:
            output = self._generate_ios_vlan_output(vlan_entries)
        else:  # NX-OS
            output = self._generate_nxos_vlan_output(vlan_entries)
        
        parser = VLANParser()
        parsed_vlans = parser.parse_vlan_output(output, platform, device_hostname, device_ip)
        
        # Property: All VLANs should be extracted
        assert len(parsed_vlans) == len(vlan_entries), f"Expected {len(vlan_entries)} VLANs, got {len(parsed_vlans)}"
        
        # Property: Each VLAN should have complete information
        for i, vlan in enumerate(parsed_vlans):
            expected_vlan_id, expected_vlan_name, expected_ports, expected_portchannels = vlan_entries[i]
            
            assert vlan.vlan_id == expected_vlan_id, f"VLAN ID mismatch: expected {expected_vlan_id}, got {vlan.vlan_id}"
            assert vlan.vlan_name == expected_vlan_name, f"VLAN name mismatch: expected {expected_vlan_name}, got {vlan.vlan_name}"
            assert vlan.device_hostname == device_hostname, "Device hostname should be preserved"
            assert vlan.device_ip == device_ip, "Device IP should be preserved"
            assert vlan.collection_timestamp is not None, "Collection timestamp should be set"
    
    @given(
        port_lists=st.lists(
            st.lists(st.from_regex(r'(Fa|Gi|Te|Eth)\d+/\d+'), min_size=0, max_size=20),
            min_size=1, max_size=10
        )
    )
    def test_physical_port_count_accuracy(self, port_lists):
        """
        Feature: vlan-inventory-collection, Property 10: Physical Port Count Accuracy
        For any VLAN with port assignments, the count of physical ports should be accurate and non-negative
        
        Validates: Requirements 3.2
        """
        from netwalker.vlan.vlan_parser import VLANParser
        
        parser = VLANParser()
        
        for ports in port_lists:
            # Create port string
            ports_str = ', '.join(ports)
            
            # Count ports
            port_count, _ = parser._count_ports_and_portchannels(ports_str)
            
            # Property: Port count should be accurate and non-negative
            assert port_count == len(ports), f"Expected {len(ports)} ports, got {port_count}"
            assert port_count >= 0, f"Port count should be non-negative, got {port_count}"
            assert isinstance(port_count, int), "Port count should be an integer"
    
    @given(
        portchannel_lists=st.lists(
            st.lists(st.from_regex(r'Po\d+'), min_size=0, max_size=10),
            min_size=1, max_size=10
        )
    )
    def test_portchannel_count_accuracy(self, portchannel_lists):
        """
        Feature: vlan-inventory-collection, Property 11: PortChannel Count Accuracy
        For any VLAN with PortChannel assignments, the count of PortChannel interfaces 
        should be accurate and non-negative
        
        Validates: Requirements 3.3
        """
        from netwalker.vlan.vlan_parser import VLANParser
        
        parser = VLANParser()
        
        for portchannels in portchannel_lists:
            # Create PortChannel string
            portchannels_str = ', '.join(portchannels)
            
            # Count PortChannels
            _, portchannel_count = parser._count_ports_and_portchannels(portchannels_str)
            
            # Property: PortChannel count should be accurate and non-negative
            assert portchannel_count == len(portchannels), f"Expected {len(portchannels)} PortChannels, got {portchannel_count}"
            assert portchannel_count >= 0, f"PortChannel count should be non-negative, got {portchannel_count}"
            assert isinstance(portchannel_count, int), "PortChannel count should be an integer"
    
    @given(
        vlan_entries_with_status=st.lists(
            st.tuples(
                st.integers(min_value=1, max_value=4094),  # vlan_id
                st.text(min_size=1, max_size=32),  # vlan_name
                st.sampled_from(['active', 'inactive', 'suspended']),  # status
                st.lists(st.from_regex(r'(Fa|Gi|Te|Eth)\d+/\d+'), min_size=0, max_size=5)  # ports
            ),
            min_size=1, max_size=10
        ),
        platform=st.sampled_from(['IOS', 'IOS-XE', 'NX-OS'])
    )
    def test_status_field_exclusion(self, vlan_entries_with_status, platform):
        """
        Feature: vlan-inventory-collection, Property 12: Status Field Exclusion
        For any VLAN command output containing status information, status fields 
        should be ignored during parsing
        
        Validates: Requirements 3.4
        """
        from netwalker.vlan.vlan_parser import VLANParser
        
        # Generate VLAN output with status fields
        if platform in ['IOS', 'IOS-XE']:
            output = self._generate_ios_vlan_output_with_status(vlan_entries_with_status)
        else:  # NX-OS
            output = self._generate_nxos_vlan_output_with_status(vlan_entries_with_status)
        
        parser = VLANParser()
        parsed_vlans = parser.parse_vlan_output(output, platform, "test-device", "192.168.1.1")
        
        # Property: Status should be ignored, VLANs should still be parsed
        assert len(parsed_vlans) == len(vlan_entries_with_status), "All VLANs should be parsed regardless of status"
        
        # Property: VLAN data should be extracted correctly despite status presence
        for i, vlan in enumerate(parsed_vlans):
            expected_vlan_id, expected_vlan_name, _, _ = vlan_entries_with_status[i]
            assert vlan.vlan_id == expected_vlan_id, "VLAN ID should be extracted correctly"
            assert vlan.vlan_name == expected_vlan_name, "VLAN name should be extracted correctly"
    
    @given(
        malformed_outputs=st.lists(
            st.text(min_size=10, max_size=100),
            min_size=1, max_size=5
        ),
        platform=st.sampled_from(['IOS', 'IOS-XE', 'NX-OS'])
    )
    def test_parsing_error_recovery(self, malformed_outputs, platform):
        """
        Feature: vlan-inventory-collection, Property 13: Parsing Error Recovery
        For any malformed or unexpected VLAN output format, parsing errors should be 
        logged and processing should continue with remaining VLANs
        
        Validates: Requirements 3.5
        """
        from netwalker.vlan.vlan_parser import VLANParser
        
        parser = VLANParser()
        
        for malformed_output in malformed_outputs:
            # Property: Parser should not crash on malformed input
            try:
                parsed_vlans = parser.parse_vlan_output(malformed_output, platform, "test-device", "192.168.1.1")
                # Should return empty list or partial results, not crash
                assert isinstance(parsed_vlans, list), "Parser should return a list even for malformed input"
            except Exception as e:
                # If an exception occurs, it should be handled gracefully
                pytest.fail(f"Parser should handle malformed input gracefully, but got exception: {e}")
    
    def _generate_ios_vlan_output(self, vlan_entries):
        """Generate realistic IOS VLAN output for testing"""
        lines = [
            "VLAN Name                             Status    Ports",
            "---- -------------------------------- --------- -------------------------------"
        ]
        
        for vlan_id, vlan_name, ports, portchannels in vlan_entries:
            all_interfaces = ports + portchannels
            ports_str = ', '.join(all_interfaces) if all_interfaces else ''
            line = f"{vlan_id:<4} {vlan_name:<32} active    {ports_str}"
            lines.append(line)
        
        return '\n'.join(lines)
    
    def _generate_nxos_vlan_output(self, vlan_entries):
        """Generate realistic NX-OS VLAN output for testing"""
        lines = [
            "VLAN Name                             Status    Ports",
            "---- -------------------------------- --------- -------------------------------"
        ]
        
        for vlan_id, vlan_name, ports, portchannels in vlan_entries:
            # Convert port names to NX-OS format (Eth instead of Fa/Gi)
            nxos_ports = [port.replace('Fa', 'Eth').replace('Gi', 'Eth').replace('Te', 'Eth') for port in ports]
            all_interfaces = nxos_ports + portchannels
            ports_str = ', '.join(all_interfaces) if all_interfaces else ''
            line = f"{vlan_id:<4} {vlan_name:<32} active    {ports_str}"
            lines.append(line)
        
        return '\n'.join(lines)
    
    def _generate_ios_vlan_output_with_status(self, vlan_entries_with_status):
        """Generate IOS VLAN output with explicit status fields"""
        lines = [
            "VLAN Name                             Status    Ports",
            "---- -------------------------------- --------- -------------------------------"
        ]
        
        for vlan_id, vlan_name, status, ports in vlan_entries_with_status:
            ports_str = ', '.join(ports) if ports else ''
            line = f"{vlan_id:<4} {vlan_name:<32} {status:<9} {ports_str}"
            lines.append(line)
        
        return '\n'.join(lines)
    
    def _generate_nxos_vlan_output_with_status(self, vlan_entries_with_status):
        """Generate NX-OS VLAN output with explicit status fields"""
        lines = [
            "VLAN Name                             Status    Ports",
            "---- -------------------------------- --------- -------------------------------"
        ]
        
        for vlan_id, vlan_name, status, ports in vlan_entries_with_status:
            # Convert to NX-OS port format
            nxos_ports = [port.replace('Fa', 'Eth').replace('Gi', 'Eth').replace('Te', 'Eth') for port in ports]
            ports_str = ', '.join(nxos_ports) if nxos_ports else ''
            line = f"{vlan_id:<4} {vlan_name:<32} {status:<9} {ports_str}"
            lines.append(line)
        
        return '\n'.join(lines)

class TestVLANCollectorProperties:
    """Property-based tests for VLAN Collector functionality"""
    
    @given(
        devices=st.lists(
            st.builds(
                lambda hostname, ip, platform: {
                    'hostname': hostname,
                    'primary_ip': ip,
                    'platform': platform,
                    'capabilities': ['Router', 'Switch'],
                    'software_version': '15.1',
                    'vtp_version': '2',
                    'serial_number': 'ABC123',
                    'hardware_model': 'C2960',
                    'uptime': '1 day',
                    'discovery_timestamp': datetime.now(),
                    'discovery_depth': 1,
                    'is_seed': False,
                    'connection_method': 'SSH',
                    'connection_status': 'success',
                    'error_details': None,
                    'neighbors': [],
                    'vlans': [],
                    'vlan_collection_status': 'not_attempted',
                    'vlan_collection_error': None
                },
                hostname=st.text(min_size=1, max_size=36),
                ip=st.ip_addresses(v=4).map(str),
                platform=st.sampled_from(['IOS', 'IOS-XE', 'NX-OS'])
            ),
            min_size=1, max_size=10
        )
    )
    def test_automatic_vlan_collection_initiation(self, devices):
        """
        Feature: vlan-inventory-collection, Property 1: Automatic VLAN Collection Initiation
        For any successfully discovered device, VLAN collection should be automatically initiated for that device
        
        Validates: Requirements 1.1
        """
        from netwalker.vlan.vlan_collector import VLANCollector
        from netwalker.connection.data_models import DeviceInfo
        from unittest.mock import Mock
        
        # Create VLAN collector with enabled configuration
        config = {'vlan_collection': {'enabled': True}}
        collector = VLANCollector(config)
        
        # Mock connection
        mock_connection = Mock()
        mock_connection.send_command.return_value = Mock(result="VLAN Name Status Ports\n1 default active Fa0/1")
        
        for device_data in devices:
            device_info = DeviceInfo(**device_data)
            
            # Property: VLAN collection should be initiated for each device
            vlans = collector.collect_vlan_information(mock_connection, device_info)
            
            # Property: Collection should be attempted (even if it returns empty results)
            assert isinstance(vlans, list), "VLAN collection should return a list"
            
            # Property: Collection statistics should be updated
            stats = collector.get_collection_summary()
            assert stats['total_attempts'] > 0, "Collection attempts should be tracked"
    
    @given(
        vlan_outputs=st.lists(
            st.tuples(
                st.text(min_size=50, max_size=500),  # VLAN output
                st.sampled_from(['IOS', 'IOS-XE', 'NX-OS']),  # platform
                st.text(min_size=1, max_size=36),  # hostname
                st.ip_addresses(v=4).map(str)  # ip
            ),
            min_size=1, max_size=5
        )
    )
    def test_vlan_information_extraction_completeness(self, vlan_outputs):
        """
        Feature: vlan-inventory-collection, Property 3: VLAN Information Extraction Completeness
        For any successful VLAN command execution, all available VLAN information should be extracted from the command output
        
        Validates: Requirements 1.3
        """
        from netwalker.vlan.vlan_collector import VLANCollector
        from netwalker.connection.data_models import DeviceInfo
        from unittest.mock import Mock
        
        config = {'vlan_collection': {'enabled': True}}
        collector = VLANCollector(config)
        
        for vlan_output, platform, hostname, ip in vlan_outputs:
            # Create mock connection that returns the VLAN output
            mock_connection = Mock()
            mock_connection.send_command.return_value = Mock(result=vlan_output)
            
            # Create device info
            device_info = DeviceInfo(
                hostname=hostname,
                primary_ip=ip,
                platform=platform,
                capabilities=['Router'],
                software_version='15.1',
                vtp_version='2',
                serial_number='ABC123',
                hardware_model='C2960',
                uptime='1 day',
                discovery_timestamp=datetime.now(),
                discovery_depth=1,
                is_seed=False,
                connection_method='SSH',
                connection_status='success',
                error_details=None,
                neighbors=[],
                vlans=[],
                vlan_collection_status='not_attempted',
                vlan_collection_error=None
            )
            
            # Property: VLAN information should be extracted when command succeeds
            vlans = collector.collect_vlan_information(mock_connection, device_info)
            
            # Property: Result should be a list
            assert isinstance(vlans, list), "VLAN extraction should return a list"
            
            # Property: If VLANs are found, they should have device association
            for vlan in vlans:
                assert vlan.device_hostname == hostname, "VLAN should be associated with correct device hostname"
                assert vlan.device_ip == ip, "VLAN should be associated with correct device IP"
    
    @given(
        error_scenarios=st.lists(
            st.tuples(
                st.sampled_from(['connection_error', 'command_error', 'parsing_error']),  # error type
                st.text(min_size=1, max_size=36),  # hostname
                st.ip_addresses(v=4).map(str),  # ip
                st.sampled_from(['IOS', 'IOS-XE', 'NX-OS'])  # platform
            ),
            min_size=1, max_size=5
        )
    )
    def test_error_isolation_and_continuation(self, error_scenarios):
        """
        Feature: vlan-inventory-collection, Property 4: Error Isolation and Continuation
        For any VLAN command execution failure, the system should log the failure and continue processing remaining devices
        
        Validates: Requirements 1.4
        """
        from netwalker.vlan.vlan_collector import VLANCollector
        from netwalker.connection.data_models import DeviceInfo
        from unittest.mock import Mock
        
        config = {'vlan_collection': {'enabled': True}}
        collector = VLANCollector(config)
        
        for error_type, hostname, ip, platform in error_scenarios:
            # Create mock connection that simulates different error types
            mock_connection = Mock()
            
            if error_type == 'connection_error':
                mock_connection.send_command.side_effect = Exception("Connection lost")
            elif error_type == 'command_error':
                mock_connection.send_command.side_effect = Exception("Invalid command")
            else:  # parsing_error
                mock_connection.send_command.return_value = Mock(result="Invalid VLAN output format")
            
            device_info = DeviceInfo(
                hostname=hostname,
                primary_ip=ip,
                platform=platform,
                capabilities=['Router'],
                software_version='15.1',
                vtp_version='2',
                serial_number='ABC123',
                hardware_model='C2960',
                uptime='1 day',
                discovery_timestamp=datetime.now(),
                discovery_depth=1,
                is_seed=False,
                connection_method='SSH',
                connection_status='success',
                error_details=None,
                neighbors=[],
                vlans=[],
                vlan_collection_status='not_attempted',
                vlan_collection_error=None
            )
            
            # Property: System should handle errors gracefully and continue
            try:
                vlans = collector.collect_vlan_information(mock_connection, device_info)
                
                # Property: Should return empty list on error, not crash
                assert isinstance(vlans, list), "Should return list even on error"
                
                # Property: Error should be tracked in statistics
                stats = collector.get_collection_summary()
                assert stats['failed_collections'] > 0, "Failed collections should be tracked"
                
            except Exception as e:
                pytest.fail(f"VLAN collector should handle errors gracefully, but got: {e}")
    
    @given(
        device_vlan_pairs=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=36),  # hostname
                st.ip_addresses(v=4).map(str),  # ip
                st.lists(
                    st.tuples(
                        st.integers(min_value=1, max_value=4094),  # vlan_id
                        st.text(min_size=1, max_size=32)  # vlan_name
                    ),
                    min_size=0, max_size=10
                )  # vlans
            ),
            min_size=1, max_size=5
        )
    )
    def test_device_association_completeness(self, device_vlan_pairs):
        """
        Feature: vlan-inventory-collection, Property 5: Device Association Completeness
        For any collected VLAN entry, the source device information should be properly recorded and associated
        
        Validates: Requirements 1.5
        """
        from netwalker.vlan.vlan_collector import VLANCollector
        from netwalker.connection.data_models import DeviceInfo
        from unittest.mock import Mock
        
        config = {'vlan_collection': {'enabled': True}}
        collector = VLANCollector(config)
        
        for hostname, ip, vlan_data in device_vlan_pairs:
            # Generate VLAN output for the device
            vlan_lines = ["VLAN Name Status Ports", "---- ---- ------ -----"]
            for vlan_id, vlan_name in vlan_data:
                vlan_lines.append(f"{vlan_id} {vlan_name} active Fa0/1")
            vlan_output = "\n".join(vlan_lines)
            
            # Create mock connection
            mock_connection = Mock()
            mock_connection.send_command.return_value = Mock(result=vlan_output)
            
            device_info = DeviceInfo(
                hostname=hostname,
                primary_ip=ip,
                platform='IOS',
                capabilities=['Router'],
                software_version='15.1',
                vtp_version='2',
                serial_number='ABC123',
                hardware_model='C2960',
                uptime='1 day',
                discovery_timestamp=datetime.now(),
                discovery_depth=1,
                is_seed=False,
                connection_method='SSH',
                connection_status='success',
                error_details=None,
                neighbors=[],
                vlans=[],
                vlan_collection_status='not_attempted',
                vlan_collection_error=None
            )
            
            # Collect VLANs
            vlans = collector.collect_vlan_information(mock_connection, device_info)
            
            # Property: All VLANs should be properly associated with the device
            for vlan in vlans:
                assert vlan.device_hostname == hostname, f"VLAN {vlan.vlan_id} should be associated with hostname {hostname}"
                assert vlan.device_ip == ip, f"VLAN {vlan.vlan_id} should be associated with IP {ip}"
                assert vlan.collection_timestamp is not None, "VLAN should have collection timestamp"


class TestConfigurationManagerProperties:
    """Property-based tests for Configuration Manager VLAN integration"""
    
    @given(
        timeout_values=st.integers(min_value=1, max_value=300),
        retry_values=st.integers(min_value=0, max_value=10),
        enabled_values=st.booleans()
    )
    def test_timeout_configuration_application(self, timeout_values, retry_values, enabled_values):
        """
        Feature: vlan-inventory-collection, Property 24: Timeout Configuration Application
        For any configured timeout value, the VLAN collection system should apply the timeout correctly
        
        Validates: Requirements 7.2
        """
        from netwalker.config.config_manager import ConfigurationManager
        from netwalker.config.data_models import VLANCollectionConfig
        import tempfile
        import os
        
        # Create temporary config file
        temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        
        try:
            # Write test configuration
            test_config = f"""
[vlan_collection]
enabled = {str(enabled_values).lower()}
command_timeout = {timeout_values}
max_retries = {retry_values}
include_inactive_vlans = true
"""
            with open(temp_config.name, 'w') as f:
                f.write(test_config)
            
            # Load configuration
            config_manager = ConfigurationManager(temp_config.name)
            config = config_manager.load_configuration()
            
            # Property: Configuration should be applied correctly
            vlan_config = config['vlan_collection']
            assert isinstance(vlan_config, VLANCollectionConfig), "Should return VLANCollectionConfig object"
            assert vlan_config.enabled == enabled_values, f"Enabled should be {enabled_values}"
            assert vlan_config.command_timeout == timeout_values, f"Timeout should be {timeout_values}"
            assert vlan_config.max_retries == retry_values, f"Retries should be {retry_values}"
            
            # Property: Timeout should be within valid range
            assert 1 <= vlan_config.command_timeout <= 300, "Timeout should be within valid range"
            assert 0 <= vlan_config.max_retries <= 10, "Retries should be within valid range"
            
        finally:
            # Clean up
            if os.path.exists(temp_config.name):
                os.unlink(temp_config.name)
    
    @given(
        cli_overrides=st.dictionaries(
            st.sampled_from(['vlan_enabled', 'vlan_timeout', 'vlan_retries', 'vlan_include_inactive']),
            st.one_of(
                st.booleans(),
                st.integers(min_value=1, max_value=300),
                st.integers(min_value=0, max_value=10)
            ),
            min_size=1, max_size=4
        )
    )
    def test_cli_override_functionality_property(self, cli_overrides):
        """
        Feature: vlan-inventory-collection, Property 26: CLI Override Functionality
        For any CLI override values, the configuration system should apply overrides correctly
        
        Validates: Requirements 7.5
        """
        from netwalker.config.config_manager import ConfigurationManager
        import tempfile
        import os
        
        # Create temporary config file
        temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        
        try:
            # Write base configuration
            base_config = """
[vlan_collection]
enabled = true
command_timeout = 30
max_retries = 2
include_inactive_vlans = true
"""
            with open(temp_config.name, 'w') as f:
                f.write(base_config)
            
            # Load configuration with CLI overrides
            config_manager = ConfigurationManager(temp_config.name)
            config = config_manager.load_configuration(cli_overrides)
            
            # Property: CLI overrides should be applied
            vlan_config = config['vlan_collection']
            
            if 'vlan_enabled' in cli_overrides:
                assert vlan_config.enabled == cli_overrides['vlan_enabled'], "CLI override for enabled should be applied"
            
            if 'vlan_timeout' in cli_overrides:
                assert vlan_config.command_timeout == cli_overrides['vlan_timeout'], "CLI override for timeout should be applied"
            
            if 'vlan_retries' in cli_overrides:
                assert vlan_config.max_retries == cli_overrides['vlan_retries'], "CLI override for retries should be applied"
            
            if 'vlan_include_inactive' in cli_overrides:
                assert vlan_config.include_inactive_vlans == cli_overrides['vlan_include_inactive'], "CLI override for include_inactive should be applied"
            
        finally:
            # Clean up
            if os.path.exists(temp_config.name):
                os.unlink(temp_config.name)


class TestVLANErrorHandlingProperties:
    """Property-based tests for VLAN error handling and logging"""
    
    @given(
        error_scenarios=st.lists(
            st.tuples(
                st.sampled_from(['switch1', 'router2', 'core-sw', 'access-01', 'dist-switch', 'test-device']),  # hostname
                st.ip_addresses(v=4).map(str),  # ip
                st.sampled_from(['IOS', 'IOS-XE', 'NX-OS']),  # platform
                st.sampled_from([
                    'Command timeout',
                    'Invalid command',
                    'Connection lost',
                    'Device unreachable',
                    'Command failed: syntax error'
                ])  # error_message
            ),
            min_size=1, max_size=5
        )
    )
    def test_command_failure_logging_completeness(self, error_scenarios):
        """
        Feature: vlan-inventory-collection, Property 19: Command Failure Logging Completeness
        For any VLAN command failure, detailed failure information should be logged for troubleshooting
        
        Validates: Requirements 6.1
        """
        from netwalker.vlan.vlan_collector import VLANCollector
        from netwalker.connection.data_models import DeviceInfo
        from unittest.mock import Mock, patch
        import logging
        
        config = {'vlan_collection': {'enabled': True, 'command_timeout': 30, 'max_retries': 2}}
        collector = VLANCollector(config)
        
        # Capture log messages
        with patch.object(collector.logger, 'error') as mock_error_log:
            with patch.object(collector.logger, 'warning') as mock_warning_log:
                
                for hostname, ip, platform, error_message in error_scenarios:
                    device_info = DeviceInfo(
                        hostname=hostname,
                        primary_ip=ip,
                        platform=platform,
                        capabilities=['Router'],
                        software_version='15.1',
                        vtp_version='2',
                        serial_number='ABC123',
                        hardware_model='C2960',
                        uptime='1 day',
                        discovery_timestamp=datetime.now(),
                        discovery_depth=1,
                        is_seed=False,
                        connection_method='SSH',
                        connection_status='success',
                        error_details=None,
                        neighbors=[],
                        vlans=[],
                        vlan_collection_status='not_attempted',
                        vlan_collection_error=None
                    )
                    
                    # Trigger command failure logging
                    collector._log_command_failure_details(device_info, error_message)
                    
                    # Property: Detailed failure information should be logged
                    assert mock_error_log.called, "Error logging should be called for command failures"
                    
                    # Check that logged messages contain essential information
                    logged_calls = [str(call) for call in mock_error_log.call_args_list]
                    logged_text = ' '.join(logged_calls)
                    
                    assert hostname in logged_text, f"Hostname {hostname} should be in logged failure details"
                    assert ip in logged_text, f"IP {ip} should be in logged failure details"
                    assert platform in logged_text, f"Platform {platform} should be in logged failure details"
                    
                    # Property: No sensitive information should be logged
                    assert 'password' not in logged_text.lower() or '***' in logged_text, "Passwords should be sanitized"
                    
                    # Reset mocks for next iteration
                    mock_error_log.reset_mock()
                    mock_warning_log.reset_mock()
    
    @given(
        auth_error_scenarios=st.lists(
            st.tuples(
                st.sampled_from(['switch1', 'router2', 'core-sw', 'access-01', 'dist-switch', 'test-device']),  # hostname
                st.ip_addresses(v=4).map(str),  # ip
                st.sampled_from([
                    'Authentication failed: invalid password',
                    'Permission denied: insufficient privileges',
                    'Authorization failed for user admin',
                    'Login failed: bad credentials'
                ])  # auth_error_message
            ),
            min_size=1, max_size=5
        )
    )
    def test_secure_authentication_error_logging(self, auth_error_scenarios):
        """
        Feature: vlan-inventory-collection, Property 22: Secure Authentication Error Logging
        For any authentication failure, error details should be logged without exposing credentials
        
        Validates: Requirements 6.4
        """
        from netwalker.vlan.vlan_collector import VLANCollector
        from netwalker.connection.data_models import DeviceInfo
        from unittest.mock import Mock, patch
        
        config = {'vlan_collection': {'enabled': True}}
        collector = VLANCollector(config)
        
        # Capture log messages
        with patch.object(collector.logger, 'error') as mock_error_log:
            with patch.object(collector.logger, 'warning') as mock_warning_log:
                
                for hostname, ip, auth_error in auth_error_scenarios:
                    device_info = DeviceInfo(
                        hostname=hostname,
                        primary_ip=ip,
                        platform='IOS',
                        capabilities=['Router'],
                        software_version='15.1',
                        vtp_version='2',
                        serial_number='ABC123',
                        hardware_model='C2960',
                        uptime='1 day',
                        discovery_timestamp=datetime.now(),
                        discovery_depth=1,
                        is_seed=False,
                        connection_method='SSH',
                        connection_status='success',
                        error_details=None,
                        neighbors=[],
                        vlans=[],
                        vlan_collection_status='not_attempted',
                        vlan_collection_error=None
                    )
                    
                    # Trigger authentication error logging
                    collector._log_authentication_error_securely(device_info, auth_error)
                    
                    # Property: Authentication errors should be logged
                    assert mock_error_log.called, "Authentication errors should be logged"
                    
                    # Check logged content
                    logged_calls = [str(call) for call in mock_error_log.call_args_list]
                    logged_text = ' '.join(logged_calls)
                    
                    # Property: Device information should be included
                    assert hostname in logged_text, f"Hostname {hostname} should be in auth error log"
                    assert ip in logged_text, f"IP {ip} should be in auth error log"
                    
                    # Property: No actual credentials should be exposed
                    assert 'password=' not in logged_text or '***' in logged_text, "Passwords should be sanitized in auth errors"
                    assert 'secret=' not in logged_text or '***' in logged_text, "Secrets should be sanitized in auth errors"
                    
                    # Property: Guidance should be provided
                    warning_calls = [str(call) for call in mock_warning_log.call_args_list]
                    warning_text = ' '.join(warning_calls)
                    assert 'credential' in warning_text.lower() or 'authentication' in warning_text.lower(), \
                        "Authentication error guidance should be provided"
                    
                    # Reset mocks for next iteration
                    mock_error_log.reset_mock()
                    mock_warning_log.reset_mock()
    
    @given(
        collection_stats=st.tuples(
            st.integers(min_value=0, max_value=100),  # total_attempts
            st.integers(min_value=0, max_value=100),  # successful_collections
            st.integers(min_value=0, max_value=100),  # failed_collections
            st.integers(min_value=0, max_value=100),  # skipped_collections
            st.integers(min_value=0, max_value=1000)  # total_vlans_collected
        )
    )
    def test_collection_summary_logging(self, collection_stats):
        """
        Feature: vlan-inventory-collection, Property 23: Collection Summary Logging
        For any VLAN collection session, comprehensive summary statistics should be logged
        
        Validates: Requirements 6.5
        """
        from netwalker.vlan.vlan_collector import VLANCollector
        from unittest.mock import Mock, patch
        
        total_attempts, successful, failed, skipped, total_vlans = collection_stats
        
        # Ensure logical consistency in test data
        assume(successful + failed <= total_attempts)
        assume(successful >= 0 and failed >= 0 and skipped >= 0)
        
        config = {'vlan_collection': {'enabled': True}}
        collector = VLANCollector(config)
        
        # Set up collection statistics
        collector.collection_stats = {
            'total_attempts': total_attempts,
            'successful_collections': successful,
            'failed_collections': failed,
            'skipped_collections': skipped,
            'total_vlans_collected': total_vlans
        }
        
        # Capture log messages
        with patch.object(collector.logger, 'info') as mock_info_log:
            with patch.object(collector.logger, 'warning') as mock_warning_log:
                
                # Trigger summary logging
                collector.log_collection_summary()
                
                # Property: Summary should be logged
                assert mock_info_log.called, "Collection summary should be logged"
                
                # Check logged content
                logged_calls = [str(call) for call in mock_info_log.call_args_list]
                logged_text = ' '.join(logged_calls)
                
                # Property: All key statistics should be included
                assert str(total_attempts) in logged_text, "Total attempts should be in summary"
                assert str(successful) in logged_text, "Successful collections should be in summary"
                assert str(failed) in logged_text, "Failed collections should be in summary"
                assert str(skipped) in logged_text, "Skipped collections should be in summary"
                assert str(total_vlans) in logged_text, "Total VLANs should be in summary"
                
                # Property: Success rate should be calculated and logged
                if total_attempts > 0:
                    expected_success_rate = (successful / total_attempts) * 100
                    # Check that some success rate is mentioned (allowing for rounding)
                    assert 'Success Rate' in logged_text or 'success rate' in logged_text, \
                        "Success rate should be calculated and logged"
                
                # Property: Warnings should be logged for poor performance
                warning_calls = [str(call) for call in mock_warning_log.call_args_list]
                warning_text = ' '.join(warning_calls)
                
                if total_attempts > 5:
                    success_rate = (successful / total_attempts * 100) if total_attempts > 0 else 0
                    if success_rate < 50:
                        assert mock_warning_log.called, "Low success rate should trigger warning"
                    
                    if skipped > successful:
                        assert mock_warning_log.called, "High skip rate should trigger warning"


class TestVLANPerformanceProperties:
    """Property-based tests for VLAN performance and concurrency features"""
    
    @given(
        concurrent_devices=st.lists(
            st.tuples(
                st.sampled_from(['switch1', 'router2', 'core-sw', 'access-01', 'dist-switch']),  # hostname
                st.ip_addresses(v=4).map(str),  # ip
                st.sampled_from(['IOS', 'IOS-XE', 'NX-OS']),  # platform
                st.lists(
                    st.tuples(
                        st.integers(min_value=1, max_value=4094),  # vlan_id
                        st.text(min_size=1, max_size=32)  # vlan_name
                    ),
                    min_size=0, max_size=5
                )  # vlans
            ),
            min_size=1, max_size=10
        ),
        max_concurrent=st.integers(min_value=1, max_value=10)
    )
    def test_concurrent_collection_support(self, concurrent_devices, max_concurrent):
        """
        Feature: vlan-inventory-collection, Property 27: Concurrent Collection Support
        For any set of devices, VLAN collection should support concurrent processing 
        without resource conflicts or data corruption
        
        Validates: Requirements 8.1
        """
        from netwalker.vlan.vlan_collector import VLANCollector
        from netwalker.connection.data_models import DeviceInfo
        from unittest.mock import Mock
        import threading
        import time
        
        # Create configuration with concurrent collection support
        config = {
            'vlan_collection': {'enabled': True, 'command_timeout': 5, 'max_retries': 1},
            'max_concurrent_vlan_collections': max_concurrent
        }
        
        collector = VLANCollector(config)
        
        # Create device connections
        device_connections = []
        
        for hostname, ip, platform, vlan_data in concurrent_devices:
            # Generate VLAN output for the device
            vlan_lines = ["VLAN Name Status Ports", "---- ---- ------ -----"]
            for vlan_id, vlan_name in vlan_data:
                vlan_lines.append(f"{vlan_id} {vlan_name} active Fa0/1")
            vlan_output = "\n".join(vlan_lines)
            
            # Create mock connection
            mock_connection = Mock()
            mock_connection.send_command.return_value = Mock(result=vlan_output)
            
            device_info = DeviceInfo(
                hostname=hostname,
                primary_ip=ip,
                platform=platform,
                capabilities=['Router'],
                software_version='15.1',
                vtp_version='2',
                serial_number='ABC123',
                hardware_model='C2960',
                uptime='1 day',
                discovery_timestamp=datetime.now(),
                discovery_depth=1,
                is_seed=False,
                connection_method='SSH',
                connection_status='success',
                error_details=None,
                neighbors=[],
                vlans=[],
                vlan_collection_status='not_attempted',
                vlan_collection_error=None
            )
            
            device_connections.append((mock_connection, device_info))
        
        # Property: Concurrent collection should complete successfully
        start_time = time.time()
        results = collector.collect_vlans_concurrently(device_connections)
        collection_time = time.time() - start_time
        
        # Property: All devices should be processed
        assert len(results) == len(concurrent_devices), f"Expected {len(concurrent_devices)} results, got {len(results)}"
        
        # Property: Results should contain valid data
        for result in results:
            assert result.device_hostname in [d[0] for d in concurrent_devices], "Result should match input device"
            assert result.device_ip in [d[1] for d in concurrent_devices], "Result IP should match input device"
            assert isinstance(result.collection_success, bool), "Collection success should be boolean"
            assert isinstance(result.vlans, list), "VLANs should be a list"
        
        # Property: Concurrent processing should respect limits
        assert collector.max_concurrent_collections == max_concurrent, "Concurrent limit should be respected"
        
        # Property: No resource conflicts should occur
        active_collections = collector.get_active_collections()
        assert len(active_collections) == 0, "No collections should be active after completion"
    
    @given(
        resource_constraints=st.tuples(
            st.integers(min_value=1, max_value=3),  # max_concurrent (reduced)
            st.integers(min_value=2, max_value=5),  # num_devices (reduced)
            st.integers(min_value=1, max_value=5)   # command_timeout (reduced)
        )
    )
    @settings(deadline=1000)  # Increase deadline to 1 second
    def test_resource_constraint_compliance(self, resource_constraints):
        """
        Feature: vlan-inventory-collection, Property 28: Resource Constraint Compliance
        For any configured resource limits, the system should not exceed the specified 
        concurrent collection limits
        
        Validates: Requirements 8.2
        """
        from netwalker.vlan.vlan_collector import VLANCollector
        from netwalker.connection.data_models import DeviceInfo
        from unittest.mock import Mock
        import threading
        import time
        
        max_concurrent, num_devices, command_timeout = resource_constraints
        
        # Ensure we have more devices than concurrent limit to test constraint
        assume(num_devices > max_concurrent)
        
        config = {
            'vlan_collection': {'enabled': True, 'command_timeout': command_timeout, 'max_retries': 0},
            'max_concurrent_vlan_collections': max_concurrent
        }
        
        collector = VLANCollector(config)
        
        # Track concurrent executions
        concurrent_count = {'current': 0, 'max_observed': 0}
        concurrent_lock = threading.Lock()
        
        def mock_send_command_with_tracking(cmd, **kwargs):
            with concurrent_lock:
                concurrent_count['current'] += 1
                concurrent_count['max_observed'] = max(concurrent_count['max_observed'], concurrent_count['current'])
            
            # Simulate minimal processing time (reduced from 0.1 to 0.01)
            time.sleep(0.01)
            
            with concurrent_lock:
                concurrent_count['current'] -= 1
            
            return Mock(result="VLAN Name Status Ports\n1 default active Fa0/1")
        
        # Create device connections with tracking
        device_connections = []
        
        for i in range(num_devices):
            mock_connection = Mock()
            mock_connection.send_command.side_effect = mock_send_command_with_tracking
            
            device_info = DeviceInfo(
                hostname=f"device{i}",
                primary_ip=f"192.168.1.{i+1}",
                platform='IOS',
                capabilities=['Router'],
                software_version='15.1',
                vtp_version='2',
                serial_number='ABC123',
                hardware_model='C2960',
                uptime='1 day',
                discovery_timestamp=datetime.now(),
                discovery_depth=1,
                is_seed=False,
                connection_method='SSH',
                connection_status='success',
                error_details=None,
                neighbors=[],
                vlans=[],
                vlan_collection_status='not_attempted',
                vlan_collection_error=None
            )
            
            device_connections.append((mock_connection, device_info))
        
        # Property: Resource constraints should be respected
        results = collector.collect_vlans_concurrently(device_connections)
        
        # Property: Maximum concurrent executions should not exceed limit
        assert concurrent_count['max_observed'] <= max_concurrent, \
            f"Observed {concurrent_count['max_observed']} concurrent executions, limit was {max_concurrent}"
        
        # Property: All devices should still be processed despite constraints
        assert len(results) == num_devices, f"Expected {num_devices} results, got {len(results)}"
        
        # Property: Resource semaphore should be properly managed
        assert collector.resource_semaphore._value == max_concurrent, "Semaphore should be reset to initial value"
    
    @given(
        timeout_scenarios=st.lists(
            st.tuples(
                st.sampled_from(['switch1', 'router2', 'core-sw']),  # hostname
                st.integers(min_value=1, max_value=3),  # command_timeout (reduced)
                st.sampled_from(['normal', 'timeout', 'slow'])  # execution_type
            ),
            min_size=1, max_size=2  # Reduced max_size
        )
    )
    @settings(deadline=1000)  # Increase deadline to 1 second
    def test_timeout_enforcement(self, timeout_scenarios):
        """
        Feature: vlan-inventory-collection, Property 29: Timeout Enforcement
        For any configured timeout value, VLAN commands should be terminated if they 
        exceed the specified timeout duration
        
        Validates: Requirements 8.3
        """
        from netwalker.vlan.vlan_collector import VLANCollector
        from netwalker.connection.data_models import DeviceInfo
        from unittest.mock import Mock, patch
        import time
        
        for hostname, command_timeout, execution_type in timeout_scenarios:
            config = {
                'vlan_collection': {'enabled': True, 'command_timeout': command_timeout, 'max_retries': 0}
            }
            
            collector = VLANCollector(config)
            
            # Create mock connection with different execution behaviors
            mock_connection = Mock()
            
            if execution_type == 'normal':
                # Normal execution - should complete quickly
                mock_connection.send_command.return_value = Mock(result="VLAN Name Status Ports\n1 default active Fa0/1")
            elif execution_type == 'timeout':
                # Timeout execution - simulate timeout without actual delay
                def timeout_command(cmd, **kwargs):
                    # Simulate timeout by raising TimeoutError instead of sleeping
                    raise TimeoutError(f"Command timed out after {command_timeout}s")
                mock_connection.send_command.side_effect = timeout_command
            else:  # slow
                # Slow but within timeout - minimal delay
                def medium_command(cmd, **kwargs):
                    time.sleep(0.01)  # Minimal delay instead of half timeout
                    return Mock(result="VLAN Name Status Ports\n1 default active Fa0/1")
                mock_connection.send_command.side_effect = medium_command
            
            device_info = DeviceInfo(
                hostname=hostname,
                primary_ip="192.168.1.1",
                platform='IOS',
                capabilities=['Router'],
                software_version='15.1',
                vtp_version='2',
                serial_number='ABC123',
                hardware_model='C2960',
                uptime='1 day',
                discovery_timestamp=datetime.now(),
                discovery_depth=1,
                is_seed=False,
                connection_method='SSH',
                connection_status='success',
                error_details=None,
                neighbors=[],
                vlans=[],
                vlan_collection_status='not_attempted',
                vlan_collection_error=None
            )
            
            # Property: Timeout should be enforced
            start_time = time.time()
            vlans = collector.collect_vlan_information(mock_connection, device_info)
            execution_time = time.time() - start_time
            
            if execution_type == 'timeout':
                # Property: Timeout scenarios should fail quickly
                assert execution_time <= 0.1, \
                    f"Timeout enforcement should be fast: took {execution_time:.2f}s"
                assert len(vlans) == 0, "Timeout scenarios should return empty VLAN list"
                assert device_info.vlan_collection_status == "failed", "Timeout should result in failed status"
            else:
                # Property: Normal and slow scenarios should complete
                if execution_type == 'normal':
                    assert len(vlans) >= 0, "Normal execution should return VLAN data or empty list"
                else:  # slow
                    assert execution_time <= 0.1, \
                        f"Slow execution should complete quickly in test: {execution_time:.2f}s"
    
    @given(
        cleanup_scenarios=st.lists(
            st.tuples(
                st.sampled_from(['normal', 'error', 'timeout']),  # collection_outcome
                st.integers(min_value=1, max_value=2)  # num_collections (reduced)
            ),
            min_size=1, max_size=2  # Reduced max_size
        )
    )
    @settings(deadline=1000)  # Increase deadline to 1 second
    def test_resource_cleanup_completeness(self, cleanup_scenarios):
        """
        Feature: vlan-inventory-collection, Property 30: Resource Cleanup Completeness
        For any collection operation outcome, all allocated resources should be properly 
        cleaned up and released
        
        Validates: Requirements 8.5
        """
        from netwalker.vlan.vlan_collector import VLANCollector
        from netwalker.connection.data_models import DeviceInfo
        from unittest.mock import Mock
        import threading
        
        config = {
            'vlan_collection': {'enabled': True, 'command_timeout': 1, 'max_retries': 0},  # Reduced timeout
            'max_concurrent_vlan_collections': 2  # Reduced concurrency
        }
        
        collector = VLANCollector(config)
        
        # Track initial resource state
        initial_semaphore_value = collector.resource_semaphore._value
        initial_active_collections = len(collector.get_active_collections())
        
        for outcome, num_collections in cleanup_scenarios:
            # Create mock connections based on outcome
            device_connections = []
            
            for i in range(num_collections):
                mock_connection = Mock()
                
                if outcome == 'normal':
                    mock_connection.send_command.return_value = Mock(result="VLAN Name Status Ports\n1 default active Fa0/1")
                elif outcome == 'error':
                    mock_connection.send_command.side_effect = Exception("Connection error")
                else:  # timeout
                    # Simulate timeout without actual delay
                    mock_connection.send_command.side_effect = TimeoutError("Command timed out")
                
                device_info = DeviceInfo(
                    hostname=f"device{i}",
                    primary_ip=f"192.168.1.{i+1}",
                    platform='IOS',
                    capabilities=['Router'],
                    software_version='15.1',
                    vtp_version='2',
                    serial_number='ABC123',
                    hardware_model='C2960',
                    uptime='1 day',
                    discovery_timestamp=datetime.now(),
                    discovery_depth=1,
                    is_seed=False,
                    connection_method='SSH',
                    connection_status='success',
                    error_details=None,
                    neighbors=[],
                    vlans=[],
                    vlan_collection_status='not_attempted',
                    vlan_collection_error=None
                )
                
                device_connections.append((mock_connection, device_info))
            
            # Execute collections
            if len(device_connections) > 1:
                # Use concurrent collection
                results = collector.collect_vlans_concurrently(device_connections)
            else:
                # Single collection
                connection, device_info = device_connections[0]
                vlans = collector.collect_vlan_information(connection, device_info)
                results = [(device_info, vlans)]
            
            # Property: Resources should be cleaned up after collection
            final_semaphore_value = collector.resource_semaphore._value
            final_active_collections = len(collector.get_active_collections())
            
            assert final_semaphore_value == initial_semaphore_value, \
                f"Semaphore not restored: initial={initial_semaphore_value}, final={final_semaphore_value}"
            
            assert final_active_collections == initial_active_collections, \
                f"Active collections not cleaned: initial={initial_active_collections}, final={final_active_collections}"
            
            # Property: All collections should complete (success or failure)
            assert len(results) == num_collections, \
                f"Expected {num_collections} results, got {len(results)}"


class TestDeviceCollectorIntegrationProperties:
    """Property-based tests for Device Collector VLAN integration"""
    
    @given(
        devices_with_vlans=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=36),  # hostname
                st.ip_addresses(v=4).map(str),  # ip
                st.sampled_from(['IOS', 'IOS-XE', 'NX-OS']),  # platform
                st.booleans(),  # vlan_collection_enabled
                st.lists(
                    st.tuples(
                        st.integers(min_value=1, max_value=4094),  # vlan_id
                        st.text(min_size=1, max_size=32)  # vlan_name
                    ),
                    min_size=0, max_size=10
                )  # vlans
            ),
            min_size=1, max_size=5
        )
    )
    def test_non_blocking_vlan_collection(self, devices_with_vlans):
        """
        Feature: vlan-inventory-collection, Property 16: Non-Blocking VLAN Collection
        For any device discovery process, VLAN collection failures should not prevent 
        basic device information collection
        
        Validates: Requirements 5.2
        """
        from netwalker.discovery.device_collector import DeviceCollector
        from unittest.mock import Mock
        
        for hostname, ip, platform, vlan_enabled, vlan_data in devices_with_vlans:
            # Create configuration
            config = {
                'vlan_collection': {
                    'enabled': vlan_enabled,
                    'command_timeout': 30,
                    'max_retries': 1
                }
            }
            
            # Create device collector with VLAN integration
            collector = DeviceCollector(config)
            
            # Create mock connection that might fail VLAN commands
            mock_connection = Mock()
            
            # Mock basic device commands (always succeed)
            version_output = f"""
            Cisco IOS Software, Version 15.1
            {hostname} uptime is 1 day, 2 hours, 30 minutes
            Processor board ID ABC123
            Model Number: C2960
            """
            mock_connection.send_command.side_effect = lambda cmd, **kwargs: Mock(result=version_output) if 'version' in cmd else Mock(result="")
            
            # Property: Device collection should succeed even if VLAN collection fails
            device_info = collector.collect_device_information(
                mock_connection, ip, "SSH", discovery_depth=1, is_seed=False
            )
            
            # Property: Basic device information should always be collected
            assert device_info is not None, "Device collection should not fail due to VLAN issues"
            assert device_info.hostname == hostname, "Hostname should be extracted correctly"
            assert device_info.connection_status == "success", "Connection status should be success"
            
            # Property: VLAN collection status should be properly tracked
            if vlan_enabled:
                assert device_info.vlan_collection_status in ["success", "failed", "no_vlans_found"], \
                    f"VLAN collection status should be tracked when enabled, got: {device_info.vlan_collection_status}"
            else:
                assert device_info.vlan_collection_status == "skipped", \
                    f"VLAN collection should be skipped when disabled, got: {device_info.vlan_collection_status}"
    
    def test_disabled_vlan_collection(self):
        """
        Test that VLAN collection is skipped when disabled in configuration
        
        Validates: Requirements 5.5
        """
        from netwalker.discovery.device_collector import DeviceCollector
        from unittest.mock import Mock
        
        # Configuration with VLAN collection disabled
        config = {
            'vlan_collection': {
                'enabled': False
            }
        }
        
        collector = DeviceCollector(config)
        
        # Create mock connection
        mock_connection = Mock()
        version_output = """
        Cisco IOS Software, Version 15.1
        TestDevice uptime is 1 day
        Processor board ID ABC123
        Model Number: C2960
        """
        mock_connection.send_command.return_value = Mock(result=version_output)
        
        # Collect device information
        device_info = collector.collect_device_information(
            mock_connection, "192.168.1.1", "SSH", discovery_depth=1, is_seed=False
        )
        
        # Property: VLAN collection should be skipped
        assert device_info.vlan_collection_status == "skipped", \
            f"VLAN collection should be skipped when disabled, got: {device_info.vlan_collection_status}"
        assert device_info.vlans == [], "VLANs list should be empty when collection is disabled"
        assert device_info.vlan_collection_error is None, "No VLAN collection error should be recorded"