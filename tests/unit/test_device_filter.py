"""
Unit tests for device filter module
Feature: command-executor
Task: 2.1 - Create device filter module
"""

from unittest.mock import Mock, MagicMock
from netwalker.database.database_manager import DatabaseManager
from netwalker.executor.device_filter import DeviceFilter
from netwalker.executor.data_models import DeviceInfo


class TestDeviceFilter:
    """Unit tests for DeviceFilter class"""
    
    def test_filter_devices_with_matching_pattern(self):
        """
        Test filtering devices with a pattern that matches devices
        Requirements: 2.1, 2.2, 2.4, 2.5
        """
        # Create mock database manager
        db_config = {
            'enabled': True,
            'server': 'localhost',
            'database': 'test_db',
            'username': 'test',
            'password': 'test'
        }
        
        db_manager = DatabaseManager(db_config)
        db_manager.connection = MagicMock()
        db_manager.enabled = True
        
        # Mock cursor to return test devices
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('BORO-SW-UW01', '10.1.1.1'),
            ('BORO-SW-UW02', '10.1.1.2'),
            ('BORO-RTR-UW01', '10.1.1.10')
        ]
        
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Create device filter
        device_filter = DeviceFilter(db_manager)
        
        # Filter devices with pattern
        devices = device_filter.filter_devices('%-uw%')
        
        # Verify results
        assert len(devices) == 3, "Should return 3 matching devices"
        assert devices[0].device_name == 'BORO-SW-UW01'
        assert devices[0].ip_address == '10.1.1.1'
        assert devices[1].device_name == 'BORO-SW-UW02'
        assert devices[1].ip_address == '10.1.1.2'
        assert devices[2].device_name == 'BORO-RTR-UW01'
        assert devices[2].ip_address == '10.1.1.10'
        
        # Verify SQL query was executed with correct pattern
        # Note: execute is called twice - once for is_connected() check, once for actual query
        assert mock_cursor.execute.call_count >= 1, "Should execute at least one query"
        # Get the last call (the actual filter query)
        call_args = mock_cursor.execute.call_args
        # Pattern is in the second argument (tuple of parameters)
        assert call_args[0][1] == ('%-uw%',), "Should use the provided pattern in query parameters"
    
    def test_filter_devices_with_no_matches(self):
        """
        Test filtering devices with a pattern that matches no devices
        Requirements: 2.3
        """
        db_config = {
            'enabled': True,
            'server': 'localhost',
            'database': 'test_db',
            'username': 'test',
            'password': 'test'
        }
        
        db_manager = DatabaseManager(db_config)
        db_manager.connection = MagicMock()
        db_manager.enabled = True
        
        # Mock cursor to return empty result
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Create device filter
        device_filter = DeviceFilter(db_manager)
        
        # Filter devices with pattern that matches nothing
        devices = device_filter.filter_devices('NONEXISTENT%')
        
        # Verify empty result
        assert len(devices) == 0, "Should return empty list when no devices match"
    
    def test_filter_devices_with_database_disabled(self):
        """
        Test filtering devices when database is disabled
        Requirements: 2.3
        """
        db_config = {
            'enabled': False
        }
        
        db_manager = DatabaseManager(db_config)
        
        # Create device filter
        device_filter = DeviceFilter(db_manager)
        
        # Filter devices with database disabled
        devices = device_filter.filter_devices('%-uw%')
        
        # Verify empty result
        assert len(devices) == 0, "Should return empty list when database is disabled"
    
    def test_filter_devices_with_database_not_connected(self):
        """
        Test filtering devices when database is not connected
        Should attempt to connect
        Requirements: 2.1
        """
        db_config = {
            'enabled': True,
            'server': 'localhost',
            'database': 'test_db',
            'username': 'test',
            'password': 'test'
        }
        
        db_manager = DatabaseManager(db_config)
        db_manager.enabled = True
        db_manager.connection = None
        
        # Mock connect method to fail
        db_manager.connect = Mock(return_value=False)
        
        # Create device filter
        device_filter = DeviceFilter(db_manager)
        
        # Filter devices when not connected
        devices = device_filter.filter_devices('%-uw%')
        
        # Verify connect was attempted
        db_manager.connect.assert_called_once()
        
        # Verify empty result (connection failed)
        assert len(devices) == 0, "Should return empty list when connection fails"
    
    def test_filter_devices_returns_most_recent_ip(self):
        """
        Test that filter returns the most recent IP address for each device
        Requirements: 2.5
        """
        db_config = {
            'enabled': True,
            'server': 'localhost',
            'database': 'test_db',
            'username': 'test',
            'password': 'test'
        }
        
        db_manager = DatabaseManager(db_config)
        db_manager.connection = MagicMock()
        db_manager.enabled = True
        
        # Mock cursor to return device with most recent IP
        # The SQL query uses ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY last_seen DESC)
        # to get the most recent IP, so we only get one row per device
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('TEST-DEVICE', '192.168.1.100')  # Most recent IP
        ]
        
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Create device filter
        device_filter = DeviceFilter(db_manager)
        
        # Filter devices
        devices = device_filter.filter_devices('TEST%')
        
        # Verify result
        assert len(devices) == 1, "Should return one device"
        assert devices[0].device_name == 'TEST-DEVICE'
        assert devices[0].ip_address == '192.168.1.100', "Should return most recent IP"
    
    def test_filter_devices_with_wildcard_patterns(self):
        """
        Test filtering with various SQL wildcard patterns
        Requirements: 2.2
        """
        db_config = {
            'enabled': True,
            'server': 'localhost',
            'database': 'test_db',
            'username': 'test',
            'password': 'test'
        }
        
        db_manager = DatabaseManager(db_config)
        db_manager.connection = MagicMock()
        db_manager.enabled = True
        
        # Mock cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('BORO-SW-01', '10.1.1.1')
        ]
        
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Create device filter
        device_filter = DeviceFilter(db_manager)
        
        # Test with % wildcard (multiple characters)
        devices = device_filter.filter_devices('BORO%')
        assert len(devices) == 1
        
        # Test with _ wildcard (single character)
        mock_cursor.reset_mock()
        devices = device_filter.filter_devices('BORO-SW-0_')
        assert len(devices) == 1
        
        # Test with combination of wildcards
        mock_cursor.reset_mock()
        devices = device_filter.filter_devices('%SW%')
        assert len(devices) == 1
    
    def test_filter_devices_handles_query_error(self):
        """
        Test that filter handles database query errors gracefully
        Requirements: 2.3
        """
        db_config = {
            'enabled': True,
            'server': 'localhost',
            'database': 'test_db',
            'username': 'test',
            'password': 'test'
        }
        
        db_manager = DatabaseManager(db_config)
        db_manager.connection = MagicMock()
        db_manager.enabled = True
        
        # Mock cursor to raise exception
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Database query error")
        
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Create device filter
        device_filter = DeviceFilter(db_manager)
        
        # Filter devices (should handle error gracefully)
        devices = device_filter.filter_devices('%-uw%')
        
        # Verify empty result (error was handled)
        assert len(devices) == 0, "Should return empty list when query fails"
    
    def test_filter_devices_returns_deviceinfo_objects(self):
        """
        Test that filter returns proper DeviceInfo objects
        Requirements: 2.4
        """
        db_config = {
            'enabled': True,
            'server': 'localhost',
            'database': 'test_db',
            'username': 'test',
            'password': 'test'
        }
        
        db_manager = DatabaseManager(db_config)
        db_manager.connection = MagicMock()
        db_manager.enabled = True
        
        # Mock cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('TEST-DEVICE', '192.168.1.1')
        ]
        
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Create device filter
        device_filter = DeviceFilter(db_manager)
        
        # Filter devices
        devices = device_filter.filter_devices('TEST%')
        
        # Verify result type
        assert len(devices) == 1
        assert isinstance(devices[0], DeviceInfo), "Should return DeviceInfo objects"
        assert hasattr(devices[0], 'device_name'), "DeviceInfo should have device_name"
        assert hasattr(devices[0], 'ip_address'), "DeviceInfo should have ip_address"
