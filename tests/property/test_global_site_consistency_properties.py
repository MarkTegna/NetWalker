"""
Property-based tests for global vs site statistics consistency.

These tests validate that aggregated site statistics are consistent with
global statistics and that site vs global separation is accurate.
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
def consistent_site_and_global_inventory_strategy(draw):
    """Generate site inventories and a consistent global inventory"""
    num_sites = draw(st.integers(min_value=1, max_value=4))
    site_inventories = {}
    global_inventory = {}
    
    # Generate devices for each site
    for site_idx in range(num_sites):
        site_name = f"SITE-{site_idx+1}"
        devices_in_site = draw(st.integers(min_value=1, max_value=8))
        
        site_inventory = {}
        
        for device_idx in range(devices_in_site):
            hostname = f"{site_name}-DEVICE-{device_idx+1:02d}"
            ip_address = f"192.168.{site_idx+1}.{device_idx+1}"
            device_key = f"{hostname}:{ip_address}"
            
            # Generate neighbors (some within site, some external)
            num_neighbors = draw(st.integers(min_value=0, max_value=4))
            neighbors = []
            
            for neighbor_idx in range(num_neighbors):
                # 70% chance of intra-site neighbor, 30% external
                if draw(st.floats(0, 1)) < 0.7 and devices_in_site > 1:
                    # Intra-site neighbor
                    neighbor_device_idx = draw(st.integers(0, devices_in_site - 1))
                    if neighbor_device_idx != device_idx:  # Don't connect to self
                        neighbor_hostname = f"{site_name}-DEVICE-{neighbor_device_idx+1:02d}"
                        neighbor_ip = f"192.168.{site_idx+1}.{neighbor_device_idx+1}"
                    else:
                        continue
                else:
                    # External neighbor
                    external_site_idx = draw(st.integers(0, num_sites))  # Allow non-existent sites
                    neighbor_hostname = f"EXTERNAL-SITE-{external_site_idx}-DEVICE-{neighbor_idx+1:02d}"
                    neighbor_ip = f"192.168.{external_site_idx+10}.{neighbor_idx+1}"
                
                neighbor = {
                    'hostname': neighbor_hostname,
                    'ip_address': neighbor_ip,
                    'interface': f"GigabitEthernet0/{neighbor_idx+1}"
                }
                neighbors.append(neighbor)
            
            device_info = {
                'hostname': hostname,
                'ip_address': ip_address,
                'status': draw(st.sampled_from(['connected', 'failed', 'filtered', 'boundary'])),
                'connection_status': draw(st.sampled_from(['connected', 'failed', 'unknown'])),
                'platform': draw(st.sampled_from(['cisco_ios', 'cisco_nxos', 'juniper_junos', 'arista_eos'])),
                'discovery_method': draw(st.sampled_from(['seed', 'cdp', 'lldp', 'site_boundary'])),
                'discovery_depth': draw(st.integers(min_value=0, max_value=3)),
                'is_seed': draw(st.booleans()),
                'neighbors': neighbors
            }
            
            site_inventory[device_key] = device_info
            global_inventory[device_key] = device_info  # Add to global inventory
        
        site_inventories[site_name] = site_inventory
    
    # Add some non-site devices to global inventory
    num_non_site_devices = draw(st.integers(min_value=0, max_value=3))
    
    for device_idx in range(num_non_site_devices):
        hostname = f"NON-SITE-DEVICE-{device_idx+1:02d}"
        ip_address = f"192.168.99.{device_idx+1}"
        device_key = f"{hostname}:{ip_address}"
        
        device_info = {
            'hostname': hostname,
            'ip_address': ip_address,
            'status': draw(st.sampled_from(['connected', 'failed', 'filtered'])),
            'connection_status': draw(st.sampled_from(['connected', 'failed', 'unknown'])),
            'platform': draw(st.sampled_from(['cisco_ios', 'cisco_nxos', 'juniper_junos'])),
            'discovery_method': 'seed',
            'discovery_depth': 0,
            'is_seed': True,
            'neighbors': []
        }
        
        global_inventory[device_key] = device_info
    
    return site_inventories, global_inventory


@st.composite
def site_statistics_with_collection_results_strategy(draw):
    """Generate site statistics with corresponding collection results"""
    site_name = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    
    total_devices = draw(st.integers(min_value=1, max_value=20))
    connected_devices = draw(st.integers(min_value=0, max_value=total_devices))
    failed_devices = draw(st.integers(min_value=0, max_value=total_devices - connected_devices))
    remaining_devices = total_devices - connected_devices - failed_devices
    filtered_devices = draw(st.integers(min_value=0, max_value=remaining_devices))
    boundary_devices = remaining_devices - filtered_devices
    
    total_connections = draw(st.integers(min_value=0, max_value=total_devices * 3))
    intra_site_connections = draw(st.integers(min_value=0, max_value=total_connections))
    external_connections = total_connections - intra_site_connections
    
    site_stats = SiteStatistics(
        site_name=site_name,
        total_devices=total_devices,
        connected_devices=connected_devices,
        failed_devices=failed_devices,
        filtered_devices=filtered_devices,
        boundary_devices=boundary_devices,
        total_connections=total_connections,
        intra_site_connections=intra_site_connections,
        external_connections=external_connections,
        discovery_success_rate=draw(st.floats(min_value=0.0, max_value=100.0)),
        average_discovery_depth=draw(st.floats(min_value=0.0, max_value=5.0)),
        total_neighbors_discovered=draw(st.integers(min_value=0, max_value=total_devices * 5)),
        devices_processed=draw(st.integers(min_value=total_devices, max_value=total_devices + 5)),
        collection_duration_seconds=draw(st.floats(min_value=1.0, max_value=300.0)),
        platform_counts={
            'cisco_ios': draw(st.integers(min_value=0, max_value=total_devices)),
            'cisco_nxos': draw(st.integers(min_value=0, max_value=total_devices)),
            'juniper_junos': draw(st.integers(min_value=0, max_value=total_devices))
        }
    )
    
    # Create corresponding collection results
    collection_results = {
        'site_name': site_name,
        'success': True,
        'statistics': {
            'devices_processed': site_stats.devices_processed,
            'devices_successful': connected_devices,
            'devices_failed': failed_devices,
            'neighbors_discovered': site_stats.total_neighbors_discovered,
            'success_rate': site_stats.discovery_success_rate,
            'collection_duration_seconds': site_stats.collection_duration_seconds
        },
        'inventory': {}  # Simplified for this test
    }
    
    return site_stats, collection_results


class TestGlobalSiteConsistencyProperties:
    """Property-based tests for global vs site statistics consistency"""
    
    @given(site_and_global_data=consistent_site_and_global_inventory_strategy())
    @settings(max_examples=50, deadline=None)
    def test_global_vs_site_statistics_consistency_property(self, site_and_global_data):
        """
        Property 7: Global vs Site Statistics Consistency
        
        PROPERTY: For any collection of site inventories and corresponding global inventory,
        the aggregated site statistics should be consistent with global statistics.
        
        Validates: Requirements 4.1, 4.4
        """
        site_inventories, global_inventory = site_and_global_data
        
        # Arrange
        calculator = SiteStatisticsCalculator()
        
        # Generate site statistics for each site
        site_stats_list = []
        for site_name, site_inventory in site_inventories.items():
            if site_inventory:  # Only process non-empty sites
                site_stats = calculator.generate_site_summary(site_name, site_inventory)
                site_stats_list.append(site_stats)
        
        if not site_stats_list:
            return  # Skip if no valid sites
        
        # Act - Compare site statistics
        comparison = calculator.compare_site_statistics(site_stats_list)
        
        # Act - Separate site vs global statistics
        separation = calculator.separate_site_vs_global_statistics(site_stats_list, global_inventory)
        
        # Assert - Comparison should contain required fields
        required_comparison_fields = ['total_sites', 'total_devices_all_sites', 'total_connections_all_sites', 
                                    'average_success_rate', 'site_rankings', 'site_summary']
        
        for field in required_comparison_fields:
            assert field in comparison, f"Comparison missing required field: {field}"
        
        # Assert - Total sites should match
        assert comparison['total_sites'] == len(site_stats_list), \
            f"Total sites mismatch: expected {len(site_stats_list)}, got {comparison['total_sites']}"
        
        # Assert - Aggregated totals should match sum of individual sites
        expected_total_devices = sum(s.total_devices for s in site_stats_list)
        assert comparison['total_devices_all_sites'] == expected_total_devices, \
            f"Total devices mismatch: expected {expected_total_devices}, got {comparison['total_devices_all_sites']}"
        
        expected_total_connections = sum(s.total_connections for s in site_stats_list)
        assert comparison['total_connections_all_sites'] == expected_total_connections, \
            f"Total connections mismatch: expected {expected_total_connections}, got {comparison['total_connections_all_sites']}"
        
        # Assert - Separation should contain required fields
        required_separation_fields = ['global_statistics', 'site_aggregated_statistics', 
                                    'non_site_statistics', 'coverage_analysis', 'consistency_checks']
        
        for field in required_separation_fields:
            assert field in separation, f"Separation missing required field: {field}"
        
        # Assert - Global statistics should be reasonable
        global_stats = separation['global_statistics']
        assert global_stats['total_devices'] == len(global_inventory), \
            f"Global device count should match inventory size: {global_stats['total_devices']} != {len(global_inventory)}"
        
        # Assert - Site aggregated statistics should match comparison
        site_aggregated = separation['site_aggregated_statistics']
        assert site_aggregated['total_devices'] == comparison['total_devices_all_sites'], \
            "Site aggregated devices should match comparison total"
        
        # Assert - Coverage analysis should be reasonable
        coverage = separation['coverage_analysis']
        assert coverage['sites_count'] == len(site_stats_list), \
            "Coverage sites count should match site stats list length"
        
        assert 0.0 <= coverage['site_coverage_percentage'] <= 100.0, \
            f"Site coverage percentage should be 0-100%: {coverage['site_coverage_percentage']}"
        
        # Assert - Consistency checks should pass basic validation
        consistency = separation['consistency_checks']
        
        # Device count consistency (allowing for small rounding differences)
        expected_total = site_aggregated['total_devices'] + separation['non_site_statistics']['devices']
        device_diff = abs(global_stats['total_devices'] - expected_total)
        assert device_diff <= 1, \
            f"Device count consistency failed: global={global_stats['total_devices']}, " \
            f"site+non_site={expected_total}, diff={device_diff}"
        
        # Non-site statistics should be non-negative
        assert separation['non_site_statistics']['devices'] >= 0, \
            "Non-site devices should be non-negative"
        
        assert separation['non_site_statistics']['connections'] >= 0, \
            "Non-site connections should be non-negative"
    
    @given(
        site_stats_and_results=st.lists(
            site_statistics_with_collection_results_strategy(),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_site_summary_data_generation_consistency_property(self, site_stats_and_results):
        """
        Property: Site Summary Data Generation Consistency
        
        PROPERTY: For any site statistics and collection results, the generated
        summary data should be internally consistent and contain all required fields.
        
        Validates: Requirements 4.1, 4.2, 4.3
        """
        # Arrange
        calculator = SiteStatisticsCalculator()
        
        for site_stats, collection_results in site_stats_and_results:
            # Act
            summary_data = calculator.generate_site_summary_data(site_stats)
            
            # Assert - Summary data should contain required sections
            required_sections = ['site_info', 'device_breakdown', 'connection_breakdown', 
                               'discovery_metrics', 'platform_distribution', 'summary_flags']
            
            for section in required_sections:
                assert section in summary_data, f"Summary data missing section: {section}"
            
            # Assert - Site info should match site statistics
            site_info = summary_data['site_info']
            assert site_info['name'] == site_stats.site_name, \
                f"Site name mismatch: {site_info['name']} != {site_stats.site_name}"
            
            assert site_info['total_devices'] == site_stats.total_devices, \
                f"Total devices mismatch: {site_info['total_devices']} != {site_stats.total_devices}"
            
            # Assert - Device breakdown should be consistent
            device_breakdown = summary_data['device_breakdown']
            breakdown_total = (device_breakdown['connected'] + device_breakdown['failed'] + 
                             device_breakdown['filtered'] + device_breakdown['boundary'])
            
            assert breakdown_total <= device_breakdown['total'], \
                f"Device breakdown sum {breakdown_total} should not exceed total {device_breakdown['total']}"
            
            assert device_breakdown['total'] == site_stats.total_devices, \
                "Device breakdown total should match site stats total devices"
            
            # Assert - Connection breakdown should be consistent
            connection_breakdown = summary_data['connection_breakdown']
            assert connection_breakdown['total_connections'] == site_stats.total_connections, \
                "Connection breakdown total should match site stats total connections"
            
            assert connection_breakdown['intra_site'] == site_stats.intra_site_connections, \
                "Intra-site connections should match site stats"
            
            assert connection_breakdown['external'] == site_stats.external_connections, \
                "External connections should match site stats"
            
            # Assert - Connection ratio should be reasonable
            if site_stats.total_devices > 0:
                expected_ratio = site_stats.total_connections / site_stats.total_devices
                assert abs(connection_breakdown['connection_ratio'] - expected_ratio) < 0.01, \
                    f"Connection ratio mismatch: {connection_breakdown['connection_ratio']} != {expected_ratio}"
            
            # Assert - Discovery metrics should match
            discovery_metrics = summary_data['discovery_metrics']
            assert discovery_metrics['success_rate'] == site_stats.discovery_success_rate, \
                "Discovery success rate should match site stats"
            
            # Assert - Summary flags should be logical
            summary_flags = summary_data['summary_flags']
            
            assert summary_flags['has_devices'] == (site_stats.total_devices > 0), \
                "Has devices flag should match device count"
            
            assert summary_flags['has_connections'] == (site_stats.total_connections > 0), \
                "Has connections flag should match connection count"
            
            assert summary_flags['has_external_connections'] == (site_stats.external_connections > 0), \
                "Has external connections flag should match external connection count"
            
            expected_isolated = (site_stats.external_connections == 0 and site_stats.total_devices > 0)
            assert summary_flags['is_isolated_site'] == expected_isolated, \
                "Isolated site flag should be correct"
    
    @given(site_and_global_data=consistent_site_and_global_inventory_strategy())
    @settings(max_examples=50, deadline=None)
    def test_site_vs_global_separation_accuracy_property(self, site_and_global_data):
        """
        Property: Site vs Global Separation Accuracy
        
        PROPERTY: For any site inventories and global inventory, the separation
        of site-specific vs global statistics should be mathematically accurate.
        
        Validates: Requirements 4.1, 4.4
        """
        site_inventories, global_inventory = site_and_global_data
        
        # Arrange
        calculator = SiteStatisticsCalculator()
        
        # Generate site statistics
        site_stats_list = []
        total_site_devices = 0
        
        for site_name, site_inventory in site_inventories.items():
            if site_inventory:
                site_stats = calculator.generate_site_summary(site_name, site_inventory)
                site_stats_list.append(site_stats)
                total_site_devices += len(site_inventory)
        
        if not site_stats_list:
            return  # Skip if no valid sites
        
        # Act
        separation = calculator.separate_site_vs_global_statistics(site_stats_list, global_inventory)
        
        # Manual calculation for verification
        manual_global_devices = len(global_inventory)
        manual_non_site_devices = manual_global_devices - total_site_devices
        
        # Assert - Global statistics should match manual calculation
        global_stats = separation['global_statistics']
        assert global_stats['total_devices'] == manual_global_devices, \
            f"Global device count mismatch: {global_stats['total_devices']} != {manual_global_devices}"
        
        # Assert - Site aggregated statistics should match sum of sites
        site_aggregated = separation['site_aggregated_statistics']
        manual_site_total = sum(s.total_devices for s in site_stats_list)
        
        assert site_aggregated['total_devices'] == manual_site_total, \
            f"Site aggregated devices mismatch: {site_aggregated['total_devices']} != {manual_site_total}"
        
        # Assert - Non-site statistics should be reasonable
        non_site_stats = separation['non_site_statistics']
        assert non_site_stats['devices'] == manual_non_site_devices, \
            f"Non-site devices mismatch: {non_site_stats['devices']} != {manual_non_site_devices}"
        
        # Assert - Coverage analysis should be mathematically correct
        coverage = separation['coverage_analysis']
        
        if manual_global_devices > 0:
            expected_coverage = (manual_site_total / manual_global_devices) * 100
            assert abs(coverage['site_coverage_percentage'] - expected_coverage) < 0.1, \
                f"Site coverage percentage mismatch: {coverage['site_coverage_percentage']} != {expected_coverage}"
        
        if site_stats_list:
            expected_avg_devices = manual_site_total / len(site_stats_list)
            assert abs(coverage['average_devices_per_site'] - expected_avg_devices) < 0.1, \
                f"Average devices per site mismatch: {coverage['average_devices_per_site']} != {expected_avg_devices}"
        
        # Assert - Consistency checks should validate correctly
        consistency = separation['consistency_checks']
        
        # Check device count consistency
        calculated_total = site_aggregated['total_devices'] + non_site_stats['devices']
        device_consistency = abs(global_stats['total_devices'] - calculated_total) <= 1
        assert consistency['device_count_matches'] == device_consistency, \
            "Device count consistency check should be accurate"
        
        # Check non-negative values
        non_negative_check = (non_site_stats['devices'] >= 0 and non_site_stats['connections'] >= 0)
        assert consistency['no_negative_non_site'] == non_negative_check, \
            "Non-negative non-site check should be accurate"
    
    @given(
        site_stats_list=st.lists(
            st.builds(
                SiteStatistics,
                site_name=st.integers(min_value=1, max_value=1000).map(lambda x: f"SITE-{x}"),  # Ensure unique site names
                total_devices=st.integers(min_value=0, max_value=50),
                connected_devices=st.integers(min_value=0, max_value=50),
                total_connections=st.integers(min_value=0, max_value=100),
                discovery_success_rate=st.floats(min_value=0.0, max_value=100.0),
                platform_counts=st.dictionaries(
                    st.sampled_from(['cisco_ios', 'cisco_nxos', 'juniper_junos']),
                    st.integers(min_value=0, max_value=20),
                    min_size=0,
                    max_size=3
                )
            ),
            min_size=1,
            max_size=5,
            unique_by=lambda x: x.site_name  # Ensure unique site names
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_site_comparison_mathematical_consistency_property(self, site_stats_list):
        """
        Property: Site Comparison Mathematical Consistency
        
        PROPERTY: For any list of site statistics, the comparison results should
        be mathematically consistent and rankings should be properly ordered.
        
        Validates: Requirements 4.1, 4.4
        """
        # Arrange
        calculator = SiteStatisticsCalculator()
        
        # Act
        comparison = calculator.compare_site_statistics(site_stats_list)
        
        # Assert - Basic structure validation
        assert comparison['total_sites'] == len(site_stats_list), \
            "Total sites should match input list length"
        
        # Assert - Aggregated totals should be mathematically correct
        expected_total_devices = sum(s.total_devices for s in site_stats_list)
        assert comparison['total_devices_all_sites'] == expected_total_devices, \
            f"Total devices aggregation incorrect: {comparison['total_devices_all_sites']} != {expected_total_devices}"
        
        expected_total_connections = sum(s.total_connections for s in site_stats_list)
        assert comparison['total_connections_all_sites'] == expected_total_connections, \
            f"Total connections aggregation incorrect: {comparison['total_connections_all_sites']} != {expected_total_connections}"
        
        # Assert - Average success rate should be mathematically correct
        if site_stats_list:
            expected_avg_success = sum(s.discovery_success_rate for s in site_stats_list) / len(site_stats_list)
            assert abs(comparison['average_success_rate'] - expected_avg_success) < 0.01, \
                f"Average success rate incorrect: {comparison['average_success_rate']} != {expected_avg_success}"
        
        # Assert - Rankings should be properly ordered
        rankings = comparison['site_rankings']
        
        # Check device ranking order
        devices_ranking = rankings['largest_by_devices']
        assert len(devices_ranking) == len(site_stats_list), \
            "Device ranking should contain all sites"
        
        for i in range(len(devices_ranking) - 1):
            assert devices_ranking[i].total_devices >= devices_ranking[i + 1].total_devices, \
                f"Device ranking not properly ordered at position {i}"
        
        # Check success rate ranking order
        success_ranking = rankings['highest_success_rate']
        assert len(success_ranking) == len(site_stats_list), \
            "Success rate ranking should contain all sites"
        
        for i in range(len(success_ranking) - 1):
            assert success_ranking[i].discovery_success_rate >= success_ranking[i + 1].discovery_success_rate, \
                f"Success rate ranking not properly ordered at position {i}"
        
        # Check connections ranking order
        connections_ranking = rankings['most_connections']
        assert len(connections_ranking) == len(site_stats_list), \
            "Connections ranking should contain all sites"
        
        for i in range(len(connections_ranking) - 1):
            assert connections_ranking[i].total_connections >= connections_ranking[i + 1].total_connections, \
                f"Connections ranking not properly ordered at position {i}"
        
        # Assert - Site summary should contain all sites
        site_summary = comparison['site_summary']
        assert len(site_summary) == len(site_stats_list), \
            "Site summary should contain all sites"
        
        # Verify site summary data consistency
        for i, summary_item in enumerate(site_summary):
            # Find corresponding site stats
            matching_site = next((s for s in site_stats_list if s.site_name == summary_item['site_name']), None)
            assert matching_site is not None, f"Site summary item {i} has no matching site stats"
            
            assert summary_item['devices'] == matching_site.total_devices, \
                f"Site summary devices mismatch for {summary_item['site_name']}"
            
            assert summary_item['connections'] == matching_site.total_connections, \
                f"Site summary connections mismatch for {summary_item['site_name']}"
            
            assert summary_item['success_rate'] == matching_site.discovery_success_rate, \
                f"Site summary success rate mismatch for {summary_item['site_name']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])