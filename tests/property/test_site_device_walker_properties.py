"""
Property-based tests for Site Device Walker

Tests universal properties of site-specific device walking functionality.
"""

import pytest
from hypothesis import given, strategies as st, assume
from unittest.mock import Mock, MagicMock
from datetime import datetime

from netwalker.discovery.site_device_walker import SiteDeviceWalker, SiteWalkResult
from netwalker.discovery.discovery_engine import DiscoveryNode
from netwalker.discovery.site_association_validator import SiteAssociationValidator
from netwalker.connection.data_models import ConnectionResult, ConnectionMethod, ConnectionStatus


class TestSiteDeviceWalkerProperties:
    """Property-based tests for SiteDeviceWalker functionality"""
    
    def create_mock_connection_manager(self, success_rate: float = 1.0):
        """Create a mock connection manager with configurable success rate"""
        mock_manager = Mock()
        
        def mock_connect(ip_address, credentials):
            # Simulate connection success/failure based on success_rate
            import random
            success = random.random() < success_rate
            
            if success:
                mock_connection = Mock()
                connection_result = ConnectionResult(
                    host=ip_address,
                    method=ConnectionMethod.SSH,
                    status=ConnectionStatus.SUCCESS,
                    error_message=None,
                    connection_time=0.5
                )
                return mock_connection, connection_result
            else:
                connection_result = ConnectionResult(
                    host=ip_address,
                    method=ConnectionMethod.SSH,
                    status=ConnectionStatus.FAILED,
                    error_message="Connection failed",
                    connection_time=None
                )
                return None, connection_result
        
        mock_manager.connect_device.side_effect = mock_connect
        mock_manager.close_connection.return_value = None
        
        return mock_manager
    
    def create_mock_device_collector(self, neighbors_per_device: int = 3):
        """Create a mock device collector that returns device info with neighbors"""
        mock_collector = Mock()
        
        def mock_collect_info(connection, hostname, ip_address):
            # Create mock neighbors
            neighbors = []
            for i in range(neighbors_per_device):
                neighbor = Mock()
                neighbor.hostname = f"{hostname}-NEIGHBOR-{i+1:02d}"
                neighbor.ip_address = f"192.168.{i+1}.{i+1}"
                neighbors.append(neighbor)
            
            return {
                'hostname': hostname,
                'ip_address': ip_address,
                'device_type': 'switch',
                'neighbors': neighbors,
                'interfaces': ['GigabitEthernet0/1', 'GigabitEthernet0/2']
            }
        
        mock_collector.collect_device_info.side_effect = mock_collect_info
        return mock_collector
    
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
        site_name=st.text(min_size=3, max_size=10, alphabet=st.characters(min_codepoint=65, max_codepoint=90)),
        device_count=st.integers(min_value=1, max_value=10),
        neighbors_per_device=st.integers(min_value=0, max_value=5)
    )
    def test_site_device_walking_consistency_property(self, site_name, device_count, neighbors_per_device):
        """
        Property 4: Site Device Walking Consistency
        
        For any device added to a site queue, the system should attempt to walk it 
        using the same connection methods as global discovery.
        
        **Feature: site-specific-device-collection-reporting, Property 4: Site Device Walking Consistency**
        **Validates: Requirements 2.1, 2.2**
        """
        # Create mocks
        connection_manager = self.create_mock_connection_manager(success_rate=1.0)
        device_collector = self.create_mock_device_collector(neighbors_per_device)
        site_validator = SiteAssociationValidator('*-CORE-*')
        
        walker = SiteDeviceWalker(connection_manager, device_collector, site_validator)
        
        # Create test devices
        devices = []
        for i in range(device_count):
            hostname = f"{site_name}-SW-{i+1:02d}"
            ip_address = f"192.168.1.{i+1}"
            device_node = self.create_discovery_node(hostname, ip_address)
            devices.append(device_node)
        
        # Walk all devices
        results = []
        for device_node in devices:
            result = walker.walk_site_device(device_node, site_name)
            results.append(result)
        
        # Property: All devices should be attempted for walking
        assert len(results) == device_count, \
            f"Expected {device_count} walk results, got {len(results)}"
        
        # Property: All walks should be successful (since we mocked 100% success)
        successful_walks = [r for r in results if r.walk_success]
        assert len(successful_walks) == device_count, \
            f"Expected {device_count} successful walks, got {len(successful_walks)}"
        
        # Property: Each device should have consistent connection attempts
        for result in results:
            assert result.site_name == site_name, \
                f"Result site name {result.site_name} should match expected {site_name}"
            assert result.connection_method == "SSH", \
                f"Connection method should be SSH, got {result.connection_method}"
            assert result.walk_success, \
                f"Walk should be successful for {result.device_key}"
        
        # Property: Connection manager should be called for each device
        assert connection_manager.connect_device.call_count == device_count, \
            f"Connection manager should be called {device_count} times, was called {connection_manager.connect_device.call_count} times"
        
        # Property: Device collector should be called for each successful connection
        assert device_collector.collect_device_info.call_count == device_count, \
            f"Device collector should be called {device_count} times, was called {device_collector.collect_device_info.call_count} times"
    
    @given(
        site_name=st.text(min_size=3, max_size=10, alphabet=st.characters(min_codepoint=65, max_codepoint=90)),
        parent_devices=st.lists(
            st.tuples(
                st.text(min_size=5, max_size=15, alphabet=st.characters(min_codepoint=65, max_codepoint=90)),
                st.integers(min_value=1, max_value=5)  # neighbors per device
            ),
            min_size=1, max_size=5, unique_by=lambda x: x[0]
        )
    )
    def test_neighbor_site_association_propagation_property(self, site_name, parent_devices):
        """
        Property 5: Neighbor Site Association Propagation
        
        For any device discovered as a neighbor within a site, it should be associated 
        with the same site as its parent device unless it matches a different site boundary pattern.
        
        **Feature: site-specific-device-collection-reporting, Property 5: Neighbor Site Association Propagation**
        **Validates: Requirements 1.3, 2.4**
        """
        # Create mocks
        connection_manager = self.create_mock_connection_manager(success_rate=1.0)
        site_validator = SiteAssociationValidator('*-CORE-*')
        
        # Create a custom device collector that generates neighbors with site-specific names
        mock_collector = Mock()
        
        def mock_collect_info(connection, hostname, ip_address):
            # The mock should return neighbors based on the current device being walked
            # For this test, we'll use a fixed number of neighbors per device
            neighbors_per_device = 2  # Fixed for simplicity
            
            # Create neighbors - some in same site, some potentially in other sites
            neighbors = []
            for i in range(neighbors_per_device):
                if i < neighbors_per_device // 2:
                    # Same site neighbors
                    neighbor_hostname = f"{site_name}-SW-{i + 1:02d}"
                else:
                    # Potentially different site neighbors (but still follow naming convention)
                    neighbor_hostname = f"{site_name}-IDF-{i + 1:02d}"
                
                neighbor = Mock()
                neighbor.hostname = neighbor_hostname
                neighbor.ip_address = f"192.168.1.{i + 10}"
                neighbors.append(neighbor)
            
            return {
                'hostname': hostname,
                'ip_address': ip_address,
                'device_type': 'switch',
                'neighbors': neighbors
            }
        
        mock_collector.collect_device_info.side_effect = mock_collect_info
        
        walker = SiteDeviceWalker(connection_manager, mock_collector, site_validator)
        
        # Test each parent device
        all_processed_neighbors = []
        neighbors_per_device = 2  # Fixed for this test
        
        for parent_hostname, expected_neighbor_count in parent_devices:
            # Create parent device node
            parent_device_hostname = f"{site_name}-CORE-01"  # Make it a site boundary device
            parent_ip = "192.168.1.1"
            parent_node = self.create_discovery_node(parent_device_hostname, parent_ip)
            
            # Walk the parent device
            result = walker.walk_site_device(parent_node, site_name)
            
            # Property: Walk should be successful
            assert result.walk_success, \
                f"Parent device walk should be successful for {parent_device_hostname}"
            
            # Property: Should have expected number of neighbors (using our fixed count)
            assert len(result.neighbors_found) == neighbors_per_device, \
                f"Expected {neighbors_per_device} neighbors, got {len(result.neighbors_found)}"
            
            # Process neighbors to check site association
            processed_neighbors = walker.process_site_neighbors(result.neighbors_found, site_name)
            all_processed_neighbors.extend(processed_neighbors)
            
            # Property: All processed neighbors should be valid DiscoveryNode objects
            for neighbor_node in processed_neighbors:
                assert isinstance(neighbor_node, DiscoveryNode), \
                    f"Processed neighbor should be DiscoveryNode, got {type(neighbor_node)}"
                assert neighbor_node.hostname, \
                    "Neighbor should have a hostname"
                assert neighbor_node.ip_address, \
                    "Neighbor should have an IP address"
                assert neighbor_node.discovery_method == "site_walk", \
                    f"Neighbor discovery method should be 'site_walk', got {neighbor_node.discovery_method}"
        
        # Property: Total processed neighbors should match total expected
        total_expected = len(parent_devices) * neighbors_per_device  # Each device produces fixed neighbors
        assert len(all_processed_neighbors) == total_expected, \
            f"Expected {total_expected} total processed neighbors, got {len(all_processed_neighbors)}"
        
        # Property: Neighbors with site-matching names should be associated with the parent site
        for neighbor_node in all_processed_neighbors:
            neighbor_site = site_validator.determine_device_site(
                neighbor_node.hostname, neighbor_node.ip_address, site_name
            )
            
            # Since we created neighbors with the same site prefix, they should be associated with the same site
            if neighbor_node.hostname.startswith(site_name):
                assert neighbor_site == site_name or neighbor_site != 'GLOBAL', \
                    f"Neighbor {neighbor_node.hostname} should be associated with site {site_name} or a specific site, got {neighbor_site}"
    
    @given(
        site_name=st.text(min_size=3, max_size=10, alphabet=st.characters(min_codepoint=65, max_codepoint=90)),
        device_count=st.integers(min_value=2, max_value=8),
        failure_rate=st.floats(min_value=0.0, max_value=0.5)  # 0-50% failure rate
    )
    def test_site_walking_error_resilience_property(self, site_name, device_count, failure_rate):
        """
        Property: Site Walking Error Resilience
        
        For any site collection operation, errors in processing one device should 
        not prevent processing of remaining devices in the same site.
        
        **Feature: site-specific-device-collection-reporting, Property: Site Walking Error Resilience**
        **Validates: Requirements 1.4, 9.1**
        """
        # Create mocks with configurable failure rate
        connection_manager = self.create_mock_connection_manager(success_rate=1.0 - failure_rate)
        device_collector = self.create_mock_device_collector(neighbors_per_device=2)
        site_validator = SiteAssociationValidator('*-CORE-*')
        
        walker = SiteDeviceWalker(connection_manager, device_collector, site_validator)
        
        # Create test devices
        devices = []
        for i in range(device_count):
            hostname = f"{site_name}-SW-{i+1:02d}"
            ip_address = f"192.168.1.{i+1}"
            device_node = self.create_discovery_node(hostname, ip_address)
            devices.append(device_node)
        
        # Walk all devices using the batch method
        results = walker.walk_multiple_devices(devices, site_name)
        
        # Property: Should get a result for every device, regardless of failures
        assert len(results) == device_count, \
            f"Should get {device_count} results regardless of failures, got {len(results)}"
        
        # Property: Each result should have the correct site name
        for result in results:
            assert result.site_name == site_name, \
                f"Result site should be {site_name}, got {result.site_name}"
        
        # Property: Failed walks should have error messages
        failed_results = [r for r in results if not r.walk_success]
        for failed_result in failed_results:
            assert failed_result.error_message is not None, \
                f"Failed walk for {failed_result.device_key} should have error message"
            assert failed_result.device_info is None, \
                f"Failed walk for {failed_result.device_key} should not have device info"
        
        # Property: Successful walks should have device info and no error messages
        successful_results = [r for r in results if r.walk_success]
        for successful_result in successful_results:
            assert successful_result.error_message is None, \
                f"Successful walk for {successful_result.device_key} should not have error message"
            assert successful_result.device_info is not None, \
                f"Successful walk for {successful_result.device_key} should have device info"
        
        # Property: Statistics should be consistent
        stats = walker.get_walk_statistics()
        assert stats['total_walks'] == device_count, \
            f"Total walks should be {device_count}, got {stats['total_walks']}"
        assert stats['successful_walks'] == len(successful_results), \
            f"Successful walks should be {len(successful_results)}, got {stats['successful_walks']}"
        assert stats['failed_walks'] == len(failed_results), \
            f"Failed walks should be {len(failed_results)}, got {stats['failed_walks']}"
    
    @given(
        site_name=st.text(min_size=3, max_size=10, alphabet=st.characters(min_codepoint=65, max_codepoint=90)),
        device_count=st.integers(min_value=1, max_value=8),
        neighbors_per_device=st.integers(min_value=1, max_value=6)
    )
    def test_neighbor_processing_completeness_property(self, site_name, device_count, neighbors_per_device):
        """
        Property: Neighbor Processing Completeness
        
        For any device walk that discovers neighbors, all valid neighbors should be 
        processed and converted to DiscoveryNode objects.
        
        **Feature: site-specific-device-collection-reporting, Property: Neighbor Processing Completeness**
        **Validates: Requirements 2.3, 2.4**
        """
        # Create mocks
        connection_manager = self.create_mock_connection_manager(success_rate=1.0)
        device_collector = self.create_mock_device_collector(neighbors_per_device)
        site_validator = SiteAssociationValidator('*-CORE-*')
        
        walker = SiteDeviceWalker(connection_manager, device_collector, site_validator)
        
        # Create and walk devices
        total_expected_neighbors = 0
        all_results = []
        
        for i in range(device_count):
            hostname = f"{site_name}-SW-{i+1:02d}"
            ip_address = f"192.168.1.{i+1}"
            device_node = self.create_discovery_node(hostname, ip_address)
            
            result = walker.walk_site_device(device_node, site_name)
            all_results.append(result)
            
            if result.walk_success:
                total_expected_neighbors += neighbors_per_device
        
        # Property: All successful walks should have the expected number of neighbors
        for result in all_results:
            if result.walk_success:
                assert len(result.neighbors_found) == neighbors_per_device, \
                    f"Device {result.device_key} should have {neighbors_per_device} neighbors, got {len(result.neighbors_found)}"
        
        # Property: Process neighbors from all results
        all_processed_neighbors = []
        for result in all_results:
            if result.walk_success:
                processed = walker.process_site_neighbors(result.neighbors_found, site_name)
                all_processed_neighbors.extend(processed)
        
        # Property: Total processed neighbors should match total discovered
        assert len(all_processed_neighbors) == total_expected_neighbors, \
            f"Expected {total_expected_neighbors} processed neighbors, got {len(all_processed_neighbors)}"
        
        # Property: All processed neighbors should be valid DiscoveryNode objects
        for neighbor in all_processed_neighbors:
            assert isinstance(neighbor, DiscoveryNode), \
                f"Processed neighbor should be DiscoveryNode, got {type(neighbor)}"
            assert neighbor.hostname, "Neighbor should have hostname"
            assert neighbor.ip_address, "Neighbor should have IP address"
            assert neighbor.discovery_method == "site_walk", \
                f"Neighbor discovery method should be 'site_walk', got {neighbor.discovery_method}"
            assert not neighbor.is_seed, "Neighbors should not be marked as seed devices"
        
        # Property: Neighbor summary should be accurate
        summary = walker.get_site_neighbor_summary(all_results)
        successful_walks = len([r for r in all_results if r.walk_success])
        
        assert summary['total_devices_walked'] == device_count, \
            f"Summary should show {device_count} devices walked, got {summary['total_devices_walked']}"
        assert summary['successful_walks'] == successful_walks, \
            f"Summary should show {successful_walks} successful walks, got {summary['successful_walks']}"
        assert summary['total_neighbors_found'] == total_expected_neighbors, \
            f"Summary should show {total_expected_neighbors} neighbors found, got {summary['total_neighbors_found']}"
    
    @given(
        site_name=st.text(min_size=3, max_size=10, alphabet=st.characters(min_codepoint=65, max_codepoint=90)),
        walk_count=st.integers(min_value=5, max_value=20)
    )
    def test_statistics_accuracy_property(self, site_name, walk_count):
        """
        Property: Statistics Accuracy
        
        For any sequence of device walks, the reported statistics should accurately 
        reflect the actual walk results.
        
        **Feature: site-specific-device-collection-reporting, Property: Statistics Accuracy**
        **Validates: Requirements 7.2, 7.4**
        """
        # Create mocks with mixed success/failure
        connection_manager = self.create_mock_connection_manager(success_rate=0.7)  # 70% success
        device_collector = self.create_mock_device_collector(neighbors_per_device=3)
        site_validator = SiteAssociationValidator('*-CORE-*')
        
        walker = SiteDeviceWalker(connection_manager, device_collector, site_validator)
        
        # Reset statistics
        walker.reset_statistics()
        initial_stats = walker.get_walk_statistics()
        
        # Property: Initial statistics should be zero
        assert initial_stats['total_walks'] == 0, "Initial total walks should be 0"
        assert initial_stats['successful_walks'] == 0, "Initial successful walks should be 0"
        assert initial_stats['failed_walks'] == 0, "Initial failed walks should be 0"
        
        # Perform walks and track results
        actual_results = []
        for i in range(walk_count):
            hostname = f"{site_name}-SW-{i+1:02d}"
            ip_address = f"192.168.1.{i+1}"
            device_node = self.create_discovery_node(hostname, ip_address)
            
            result = walker.walk_site_device(device_node, site_name)
            actual_results.append(result)
        
        # Get final statistics
        final_stats = walker.get_walk_statistics()
        
        # Count actual results
        actual_successful = len([r for r in actual_results if r.walk_success])
        actual_failed = len([r for r in actual_results if not r.walk_success])
        actual_total_neighbors = sum(len(r.neighbors_found) for r in actual_results if r.walk_success)
        
        # Property: Statistics should match actual results
        assert final_stats['total_walks'] == walk_count, \
            f"Total walks should be {walk_count}, got {final_stats['total_walks']}"
        assert final_stats['successful_walks'] == actual_successful, \
            f"Successful walks should be {actual_successful}, got {final_stats['successful_walks']}"
        assert final_stats['failed_walks'] == actual_failed, \
            f"Failed walks should be {actual_failed}, got {final_stats['failed_walks']}"
        assert final_stats['neighbors_discovered'] == actual_total_neighbors, \
            f"Neighbors discovered should be {actual_total_neighbors}, got {final_stats['neighbors_discovered']}"
        
        # Property: Success rate should be calculated correctly
        expected_success_rate = actual_successful / walk_count if walk_count > 0 else 0.0
        assert abs(final_stats['success_rate'] - expected_success_rate) < 0.001, \
            f"Success rate should be {expected_success_rate}, got {final_stats['success_rate']}"
        
        # Property: Average neighbors per device should be calculated correctly
        expected_avg_neighbors = actual_total_neighbors / actual_successful if actual_successful > 0 else 0.0
        assert abs(final_stats['avg_neighbors_per_device'] - expected_avg_neighbors) < 0.001, \
            f"Average neighbors should be {expected_avg_neighbors}, got {final_stats['avg_neighbors_per_device']}"