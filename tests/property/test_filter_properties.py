"""
Property-based tests for FilterManager

Tests universal properties of filtering and boundary management functionality.
"""

import pytest
from hypothesis import given, strategies as st, assume
import ipaddress
from netwalker.filtering.filter_manager import FilterManager, FilterCriteria


class TestFilterProperties:
    """Property-based tests for FilterManager functionality"""
    
    @given(
        hostname=st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
        ip_address=st.ip_addresses(v=4).map(str),
        patterns=st.lists(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Pc'))), 
                         min_size=1, max_size=5)
    )
    def test_wildcard_name_filtering_property(self, hostname, ip_address, patterns):
        """
        Property 11: Wildcard Name Filtering
        
        For any hostname and wildcard patterns, if a hostname matches any pattern,
        it should be filtered consistently.
        """
        # Create config with test patterns
        config = {
            'hostname_excludes': patterns,
            'ip_excludes': [],
            'platform_excludes': [],
            'capability_excludes': []
        }
        
        filter_manager = FilterManager(config)
        
        # Test filtering decision consistency
        result1 = filter_manager.should_filter_device(hostname, ip_address)
        result2 = filter_manager.should_filter_device(hostname, ip_address)
        
        # Property: Filtering decision should be consistent
        assert result1 == result2, "Filtering decision should be consistent for same input"
        
        # Property: If filtered, device should be in filtered set
        if result1:
            device_key = f"{hostname}:{ip_address}"
            assert device_key in filter_manager.get_filtered_devices()
    
    @given(
        ip_address=st.ip_addresses(v=4),
        cidr_ranges=st.lists(
            st.tuples(
                st.ip_addresses(v=4),
                st.integers(min_value=8, max_value=30)
            ).map(lambda x: f"{x[0]}/{x[1]}"),
            min_size=1, max_size=3
        )
    )
    def test_cidr_range_filtering_property(self, ip_address, cidr_ranges):
        """
        Property 12: CIDR Range Filtering
        
        For any IP address and CIDR ranges, if an IP falls within any range,
        it should be filtered consistently.
        """
        hostname = "test-device"
        ip_str = str(ip_address)
        
        config = {
            'hostname_excludes': [],
            'ip_excludes': cidr_ranges,
            'platform_excludes': [],
            'capability_excludes': []
        }
        
        filter_manager = FilterManager(config)
        
        # Test filtering decision
        result = filter_manager.should_filter_device(hostname, ip_str)
        
        # Verify if IP should be in any range
        should_be_filtered = False
        for cidr_range in cidr_ranges:
            try:
                network = ipaddress.ip_network(cidr_range, strict=False)
                if ip_address in network:
                    should_be_filtered = True
                    break
            except (ipaddress.AddressValueError, ValueError):
                continue
        
        # Property: Filtering result should match manual calculation
        if should_be_filtered:
            assert result, f"IP {ip_str} should be filtered by ranges {cidr_ranges}"
    
    @given(
        hostname=st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
        ip_address=st.ip_addresses(v=4).map(str),
        platform=st.one_of(st.none(), st.sampled_from(['IOS', 'IOS-XE', 'NX-OS', 'linux', 'windows', 'unix'])),
        capabilities=st.one_of(st.none(), st.lists(st.sampled_from(['Switch', 'Router', 'Host', 'Phone', 'Camera']), 
                                                  min_size=1, max_size=3))
    )
    def test_filter_boundary_behavior_property(self, hostname, ip_address, platform, capabilities):
        """
        Property 13: Filter Boundary Behavior
        
        Filtered devices should be recorded but not used for further discovery.
        Boundary marking should be persistent and queryable.
        """
        config = {
            'hostname_excludes': ['TEST*'],
            'ip_excludes': ['192.168.1.0/24'],
            'platform_excludes': ['linux'],
            'capability_excludes': ['host']
        }
        
        filter_manager = FilterManager(config)
        
        # Test filtering
        is_filtered = filter_manager.should_filter_device(hostname, ip_address, platform, capabilities)
        
        # Property: Filtered devices should be recorded
        if is_filtered:
            device_key = f"{hostname}:{ip_address}"
            assert device_key in filter_manager.get_filtered_devices()
        
        # Test boundary marking
        reason = "Test boundary"
        filter_manager.mark_as_boundary(hostname, ip_address, reason)
        
        # Property: Boundary devices should be queryable
        assert filter_manager.is_boundary_device(hostname, ip_address)
        
        device_key = f"{hostname}:{ip_address}"
        assert device_key in filter_manager.get_boundary_devices()
    
    @given(
        devices=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
                st.ip_addresses(v=4).map(str)
            ),
            min_size=1, max_size=10,
            unique=True
        )
    )
    def test_filter_statistics_consistency_property(self, devices):
        """
        Property: Filter statistics should be consistent with actual filtering operations
        """
        config = {
            'hostname_excludes': ['FILTER*'],
            'ip_excludes': ['10.0.0.0/8'],
            'platform_excludes': [],
            'capability_excludes': []
        }
        
        filter_manager = FilterManager(config)
        
        filtered_count = 0
        boundary_count = 0
        
        for hostname, ip_address in devices:
            # Test filtering
            if filter_manager.should_filter_device(hostname, ip_address):
                filtered_count += 1
            
            # Mark some as boundary
            if hostname.startswith('B'):
                filter_manager.mark_as_boundary(hostname, ip_address, "Test")
                boundary_count += 1
        
        stats = filter_manager.get_filter_stats()
        
        # Property: Statistics should match actual operations
        assert stats['filtered_devices'] == filtered_count
        assert stats['boundary_devices'] == boundary_count
        assert stats['hostname_patterns'] == len(config['hostname_excludes'])
        assert stats['ip_ranges'] == len(config['ip_excludes'])
    
    @given(
        hostname=st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        ip_address=st.ip_addresses(v=4).map(str)
    )
    def test_case_insensitive_filtering_property(self, hostname, ip_address):
        """
        Property: Hostname filtering should be case-insensitive
        """
        config = {
            'hostname_excludes': ['TEST*'],
            'ip_excludes': [],
            'platform_excludes': [],
            'capability_excludes': []
        }
        
        filter_manager = FilterManager(config)
        
        # Test with different cases
        hostname_upper = hostname.upper()
        hostname_lower = hostname.lower()
        
        result_upper = filter_manager.should_filter_device(hostname_upper, ip_address)
        result_lower = filter_manager.should_filter_device(hostname_lower, ip_address)
        
        # Property: Case should not affect filtering decision for same hostname
        if hostname_upper.startswith('TEST') or hostname_lower.startswith('test'):
            assert result_upper == result_lower == True
    
    def test_empty_filter_criteria_property(self):
        """
        Property: Empty filter criteria should not filter any devices
        """
        config = {
            'hostname_excludes': [],
            'ip_excludes': [],
            'platform_excludes': [],
            'capability_excludes': []
        }
        
        filter_manager = FilterManager(config)
        
        # Test various devices
        test_cases = [
            ("DEVICE1", "192.168.1.1", "IOS", ["Switch"]),
            ("DEVICE2", "10.0.0.1", "NX-OS", ["Router"]),
            ("HOST1", "172.16.1.1", "linux", ["Host"])
        ]
        
        for hostname, ip, platform, capabilities in test_cases:
            result = filter_manager.should_filter_device(hostname, ip, platform, capabilities)
            # Property: No devices should be filtered with empty criteria
            assert not result, f"Device {hostname} should not be filtered with empty criteria"


class TestFilterCriteriaProperties:
    """Property-based tests for FilterCriteria data class"""
    
    @given(
        hostname_excludes=st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5),
        platform_excludes=st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5),
        capability_excludes=st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5)
    )
    def test_criteria_normalization_property(self, hostname_excludes, platform_excludes, capability_excludes):
        """
        Property: FilterCriteria should normalize all string criteria to lowercase
        """
        criteria = FilterCriteria(
            hostname_excludes=hostname_excludes,
            ip_excludes=['192.168.1.0/24'],  # IP excludes don't get normalized
            platform_excludes=platform_excludes,
            capability_excludes=capability_excludes
        )
        
        # Property: All hostname excludes should be lowercase
        for pattern in criteria.hostname_excludes:
            assert pattern == pattern.lower(), f"Hostname pattern {pattern} should be lowercase"
        
        # Property: All platform excludes should be lowercase
        for platform in criteria.platform_excludes:
            assert platform == platform.lower(), f"Platform {platform} should be lowercase"
        
        # Property: All capability excludes should be lowercase
        for capability in criteria.capability_excludes:
            assert capability == capability.lower(), f"Capability {capability} should be lowercase"