"""
Integration tests for NetWalker Application

Tests the complete NetWalker application integration.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from netwalker.netwalker_app import NetWalkerApp


class TestNetWalkerAppIntegration:
    """Integration tests for NetWalker application"""
    
    def test_app_initialization(self):
        """Test that NetWalker app initializes properly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test configuration
            config_file = os.path.join(temp_dir, 'test_netwalker.ini')
            with open(config_file, 'w') as f:
                f.write("""[DEFAULT]
reports_directory = ./reports
logs_directory = ./logs
max_discovery_depth = 3
max_concurrent_connections = 5
""")
            
            # Create seed file
            seed_file = os.path.join(temp_dir, 'seed_file.csv')
            with open(seed_file, 'w') as f:
                f.write("test-device,192.168.1.1\n")
            
            # Change to temp directory
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                # Initialize app
                app = NetWalkerApp(config_file=config_file)
                success = app.initialize()
                
                assert success, "App should initialize successfully"
                assert app.initialized, "App should be marked as initialized"
                assert len(app.seed_devices) > 0, "Should load seed devices"
                
                # Test version info
                version_info = app.get_version_info()
                assert 'version' in version_info
                assert 'author' in version_info
                
                # Cleanup
                app.cleanup()
                
            finally:
                os.chdir(original_cwd)
    
    def test_app_context_manager(self):
        """Test NetWalker app as context manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, 'test_netwalker.ini')
            with open(config_file, 'w') as f:
                f.write("""[DEFAULT]
reports_directory = ./reports
logs_directory = ./logs
""")
            
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                # Test context manager
                with NetWalkerApp(config_file=config_file) as app:
                    assert app.initialized, "App should be initialized in context manager"
                
            finally:
                os.chdir(original_cwd)
    
    def test_cli_config_override(self):
        """Test CLI configuration overrides"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, 'test_netwalker.ini')
            with open(config_file, 'w') as f:
                f.write("""[DEFAULT]
max_discovery_depth = 2
""")
            
            cli_args = {
                'max_discovery_depth': 5,
                'reports_directory': './custom_reports'
            }
            
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                app = NetWalkerApp(config_file=config_file, cli_args=cli_args)
                success = app.initialize()
                
                assert success, "App should initialize with CLI overrides"
                
                # Check that CLI args override config file
                config = app.config_manager.get_config()
                assert config.get('max_discovery_depth') == 5, "CLI should override config file"
                assert config.get('reports_directory') == './custom_reports', "CLI should set custom directory"
                
                app.cleanup()
                
            finally:
                os.chdir(original_cwd)
    
    @patch('netwalker.netwalker_app.DiscoveryEngine')
    def test_discovery_process_mock(self, mock_discovery_engine):
        """Test discovery process with mocked components"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, 'test_netwalker.ini')
            with open(config_file, 'w') as f:
                f.write("""[DEFAULT]
reports_directory = ./reports
logs_directory = ./logs
""")
            
            # Create seed file
            seed_file = os.path.join(temp_dir, 'seed_file.csv')
            with open(seed_file, 'w') as f:
                f.write("test-device,192.168.1.1\n")
            
            # Mock discovery results
            mock_engine_instance = Mock()
            mock_engine_instance.discover_topology.return_value = {
                'discovery_time_seconds': 10.0,
                'total_devices': 1,
                'successful_connections': 1,
                'failed_connections': 0,
                'filtered_devices': 0,
                'boundary_devices': 0,
                'max_depth_reached': 1
            }
            
            mock_inventory = Mock()
            mock_inventory.get_all_devices.return_value = {
                'test-device:192.168.1.1': {
                    'hostname': 'test-device',
                    'ip_address': '192.168.1.1',
                    'platform': 'IOS',
                    'status': 'connected'
                }
            }
            mock_engine_instance.get_inventory.return_value = mock_inventory
            
            # Mock site collection attributes for compatibility
            mock_engine_instance.site_collection_enabled = False
            mock_engine_instance.site_collection_manager = None
            mock_engine_instance.site_boundaries = {}
            mock_engine_instance.site_collection_results = {}
            
            mock_discovery_engine.return_value = mock_engine_instance
            
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                with NetWalkerApp(config_file=config_file) as app:
                    # Test discovery
                    results = app.discover_network()
                    assert results['total_devices'] == 1, "Should return mocked results"
                    
                    # Test report generation
                    report_files = app.generate_reports()
                    assert len(report_files) > 0, "Should generate report files"
                    
                    # Test complete discovery process
                    success = app.run_discovery()
                    assert success, "Discovery process should succeed"
                
            finally:
                os.chdir(original_cwd)
    
    @patch('netwalker.netwalker_app.DiscoveryEngine')
    def test_discovery_process_with_site_collection(self, mock_discovery_engine):
        """Test discovery process with site collection enabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, 'test_netwalker.ini')
            with open(config_file, 'w') as f:
                f.write("""[DEFAULT]
reports_directory = ./reports
logs_directory = ./logs
enable_site_collection = true

[output]
site_boundary_pattern = *-CORE-*
generate_site_workbooks = true
""")
            
            # Create seed file with site boundary device
            seed_file = os.path.join(temp_dir, 'seed_file.csv')
            with open(seed_file, 'w') as f:
                f.write("BORO-CORE-01,192.168.1.1\n")
            
            # Mock discovery results with site collection
            mock_engine_instance = Mock()
            mock_engine_instance.discover_topology.return_value = {
                'discovery_time_seconds': 15.0,
                'total_devices': 2,
                'successful_connections': 2,
                'failed_connections': 0,
                'filtered_devices': 0,
                'boundary_devices': 1,
                'max_depth_reached': 1
            }
            
            mock_inventory = Mock()
            mock_inventory.get_all_devices.return_value = {
                'BORO-CORE-01:192.168.1.1': {
                    'hostname': 'BORO-CORE-01',
                    'ip_address': '192.168.1.1',
                    'platform': 'IOS',
                    'status': 'connected',
                    'site': 'BORO'
                },
                'BORO-SW-01:192.168.1.10': {
                    'hostname': 'BORO-SW-01',
                    'ip_address': '192.168.1.10',
                    'platform': 'IOS',
                    'status': 'connected',
                    'site': 'BORO'
                }
            }
            mock_engine_instance.get_inventory.return_value = mock_inventory
            
            # Mock site collection attributes
            mock_engine_instance.site_collection_enabled = True
            mock_site_manager = Mock()
            mock_site_manager.get_all_site_stats.return_value = {
                'BORO': {
                    'site_name': 'BORO',
                    'devices_queued': 2,
                    'devices_processed': 2,
                    'devices_successful': 2,
                    'devices_failed': 0,
                    'success_rate': 100.0
                }
            }
            mock_engine_instance.site_collection_manager = mock_site_manager
            mock_engine_instance.site_boundaries = {'BORO': ['BORO-CORE-01']}
            mock_engine_instance.site_collection_results = {
                'BORO': {
                    'success': True,
                    'statistics': {
                        'devices_processed': 2,
                        'devices_successful': 2,
                        'devices_failed': 0,
                        'success_rate': 100.0
                    }
                }
            }
            
            mock_discovery_engine.return_value = mock_engine_instance
            
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                with NetWalkerApp(config_file=config_file) as app:
                    # Test discovery with site collection
                    results = app.discover_network()
                    assert results['total_devices'] == 2, "Should return mocked results with site devices"
                    assert results['boundary_devices'] == 1, "Should identify boundary devices"
                    
                    # Test report generation (should include site workbooks)
                    report_files = app.generate_reports()
                    assert len(report_files) > 0, "Should generate report files including site workbooks"
                    
                    # Test complete discovery process
                    success = app.run_discovery()
                    assert success, "Discovery process with site collection should succeed"
                
            finally:
                os.chdir(original_cwd)