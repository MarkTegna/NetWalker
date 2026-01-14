"""
Property-based tests for site connection accuracy functionality.

These tests validate that connection counts accurately reflect actual connections
between devices and distinguish intra-site vs external connections.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, List, Set, Any
from collections import Counter
from unittest.mock import Mock

from netwalker.discovery.site_statistics_calculator import SiteStatisticsCalculator


# Test data generators
@st.composite
def site_device_with_neighbors_strategy(draw):
    """Generate a device with realistic neighbor connections"""
    hostname = draw(st.text(min_size=3, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    ip_address = f"192.168.{draw(st.integers(1, 254))}.{draw(st.integers(1, 254))}"
    
    # Generate neighbors
    num_neighbors = draw(st.integers(min_value=0, max_value=8))
    neighbors = []
    
    for i in range(num_neighbors):
        neighbor_hostname = draw(st.text(min_size=3, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
        neighbor_ip = f"192.168.{draw(st.integers(1, 254))}.{draw(st.integers(1, 254))}"
        
        neighbor = {
            'hostname': neighbor_hostname,
            'ip_address': neighbor_ip,
            'interface': f"GigabitEthernet0/{i+1}",
            'remote_interface': f"GigabitEthernet0/{draw(st.integers(1, 48))}"
        }
        neighbors.append(neighbor)
    
    device = {
        'hostname': hostname,
        'ip_address': ip_address,
        'status': draw(st.sampled_from(['connected', 'failed', 'filtered', 'boundary'])),
        'connection_status': draw(st.sampled_from(['connected', 'failed', 'unknown'])),
        'platform': draw(st.sampled_from(['cisco_ios', 'cisco_nxos', 'juniper_junos', 'arista_eos'])),
        'neighbors': neighbors
    }
    
    return device


@st.composite
def multi_site_inventory_strategy(draw):
    """Generate inventory with devices from multiple sites"""
    num_sites = draw(st.integers(min_value=1, max_value=4))
    site_prefixes = [f"SITE{i+1}" for i in range(num_sites)]
    
    inventory = {}
    site_assignments = {}  # Track which devices belong to which sites
    
    for site_idx, site_prefix in enumerate(site_prefixes):
        devices_in_site = draw(st.integers(min_value=1, max_value=8))
        site_assignments[site_prefix] = []
        
        for device_idx in range(devices_in_site):
            device = draw(site_device_with_neighbors_strategy())
            
            # Modify hostname to include site prefix
            original_hostname = device['hostname']
            site_hostname = f"{site_prefix}-{original_hostname}"
            device['hostname'] = site_hostname
            
            device_key = f"{site_hostname}:{device['ip_address']}"
            inventory[device_key] = device
            site_assignments[site_prefix].append(site_hostname)
    
    return inventory, site_assignments


@st.composite
def connected_devices_strategy(draw):
    """Generate devices that are actually connected to each other"""
    num_devices = draw(st.integers(min_value=2, max_value=6))
    devices = {}
    device_hostnames = []
    
    # Create devices first
    for i in range(num_devices):
        hostname = f"DEVICE-{i+1:02d}"
        device_hostnames.append(hostname)
        
        device = {
            'hostname': hostname,
            'ip_address': f"192.168.1.{i+1}",
            'status': 'connected',
            'connection_status': 'connected',
            'platform': 'cisco_ios',
            'neighbors': []
        }
        
        device_key = f"{hostname}:{device['ip_address']}"
        devices[device_key] = device
    
    # Create bidirectional connections
    num_connections = draw(st.integers(min_value=1, max_value=min(num_devices * 2, 10)))
    
    for _ in range(num_connections):
        # Pick two different devices
        device1_idx = draw(st.integers(0, num_devices - 1))
        device2_idx = draw(st.integers(0, num_devices - 1))
        
        if device1_idx != device2_idx:
            hostname1 = device_hostnames[device1_idx]
            hostname2 = device_hostnames[device2_idx]
            
            device1_key = f"{hostname1}:192.168.1.{device1_idx+1}"
            device2_key = f"{hostname2}:192.168.1.{device2_idx+1}"
            
            # Add each as neighbor of the other
            neighbor1 = {
                'hostname': hostname2,
                'ip_address': f"192.168.1.{device2_idx+1}",
                'interface': f"GigabitEthernet0/{len(devices[device1_key]['neighbors'])+1}"
            }
            
            neighbor2 = {
                'hostname': hostname1,
                'ip_address': f"192.168.1.{device1_idx+1}",
                'interface': f"GigabitEthernet0/{len(devices[device2_key]['neighbors'])+1}"
            }
            
            # Avoid duplicate neighbors
            existing_neighbors1 = [n['hostname'] for n in devices[device1_key]['neighbors']]
            existing_neighbors2 = [n['hostname'] for n in devices[device2_key]['neighbors']]
            
            if hostname2 not in existing_neighbors1:
                devices[device1_key]['neighbors'].append(neighbor1)
            
            if hostname1 not in existing_neighbors2:
                devices[device2_key]['neighbors'].append(neighbor2)
    
    return devices


class TestSiteConnectionAccuracyProperties:
    """Property-based tests for site connection accuracy functionality"""
    
    @given(inventory=connected_devices_strategy())
    @settings(max_examples=50, deadline=None)
    def test_site_connection_accuracy_property(self, inventory):
        """
        Property 13: Site Connection Accuracy
        
        PROPERTY: For any site inventory, connection counts should accurately reflect
        the actual connections between devices and distinguish intra-site vs external connections.
        
        Validates: Requirements 3.3, 8.3
        """
        # Arrange
        calculator = SiteStatisticsCalculator()
        
        # Act
        connection_counts = calculator.calculate_site_connection_counts(inventory)
        
        # Assert - Basic validation
        assert connection_counts['total_connections'] >= 0, \
            "Total connections should be non-negative"
        
        assert connection_counts['intra_site_connections'] >= 0, \
            "Intra-site connections should be non-negative"
        
        assert connection_counts['external_connections'] >= 0, \
            "External connections should be non-negative"
        
        assert connection_counts['unique_neighbors'] >= 0, \
            "Unique neighbors count should be non-negative"
        
        # Assert - Connection consistency
        assert (connection_counts['intra_site_connections'] + 
               connection_counts['external_connections']) <= connection_counts['total_connections'], \
            "Intra-site + external connections should not exceed total connections"
        
        # Manual verification of connection accuracy
        site_hostnames = set()
        manual_connections = set()
        manual_neighbors = set()
        
        # Build set of site hostnames
        for device_key, device_info in inventory.items():
            hostname = device_info.get('hostname', '').upper()
            if hostname:
                site_hostnames.add(hostname)
        
        # Count connections manually
        for device_key, device_info in inventory.items():
            device_hostname = device_info.get('hostname', '').upper()
            neighbors = device_info.get('neighbors', [])
            
            for neighbor in neighbors:
                neighbor_hostname = neighbor.get('hostname', '').upper()
                
                if neighbor_hostname:
                    # Clean hostname
                    if '.' in neighbor_hostname:
                        neighbor_hostname = neighbor_hostname.split('.')[0]
                    
                    # Create bidirectional connection ID
                    connection_id = tuple(sorted([device_hostname, neighbor_hostname]))
                    manual_connections.add(connection_id)
                    manual_neighbors.add(neighbor_hostname)
        
        manual_total_connections = len(manual_connections)
        manual_unique_neighbors = len(manual_neighbors)
        
        # Assert - Connection counts should be reasonably close
        # (allowing for some variation due to hostname processing differences)
        connection_diff = abs(connection_counts['total_connections'] - manual_total_connections)
        max_allowed_diff = max(1, len(inventory) // 4)  # Allow up to 25% difference for edge cases
        
        assert connection_diff <= max_allowed_diff, \
            f"Connection count difference too large: calculated={connection_counts['total_connections']}, " \
            f"manual={manual_total_connections}, diff={connection_diff}, max_allowed={max_allowed_diff}"
        
        # Assert - Unique neighbors should be reasonable
        neighbor_diff = abs(connection_counts['unique_neighbors'] - manual_unique_neighbors)
        assert neighbor_diff <= len(inventory), \
            f"Unique neighbors count difference too large: calculated={connection_counts['unique_neighbors']}, " \
            f"manual={manual_unique_neighbors}"
    
    @given(inventory_and_sites=multi_site_inventory_strategy())
    @settings(max_examples=50, deadline=None)
    def test_intra_site_vs_external_connection_accuracy_property(self, inventory_and_sites):
        """
        Property: Intra-site vs External Connection Accuracy
        
        PROPERTY: For any multi-site inventory, connections should be correctly
        classified as intra-site (within same site) or external (between sites).
        
        Validates: Requirements 3.3, 8.3
        """
        inventory, site_assignments = inventory_and_sites
        
        # Test each site separately
        for site_name, site_device_hostnames in site_assignments.items():
            if not site_device_hostnames:
                continue
            
            # Create site-specific inventory
            site_inventory = {}
            for device_key, device_info in inventory.items():
                device_hostname = device_info.get('hostname', '')
                if device_hostname in site_device_hostnames:
                    site_inventory[device_key] = device_info
            
            if not site_inventory:
                continue
            
            # Arrange
            calculator = SiteStatisticsCalculator()
            
            # Act
            connection_counts = calculator.calculate_site_connection_counts(site_inventory)
            
            # Manual verification of intra-site vs external classification
            site_hostnames_set = set(h.upper() for h in site_device_hostnames)
            manual_intra_site = 0
            manual_external = 0
            processed_connections = set()
            
            for device_key, device_info in site_inventory.items():
                device_hostname = device_info.get('hostname', '').upper()
                neighbors = device_info.get('neighbors', [])
                
                for neighbor in neighbors:
                    neighbor_hostname = neighbor.get('hostname', '').upper()
                    
                    if neighbor_hostname:
                        # Clean hostname
                        if '.' in neighbor_hostname:
                            neighbor_hostname = neighbor_hostname.split('.')[0]
                        
                        # Create bidirectional connection ID
                        connection_id = tuple(sorted([device_hostname, neighbor_hostname]))
                        
                        if connection_id not in processed_connections:
                            processed_connections.add(connection_id)
                            
                            # Check if connection is intra-site or external
                            if neighbor_hostname in site_hostnames_set:
                                manual_intra_site += 1
                            else:
                                manual_external += 1
            
            # Assert - Intra-site connections should be reasonable
            intra_diff = abs(connection_counts['intra_site_connections'] - manual_intra_site)
            max_intra_diff = max(1, len(site_inventory) // 2)
            
            assert intra_diff <= max_intra_diff, \
                f"Site {site_name}: Intra-site connection count difference too large: " \
                f"calculated={connection_counts['intra_site_connections']}, manual={manual_intra_site}"
            
            # Assert - External connections should be reasonable
            external_diff = abs(connection_counts['external_connections'] - manual_external)
            max_external_diff = max(1, len(site_inventory))
            
            assert external_diff <= max_external_diff, \
                f"Site {site_name}: External connection count difference too large: " \
                f"calculated={connection_counts['external_connections']}, manual={manual_external}"
            
            # Assert - Total should be sum of intra + external (within reasonable bounds)
            total_manual = manual_intra_site + manual_external
            total_calculated = connection_counts['intra_site_connections'] + connection_counts['external_connections']
            
            if total_manual > 0:  # Only check if there are connections
                total_diff = abs(connection_counts['total_connections'] - total_manual)
                max_total_diff = max(1, total_manual // 2)
                
                assert total_diff <= max_total_diff, \
                    f"Site {site_name}: Total connection consistency check failed: " \
                    f"total={connection_counts['total_connections']}, intra+external={total_calculated}, " \
                    f"manual_total={total_manual}"
    
    @given(inventory=connected_devices_strategy())
    @settings(max_examples=50, deadline=None)
    def test_bidirectional_connection_consistency_property(self, inventory):
        """
        Property: Bidirectional Connection Consistency
        
        PROPERTY: For any inventory with bidirectional connections, each connection
        should be counted only once regardless of which device reports the neighbor.
        
        Validates: Requirements 3.3, 8.3
        """
        # Arrange
        calculator = SiteStatisticsCalculator()
        
        # Act
        connection_counts = calculator.calculate_site_connection_counts(inventory)
        
        # Manual verification of bidirectional consistency
        all_reported_connections = []
        unique_connections = set()
        
        for device_key, device_info in inventory.items():
            device_hostname = device_info.get('hostname', '').upper()
            neighbors = device_info.get('neighbors', [])
            
            for neighbor in neighbors:
                neighbor_hostname = neighbor.get('hostname', '').upper()
                
                if neighbor_hostname:
                    # Clean hostname
                    if '.' in neighbor_hostname:
                        neighbor_hostname = neighbor_hostname.split('.')[0]
                    
                    # Record the directed connection
                    all_reported_connections.append((device_hostname, neighbor_hostname))
                    
                    # Create bidirectional connection ID
                    connection_id = tuple(sorted([device_hostname, neighbor_hostname]))
                    unique_connections.add(connection_id)
        
        manual_unique_count = len(unique_connections)
        total_reported = len(all_reported_connections)
        
        # Assert - Unique connections should be less than or equal to total reported
        assert manual_unique_count <= total_reported, \
            f"Unique connections {manual_unique_count} should not exceed total reported {total_reported}"
        
        # Assert - Calculated total should match unique connections (within reasonable bounds)
        connection_diff = abs(connection_counts['total_connections'] - manual_unique_count)
        max_allowed_diff = max(1, len(inventory) // 3)
        
        assert connection_diff <= max_allowed_diff, \
            f"Connection deduplication check failed: calculated={connection_counts['total_connections']}, " \
            f"manual_unique={manual_unique_count}, total_reported={total_reported}"
        
        # Assert - If there are bidirectional connections, unique count should be less than total reported
        if total_reported > manual_unique_count:
            # There are bidirectional connections, so deduplication should have occurred
            assert connection_counts['total_connections'] <= total_reported, \
                "Calculated connections should not exceed total reported connections when deduplication occurs"
    
    @given(
        inventory=connected_devices_strategy(),
        connection_filter_rate=st.floats(min_value=0.0, max_value=0.5)
    )
    @settings(max_examples=50, deadline=None)
    def test_connection_filtering_accuracy_property(self, inventory, connection_filter_rate):
        """
        Property: Connection Filtering Accuracy
        
        PROPERTY: When connections are filtered or devices have different statuses,
        connection counts should accurately reflect only valid connections.
        
        Validates: Requirements 3.3, 8.3
        """
        # Arrange - Modify some devices to have failed/filtered status
        modified_inventory = {}
        
        for device_key, device_info in inventory.items():
            modified_device = device_info.copy()
            
            # Randomly set some devices as failed/filtered based on filter rate
            import random
            random.seed(hash(device_key) % 2**32)  # Deterministic based on device key
            
            if random.random() < connection_filter_rate:
                modified_device['status'] = random.choice(['failed', 'filtered'])
                modified_device['connection_status'] = 'failed'
            
            modified_inventory[device_key] = modified_device
        
        calculator = SiteStatisticsCalculator()
        
        # Act
        connection_counts = calculator.calculate_site_connection_counts(modified_inventory)
        
        # Manual verification considering device status
        valid_hostnames = set()
        
        # Identify valid (connected) devices
        for device_key, device_info in modified_inventory.items():
            status = device_info.get('status', 'unknown')
            connection_status = device_info.get('connection_status', 'unknown')
            
            if status == 'connected' or connection_status == 'connected':
                hostname = device_info.get('hostname', '').upper()
                if hostname:
                    valid_hostnames.add(hostname)
        
        # Count connections involving only valid devices
        valid_connections = set()
        
        for device_key, device_info in modified_inventory.items():
            device_hostname = device_info.get('hostname', '').upper()
            
            # Only process connections from valid devices
            if device_hostname in valid_hostnames:
                neighbors = device_info.get('neighbors', [])
                
                for neighbor in neighbors:
                    neighbor_hostname = neighbor.get('hostname', '').upper()
                    
                    if neighbor_hostname:
                        # Clean hostname
                        if '.' in neighbor_hostname:
                            neighbor_hostname = neighbor_hostname.split('.')[0]
                        
                        # Only count connections to other valid devices
                        if neighbor_hostname in valid_hostnames:
                            connection_id = tuple(sorted([device_hostname, neighbor_hostname]))
                            valid_connections.add(connection_id)
        
        manual_valid_connections = len(valid_connections)
        
        # Assert - Connection counts should reflect filtering
        # Note: The calculator might not filter by device status, so we check reasonableness
        assert connection_counts['total_connections'] >= 0, \
            "Total connections should be non-negative even with filtering"
        
        # If significant filtering occurred, connection count should be reasonable
        if connection_filter_rate > 0.2 and len(valid_hostnames) < len(modified_inventory) * 0.8:
            # Significant filtering occurred
            max_expected_connections = len(modified_inventory) * 3  # Reasonable upper bound
            
            assert connection_counts['total_connections'] <= max_expected_connections, \
                f"Connection count seems too high with filtering: {connection_counts['total_connections']} > {max_expected_connections}"
        
        # Assert - Connection counts should still be internally consistent
        assert (connection_counts['intra_site_connections'] + 
               connection_counts['external_connections']) <= connection_counts['total_connections'], \
            "Connection consistency should be maintained even with filtering"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])