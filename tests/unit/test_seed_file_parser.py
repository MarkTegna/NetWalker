"""
Unit tests for seed file parser enhancements
Feature: database-ip-lookup-for-seed-devices
Task: 4.9 - Write unit tests for seed file parser enhancements

Tests cover:
- Blank IP detection (empty string, whitespace variations)
- Explicit IP bypass (no resolution triggered)
- Device skipping on resolution failure
- Attribute preservation during resolution
- Entry order preservation

Requirements: 1.1, 1.2, 1.3, 3.3, 5.1, 7.2, 7.4
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, MagicMock, patch
from netwalker.netwalker_app import NetWalkerApp


class TestSeedFileParserEnhancements:
    """Unit tests for seed file parser enhancements"""

    def create_temp_seed_file(self, content):
        """Helper to create a temporary seed file with given content"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_file.write(content)
        temp_file.close()
        return temp_file.name

    def test_blank_ip_detection_empty_string(self):
        """
        Test blank IP detection with empty string
        Validates Requirements: 1.1, 1.2
        """
        # Create seed file with empty IP
        seed_content = """hostname,ip,status
ROUTER-01,,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True
            app.db_manager.get_primary_ip_by_hostname.return_value = '192.168.1.1'

            # Parse seed file
            with patch('netwalker.netwalker_app.logger') as mock_logger:
                result = app._parse_seed_file(seed_file)

                # Verify blank IP was detected and resolution was triggered
                mock_logger.info.assert_any_call(
                    'Blank IP detected for ROUTER-01, attempting resolution...'
                )

                # Verify device was added with resolved IP
                assert len(result) == 1
                assert result[0] == 'ROUTER-01:192.168.1.1'

                # Verify database lookup was called
                app.db_manager.get_primary_ip_by_hostname.assert_called_once_with('ROUTER-01')

        finally:
            os.unlink(seed_file)

    def test_blank_ip_detection_whitespace_only(self):
        """
        Test blank IP detection with whitespace-only string
        Validates Requirements: 1.1, 1.2
        """
        # Create seed file with whitespace-only IP
        seed_content = """hostname,ip,status
ROUTER-02,   ,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True
            app.db_manager.get_primary_ip_by_hostname.return_value = '10.0.0.5'

            # Parse seed file
            with patch('netwalker.netwalker_app.logger') as mock_logger:
                result = app._parse_seed_file(seed_file)

                # Verify blank IP was detected
                mock_logger.info.assert_any_call(
                    'Blank IP detected for ROUTER-02, attempting resolution...'
                )

                # Verify device was added with resolved IP
                assert len(result) == 1
                assert result[0] == 'ROUTER-02:10.0.0.5'

        finally:
            os.unlink(seed_file)

    def test_blank_ip_detection_tabs_and_spaces(self):
        """
        Test blank IP detection with tabs and spaces
        Validates Requirements: 1.1, 1.2
        """
        # Create seed file with tabs and spaces in IP field
        seed_content = """hostname,ip,status
ROUTER-03,\t  \t,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True
            app.db_manager.get_primary_ip_by_hostname.return_value = '172.16.0.1'

            # Parse seed file
            with patch('netwalker.netwalker_app.logger'):
                result = app._parse_seed_file(seed_file)

                # Verify device was added with resolved IP
                assert len(result) == 1
                assert result[0] == 'ROUTER-03:172.16.0.1'

        finally:
            os.unlink(seed_file)

    def test_explicit_ip_bypass_no_resolution(self):
        """
        Test that explicit IP bypasses resolution (no database/DNS lookup)
        Validates Requirements: 5.1
        """
        # Create seed file with explicit IP
        seed_content = """hostname,ip,status
ROUTER-04,192.168.100.1,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True

            # Parse seed file
            with patch('netwalker.netwalker_app.logger') as mock_logger:
                with patch('socket.gethostbyname') as mock_dns:
                    result = app._parse_seed_file(seed_file)

                    # Verify device was added with explicit IP
                    assert len(result) == 1
                    assert result[0] == 'ROUTER-04:192.168.100.1'

                    # Verify NO resolution was attempted
                    app.db_manager.get_primary_ip_by_hostname.assert_not_called()
                    mock_dns.assert_not_called()

                    # Verify no "Blank IP detected" message
                    info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                    assert not any('Blank IP detected' in msg for msg in info_calls)

        finally:
            os.unlink(seed_file)

    def test_explicit_ip_bypass_multiple_devices(self):
        """
        Test that multiple devices with explicit IPs bypass resolution
        Validates Requirements: 5.1
        """
        # Create seed file with multiple explicit IPs
        seed_content = """hostname,ip,status
ROUTER-05,10.1.1.1,pending
ROUTER-06,10.1.1.2,pending
ROUTER-07,10.1.1.3,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True

            # Parse seed file
            result = app._parse_seed_file(seed_file)

            # Verify all devices were added with explicit IPs
            assert len(result) == 3
            assert result[0] == 'ROUTER-05:10.1.1.1'
            assert result[1] == 'ROUTER-06:10.1.1.2'
            assert result[2] == 'ROUTER-07:10.1.1.3'

            # Verify NO resolution was attempted
            app.db_manager.get_primary_ip_by_hostname.assert_not_called()

        finally:
            os.unlink(seed_file)

    def test_device_skipping_on_resolution_failure(self):
        """
        Test that devices are skipped when resolution fails
        Validates Requirements: 3.3
        """
        # Create seed file with blank IP
        seed_content = """hostname,ip,status
ROUTER-08,,pending
ROUTER-09,192.168.1.9,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True
            app.db_manager.get_primary_ip_by_hostname.return_value = None

            # Mock DNS to also fail
            with patch('socket.gethostbyname', side_effect=Exception("DNS failed")):
                with patch('netwalker.netwalker_app.logger') as mock_logger:
                    result = app._parse_seed_file(seed_file)

                    # Verify only the device with explicit IP was added
                    assert len(result) == 1
                    assert result[0] == 'ROUTER-09:192.168.1.9'

                    # Verify warning was logged for skipped device
                    mock_logger.warning.assert_any_call(
                        'Skipping ROUTER-08: could not resolve IP address'
                    )

        finally:
            os.unlink(seed_file)

    def test_device_skipping_multiple_failures(self):
        """
        Test that multiple devices are skipped when resolution fails
        Validates Requirements: 3.3
        """
        # Create seed file with multiple blank IPs
        seed_content = """hostname,ip,status
ROUTER-10,,pending
ROUTER-11,,pending
ROUTER-12,192.168.1.12,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True
            app.db_manager.get_primary_ip_by_hostname.return_value = None

            # Mock DNS to also fail
            with patch('socket.gethostbyname', side_effect=Exception("DNS failed")):
                with patch('netwalker.netwalker_app.logger') as mock_logger:
                    result = app._parse_seed_file(seed_file)

                    # Verify only the device with explicit IP was added
                    assert len(result) == 1
                    assert result[0] == 'ROUTER-12:192.168.1.12'

                    # Verify warnings were logged for both skipped devices
                    warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
                    assert any('Skipping ROUTER-10' in msg for msg in warning_calls)
                    assert any('Skipping ROUTER-11' in msg for msg in warning_calls)

        finally:
            os.unlink(seed_file)

    def test_attribute_preservation_hostname(self):
        """
        Test that hostname is preserved during resolution
        Validates Requirements: 7.2
        """
        # Create seed file with blank IP
        seed_content = """hostname,ip,status
SPECIAL-ROUTER-NAME,,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True
            app.db_manager.get_primary_ip_by_hostname.return_value = '192.168.1.100'

            # Parse seed file
            result = app._parse_seed_file(seed_file)

            # Verify hostname is preserved exactly
            assert len(result) == 1
            assert result[0].startswith('SPECIAL-ROUTER-NAME:')
            assert result[0] == 'SPECIAL-ROUTER-NAME:192.168.1.100'

        finally:
            os.unlink(seed_file)

    def test_attribute_preservation_with_special_characters(self):
        """
        Test that hostnames with special characters are preserved
        Validates Requirements: 7.2
        """
        # Create seed file with special characters in hostname
        seed_content = """hostname,ip,status
ROUTER_01-CORE.example,,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True
            app.db_manager.get_primary_ip_by_hostname.return_value = '10.0.0.1'

            # Parse seed file
            result = app._parse_seed_file(seed_file)

            # Verify hostname with special characters is preserved
            assert len(result) == 1
            assert result[0] == 'ROUTER_01-CORE.example:10.0.0.1'

        finally:
            os.unlink(seed_file)

    def test_entry_order_preservation_all_explicit(self):
        """
        Test that entry order is preserved with explicit IPs
        Validates Requirements: 7.4
        """
        # Create seed file with specific order
        seed_content = """hostname,ip,status
ROUTER-A,10.0.0.1,pending
ROUTER-B,10.0.0.2,pending
ROUTER-C,10.0.0.3,pending
ROUTER-D,10.0.0.4,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True

            # Parse seed file
            result = app._parse_seed_file(seed_file)

            # Verify order is preserved
            assert len(result) == 4
            assert result[0] == 'ROUTER-A:10.0.0.1'
            assert result[1] == 'ROUTER-B:10.0.0.2'
            assert result[2] == 'ROUTER-C:10.0.0.3'
            assert result[3] == 'ROUTER-D:10.0.0.4'

        finally:
            os.unlink(seed_file)

    def test_entry_order_preservation_with_resolution(self):
        """
        Test that entry order is preserved with resolved IPs
        Validates Requirements: 7.4
        """
        # Create seed file with blank IPs
        seed_content = """hostname,ip,status
ROUTER-E,,pending
ROUTER-F,,pending
ROUTER-G,,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True

            # Mock database to return different IPs for each hostname
            def mock_get_ip(hostname):
                ip_map = {
                    'ROUTER-E': '192.168.1.5',
                    'ROUTER-F': '192.168.1.6',
                    'ROUTER-G': '192.168.1.7'
                }
                return ip_map.get(hostname)

            app.db_manager.get_primary_ip_by_hostname.side_effect = mock_get_ip

            # Parse seed file
            result = app._parse_seed_file(seed_file)

            # Verify order is preserved
            assert len(result) == 3
            assert result[0] == 'ROUTER-E:192.168.1.5'
            assert result[1] == 'ROUTER-F:192.168.1.6'
            assert result[2] == 'ROUTER-G:192.168.1.7'

        finally:
            os.unlink(seed_file)

    def test_entry_order_preservation_mixed_with_skipped(self):
        """
        Test that entry order is preserved with mixed IPs and skipped devices
        Validates Requirements: 7.4
        """
        # Create seed file with mixed entries
        seed_content = """hostname,ip,status
ROUTER-H,10.0.0.8,pending
ROUTER-I,,pending
ROUTER-J,,pending
ROUTER-K,10.0.0.11,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True

            # Mock database to return IP for ROUTER-I but not ROUTER-J
            def mock_get_ip(hostname):
                if hostname == 'ROUTER-I':
                    return '192.168.1.9'
                return None

            app.db_manager.get_primary_ip_by_hostname.side_effect = mock_get_ip

            # Mock DNS to also fail for ROUTER-J
            with patch('socket.gethostbyname', side_effect=Exception("DNS failed")):
                with patch('netwalker.netwalker_app.logger'):
                    result = app._parse_seed_file(seed_file)

                    # Verify order is preserved (excluding skipped ROUTER-J)
                    assert len(result) == 3
                    assert result[0] == 'ROUTER-H:10.0.0.8'
                    assert result[1] == 'ROUTER-I:192.168.1.9'
                    assert result[2] == 'ROUTER-K:10.0.0.11'

        finally:
            os.unlink(seed_file)

    def test_blank_ip_detection_with_leading_trailing_whitespace(self):
        """
        Test blank IP detection with leading/trailing whitespace
        Validates Requirements: 1.1, 1.2
        """
        # Create seed file with whitespace around blank IP
        seed_content = """hostname,ip,status
ROUTER-13,  ,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True
            app.db_manager.get_primary_ip_by_hostname.return_value = '172.31.0.13'

            # Parse seed file
            with patch('netwalker.netwalker_app.logger') as mock_logger:
                result = app._parse_seed_file(seed_file)

                # Verify blank IP was detected
                mock_logger.info.assert_any_call(
                    'Blank IP detected for ROUTER-13, attempting resolution...'
                )

                # Verify device was added with resolved IP
                assert len(result) == 1
                assert result[0] == 'ROUTER-13:172.31.0.13'

        finally:
            os.unlink(seed_file)

    def test_explicit_ip_with_whitespace_trimmed(self):
        """
        Test that explicit IPs with whitespace are trimmed but not resolved
        Validates Requirements: 5.1
        """
        # Create seed file with whitespace around explicit IP
        seed_content = """hostname,ip,status
ROUTER-14,  192.168.1.14  ,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True

            # Parse seed file
            result = app._parse_seed_file(seed_file)

            # Verify device was added with trimmed explicit IP
            assert len(result) == 1
            assert result[0] == 'ROUTER-14:192.168.1.14'

            # Verify NO resolution was attempted
            app.db_manager.get_primary_ip_by_hostname.assert_not_called()

        finally:
            os.unlink(seed_file)

    def test_mixed_blank_and_explicit_ips(self):
        """
        Test processing of mixed blank and explicit IPs
        Validates Requirements: 1.2, 1.3, 5.1
        """
        # Create seed file with mixed IPs
        seed_content = """hostname,ip,status
ROUTER-15,192.168.1.15,pending
ROUTER-16,,pending
ROUTER-17,192.168.1.17,pending
ROUTER-18,,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True

            # Mock database to return IPs for blank entries
            def mock_get_ip(hostname):
                ip_map = {
                    'ROUTER-16': '192.168.1.16',
                    'ROUTER-18': '192.168.1.18'
                }
                return ip_map.get(hostname)

            app.db_manager.get_primary_ip_by_hostname.side_effect = mock_get_ip

            # Parse seed file
            result = app._parse_seed_file(seed_file)

            # Verify all devices were processed correctly
            assert len(result) == 4
            assert result[0] == 'ROUTER-15:192.168.1.15'  # Explicit IP
            assert result[1] == 'ROUTER-16:192.168.1.16'  # Resolved IP
            assert result[2] == 'ROUTER-17:192.168.1.17'  # Explicit IP
            assert result[3] == 'ROUTER-18:192.168.1.18'  # Resolved IP

            # Verify resolution was only called for blank IPs
            assert app.db_manager.get_primary_ip_by_hostname.call_count == 2
            app.db_manager.get_primary_ip_by_hostname.assert_any_call('ROUTER-16')
            app.db_manager.get_primary_ip_by_hostname.assert_any_call('ROUTER-18')

        finally:
            os.unlink(seed_file)

    def test_empty_hostname_skipped(self):
        """
        Test that entries with empty hostnames are skipped
        Validates Requirements: 3.3
        """
        # Create seed file with empty hostname
        seed_content = """hostname,ip,status
,192.168.1.1,pending
ROUTER-19,192.168.1.19,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True

            # Parse seed file
            with patch('netwalker.netwalker_app.logger') as mock_logger:
                result = app._parse_seed_file(seed_file)

                # Verify only valid entry was added
                assert len(result) == 1
                assert result[0] == 'ROUTER-19:192.168.1.19'

                # Verify warning was logged
                mock_logger.warning.assert_any_call('Skipping entry with empty hostname')

        finally:
            os.unlink(seed_file)

    def test_resolution_preserves_hostname_case(self):
        """
        Test that hostname case is preserved during resolution
        Validates Requirements: 7.2
        """
        # Create seed file with mixed case hostname
        seed_content = """hostname,ip,status
MixedCase-Router-20,,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            app.db_manager = MagicMock()
            app.db_manager.enabled = True
            app.db_manager.get_primary_ip_by_hostname.return_value = '192.168.1.20'

            # Parse seed file
            result = app._parse_seed_file(seed_file)

            # Verify hostname case is preserved
            assert len(result) == 1
            assert result[0] == 'MixedCase-Router-20:192.168.1.20'

            # Verify database was called with exact hostname
            app.db_manager.get_primary_ip_by_hostname.assert_called_once_with('MixedCase-Router-20')

        finally:
            os.unlink(seed_file)
