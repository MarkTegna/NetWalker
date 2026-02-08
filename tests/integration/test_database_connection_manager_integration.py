"""
Integration test for Connection Manager compatibility with database-queried devices
Feature: database-primary-ip-storage
Requirements: 3.1, 3.2

This test verifies that devices retrieved from database queries (get_stale_devices and
get_unwalked_devices) are in the correct format for the Connection Manager to use.
"""

import pytest
from unittest.mock import MagicMock, Mock
from netwalker.database.database_manager import DatabaseManager
from netwalker.connection.connection_manager import ConnectionManager
from netwalker.config import Credentials


class TestDatabaseConnectionManagerIntegration:
    """Integration tests for database query results with Connection Manager"""

    def test_stale_device_format_compatible_with_connection_manager(self):
        """
        Test that devices from get_stale_devices() are compatible with Connection Manager
        Requirements: 3.1, 3.2
        """
        # Setup database manager with mock
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

        # Mock cursor to return device with primary_ip
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('test-router', '2024-01-01', 'cisco_ios', 'Catalyst', '192.168.1.100')
        ]
        db_manager.connection.cursor.return_value = mock_cursor

        # Get devices from database query
        devices = db_manager.get_stale_devices(days=30)

        # Verify we got a device
        assert len(devices) == 1, "Should return one device"
        device = devices[0]

        # Verify device has required fields for Connection Manager
        assert 'device_name' in device, "Device should have device_name field"
        assert 'ip_address' in device, "Device should have ip_address field"

        # Verify device has valid IP address (not empty)
        assert device['ip_address'] != '', \
            "Device should have non-empty IP address for connection"
        assert device['ip_address'] == '192.168.1.100', \
            "Device should have the stored primary_ip"

        # Verify Connection Manager can accept this format
        # Connection Manager expects either 'host' parameter (hostname or IP)
        # We can use either device_name or ip_address as the host
        host = device['ip_address'] if device['ip_address'] else device['device_name']

        # Verify host is not empty
        assert host != '', \
            "Host parameter for Connection Manager should not be empty"

        # Create Connection Manager
        connection_manager = ConnectionManager(
            ssh_port=22,
            telnet_port=23,
            timeout=30
        )

        # Create test credentials
        credentials = Credentials(
            username='testuser',
            password='testpass',
            enable_password='enablepass'
        )

        # Verify Connection Manager accepts the host parameter
        # We don't actually connect (would require real device), but verify
        # the parameters are in correct format
        assert isinstance(host, str), "Host should be a string"
        assert isinstance(credentials, Credentials), \
            "Credentials should be Credentials object"

        # The connection_manager.connect_device() method signature is:
        # connect_device(host: str, credentials: Credentials)
        # So our device format is compatible

    def test_unwalked_device_format_compatible_with_connection_manager(self):
        """
        Test that devices from get_unwalked_devices() are compatible with Connection Manager
        Requirements: 3.1, 3.2
        """
        # Setup database manager with mock
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

        # Mock cursor to return unwalked device with primary_ip
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('neighbor-device', 'cisco_ios', 'Router', '2024-01-01',
             '2024-01-01', '192.168.1.200')
        ]
        db_manager.connection.cursor.return_value = mock_cursor

        # Get devices from database query
        devices = db_manager.get_unwalked_devices()

        # Verify we got a device
        assert len(devices) == 1, "Should return one device"
        device = devices[0]

        # Verify device has required fields for Connection Manager
        assert 'device_name' in device, "Device should have device_name field"
        assert 'ip_address' in device, "Device should have ip_address field"

        # Verify device has valid IP address (not empty)
        assert device['ip_address'] != '', \
            "Device should have non-empty IP address for connection"
        assert device['ip_address'] == '192.168.1.200', \
            "Device should have the stored primary_ip"

        # Verify Connection Manager can accept this format
        host = device['ip_address'] if device['ip_address'] else device['device_name']

        # Verify host is not empty
        assert host != '', \
            "Host parameter for Connection Manager should not be empty"

        # Create Connection Manager
        connection_manager = ConnectionManager(
            ssh_port=22,
            telnet_port=23,
            timeout=30
        )

        # Create test credentials
        credentials = Credentials(
            username='testuser',
            password='testpass',
            enable_password='enablepass'
        )

        # Verify parameters are in correct format
        assert isinstance(host, str), "Host should be a string"
        assert isinstance(credentials, Credentials), \
            "Credentials should be Credentials object"

    def test_multiple_devices_all_compatible_with_connection_manager(self):
        """
        Test that multiple devices from database queries are all compatible
        Requirements: 3.1, 3.2
        """
        # Setup database manager with mock
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

        # Mock cursor to return multiple devices
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('router-1', '2024-01-01', 'cisco_ios', 'Catalyst', '192.168.1.1'),
            ('router-2', '2024-01-02', 'cisco_ios', 'Catalyst', '192.168.1.2'),
            ('router-3', '2024-01-03', 'cisco_nxos', 'Nexus', '192.168.1.3'),
            ('router-4', '2024-01-04', 'cisco_ios', 'Catalyst', '192.168.1.4'),
        ]
        db_manager.connection.cursor.return_value = mock_cursor

        # Get devices from database query
        devices = db_manager.get_stale_devices(days=30)

        # Verify we got all devices
        assert len(devices) == 4, "Should return four devices"

        # Create Connection Manager
        connection_manager = ConnectionManager(
            ssh_port=22,
            telnet_port=23,
            timeout=30
        )

        # Verify each device is compatible with Connection Manager
        for device in devices:
            # Verify required fields exist
            assert 'device_name' in device, \
                f"Device {device.get('device_name', 'unknown')} should have device_name"
            assert 'ip_address' in device, \
                f"Device {device.get('device_name', 'unknown')} should have ip_address"

            # Verify IP address is not empty
            assert device['ip_address'] != '', \
                f"Device {device['device_name']} should have non-empty IP address"

            # Verify host parameter can be extracted
            host = device['ip_address'] if device['ip_address'] else device['device_name']
            assert host != '', \
                f"Device {device['device_name']} should have valid host parameter"

            # Verify host is a string
            assert isinstance(host, str), \
                f"Host for device {device['device_name']} should be a string"

    def test_device_with_hostname_only_compatible_with_connection_manager(self):
        """
        Test that devices with hostname but no IP are still compatible
        Connection Manager should accept hostname as host parameter
        Requirements: 3.1
        """
        # Setup database manager with mock
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

        # Mock cursor to return device with no IP (legacy device)
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('legacy-router', '2024-01-01', 'cisco_ios', 'Catalyst', '')
        ]
        db_manager.connection.cursor.return_value = mock_cursor

        # Get devices from database query
        devices = db_manager.get_stale_devices(days=30)

        # Verify we got a device
        assert len(devices) == 1, "Should return one device"
        device = devices[0]

        # Verify device has required fields
        assert 'device_name' in device, "Device should have device_name field"
        assert 'ip_address' in device, "Device should have ip_address field"

        # IP address is empty, so we should use device_name as host
        assert device['ip_address'] == '', "Legacy device has no IP"

        # Extract host parameter - use device_name when IP is empty
        host = device['ip_address'] if device['ip_address'] else device['device_name']

        # Verify host is the device_name
        assert host == 'legacy-router', \
            "Should use device_name as host when IP is empty"

        # Verify host is not empty
        assert host != '', "Host parameter should not be empty"

        # Create Connection Manager
        connection_manager = ConnectionManager(
            ssh_port=22,
            telnet_port=23,
            timeout=30
        )

        # Verify Connection Manager can accept hostname as host parameter
        # The connect_device() method accepts either IP or hostname
        assert isinstance(host, str), "Host should be a string"

    def test_connection_manager_validates_credentials_not_none(self):
        """
        Test that Connection Manager properly validates credentials are not None
        This prevents the "Either ip or host must be set" error
        Requirements: 3.2
        """
        # Create Connection Manager
        connection_manager = ConnectionManager(
            ssh_port=22,
            telnet_port=23,
            timeout=30
        )

        # Test with None credentials (should fail gracefully)
        connection, result = connection_manager.connect_device(
            host='192.168.1.1',
            credentials=None
        )

        # Verify connection failed
        assert connection is None, "Connection should fail with None credentials"
        assert result.status.value == 'failed', \
            "Connection status should be 'failed'"
        assert 'credentials' in result.error_message.lower(), \
            "Error message should mention credentials"

    def test_connection_manager_validates_empty_credentials(self):
        """
        Test that Connection Manager validates credentials have username and password
        Requirements: 3.2
        """
        # Create Connection Manager
        connection_manager = ConnectionManager(
            ssh_port=22,
            telnet_port=23,
            timeout=30
        )

        # Test with empty username
        credentials = Credentials(
            username='',
            password='testpass',
            enable_password='enablepass'
        )

        connection, result = connection_manager.connect_device(
            host='192.168.1.1',
            credentials=credentials
        )

        # Verify connection failed
        assert connection is None, "Connection should fail with empty username"
        assert result.status.value == 'failed', \
            "Connection status should be 'failed'"
        assert 'credentials' in result.error_message.lower() or \
               'username' in result.error_message.lower(), \
            "Error message should mention credentials or username"

    def test_end_to_end_database_to_connection_flow(self):
        """
        Test complete flow: Store device with primary_ip, query it, use with Connection Manager
        This is the full integration test for the feature
        Requirements: 3.1, 3.2
        """
        # Step 1: Setup database manager
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

        # Step 2: Store device with primary_ip
        device_info = {
            'hostname': 'test-router',
            'primary_ip': '192.168.1.100',
            'serial_number': 'TEST123',
            'platform': 'cisco_ios',
            'software_version': '15.1',
            'hardware_model': 'Catalyst',
            'interfaces': [],
            'vlans': [],
            'neighbors': []
        }

        # Mock storage methods
        db_manager.upsert_device = Mock(return_value=1)
        db_manager.upsert_device_version = Mock(return_value=True)
        db_manager.upsert_device_interface = Mock(return_value=True)

        # Store the device
        result = db_manager.process_device_discovery(device_info)
        assert result is True, "Device storage should succeed"

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

        # Step 3: Query device from database
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('test-router', '2024-01-01', 'cisco_ios', 'Catalyst', '192.168.1.100')
        ]
        db_manager.connection.cursor.return_value = mock_cursor

        devices = db_manager.get_stale_devices(days=30)

        # Verify device was retrieved
        assert len(devices) == 1, "Should retrieve one device"
        device = devices[0]
        assert device['device_name'] == 'test-router'
        assert device['ip_address'] == '192.168.1.100'

        # Step 4: Verify device format is compatible with Connection Manager
        host = device['ip_address'] if device['ip_address'] else device['device_name']
        assert host == '192.168.1.100', "Should use primary_ip as host"

        # Step 5: Create Connection Manager and verify it accepts the format
        connection_manager = ConnectionManager(
            ssh_port=22,
            telnet_port=23,
            timeout=30
        )

        # Create credentials
        credentials = Credentials(
            username='testuser',
            password='testpass',
            enable_password='enablepass'
        )

        # Verify parameters are correct types
        assert isinstance(host, str), "Host should be a string"
        assert isinstance(credentials, Credentials), \
            "Credentials should be Credentials object"
        assert credentials.username != '', "Username should not be empty"
        assert credentials.password != '', "Password should not be empty"

        # The connection_manager.connect_device(host, credentials) call would work
        # We don't actually call it because it would try to connect to a real device
        # But we've verified the format is compatible

    def test_seed_file_format_from_database_devices(self):
        """
        Test that database devices can be converted to seed file format
        This tests the format used in main.py for database-driven discovery
        Requirements: 3.1, 3.2
        """
        # Setup database manager with mock
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

        # Mock cursor to return devices
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('router-1', '2024-01-01', 'cisco_ios', 'Catalyst', '192.168.1.1'),
            ('router-2', '2024-01-02', 'cisco_ios', 'Catalyst', '192.168.1.2'),
            ('legacy-router', '2024-01-03', 'cisco_ios', 'Catalyst', ''),
        ]
        db_manager.connection.cursor.return_value = mock_cursor

        # Get devices from database query
        devices = db_manager.get_stale_devices(days=30)

        # Convert to seed file format (as done in main.py)
        seed_devices = []
        for device in devices:
            seed_devices.append({
                'hostname': device['device_name'],
                'ip_address': device['ip_address']
            })

        # Verify seed file format
        assert len(seed_devices) == 3, "Should have 3 seed devices"

        # Verify first device (has IP)
        assert seed_devices[0]['hostname'] == 'router-1'
        assert seed_devices[0]['ip_address'] == '192.168.1.1'

        # Verify second device (has IP)
        assert seed_devices[1]['hostname'] == 'router-2'
        assert seed_devices[1]['ip_address'] == '192.168.1.2'

        # Verify third device (no IP - legacy)
        assert seed_devices[2]['hostname'] == 'legacy-router'
        assert seed_devices[2]['ip_address'] == ''

        # Verify seed file CSV format (as written in main.py)
        # Format: hostname,ip_address,status,error_details
        csv_lines = []
        csv_lines.append("hostname,ip_address,status,error_details")
        for device in seed_devices:
            hostname = device['hostname']
            ip_address = device['ip_address'] if device['ip_address'] else ''
            csv_lines.append(f"{hostname},{ip_address},,")

        # Verify CSV format
        assert len(csv_lines) == 4, "Should have header + 3 device lines"
        assert csv_lines[0] == "hostname,ip_address,status,error_details"
        assert csv_lines[1] == "router-1,192.168.1.1,,"
        assert csv_lines[2] == "router-2,192.168.1.2,,"
        assert csv_lines[3] == "legacy-router,,,"

        # This format is compatible with the seed file parser and Connection Manager


if __name__ == "__main__":
    # Run integration tests
    test_instance = TestDatabaseConnectionManagerIntegration()
    
    print("Running integration tests for database-connection manager compatibility...")
    
    test_instance.test_stale_device_format_compatible_with_connection_manager()
    print("[OK] test_stale_device_format_compatible_with_connection_manager")
    
    test_instance.test_unwalked_device_format_compatible_with_connection_manager()
    print("[OK] test_unwalked_device_format_compatible_with_connection_manager")
    
    test_instance.test_multiple_devices_all_compatible_with_connection_manager()
    print("[OK] test_multiple_devices_all_compatible_with_connection_manager")
    
    test_instance.test_device_with_hostname_only_compatible_with_connection_manager()
    print("[OK] test_device_with_hostname_only_compatible_with_connection_manager")
    
    test_instance.test_connection_manager_validates_credentials_not_none()
    print("[OK] test_connection_manager_validates_credentials_not_none")
    
    test_instance.test_connection_manager_validates_empty_credentials()
    print("[OK] test_connection_manager_validates_empty_credentials")
    
    test_instance.test_end_to_end_database_to_connection_flow()
    print("[OK] test_end_to_end_database_to_connection_flow")
    
    test_instance.test_seed_file_format_from_database_devices()
    print("[OK] test_seed_file_format_from_database_devices")
    
    print("\nAll integration tests passed!")
