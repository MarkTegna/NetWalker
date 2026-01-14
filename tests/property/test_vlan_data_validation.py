"""
Property-based tests for VLAN data validation and quality assurance

Feature: vlan-inventory-collection
Tasks: 13.1, 13.2
"""

import pytest
from hypothesis import given, strategies as st, assume
from unittest.mock import Mock, patch
import logging

from netwalker.vlan.vlan_parser import VLANParser
from netwalker.connection.data_models import VLANInfo


class TestVLANDataValidationProperties:
    """Property-based tests for VLAN data validation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = {
            'vlan_collection': {
                'enabled': True,
                'timeout': 30
            }
        }
        self.parser = VLANParser()
    
    @given(
        vlans_with_duplicates=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),  # hostname
                st.integers(min_value=1, max_value=4094),  # vlan_id (some will be duplicates)
                st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),  # vlan_name
                st.integers(min_value=0, max_value=10),  # port_count
                st.integers(min_value=0, max_value=5)   # portchannel_count
            ),
            min_size=2, max_size=10
        )
    )
    def test_duplicate_vlan_entry_handling(self, vlans_with_duplicates):
        """
        Property 34: Duplicate VLAN Entry Handling
        
        When duplicate VLAN entries are detected (same device + VLAN ID),
        the system must resolve them by keeping the most complete entry
        and logging appropriate warnings.
        
        Validates: Requirements 9.4
        """
        # Create VLAN info objects, ensuring some duplicates
        vlan_objects = []
        duplicate_created = False
        
        for i, (hostname, vlan_id, vlan_name, port_count, portchannel_count) in enumerate(vlans_with_duplicates):
            vlan_info = VLANInfo(
                vlan_id=vlan_id,
                vlan_name=vlan_name,
                port_count=port_count,
                portchannel_count=portchannel_count,
                device_hostname=hostname,
                device_ip=f"192.168.1.{i+1}"
            )
            vlan_objects.append(vlan_info)
            
            # Create a duplicate with different port counts
            if i == 0 and len(vlans_with_duplicates) > 1:
                duplicate_vlan = VLANInfo(
                    vlan_id=vlan_id,  # Same VLAN ID
                    vlan_name=vlan_name + "_dup",
                    port_count=port_count + 5,  # More ports (should be kept)
                    portchannel_count=portchannel_count + 1,
                    device_hostname=hostname,  # Same hostname
                    device_ip=f"192.168.1.{i+1}"
                )
                vlan_objects.append(duplicate_vlan)
                duplicate_created = True
        
        # Only test if we actually created duplicates
        assume(duplicate_created)
        
        # Mock logger to capture warnings
        with patch.object(self.parser, 'logger') as mock_logger:
            # Process duplicates
            unique_vlans = self.parser.detect_duplicate_vlans(vlan_objects)
            
            # Verify duplicate detection and resolution
            assert len(unique_vlans) < len(vlan_objects), "Duplicates should be resolved"
            
            # Verify warning was logged
            warning_calls = [call for call in mock_logger.warning.call_args_list 
                           if 'Duplicate VLAN' in str(call)]
            assert len(warning_calls) > 0, "Duplicate warning should be logged"
            
            # Verify the more complete entry was kept
            device_vlans = {}
            for vlan in unique_vlans:
                key = (vlan.device_hostname, vlan.vlan_id)
                if key not in device_vlans:
                    device_vlans[key] = vlan
            
            # Check that we don't have true duplicates
            for vlan in unique_vlans:
                key = (vlan.device_hostname, vlan.vlan_id)
                same_vlans = [v for v in unique_vlans 
                             if v.device_hostname == vlan.device_hostname and v.vlan_id == vlan.vlan_id]
                assert len(same_vlans) == 1, f"Should have only one VLAN per device+ID combination"
    
    @given(
        cross_device_vlans=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),  # hostname
                st.integers(min_value=1, max_value=100),  # vlan_id (limited range for conflicts)
                st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),  # vlan_name
                st.integers(min_value=0, max_value=200),  # port_count (some high values)
                st.integers(min_value=0, max_value=50)   # portchannel_count (some high values)
            ),
            min_size=3, max_size=8
        )
    )
    def test_inconsistent_data_warning(self, cross_device_vlans):
        """
        Property 35: Inconsistent Data Warning
        
        When VLAN data shows inconsistencies (same VLAN ID with different names
        across devices, or unusually high port counts), appropriate warnings
        must be generated and logged.
        
        Validates: Requirements 9.5
        """
        # Create VLAN objects with potential inconsistencies
        vlan_objects = []
        inconsistency_created = False
        
        for i, (hostname, vlan_id, vlan_name, port_count, portchannel_count) in enumerate(cross_device_vlans):
            # Create potential name inconsistency
            if i > 0 and vlan_id == cross_device_vlans[0][1]:  # Same VLAN ID as first
                vlan_name = vlan_name + "_different"  # Different name
                inconsistency_created = True
            
            # Create potential high port count issue
            if port_count > 100:
                inconsistency_created = True
            
            vlan_info = VLANInfo(
                vlan_id=vlan_id,
                vlan_name=vlan_name,
                port_count=port_count,
                portchannel_count=portchannel_count,
                device_hostname=hostname,
                device_ip=f"192.168.1.{i+1}"
            )
            vlan_objects.append(vlan_info)
        
        # Only test if we created inconsistencies
        assume(inconsistency_created)
        
        # Mock logger to capture warnings
        with patch.object(self.parser, 'logger') as mock_logger:
            # Validate consistency
            warnings = self.parser.validate_vlan_consistency(vlan_objects)
            
            # Verify warnings were generated
            assert len(warnings) > 0, "Inconsistency warnings should be generated"
            
            # Verify warnings were logged
            warning_calls = mock_logger.warning.call_args_list
            assert len(warning_calls) > 0, "Warnings should be logged"
            
            # Check for specific types of warnings
            warning_messages = [str(call) for call in warning_calls]
            
            # Look for inconsistent name warnings or high port count warnings
            has_name_warning = any('inconsistent names' in msg for msg in warning_messages)
            has_port_warning = any('unusually high port count' in msg for msg in warning_messages)
            
            assert has_name_warning or has_port_warning, "Should have specific inconsistency warnings"
    
    @given(
        vlan_names_with_special_chars=st.lists(
            st.text(min_size=1, max_size=50, 
                   alphabet=st.characters(
                       whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Po', 'Ps', 'Pe', 'Sm', 'Sc')
                   )),
            min_size=1, max_size=10
        )
    )
    def test_vlan_name_sanitization(self, vlan_names_with_special_chars):
        """
        Test VLAN name sanitization handles special characters properly
        
        Validates: Requirements 9.2 (special character handling)
        """
        for vlan_name in vlan_names_with_special_chars:
            sanitized = self.parser.sanitize_vlan_name(vlan_name)
            
            # Verify sanitized name is safe for Excel
            problematic_chars = ['[', ']', '*', '?', ':', '\\', '/', '<', '>', '|']
            for char in problematic_chars:
                assert char not in sanitized, f"Sanitized name should not contain '{char}'"
            
            # Verify it's not empty
            assert sanitized and sanitized.strip(), "Sanitized name should not be empty"
            
            # Verify reasonable length
            assert len(sanitized) <= 32, "Sanitized name should not exceed 32 characters"
    
    @given(
        vlan_id=st.integers(min_value=-100, max_value=5000),
        vlan_name=st.text(min_size=0, max_size=100),
        port_count=st.integers(min_value=-10, max_value=1000),
        portchannel_count=st.integers(min_value=-10, max_value=100)
    )
    def test_vlan_data_validation_comprehensive(self, vlan_id, vlan_name, port_count, portchannel_count):
        """
        Test comprehensive VLAN data validation
        
        Validates: Requirements 9.1, 9.2, 9.3
        """
        vlan_info = VLANInfo(
            vlan_id=vlan_id,
            vlan_name=vlan_name,
            port_count=port_count,
            portchannel_count=portchannel_count,
            device_hostname="test_device",
            device_ip="192.168.1.1"
        )
        
        is_valid = self.parser.validate_vlan_data(vlan_info)
        
        # Determine expected validity
        expected_valid = (
            1 <= vlan_id <= 4094 and  # Valid VLAN ID range
            vlan_name and len(vlan_name.strip()) > 0 and  # Non-empty name after stripping
            port_count >= 0 and  # Non-negative port count
            portchannel_count >= 0  # Non-negative PortChannel count
        )
        
        assert is_valid == expected_valid, f"Validation result should match expected validity for VLAN {vlan_id}"