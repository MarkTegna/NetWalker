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