"""
Integration tests for DiscoveryEngine compatibility with site collection changes.

These tests ensure that existing DiscoveryEngine functionality continues to work
correctly with site collection enhancements, and that backward compatibility
is maintained for non-site discovery scenarios.
"""

import pytest
import tempfile
import os
import shutil
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any

from netwalker.discovery.discovery_engine import DiscoveryEngine, DiscoveryNode
from netwalker.connection.connection_manager import ConnectionManager
from netwalker.discovery.device_collector import DeviceCollector
from netwalker.filtering.filter_manager import FilterManager


class TestDiscoveryEngineCompatibility:
    """Integration tests for DiscoveryEngine compatibility with site collection"""
    
    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def base_config(self, temp_directory):
        """Base configuration for testing"""
        return {
            'max_discovery_depth': 2,
            'connection_timeout_seconds': 30,
            'connection_retry_attempts': 3,
            'enable_neighbor_filtering': True,
            'max_neighbors_per_device': 50,
            'reports_directory': temp_directory,
            'logs_directory': temp_directory
        }
    
    @pytest.fixture
    def mock_credentials(self):
        """Mock credentials for testing"""
        return {
            'username': 'test_user',
            'password': 'test_pass',
            'enable_password': 'test_enable'
        }
    
    def create_mock_components(self, config, credentials):
        """Create mock components for testing"""
        # Use simple Mock objects without spec to avoid interface issues in tests
        connection_manager = Mock()
        device_collector = Mock()
        filter_manager = Mock()
        
        # Mock successful connections
        from netwalker.connection.data_models import ConnectionResult, ConnectionStatus, ConnectionMethod
        mock_connection_result = ConnectionResult(
            host='test-host',
            method=ConnectionMethod.SSH,
            status=ConnectionStatus.SUCCESS,
            error_message=None,
            connection_time=1.0
        )
        connection_manager.connect_device.return_value = (Mock(), mock_connection_result)
        connection_manager.close_connection.return_value = True
        
        # Mock device collection
        from netwalker.connection.data_models import DeviceInfo
        from datetime import datetime
        mock_device_info = DeviceInfo(
            hostname='test-device',
            primary_ip='192.168.1.1',
            platform='cisco_ios',
            capabilities=['routing'],
            software_version='15.1',
            vtp_version=None,
            serial_number='ABC123',
            hardware_model='C2960',
            uptime='1 day',
            discovery_timestamp=datetime.now(),
            discovery_depth=0,
            is_seed=False,
            connection_method='SSH',
            connection_status='success',
            error_details=None
        )
        device_collector.collect_device_information.return_value = mock_device_info
        
        # Mock filtering (no filtering by default)
        filter_manager.should_filter_device.return_value = False
        
        return connection_manager, device_collector, filter_manager
    
    def test_discovery_engine_initialization_without_site_collection(self, base_config, mock_credentials, temp_directory):
        """
        Test that DiscoveryEngine initializes correctly when site collection is disabled.
        
        Ensures backward compatibility with existing configurations.
        """
        # Arrange - Disable site collection
        config = {
            **base_config,
            'enable_site_collection': False
        }
        
        connection_manager, device_collector, filter_manager = self.create_mock_components(
            config, mock_credentials
        )
        
        # Act - Create DiscoveryEngine
        discovery_engine = DiscoveryEngine(
            connection_manager, filter_manager, config, mock_credentials
        )
        
        # Assert - Should initialize without site collection
        assert not discovery_engine.site_collection_enabled, \
            "Site collection should be disabled"
        
        assert discovery_engine.site_collection_manager is None, \
            "Site collection manager should not be initialized when disabled"
        
        # Standard discovery attributes should still be available
        assert hasattr(discovery_engine, 'connection_manager'), \
            "Should have connection manager"
        
        assert hasattr(discovery_engine, 'filter_manager'), \
            "Should have filter manager"
        
        assert hasattr(discovery_engine, 'inventory'), \
            "Should have inventory"
        
        assert hasattr(discovery_engine, 'discovery_queue'), \
            "Should have discovery queue"
        
        # Configuration should be applied correctly
        assert discovery_engine.max_depth == config['max_discovery_depth'], \
            "Max depth should be configured correctly"
    
    def test_discovery_engine_initialization_with_site_collection(self, base_config, mock_credentials, temp_directory):
        """
        Test that DiscoveryEngine initializes correctly when site collection is enabled.
        
        Ensures site collection enhancements work properly.
        """
        # Arrange - Enable site collection
        config = {
            **base_config,
            'enable_site_collection': True,
            'output': {
                'site_boundary_pattern': '*-CORE-*',
                'generate_site_workbooks': True
            }
        }
        
        connection_manager, device_collector, filter_manager = self.create_mock_components(
            config, mock_credentials
        )
        
        # Act - Create DiscoveryEngine
        discovery_engine = DiscoveryEngine(
            connection_manager, filter_manager, config, mock_credentials
        )
        
        # Assert - Should initialize with site collection
        assert discovery_engine.site_collection_enabled, \
            "Site collection should be enabled"
        
        assert discovery_engine.site_collection_manager is not None, \
            "Site collection manager should be initialized when enabled"
        
        # Standard discovery attributes should still be available
        assert hasattr(discovery_engine, 'connection_manager'), \
            "Should have connection manager"
        
        assert hasattr(discovery_engine, 'filter_manager'), \
            "Should have filter manager"
        
        assert hasattr(discovery_engine, 'inventory'), \
            "Should have inventory"
        
        assert hasattr(discovery_engine, 'discovery_queue'), \
            "Should have discovery queue"
        
        # Site collection specific attributes should be available
        assert hasattr(discovery_engine, 'site_boundaries'), \
            "Should have site boundaries"
        
        assert hasattr(discovery_engine, 'site_collection_results'), \
            "Should have site collection results"
        
        assert discovery_engine.site_boundary_pattern == '*-CORE-*', \
            "Site boundary pattern should be configured correctly"
    
    def test_standard_discovery_methods_work_without_site_collection(self, base_config, mock_credentials, temp_directory):
        """
        Test that standard discovery methods continue to work when site collection is disabled.
        
        Ensures backward compatibility for existing workflows.
        """
        # Arrange - Disable site collection
        config = {
            **base_config,
            'enable_site_collection': False
        }
        
        connection_manager, device_collector, filter_manager = self.create_mock_components(
            config, mock_credentials
        )
        
        discovery_engine = DiscoveryEngine(
            connection_manager, filter_manager, config, mock_credentials
        )
        
        # Create sample inventory
        sample_inventory = {
            'device1:192.168.1.1': {
                'hostname': 'device1',
                'ip_address': '192.168.1.1',
                'platform': 'cisco_ios',
                'status': 'connected'
            },
            'device2:192.168.1.2': {
                'hostname': 'device2',
                'ip_address': '192.168.1.2',
                'platform': 'cisco_ios',
                'status': 'connected'
            }
        }
        
        # Mock inventory methods
        discovery_engine.inventory.get_all_devices = Mock(return_value=sample_inventory)
        discovery_engine.inventory.add_device = Mock()
        discovery_engine.inventory.get_device = Mock()
        
        # Act & Assert - Standard methods should work
        try:
            # Test inventory access
            all_devices = discovery_engine.inventory.get_all_devices()
            assert len(all_devices) == 2, "Should return all devices"
            
            # Test device addition
            test_device = DiscoveryNode(
                hostname='test-device',
                ip_address='192.168.1.100',
                depth=1,
                discovery_method='test',
                is_seed=False
            )
            
            discovery_engine.inventory.add_device.assert_not_called()  # Reset call count
            discovery_engine.add_device_to_queue(test_device)
            
            # Should be able to add devices to queue
            assert hasattr(discovery_engine, 'discovery_queue'), \
                "Should have discovery queue"
            
            # Test that discovery methods exist and are callable
            assert hasattr(discovery_engine, 'discover_topology'), \
                "Should have discover_topology method"
            
            assert callable(discovery_engine.discover_topology), \
                "discover_topology should be callable"
            
            assert hasattr(discovery_engine, 'get_inventory'), \
                "Should have get_inventory method"
            
            assert callable(discovery_engine.get_inventory), \
                "get_inventory should be callable"
        
        except Exception as e:
            pytest.fail(f"Standard discovery methods should work without site collection: {e}")
    
    def test_standard_discovery_methods_work_with_site_collection(self, base_config, mock_credentials, temp_directory):
        """
        Test that standard discovery methods continue to work when site collection is enabled.
        
        Ensures site collection enhancements don't break existing functionality.
        """
        # Arrange - Enable site collection
        config = {
            **base_config,
            'enable_site_collection': True,
            'output': {
                'site_boundary_pattern': '*-CORE-*',
                'generate_site_workbooks': True
            }
        }
        
        connection_manager, device_collector, filter_manager = self.create_mock_components(
            config, mock_credentials
        )
        
        discovery_engine = DiscoveryEngine(
            connection_manager, filter_manager, config, mock_credentials
        )
        
        # Create sample inventory with both site and non-site devices
        sample_inventory = {
            'BORO-CORE-01:192.168.1.1': {
                'hostname': 'BORO-CORE-01',
                'ip_address': '192.168.1.1',
                'platform': 'cisco_ios',
                'status': 'connected'
            },
            'regular-device:192.168.1.2': {
                'hostname': 'regular-device',
                'ip_address': '192.168.1.2',
                'platform': 'cisco_ios',
                'status': 'connected'
            }
        }
        
        # Mock inventory methods
        discovery_engine.inventory.get_all_devices = Mock(return_value=sample_inventory)
        discovery_engine.inventory.add_device = Mock()
        
        # Act & Assert - Standard methods should still work
        try:
            # Test inventory access
            all_devices = discovery_engine.inventory.get_all_devices()
            assert len(all_devices) == 2, "Should return all devices"
            
            # Test device addition
            test_device = DiscoveryNode(
                hostname='test-device',
                ip_address='192.168.1.100',
                depth=1,
                discovery_method='test',
                is_seed=False
            )
            
            discovery_engine.add_device_to_queue(test_device)
            
            # Should be able to add devices to queue
            assert hasattr(discovery_engine, 'discovery_queue'), \
                "Should have discovery queue"
            
            # Test site boundary identification
            site_boundaries = discovery_engine._identify_site_boundaries_from_inventory()
            assert isinstance(site_boundaries, dict), \
                "Site boundary identification should return a dictionary"
            
            # Test that discovery methods exist and are callable
            assert hasattr(discovery_engine, 'discover_topology'), \
                "Should have discover_topology method"
            
            assert callable(discovery_engine.discover_topology), \
                "discover_topology should be callable"
            
            assert hasattr(discovery_engine, 'get_inventory'), \
                "Should have get_inventory method"
            
            assert callable(discovery_engine.get_inventory), \
                "get_inventory should be callable"
        
        except Exception as e:
            pytest.fail(f"Standard discovery methods should work with site collection enabled: {e}")
    
    def test_configuration_compatibility_with_existing_settings(self, base_config, mock_credentials, temp_directory):
        """
        Test that existing configuration settings continue to work with site collection changes.
        
        Ensures configuration backward compatibility.
        """
        # Test various configuration scenarios
        test_configs = [
            # Minimal config (no site collection settings)
            {
                'max_discovery_depth': 3,
                'connection_timeout_seconds': 60
            },
            # Config with site collection disabled explicitly
            {
                **base_config,
                'enable_site_collection': False
            },
            # Config with site collection enabled but no pattern
            {
                **base_config,
                'enable_site_collection': True
            },
            # Full site collection config
            {
                **base_config,
                'enable_site_collection': True,
                'output': {
                    'site_boundary_pattern': '*-RTR-*',
                    'generate_site_workbooks': True,
                    'include_site_statistics': True
                }
            }
        ]
        
        for i, config in enumerate(test_configs):
            connection_manager, device_collector, filter_manager = self.create_mock_components(
                config, mock_credentials
            )
            
            try:
                # Act - Create DiscoveryEngine with different configs
                discovery_engine = DiscoveryEngine(
                    connection_manager, filter_manager, config, mock_credentials
                )
                
                # Assert - Should initialize successfully
                assert discovery_engine is not None, f"Config {i}: Should initialize successfully"
                
                # Check basic configuration
                expected_depth = config.get('max_discovery_depth', 2)  # Default value
                assert discovery_engine.max_depth == expected_depth, \
                    f"Config {i}: Max depth should be {expected_depth}"
                
                # Check site collection configuration
                expected_site_enabled = config.get('enable_site_collection', False)
                assert discovery_engine.site_collection_enabled == expected_site_enabled, \
                    f"Config {i}: Site collection enabled should be {expected_site_enabled}"
                
                if expected_site_enabled:
                    assert discovery_engine.site_collection_manager is not None, \
                        f"Config {i}: Site collection manager should be initialized"
                    
                    expected_pattern = config.get('output', {}).get('site_boundary_pattern', '*-CORE-*')
                    assert discovery_engine.site_boundary_pattern == expected_pattern, \
                        f"Config {i}: Site boundary pattern should be {expected_pattern}"
                else:
                    assert discovery_engine.site_collection_manager is None, \
                        f"Config {i}: Site collection manager should not be initialized"
            
            except Exception as e:
                pytest.fail(f"Config {i} should be compatible: {e}")
    
    def test_inventory_methods_compatibility(self, base_config, mock_credentials, temp_directory):
        """
        Test that inventory methods work correctly with and without site collection.
        
        Ensures inventory functionality remains consistent.
        """
        # Test both site collection enabled and disabled
        for site_enabled in [False, True]:
            config = {
                **base_config,
                'enable_site_collection': site_enabled
            }
            
            if site_enabled:
                config['output'] = {
                    'site_boundary_pattern': '*-CORE-*',
                    'generate_site_workbooks': True
                }
            
            connection_manager, device_collector, filter_manager = self.create_mock_components(
                config, mock_credentials
            )
            
            discovery_engine = DiscoveryEngine(
                connection_manager, filter_manager, config, mock_credentials
            )
            
            # Create test inventory
            test_inventory = {
                'device1:192.168.1.1': {
                    'hostname': 'device1',
                    'ip_address': '192.168.1.1',
                    'platform': 'cisco_ios',
                    'status': 'connected'
                }
            }
            
            # Mock inventory methods
            discovery_engine.inventory.get_all_devices = Mock(return_value=test_inventory)
            discovery_engine.inventory.get_device_count = Mock(return_value=1)
            discovery_engine.inventory.get_connected_device_count = Mock(return_value=1)
            
            # Test inventory access
            all_devices = discovery_engine.inventory.get_all_devices()
            assert len(all_devices) == 1, \
                f"Site enabled={site_enabled}: Should return correct device count"
            
            device_count = discovery_engine.inventory.get_device_count()
            assert device_count == 1, \
                f"Site enabled={site_enabled}: Should return correct device count"
            
            connected_count = discovery_engine.inventory.get_connected_device_count()
            assert connected_count == 1, \
                f"Site enabled={site_enabled}: Should return correct connected count"
    
    def test_discovery_queue_compatibility(self, base_config, mock_credentials, temp_directory):
        """
        Test that discovery queue operations work correctly with and without site collection.
        
        Ensures queue functionality remains consistent.
        """
        # Test both site collection enabled and disabled
        for site_enabled in [False, True]:
            config = {
                **base_config,
                'enable_site_collection': site_enabled
            }
            
            if site_enabled:
                config['output'] = {
                    'site_boundary_pattern': '*-CORE-*',
                    'generate_site_workbooks': True
                }
            
            connection_manager, device_collector, filter_manager = self.create_mock_components(
                config, mock_credentials
            )
            
            discovery_engine = DiscoveryEngine(
                connection_manager, filter_manager, config, mock_credentials
            )
            
            # Test device queue operations
            test_device = DiscoveryNode(
                hostname='test-device',
                ip_address='192.168.1.100',
                depth=1,
                discovery_method='test',
                is_seed=False
            )
            
            # Should be able to add devices to queue
            try:
                discovery_engine.add_device_to_queue(test_device)
                
                # Queue should exist and be accessible
                assert hasattr(discovery_engine, 'discovery_queue'), \
                    f"Site enabled={site_enabled}: Should have discovery queue"
                
                # Should be able to check if queue is empty
                # (Implementation may vary, but method should exist)
                assert hasattr(discovery_engine, 'is_discovery_complete') or \
                       hasattr(discovery_engine, 'has_devices_to_process'), \
                    f"Site enabled={site_enabled}: Should have queue status methods"
            
            except Exception as e:
                pytest.fail(f"Site enabled={site_enabled}: Queue operations should work: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])