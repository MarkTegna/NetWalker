"""
Property-based tests for Site Queue Management

Tests universal properties of site-specific device queue functionality.
"""

import pytest
from hypothesis import given, strategies as st, assume
from unittest.mock import Mock
from datetime import datetime

from netwalker.discovery.site_queue_manager import SiteQueueManager
from netwalker.discovery.discovery_engine import DiscoveryNode


class TestSiteQueueManagerProperties:
    """Property-based tests for SiteQueueManager functionality"""
    
    def create_discovery_node(self, hostname: str, ip_address: str, depth: int = 0) -> DiscoveryNode:
        """Create a DiscoveryNode for testing"""
        return DiscoveryNode(
            hostname=hostname,
            ip_address=ip_address,
            depth=depth,
            parent_device=None,
            discovery_method="test",
            is_seed=False
        )
    
    @given(
        site1_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
        site2_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
        devices=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
                st.ip_addresses(v=4).map(str),
                st.integers(min_value=0, max_value=3)
            ),
            min_size=1, max_size=20,
            unique_by=lambda x: f"{x[0]}:{x[1]}"  # Unique by hostname:ip
        )
    )
    def test_site_queue_isolation_property(self, site1_name, site2_name, devices):
        """
        Property 1: Site Queue Isolation
        
        For any two different sites, devices added to one site's queue should 
        never appear in another site's queue.
        
        **Feature: site-specific-device-collection-reporting, Property 1: Site Queue Isolation**
        **Validates: Requirements 5.2**
        """
        # Ensure sites are different
        assume(site1_name != site2_name)
        assume(len(devices) >= 2)  # Need at least 2 devices to test isolation
        
        manager = SiteQueueManager()
        
        # Split devices between two sites
        site1_devices = devices[:len(devices)//2]
        site2_devices = devices[len(devices)//2:]
        
        # Add devices to site1
        site1_device_keys = set()
        for hostname, ip_address, depth in site1_devices:
            device_node = self.create_discovery_node(hostname, ip_address, depth)
            manager.add_device_to_site(site1_name, device_node)
            site1_device_keys.add(device_node.device_key)
        
        # Add devices to site2
        site2_device_keys = set()
        for hostname, ip_address, depth in site2_devices:
            device_node = self.create_discovery_node(hostname, ip_address, depth)
            manager.add_device_to_site(site2_name, device_node)
            site2_device_keys.add(device_node.device_key)
        
        # Verify isolation: devices from site1 should not appear in site2 queue
        site2_retrieved_keys = set()
        while not manager.is_site_queue_empty(site2_name):
            device = manager.get_next_device(site2_name)
            if device:
                site2_retrieved_keys.add(device.device_key)
        
        # Property: No device from site1 should appear in site2's queue
        assert site1_device_keys.isdisjoint(site2_retrieved_keys), \
            f"Site isolation violated: {site1_device_keys & site2_retrieved_keys} appeared in both sites"
        
        # Verify site2 devices were correctly retrieved
        assert site2_device_keys == site2_retrieved_keys, \
            f"Site2 devices mismatch: expected {site2_device_keys}, got {site2_retrieved_keys}"
    
    @given(
        site_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
        devices=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
                st.ip_addresses(v=4).map(str),
                st.integers(min_value=0, max_value=3)
            ),
            min_size=1, max_size=15,
            unique_by=lambda x: f"{x[0]}:{x[1]}"  # Unique by hostname:ip
        )
    )
    def test_site_queue_deduplication_property(self, site_name, devices):
        """
        Property 9: Site Queue Deduplication
        
        For any site queue, the same device should not appear multiple times 
        in the queue, even if added multiple times.
        
        **Feature: site-specific-device-collection-reporting, Property 9: Site Queue Deduplication**
        **Validates: Requirements 5.1**
        """
        manager = SiteQueueManager()
        
        # Add each device multiple times (2-4 times each)
        device_nodes = []
        expected_unique_keys = set()
        
        for hostname, ip_address, depth in devices:
            device_node = self.create_discovery_node(hostname, ip_address, depth)
            device_nodes.append(device_node)
            expected_unique_keys.add(device_node.device_key)
            
            # Add the same device multiple times
            add_count = 0
            for _ in range(3):  # Try to add 3 times
                result = manager.add_device_to_site(site_name, device_node)
                if result:  # Only count successful additions
                    add_count += 1
            
            # Property: Only the first addition should succeed
            assert add_count == 1, f"Device {device_node.device_key} was added {add_count} times, expected 1"
        
        # Verify queue contains exactly one instance of each unique device
        retrieved_keys = set()
        retrieved_count = 0
        
        while not manager.is_site_queue_empty(site_name):
            device = manager.get_next_device(site_name)
            if device:
                retrieved_count += 1
                assert device.device_key not in retrieved_keys, \
                    f"Duplicate device {device.device_key} found in queue"
                retrieved_keys.add(device.device_key)
        
        # Property: Retrieved devices should match exactly the unique devices added
        assert retrieved_keys == expected_unique_keys, \
            f"Queue deduplication failed: expected {expected_unique_keys}, got {retrieved_keys}"
        
        # Property: Queue size should equal number of unique devices
        assert retrieved_count == len(expected_unique_keys), \
            f"Queue size mismatch: expected {len(expected_unique_keys)}, got {retrieved_count}"
    
    @given(
        site_names=st.lists(
            st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
            min_size=2, max_size=5, unique=True
        ),
        devices_per_site=st.integers(min_value=1, max_value=10)
    )
    def test_multiple_site_isolation_property(self, site_names, devices_per_site):
        """
        Property: Multiple Site Isolation
        
        For any number of sites, devices added to each site should remain 
        isolated from all other sites.
        
        **Feature: site-specific-device-collection-reporting, Property 1: Site Queue Isolation (Extended)**
        **Validates: Requirements 5.2**
        """
        manager = SiteQueueManager()
        site_device_mappings = {}
        
        # Create unique devices for each site
        device_counter = 0
        for site_name in site_names:
            site_devices = []
            for i in range(devices_per_site):
                hostname = f"device{device_counter}"
                ip_address = f"192.168.{device_counter // 254}.{(device_counter % 254) + 1}"
                device_node = self.create_discovery_node(hostname, ip_address, 0)
                site_devices.append(device_node)
                manager.add_device_to_site(site_name, device_node)
                device_counter += 1
            
            site_device_mappings[site_name] = {d.device_key for d in site_devices}
        
        # Retrieve devices from each site and verify isolation
        for site_name in site_names:
            retrieved_keys = set()
            while not manager.is_site_queue_empty(site_name):
                device = manager.get_next_device(site_name)
                if device:
                    retrieved_keys.add(device.device_key)
            
            # Property: Retrieved devices should match exactly what was added to this site
            expected_keys = site_device_mappings[site_name]
            assert retrieved_keys == expected_keys, \
                f"Site {site_name} isolation failed: expected {expected_keys}, got {retrieved_keys}"
            
            # Property: No device from this site should appear in any other site
            for other_site_name, other_site_devices in site_device_mappings.items():
                if other_site_name != site_name:
                    assert retrieved_keys.isdisjoint(other_site_devices), \
                        f"Cross-site contamination: {retrieved_keys & other_site_devices} appeared in both {site_name} and {other_site_name}"
    
    @given(
        site_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
        device_count=st.integers(min_value=0, max_value=20)
    )
    def test_queue_size_consistency_property(self, site_name, device_count):
        """
        Property: Queue Size Consistency
        
        For any site queue, the reported queue size should always match 
        the actual number of devices that can be retrieved.
        
        **Feature: site-specific-device-collection-reporting, Property: Queue Size Consistency**
        **Validates: Requirements 5.2, 5.4**
        """
        manager = SiteQueueManager()
        
        # Add specified number of unique devices
        added_devices = []
        for i in range(device_count):
            hostname = f"device{i}"
            ip_address = f"192.168.1.{i + 1}"
            device_node = self.create_discovery_node(hostname, ip_address, 0)
            added_devices.append(device_node)
            manager.add_device_to_site(site_name, device_node)
        
        # Property: Queue size should match number of added devices
        reported_size = manager.get_site_queue_size(site_name)
        assert reported_size == device_count, \
            f"Queue size mismatch after adding: expected {device_count}, got {reported_size}"
        
        # Property: Empty check should be consistent with size
        is_empty = manager.is_site_queue_empty(site_name)
        assert is_empty == (device_count == 0), \
            f"Empty check inconsistent: size={device_count}, is_empty={is_empty}"
        
        # Retrieve devices and verify size decreases correctly
        retrieved_count = 0
        while not manager.is_site_queue_empty(site_name):
            device = manager.get_next_device(site_name)
            if device:
                retrieved_count += 1
                current_size = manager.get_site_queue_size(site_name)
                expected_remaining = device_count - retrieved_count
                
                # Property: Size should decrease by 1 after each retrieval
                assert current_size == expected_remaining, \
                    f"Queue size inconsistent during retrieval: expected {expected_remaining}, got {current_size}"
        
        # Property: Final size should be 0 and queue should be empty
        final_size = manager.get_site_queue_size(site_name)
        assert final_size == 0, f"Final queue size should be 0, got {final_size}"
        assert manager.is_site_queue_empty(site_name), "Queue should be empty after retrieving all devices"
        assert retrieved_count == device_count, f"Retrieved count mismatch: expected {device_count}, got {retrieved_count}"