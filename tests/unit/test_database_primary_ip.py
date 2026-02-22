"""
Unit tests for database primary IP storage
Feature: database-primary-ip-storage
"""

from unittest.mock import Mock, MagicMock
from netwalker.database.database_manager import DatabaseManager


class TestPrimaryIPStorage:
    """Unit tests for primary IP storage functionality"""
    
    def test_primary_ip_storage_example(self):
        """
        Test specific device_info with known primary_ip
        Verify storage in device_interfaces table
        Requirements: 1.1, 1.2, 1.3
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
        
        # Mock the connection and methods
        db_manager.connection = MagicMock()
        db_manager.enabled = True
        
        # Mock upsert_device to return a device_id
        db_manager.upsert_device = Mock(return_value=(1, True))
        db_manager.upsert_device_version = Mock(return_value=True)
        db_manager.upsert_device_interface = Mock(return_value=True)
        
        # Create device_info with primary_ip
        device_info = {
            'hostname': 'test-router',
            'primary_ip': '192.168.1.1',
            'serial_number': 'ABC123',
            'platform': 'cisco_ios',
            'software_version': '15.1',
            'interfaces': [],
            'vlans': [],
            'neighbors': []
        }
        
        # Call process_device_discovery
        success, is_new = db_manager.process_device_discovery(device_info)
        
        # Verify success
        assert success is True, "process_device_discovery should return True"
        
        # Verify upsert_device was called
        db_manager.upsert_device.assert_called_once_with(device_info)
        
        # Verify upsert_device_interface was called for primary_ip
        calls = db_manager.upsert_device_interface.call_args_list
        
        # Find the call for primary_ip (should be first interface call)
        primary_ip_call = None
        for call in calls:
            args = call[0]
            if len(args) >= 2:
                interface_info = args[1]
                if interface_info.get('interface_name') == 'Primary Management':
                    primary_ip_call = interface_info
                    break
        
        # Verify primary_ip interface was stored
        assert primary_ip_call is not None, "Primary IP interface should be stored"
        assert primary_ip_call['interface_name'] == 'Primary Management'
        assert primary_ip_call['ip_address'] == '192.168.1.1'
        assert primary_ip_call['interface_type'] == 'management'
        assert primary_ip_call['subnet_mask'] == ''
    
    def test_primary_ip_storage_with_empty_primary_ip(self):
        """
        Test that empty primary_ip is handled gracefully
        Requirements: 4.1
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
        
        db_manager.upsert_device = Mock(return_value=(1, True))
        db_manager.upsert_device_version = Mock(return_value=True)
        db_manager.upsert_device_interface = Mock(return_value=True)
        
        # Create device_info with empty primary_ip
        device_info = {
            'hostname': 'test-router',
            'primary_ip': '',
            'serial_number': 'ABC123',
            'platform': 'cisco_ios',
            'software_version': '15.1',
            'interfaces': [],
            'vlans': [],
            'neighbors': []
        }
        
        # Call process_device_discovery
        success, is_new = db_manager.process_device_discovery(device_info)
        
        # Verify success (should not fail due to empty primary_ip)
        assert success is True, "process_device_discovery should return True even with empty primary_ip"
        
        # Verify upsert_device_interface was NOT called for primary_ip
        # (only called for regular interfaces, which is empty list)
        assert db_manager.upsert_device_interface.call_count == 0, "Should not store empty primary_ip"
    
    def test_primary_ip_storage_with_none_primary_ip(self):
        """
        Test that None primary_ip is handled gracefully
        Requirements: 4.1
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
        
        db_manager.upsert_device = Mock(return_value=(1, True))
        db_manager.upsert_device_version = Mock(return_value=True)
        db_manager.upsert_device_interface = Mock(return_value=True)
        
        # Create device_info without primary_ip
        device_info = {
            'hostname': 'test-router',
            'serial_number': 'ABC123',
            'platform': 'cisco_ios',
            'software_version': '15.1',
            'interfaces': [],
            'vlans': [],
            'neighbors': []
        }
        
        # Call process_device_discovery
        success, is_new = db_manager.process_device_discovery(device_info)
        
        # Verify success (should not fail due to missing primary_ip)
        assert success is True, "process_device_discovery should return True even without primary_ip"
        
        # Verify upsert_device_interface was NOT called for primary_ip
        assert db_manager.upsert_device_interface.call_count == 0, "Should not store None primary_ip"
    
    def test_primary_ip_storage_with_other_interfaces(self):
        """
        Test that primary_ip is stored before other interfaces
        Requirements: 1.1, 1.2, 1.3
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
        
        db_manager.upsert_device = Mock(return_value=(1, True))
        db_manager.upsert_device_version = Mock(return_value=True)
        db_manager.upsert_device_interface = Mock(return_value=True)
        
        # Create device_info with primary_ip and other interfaces
        device_info = {
            'hostname': 'test-router',
            'primary_ip': '192.168.1.1',
            'serial_number': 'ABC123',
            'platform': 'cisco_ios',
            'software_version': '15.1',
            'interfaces': [
                {
                    'interface_name': 'GigabitEthernet0/0',
                    'ip_address': '10.0.0.1',
                    'subnet_mask': '255.255.255.0',
                    'interface_type': 'physical'
                },
                {
                    'interface_name': 'Loopback0',
                    'ip_address': '1.1.1.1',
                    'subnet_mask': '255.255.255.255',
                    'interface_type': 'loopback'
                }
            ],
            'vlans': [],
            'neighbors': []
        }
        
        # Call process_device_discovery
        success, is_new = db_manager.process_device_discovery(device_info)
        
        # Verify success
        assert success is True, "process_device_discovery should return True"
        
        # Verify upsert_device_interface was called 3 times (primary_ip + 2 interfaces)
        assert db_manager.upsert_device_interface.call_count == 3, "Should store primary_ip and 2 interfaces"
        
        # Verify first call was for primary_ip
        first_call = db_manager.upsert_device_interface.call_args_list[0]
        args = first_call[0]
        interface_info = args[1]
        
        assert interface_info['interface_name'] == 'Primary Management', "First interface should be primary_ip"
        assert interface_info['ip_address'] == '192.168.1.1'
        assert interface_info['interface_type'] == 'management'


class TestQueryIntegration:
    """Unit tests for query integration with primary IP storage"""

    def test_get_stale_devices_returns_primary_ip(self):
        """
        Test that get_stale_devices returns device with primary_ip
        Store device with only primary_ip, query using get_stale_devices()
        Requirements: 2.1, 2.2, 2.3
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

        # Mock cursor for the query
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('test-device', '2024-01-01', 'cisco_ios', 'Catalyst', '192.168.1.1')
        ]

        db_manager.connection.cursor.return_value = mock_cursor

        # Call get_stale_devices
        devices = db_manager.get_stale_devices(days=30)

        # Verify results
        assert len(devices) == 1, "Should return one device"
        assert devices[0]['device_name'] == 'test-device'
        assert devices[0]['ip_address'] == '192.168.1.1', \
            "Should return primary_ip"
        assert devices[0]['ip_address'] != '', \
            "IP address should not be empty"

    def test_get_unwalked_devices_returns_primary_ip(self):
        """
        Test that get_unwalked_devices returns device with primary_ip
        Store device with only primary_ip, query using get_unwalked_devices()
        Requirements: 2.1, 2.2, 2.3
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

        # Mock cursor for the query
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('test-device', 'cisco_ios', 'router', '2024-01-01',
             '2024-01-01', '192.168.1.1')
        ]

        db_manager.connection.cursor.return_value = mock_cursor

        # Call get_unwalked_devices
        devices = db_manager.get_unwalked_devices()

        # Verify results
        assert len(devices) == 1, "Should return one device"
        assert devices[0]['device_name'] == 'test-device'
        assert devices[0]['ip_address'] == '192.168.1.1', \
            "Should return primary_ip"
        assert devices[0]['ip_address'] != '', \
            "IP address should not be empty"

    def test_query_prioritizes_primary_management_interface(self):
        """
        Test that queries prioritize 'Primary Management' interface
        When multiple interfaces exist, primary_ip should be returned first
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

        # Mock cursor - simulate SQL query that prioritizes Management interfaces
        # The actual SQL query uses ORDER BY with CASE statement to prioritize
        # Management interfaces first
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            # Device with primary_ip (Management interface has priority 1)
            ('test-device', '2024-01-01', 'cisco_ios', 'Catalyst', '192.168.1.1')
        ]

        db_manager.connection.cursor.return_value = mock_cursor

        # Call get_stale_devices
        devices = db_manager.get_stale_devices(days=30)

        # Verify primary_ip is returned (not some other interface IP)
        assert len(devices) == 1
        assert devices[0]['ip_address'] == '192.168.1.1', \
            "Should prioritize primary_ip (Management interface)"

    def test_query_handles_device_with_no_interfaces(self):
        """
        Test that queries handle devices with no interfaces gracefully
        Should return empty string for ip_address (COALESCE behavior)
        Requirements: 2.4, 5.1, 5.2
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

        # Mock cursor - device with no interfaces (COALESCE returns '')
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('legacy-device', '2024-01-01', 'cisco_ios', 'Catalyst', '')
        ]

        db_manager.connection.cursor.return_value = mock_cursor

        # Call get_stale_devices
        devices = db_manager.get_stale_devices(days=30)

        # Verify device is returned with empty ip_address
        assert len(devices) == 1
        assert devices[0]['device_name'] == 'legacy-device'
        assert devices[0]['ip_address'] == '', \
            "Should return empty string for device with no interfaces"
        # This is expected behavior - calling code should handle empty IP

    def test_full_integration_store_and_query_primary_ip(self):
        """
        Full integration test: Store device with primary_ip, then query it back
        This tests the complete flow from storage to retrieval
        Requirements: 2.1, 2.2, 2.3
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

        # Device info with only primary_ip (no other interfaces)
        device_info = {
            'hostname': 'test-router',
            'primary_ip': '192.168.1.100',
            'serial_number': 'TEST123',
            'platform': 'cisco_ios',
            'software_version': '15.1',
            'hardware_model': 'Catalyst',
            'interfaces': [],  # No other interfaces
            'vlans': [],
            'neighbors': []
        }

        # Mock the storage methods
        device_id = 1
        db_manager.upsert_device = Mock(return_value=(device_id, True))
        db_manager.upsert_device_version = Mock(return_value=True)
        db_manager.upsert_device_interface = Mock(return_value=True)

        # Step 1: Store the device with primary_ip
        success, is_new = db_manager.process_device_discovery(device_info)
        assert success is True, "Device storage should succeed"

        # Verify primary_ip was stored
        primary_ip_stored = False
        for call in db_manager.upsert_device_interface.call_args_list:
            args = call[0]
            if len(args) >= 2:
                interface_info = args[1]
                if (interface_info.get('interface_name') == 'Primary Management'
                        and interface_info.get('ip_address') == '192.168.1.100'):
                    primary_ip_stored = True
                    break

        assert primary_ip_stored, "Primary IP should be stored"

        # Step 2: Mock the query to return the stored primary_ip
        # Simulate what the database would return after storing
        mock_cursor = MagicMock()

        # For get_stale_devices
        mock_cursor.fetchall.return_value = [
            ('test-router', '2024-01-01', 'cisco_ios', 'Catalyst',
             '192.168.1.100')
        ]
        db_manager.connection.cursor.return_value = mock_cursor

        # Step 3: Query using get_stale_devices
        devices = db_manager.get_stale_devices(days=30)

        # Verify the device is returned with primary_ip
        assert len(devices) == 1, "Should return one device"
        assert devices[0]['device_name'] == 'test-router'
        assert devices[0]['ip_address'] == '192.168.1.100', \
            "Should return the stored primary_ip"
        assert devices[0]['ip_address'] != '', \
            "IP address should not be empty"

        # Step 4: Test with get_unwalked_devices
        # Reset mock for unwalked query
        mock_cursor.fetchall.return_value = [
            ('test-router', 'cisco_ios', '', '2024-01-01',
             '2024-01-01', '192.168.1.100')
        ]

        devices = db_manager.get_unwalked_devices()

        # Verify the device is returned with primary_ip
        assert len(devices) == 1, "Should return one device"
        assert devices[0]['device_name'] == 'test-router'
        assert devices[0]['ip_address'] == '192.168.1.100', \
            "Should return the stored primary_ip"
        assert devices[0]['ip_address'] != '', \
            "IP address should not be empty"



class TestBackwardCompatibility:
    """Unit tests for backward compatibility with legacy devices"""

    def test_query_legacy_device_without_primary_ip(self):
        """
        Test that queries handle legacy devices without primary_ip gracefully
        Query legacy devices without primary_ip, verify graceful handling with no errors
        Requirements: 5.1, 5.2, 5.3
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

        # Mock cursor - simulate a legacy device with NO interfaces at all
        # The COALESCE in the SQL query returns empty string when no interfaces exist
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('legacy-device-1', '2024-01-01', 'cisco_ios', 'Catalyst', ''),
            ('legacy-device-2', '2024-01-02', 'cisco_nxos', 'Nexus', '')
        ]

        db_manager.connection.cursor.return_value = mock_cursor

        # Call get_stale_devices - should not raise exception
        devices = db_manager.get_stale_devices(days=30)

        # Verify devices are returned (not filtered out)
        assert len(devices) == 2, "Should return legacy devices even without IP"

        # Verify device structure is correct
        assert devices[0]['device_name'] == 'legacy-device-1'
        assert devices[0]['ip_address'] == '', \
            "Legacy device without interfaces should have empty ip_address"

        assert devices[1]['device_name'] == 'legacy-device-2'
        assert devices[1]['ip_address'] == '', \
            "Legacy device without interfaces should have empty ip_address"

        # Verify no exceptions were raised
        # (test passes if we get here without errors)

    def test_query_legacy_device_with_other_interfaces_but_no_primary_ip(self):
        """
        Test that legacy devices with other interfaces (but no primary_ip) work correctly
        The query should return any available interface IP
        Requirements: 5.1, 5.2
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

        # Mock cursor - simulate a legacy device with interfaces but no primary_ip
        # The SQL query will return the first available interface IP
        # (prioritized by interface type: Management > Loopback > Vlan > Other)
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            # Device with Loopback interface (no primary_ip/Management interface)
            ('legacy-with-loopback', '2024-01-01', 'cisco_ios',
             'Catalyst', '1.1.1.1'),
            # Device with VLAN interface (no primary_ip/Management interface)
            ('legacy-with-vlan', '2024-01-02', 'cisco_nxos',
             'Nexus', '10.0.0.1')
        ]

        db_manager.connection.cursor.return_value = mock_cursor

        # Call get_stale_devices
        devices = db_manager.get_stale_devices(days=30)

        # Verify devices are returned with their available IPs
        assert len(devices) == 2, "Should return legacy devices with available IPs"

        assert devices[0]['device_name'] == 'legacy-with-loopback'
        assert devices[0]['ip_address'] == '1.1.1.1', \
            "Should return Loopback IP when no primary_ip exists"

        assert devices[1]['device_name'] == 'legacy-with-vlan'
        assert devices[1]['ip_address'] == '10.0.0.1', \
            "Should return VLAN IP when no primary_ip exists"

    def test_get_unwalked_devices_handles_legacy_devices(self):
        """
        Test that get_unwalked_devices handles legacy devices without primary_ip
        Requirements: 5.1, 5.2, 5.3
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

        # Mock cursor - simulate legacy unwalked devices
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            # Legacy device with no interfaces
            ('legacy-neighbor-1', 'cisco_ios', 'Router',
             '2024-01-01', '2024-01-01', ''),
            # Legacy device with an interface IP
            ('legacy-neighbor-2', 'cisco_nxos', 'Switch',
             '2024-01-02', '2024-01-02', '192.168.1.50')
        ]

        db_manager.connection.cursor.return_value = mock_cursor

        # Call get_unwalked_devices - should not raise exception
        devices = db_manager.get_unwalked_devices()

        # Verify devices are returned
        assert len(devices) == 2, "Should return legacy unwalked devices"

        # Verify first device (no IP)
        assert devices[0]['device_name'] == 'legacy-neighbor-1'
        assert devices[0]['ip_address'] == '', \
            "Legacy device without interfaces should have empty ip_address"

        # Verify second device (has IP)
        assert devices[1]['device_name'] == 'legacy-neighbor-2'
        assert devices[1]['ip_address'] == '192.168.1.50', \
            "Legacy device with interface should have that IP"

    def test_mixed_legacy_and_new_devices(self):
        """
        Test that queries handle a mix of legacy and new devices correctly
        New devices have primary_ip, legacy devices don't
        Requirements: 5.1, 5.2
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

        # Mock cursor - simulate mix of legacy and new devices
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            # New device with primary_ip (Primary Management interface)
            ('new-device-1', '2024-01-01', 'cisco_ios',
             'Catalyst', '192.168.1.100'),
            # Legacy device with no interfaces
            ('legacy-device-1', '2024-01-02', 'cisco_ios',
             'Catalyst', ''),
            # New device with primary_ip
            ('new-device-2', '2024-01-03', 'cisco_nxos',
             'Nexus', '192.168.1.101'),
            # Legacy device with Loopback interface
            ('legacy-device-2', '2024-01-04', 'cisco_ios',
             'Catalyst', '1.1.1.1')
        ]

        db_manager.connection.cursor.return_value = mock_cursor

        # Call get_stale_devices
        devices = db_manager.get_stale_devices(days=30)

        # Verify all devices are returned (no filtering)
        assert len(devices) == 4, "Should return both legacy and new devices"

        # Verify new devices have IPs
        assert devices[0]['device_name'] == 'new-device-1'
        assert devices[0]['ip_address'] == '192.168.1.100'

        assert devices[2]['device_name'] == 'new-device-2'
        assert devices[2]['ip_address'] == '192.168.1.101'

        # Verify legacy devices are handled correctly
        assert devices[1]['device_name'] == 'legacy-device-1'
        assert devices[1]['ip_address'] == '', \
            "Legacy device without interfaces has empty IP"

        assert devices[3]['device_name'] == 'legacy-device-2'
        assert devices[3]['ip_address'] == '1.1.1.1', \
            "Legacy device with interface has that IP"

    def test_no_errors_with_empty_ip_address(self):
        """
        Test that the system doesn't crash when processing devices with empty IP
        This verifies the calling code can handle empty ip_address gracefully
        Requirements: 5.3
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

        # Mock cursor - device with empty IP
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('device-no-ip', '2024-01-01', 'cisco_ios', 'Catalyst', '')
        ]

        db_manager.connection.cursor.return_value = mock_cursor

        # Call get_stale_devices - should not raise exception
        try:
            devices = db_manager.get_stale_devices(days=30)

            # Verify device is returned
            assert len(devices) == 1
            assert devices[0]['device_name'] == 'device-no-ip'
            assert devices[0]['ip_address'] == ''

            # Test passes if no exception is raised
            success = True
        except Exception as e:
            success = False
            error_msg = str(e)

        assert success, \
            f"Should handle empty ip_address without errors, got: {error_msg if not success else 'none'}"

    def test_backward_compatibility_with_database_disabled(self):
        """
        Test that backward compatibility works even when database is disabled
        Requirements: 5.3
        """
        db_config = {
            'enabled': False,
            'server': 'localhost',
            'database': 'test_db',
            'username': 'test',
            'password': 'test'
        }

        db_manager = DatabaseManager(db_config)

        # Call get_stale_devices with database disabled
        devices = db_manager.get_stale_devices(days=30)

        # Should return empty list, not raise exception
        assert devices == [], \
            "Should return empty list when database is disabled"

        # Call get_unwalked_devices with database disabled
        devices = db_manager.get_unwalked_devices()

        # Should return empty list, not raise exception
        assert devices == [], \
            "Should return empty list when database is disabled"
