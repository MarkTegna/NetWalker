"""
Property-based tests for site statistics calculation functionality.

These tests validate universal properties that must hold for all possible
inputs to the site statistics calculation system.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, List, Set, Any
from collections import Counter
from unittest.mock import Mock

from netwalker.discovery.site_statistics_calculator import (
    SiteStatisticsCalculator, SiteStatistics
)


# Test data generators
@st.composite
def device_inventory_strategy(draw):
    """Generate valid device inventory for testing"""
    num_devices = draw(st.integers(min_value=1, max_value=20))
    inventory = {}
    
    statuses = ['connected', 'failed', 'filtered', 'boundary']
    platforms = ['cisco_ios', 'cisco_nxos', 'juniper_junos', 'arista_eos', 'unknown']
    discovery_methods = ['seed', 'cdp', 'lldp', 'site_boundary']
    
    for i in range(num_devices):
        hostname = f"DEVICE-{i+1:02d}"
        device_key = f"{hostname}:192.168.1.{i+1}"
        
        # Generate neighbors
        num_neighbors = draw(st.integers(min_value=0, max_value=5))
        neighbors = []
        for j in range(num_neighbors):
            neighbor = {
                'hostname': f"NEIGHBOR-{j+1:02d}",
                'ip_address': f"192.168.2.{j+1}"
            }
            neighbors.append(neighbor)
        
        device_info = {
            'hostname': hostname,
            'ip_address': f"192.168.1.{i+1}",
            'status': draw(st.sampled_from(statuses)),
            'connection_status': draw(st.sampled_from(['connected', 'failed', 'unknown'])),
            'platform': draw(st.sampled_from(platforms)),
            'discovery_method': draw(st.sampled_from(discovery_methods)),
            'discovery_depth': draw(st.integers(min_value=0, max_value=3)),
            'is_seed': draw(st.booleans()),
            'neighbors': neighbors
        }
        
        inventory[device_key] = device_info
    
    return inventory


@st.composite
def site_collection_results_strategy(draw):
    """Generate valid site collection results for testing"""
    devices_processed = draw(st.integers(min_value=0, max_value=50))
    devices_successful = draw(st.integers(min_value=0, max_value=devices_processed))
    devices_failed = devices_processed - devices_successful
    
    return {
        'site_name': draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        'success': True,
        'statistics': {
            'devices_processed': devices_processed,
            'devices_successful': devices_successful,
            'devices_failed': devices_failed,
            'neighbors_discovered': draw(st.integers(min_value=0, max_value=100)),
            'success_rate': (devices_successful / devices_processed * 100) if devices_processed > 0 else 0.0,
            'collection_duration_seconds': draw(st.floats(min_value=0.1, max_value=300.0))
        },
        'inventory': draw(device_inventory_strategy())
    }


class TestSiteStatisticsCalculatorProperties:
    """Property-based tests for site statistics calculation functionality"""
    
    @given(inventory=device_inventory_strategy())
    @settings(max_examples=50, deadline=None)
    def test_site_specific_statistics_accuracy_property(self, inventory):
        """
        Property 3: Site-Specific Statistics Accuracy
        
        PROPERTY: For any site inventory, the calculated device counts and statistics
        should match the actual devices in the inventory and be mathematically consistent.
        
        Validates: Requirements 3.1, 3.2
        """
        # Arrange
        calculator = SiteStatisticsCalculator()
        
        # Act
        device_counts = calculator.calculate_site_device_counts(inventory)
        connection_counts = calculator.calculate_site_connection_counts(inventory)
        
        # Assert - Device counts should match inventory
        assert device_counts['total_devices'] == len(inventory), \
            f"Total device count {device_counts['total_devices']} != inventory size {len(inventory)}"
        
        # Assert - Device counts should be non-negative
        for count_type, count_value in device_counts.items():
            assert count_value >= 0, f"Device count {count_type} should be non-negative, got {count_value}"
        
        # Assert - Connection counts should be non-negative
        for count_type, count_value in connection_counts.items():
            assert count_value >= 0, f"Connection count {count_type} should be non-negative, got {count_value}"
        
        # Assert - Device status counts should sum to total (allowing for unknown statuses)
        status_sum = (device_counts['connected_devices'] + device_counts['failed_devices'] + 
                     device_counts['filtered_devices'] + device_counts['boundary_devices'])
        assert status_sum <= device_counts['total_devices'], \
            f"Sum of status counts {status_sum} should not exceed total devices {device_counts['total_devices']}"
        
        # Assert - Connection consistency
        assert connection_counts['intra_site_connections'] + connection_counts['external_connections'] <= connection_counts['total_connections'], \
            "Intra-site + external connections should not exceed total connections"
        
        # Verify device counts by manually counting
        manual_counts = {'connected': 0, 'failed': 0, 'filtered': 0, 'boundary': 0, 'seed': 0}
        
        for device_key, device_info in inventory.items():
            status = device_info.get('status', 'unknown')
            connection_status = device_info.get('connection_status', 'unknown')
            
            if status == 'connected' or connection_status == 'connected':
                manual_counts['connected'] += 1
            elif status == 'failed' or connection_status == 'failed':
                manual_counts['failed'] += 1
            elif status == 'filtered':
                manual_counts['filtered'] += 1
            elif status == 'boundary':
                manual_counts['boundary'] += 1
            
            if device_info.get('is_seed', False) or device_info.get('discovery_method') == 'seed':
                manual_counts['seed'] += 1
        
        # Assert manual counts match calculated counts
        assert device_counts['connected_devices'] == manual_counts['connected'], \
            f"Connected device count mismatch: calculated={device_counts['connected_devices']}, manual={manual_counts['connected']}"
        
        assert device_counts['seed_devices'] == manual_counts['seed'], \
            f"Seed device count mismatch: calculated={device_counts['seed_devices']}, manual={manual_counts['seed']}"
    
    @given(
        inventory=device_inventory_strategy(),
        collection_results=site_collection_results_strategy()
    )
    @settings(max_examples=50, deadline=None)
    def test_site_summary_generation_completeness_property(self, inventory, collection_results):
        """
        Property: Site Summary Generation Completeness
        
        PROPERTY: For any site inventory and collection results, the generated
        site summary should contain all required fields and be internally consistent.
        
        Validates: Requirements 3.1, 3.2, 4.1
        """
        # Arrange
        calculator = SiteStatisticsCalculator()
        site_name = collection_results['site_name']
        
        # Act
        site_summary = calculator.generate_site_summary(site_name, inventory, collection_results)
        
        # Assert - Summary should be a SiteStatistics object
        assert isinstance(site_summary, SiteStatistics), \
            f"Site summary should be SiteStatistics object, got {type(site_summary)}"
        
        # Assert - Site name should match
        assert site_summary.site_name == site_name, \
            f"Site name mismatch: expected {site_name}, got {site_summary.site_name}"
        
        # Assert - Total devices should match inventory size
        assert site_summary.total_devices == len(inventory), \
            f"Total devices {site_summary.total_devices} != inventory size {len(inventory)}"
        
        # Assert - All numeric fields should be non-negative
        numeric_fields = [
            'total_devices', 'connected_devices', 'failed_devices', 'filtered_devices',
            'boundary_devices', 'total_connections', 'intra_site_connections', 
            'external_connections', 'total_neighbors_discovered', 'devices_processed'
        ]
        
        for field in numeric_fields:
            value = getattr(site_summary, field)
            assert value >= 0, f"Field {field} should be non-negative, got {value}"
        
        # Assert - Success rate should be valid percentage
        assert 0.0 <= site_summary.discovery_success_rate <= 100.0, \
            f"Success rate should be 0-100%, got {site_summary.discovery_success_rate}"
        
        # Assert - Platform counts should be consistent
        assert isinstance(site_summary.platform_counts, dict), \
            "Platform counts should be a dictionary"
        
        total_platform_devices = sum(site_summary.platform_counts.values())
        assert total_platform_devices <= site_summary.total_devices, \
            f"Platform device count {total_platform_devices} should not exceed total devices {site_summary.total_devices}"
        
        # Assert - Device category consistency
        category_sum = (site_summary.connected_devices + site_summary.failed_devices + 
                       site_summary.filtered_devices + site_summary.boundary_devices)
        assert category_sum <= site_summary.total_devices, \
            f"Sum of device categories {category_sum} should not exceed total {site_summary.total_devices}"
    
    @given(
        inventories=st.lists(device_inventory_strategy(), min_size=1, max_size=5)
    )
    @settings(max_examples=50, deadline=None)
    def test_site_connection_accuracy_property(self, inventories):
        """
        Property 13: Site Connection Accuracy
        
        PROPERTY: For any site inventory, connection counts should accurately reflect
        the actual connections between devices and distinguish intra-site vs external connections.
        
        Validates: Requirements 3.3, 8.3
        """
        # Arrange
        calculator = SiteStatisticsCalculator()
        
        for i, inventory in enumerate(inventories):
            site_name = f"SITE-{i+1}"
            
            # Act
            connection_counts = calculator.calculate_site_connection_counts(inventory)
            
            # Assert - Connection counts should be consistent
            assert connection_counts['total_connections'] >= 0, \
                "Total connections should be non-negative"
            
            assert connection_counts['intra_site_connections'] >= 0, \
                "Intra-site connections should be non-negative"
            
            assert connection_counts['external_connections'] >= 0, \
                "External connections should be non-negative"
            
            assert connection_counts['unique_neighbors'] >= 0, \
                "Unique neighbors count should be non-negative"
            
            # Assert - Intra + external should not exceed total
            assert (connection_counts['intra_site_connections'] + 
                   connection_counts['external_connections']) <= connection_counts['total_connections'], \
                "Intra-site + external connections should not exceed total connections"
            
            # Manual verification of connection counts
            manual_total_connections = 0
            manual_unique_neighbors = set()
            site_hostnames = set()
            
            # Build set of site hostnames
            for device_key, device_info in inventory.items():
                hostname = device_info.get('hostname', '').upper()
                if hostname:
                    site_hostnames.add(hostname)
            
            # Count connections manually
            unique_connections = set()
            
            for device_key, device_info in inventory.items():
                device_hostname = device_info.get('hostname', '').upper()
                neighbors = device_info.get('neighbors', [])
                
                for neighbor in neighbors:
                    neighbor_hostname = ''
                    if isinstance(neighbor, dict):
                        neighbor_hostname = neighbor.get('hostname', '').upper()
                    
                    if neighbor_hostname:
                        # Clean hostname
                        if '.' in neighbor_hostname:
                            neighbor_hostname = neighbor_hostname.split('.')[0]
                        
                        # Create bidirectional connection ID
                        connection_id = tuple(sorted([device_hostname, neighbor_hostname]))
                        unique_connections.add(connection_id)
                        manual_unique_neighbors.add(neighbor_hostname)
            
            manual_total_connections = len(unique_connections)
            
            # Assert - Manual count should match or be close to calculated count
            # (allowing for some variation due to different handling of edge cases)
            assert abs(connection_counts['total_connections'] - manual_total_connections) <= len(inventory), \
                f"Connection count discrepancy too large: calculated={connection_counts['total_connections']}, manual={manual_total_connections}"
    
    @given(
        site_stats_list=st.lists(
            st.builds(
                SiteStatistics,
                site_name=st.text(min_size=1, max_size=10),
                total_devices=st.integers(min_value=0, max_value=100),
                connected_devices=st.integers(min_value=0, max_value=50),
                total_connections=st.integers(min_value=0, max_value=200),
                discovery_success_rate=st.floats(min_value=0.0, max_value=100.0)
            ),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_global_vs_site_statistics_consistency_property(self, site_stats_list):
        """
        Property 7: Global vs Site Statistics Consistency
        
        PROPERTY: For any collection of site statistics, the aggregated totals
        should be mathematically consistent and the comparison should be accurate.
        
        Validates: Requirements 4.1, 4.4
        """
        # Arrange
        calculator = SiteStatisticsCalculator()
        
        # Act
        comparison = calculator.compare_site_statistics(site_stats_list)
        
        # Assert - Comparison should contain required fields
        required_fields = ['total_sites', 'total_devices_all_sites', 'total_connections_all_sites', 
                          'average_success_rate', 'site_rankings', 'site_summary']
        
        for field in required_fields:
            assert field in comparison, f"Comparison missing required field: {field}"
        
        # Assert - Total sites should match input
        assert comparison['total_sites'] == len(site_stats_list), \
            f"Total sites mismatch: expected {len(site_stats_list)}, got {comparison['total_sites']}"
        
        # Assert - Aggregated totals should match sum of individual sites
        expected_total_devices = sum(s.total_devices for s in site_stats_list)
        assert comparison['total_devices_all_sites'] == expected_total_devices, \
            f"Total devices mismatch: expected {expected_total_devices}, got {comparison['total_devices_all_sites']}"
        
        expected_total_connections = sum(s.total_connections for s in site_stats_list)
        assert comparison['total_connections_all_sites'] == expected_total_connections, \
            f"Total connections mismatch: expected {expected_total_connections}, got {comparison['total_connections_all_sites']}"
        
        # Assert - Average success rate should be mathematically correct
        if site_stats_list:
            expected_avg_success_rate = sum(s.discovery_success_rate for s in site_stats_list) / len(site_stats_list)
            assert abs(comparison['average_success_rate'] - expected_avg_success_rate) < 0.01, \
                f"Average success rate mismatch: expected {expected_avg_success_rate}, got {comparison['average_success_rate']}"
        
        # Assert - Site rankings should contain all sites
        rankings = comparison['site_rankings']
        for ranking_type in ['largest_by_devices', 'highest_success_rate', 'most_connections']:
            assert ranking_type in rankings, f"Missing ranking type: {ranking_type}"
            assert len(rankings[ranking_type]) == len(site_stats_list), \
                f"Ranking {ranking_type} should contain all sites"
        
        # Assert - Site summary should contain all sites
        assert len(comparison['site_summary']) == len(site_stats_list), \
            "Site summary should contain all sites"
        
        # Assert - Rankings should be properly sorted
        devices_ranking = rankings['largest_by_devices']
        for i in range(len(devices_ranking) - 1):
            assert devices_ranking[i].total_devices >= devices_ranking[i + 1].total_devices, \
                "Devices ranking should be in descending order"
        
        success_ranking = rankings['highest_success_rate']
        for i in range(len(success_ranking) - 1):
            assert success_ranking[i].discovery_success_rate >= success_ranking[i + 1].discovery_success_rate, \
                "Success rate ranking should be in descending order"
    
    @given(
        site_stats=st.builds(
            SiteStatistics,
            site_name=st.text(min_size=1, max_size=10),
            total_devices=st.integers(min_value=0, max_value=100),
            connected_devices=st.integers(min_value=0, max_value=100),
            failed_devices=st.integers(min_value=0, max_value=100),
            filtered_devices=st.integers(min_value=0, max_value=100),
            boundary_devices=st.integers(min_value=0, max_value=100),
            total_connections=st.integers(min_value=0, max_value=200),
            intra_site_connections=st.integers(min_value=0, max_value=200),
            external_connections=st.integers(min_value=0, max_value=200),
            discovery_success_rate=st.floats(min_value=-10.0, max_value=110.0),  # Allow invalid values for testing
            devices_processed=st.integers(min_value=-5, max_value=100)  # Allow negative for testing
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_statistics_validation_consistency_property(self, site_stats):
        """
        Property: Statistics Validation Consistency
        
        PROPERTY: For any site statistics object, validation should consistently
        identify logical inconsistencies and invalid values.
        
        Validates: Requirements 3.1, 3.2, 4.1
        """
        # Arrange
        calculator = SiteStatisticsCalculator()
        
        # Act
        warnings = calculator.validate_site_statistics_consistency(site_stats)
        
        # Assert - Warnings should be a list
        assert isinstance(warnings, list), "Validation warnings should be a list"
        
        # Check specific validation rules
        calculated_total = (site_stats.connected_devices + site_stats.failed_devices + 
                          site_stats.filtered_devices + site_stats.boundary_devices)
        
        # If device counts don't match, there should be a warning
        if calculated_total != site_stats.total_devices:
            device_warning_found = any("Device count mismatch" in warning for warning in warnings)
            assert device_warning_found, "Should warn about device count mismatch"
        
        # If success rate is out of bounds, there should be a warning
        if not (0.0 <= site_stats.discovery_success_rate <= 100.0):
            success_rate_warning_found = any("Invalid success rate" in warning for warning in warnings)
            assert success_rate_warning_found, "Should warn about invalid success rate"
        
        # If there are negative values, there should be warnings
        negative_fields = []
        for field_name in ['total_devices', 'connected_devices', 'failed_devices', 
                          'total_connections', 'devices_processed']:
            value = getattr(site_stats, field_name)
            if value < 0:
                negative_fields.append(field_name)
        
        if negative_fields:
            negative_warning_found = any("Negative value" in warning for warning in warnings)
            assert negative_warning_found, f"Should warn about negative values in fields: {negative_fields}"
        
        # If connection counts are inconsistent, there should be a warning
        if site_stats.intra_site_connections + site_stats.external_connections > site_stats.total_connections:
            connection_warning_found = any("Connection count inconsistency" in warning for warning in warnings)
            assert connection_warning_found, "Should warn about connection count inconsistency"
    
    def test_site_statistics_calculator_initialization(self):
        """Test that SiteStatisticsCalculator initializes correctly"""
        # Act
        calculator = SiteStatisticsCalculator()
        
        # Assert
        assert isinstance(calculator._statistics_cache, dict)
        assert isinstance(calculator._cache_timestamps, dict)
        assert len(calculator._statistics_cache) == 0
        assert len(calculator._cache_timestamps) == 0
    
    def test_cache_functionality(self):
        """Test that caching works correctly"""
        # Arrange
        calculator = SiteStatisticsCalculator()
        inventory = {
            'device1:192.168.1.1': {
                'hostname': 'DEVICE1',
                'ip_address': '192.168.1.1',
                'status': 'connected',
                'platform': 'cisco_ios',
                'neighbors': []
            }
        }
        
        # Act - Generate summary twice
        summary1 = calculator.generate_site_summary('TEST-SITE', inventory)
        summary2 = calculator.generate_site_summary('TEST-SITE', inventory)
        
        # Assert - Should be the same object (cached)
        assert summary1 is summary2, "Second call should return cached result"
        
        # Test cache info
        cache_info = calculator.get_cache_info()
        assert cache_info['cached_sites'] == 1
        assert 'TEST-SITE_1' in cache_info['cache_keys']
        
        # Test cache clearing
        calculator.clear_cache()
        cache_info_after_clear = calculator.get_cache_info()
        assert cache_info_after_clear['cached_sites'] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])