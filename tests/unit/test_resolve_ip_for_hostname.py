"""
Unit tests for _resolve_ip_for_hostname() method in NetWalker
Feature: database-ip-lookup-for-seed-devices
Task: 2.7 - Write unit tests for IP resolution method
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import socket
from netwalker.netwalker_app import NetWalkerApp


class TestResolveIPForHostname:
    """Unit tests for _resolve_ip_for_hostname() method"""

    def test_database_resolution_success(self):
        """
        Test database resolution success (returns IP, logs "database")
        Validates Requirements: 3.1, 4.1
        """
        # Create NetWalker app with minimal config
        app = NetWalkerApp()

        # Mock database manager
        app.db_manager = MagicMock()
        app.db_manager.enabled = True
        app.db_manager.get_primary_ip_by_hostname.return_value = '192.168.1.100'

        # Call the method
        with patch('netwalker.netwalker_app.logger') as mock_logger:
            result = app._resolve_ip_for_hostname('test-router')

            # Verify result
            assert result == '192.168.1.100', "Should return IP from database"

            # Verify database was called
            app.db_manager.get_primary_ip_by_hostname.assert_called_once_with('test-router')

            # Verify logging
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert 'test-router' in log_message, "Should include hostname in log"
            assert '192.168.1.100' in log_message, "Should include IP in log"
            assert 'database' in log_message, "Should indicate database as source"

    def test_dns_fallback_success(self):
        """
        Test DNS fallback success (database fails, DNS returns IP, logs "DNS")
        Validates Requirements: 3.2, 4.2
        """
        # Create NetWalker app with minimal config
        app = NetWalkerApp()

        # Mock database manager to return None
        app.db_manager = MagicMock()
        app.db_manager.enabled = True
        app.db_manager.get_primary_ip_by_hostname.return_value = None

        # Mock DNS to return IP
        with patch('socket.gethostbyname', return_value='10.0.0.5'):
            with patch('netwalker.netwalker_app.logger') as mock_logger:
                result = app._resolve_ip_for_hostname('dns-device')

                # Verify result
                assert result == '10.0.0.5', "Should return IP from DNS"

                # Verify database was called first
                app.db_manager.get_primary_ip_by_hostname.assert_called_once_with('dns-device')

                # Verify logging
                mock_logger.info.assert_called_once()
                log_message = mock_logger.info.call_args[0][0]
                assert 'dns-device' in log_message, "Should include hostname in log"
                assert '10.0.0.5' in log_message, "Should include IP in log"
                assert 'DNS' in log_message, "Should indicate DNS as source"

    def test_complete_failure(self):
        """
        Test complete failure (both fail, returns None, logs warning)
        Validates Requirements: 3.3, 4.3
        """
        # Create NetWalker app with minimal config
        app = NetWalkerApp()

        # Mock database manager to return None
        app.db_manager = MagicMock()
        app.db_manager.enabled = True
        app.db_manager.get_primary_ip_by_hostname.return_value = None

        # Mock DNS to fail
        with patch('socket.gethostbyname', side_effect=socket.gaierror("Name resolution failed")):
            with patch('netwalker.netwalker_app.logger') as mock_logger:
                result = app._resolve_ip_for_hostname('unknown-device')

                # Verify result
                assert result is None, "Should return None when both methods fail"

                # Verify database was called
                app.db_manager.get_primary_ip_by_hostname.assert_called_once_with('unknown-device')

                # Verify warning was logged
                mock_logger.warning.assert_called_once()
                log_message = mock_logger.warning.call_args[0][0]
                assert 'unknown-device' in log_message, "Should include hostname in log"
                assert 'Failed to resolve' in log_message or 'database or DNS' in log_message, \
                    "Should indicate resolution failure"

    def test_dns_gaierror_handling(self):
        """
        Test DNS error handling (socket.gaierror)
        Validates Requirements: 3.3, 4.3
        """
        # Create NetWalker app with minimal config
        app = NetWalkerApp()

        # Mock database manager to return None
        app.db_manager = MagicMock()
        app.db_manager.enabled = True
        app.db_manager.get_primary_ip_by_hostname.return_value = None

        # Mock DNS to raise gaierror
        with patch('socket.gethostbyname', side_effect=socket.gaierror("Name or service not known")):
            with patch('netwalker.netwalker_app.logger') as mock_logger:
                result = app._resolve_ip_for_hostname('bad-hostname')

                # Verify result
                assert result is None, "Should return None on DNS gaierror"

                # Verify warning was logged
                mock_logger.warning.assert_called_once()

    def test_dns_timeout_handling(self):
        """
        Test DNS error handling (socket.timeout)
        Validates Requirements: 3.3, 4.3
        """
        # Create NetWalker app with minimal config
        app = NetWalkerApp()

        # Mock database manager to return None
        app.db_manager = MagicMock()
        app.db_manager.enabled = True
        app.db_manager.get_primary_ip_by_hostname.return_value = None

        # Mock DNS to raise timeout
        with patch('socket.gethostbyname', side_effect=socket.timeout("DNS timeout")):
            with patch('netwalker.netwalker_app.logger') as mock_logger:
                result = app._resolve_ip_for_hostname('timeout-device')

                # Verify result
                assert result is None, "Should return None on DNS timeout"

                # Verify warning was logged
                mock_logger.warning.assert_called_once()
                log_message = mock_logger.warning.call_args[0][0]
                assert 'timeout-device' in log_message, "Should include hostname in log"

    def test_database_disabled(self):
        """
        Test behavior when database is disabled (should skip to DNS)
        Validates Requirements: 3.2
        """
        # Create NetWalker app with minimal config
        app = NetWalkerApp()

        # Mock database manager as disabled
        app.db_manager = MagicMock()
        app.db_manager.enabled = False

        # Mock DNS to return IP
        with patch('socket.gethostbyname', return_value='172.16.0.1'):
            with patch('netwalker.netwalker_app.logger') as mock_logger:
                result = app._resolve_ip_for_hostname('dns-only-device')

                # Verify result
                assert result == '172.16.0.1', "Should return IP from DNS"

                # Verify database was NOT called (because disabled)
                app.db_manager.get_primary_ip_by_hostname.assert_not_called()

                # Verify DNS logging
                mock_logger.info.assert_called_once()
                log_message = mock_logger.info.call_args[0][0]
                assert 'DNS' in log_message, "Should indicate DNS as source"

    def test_database_none(self):
        """
        Test behavior when database manager is None (should skip to DNS)
        Validates Requirements: 3.2
        """
        # Create NetWalker app with minimal config
        app = NetWalkerApp()

        # Set database manager to None
        app.db_manager = None

        # Mock DNS to return IP
        with patch('socket.gethostbyname', return_value='192.168.100.1'):
            with patch('netwalker.netwalker_app.logger') as mock_logger:
                result = app._resolve_ip_for_hostname('no-db-device')

                # Verify result
                assert result == '192.168.100.1', "Should return IP from DNS"

                # Verify DNS logging
                mock_logger.info.assert_called_once()
                log_message = mock_logger.info.call_args[0][0]
                assert 'DNS' in log_message, "Should indicate DNS as source"

    def test_database_returns_empty_string(self):
        """
        Test behavior when database returns empty string (should try DNS)
        Validates Requirements: 3.2
        """
        # Create NetWalker app with minimal config
        app = NetWalkerApp()

        # Mock database manager to return empty string
        app.db_manager = MagicMock()
        app.db_manager.enabled = True
        app.db_manager.get_primary_ip_by_hostname.return_value = ''

        # Mock DNS to return IP
        with patch('socket.gethostbyname', return_value='10.10.10.10'):
            with patch('netwalker.netwalker_app.logger') as mock_logger:
                result = app._resolve_ip_for_hostname('empty-ip-device')

                # Verify result
                assert result == '10.10.10.10', "Should return IP from DNS when database returns empty"

                # Verify database was called
                app.db_manager.get_primary_ip_by_hostname.assert_called_once_with('empty-ip-device')

                # Verify DNS logging
                mock_logger.info.assert_called_once()
                log_message = mock_logger.info.call_args[0][0]
                assert 'DNS' in log_message, "Should indicate DNS as source"

    def test_unexpected_dns_exception(self):
        """
        Test handling of unexpected DNS exceptions
        Validates Requirements: 3.3, 4.3
        """
        # Create NetWalker app with minimal config
        app = NetWalkerApp()

        # Mock database manager to return None
        app.db_manager = MagicMock()
        app.db_manager.enabled = True
        app.db_manager.get_primary_ip_by_hostname.return_value = None

        # Mock DNS to raise unexpected exception
        with patch('socket.gethostbyname', side_effect=RuntimeError("Unexpected error")):
            with patch('netwalker.netwalker_app.logger') as mock_logger:
                result = app._resolve_ip_for_hostname('error-device')

                # Verify result
                assert result is None, "Should return None on unexpected exception"

                # Verify warning was logged
                mock_logger.warning.assert_called_once()
                log_message = mock_logger.warning.call_args[0][0]
                assert 'error-device' in log_message, "Should include hostname in log"

    def test_resolution_order(self):
        """
        Test that database is tried before DNS
        Validates Requirements: 3.1, 3.2
        """
        # Create NetWalker app with minimal config
        app = NetWalkerApp()

        # Mock database manager to return IP
        app.db_manager = MagicMock()
        app.db_manager.enabled = True
        app.db_manager.get_primary_ip_by_hostname.return_value = '192.168.1.1'

        # Mock DNS (should NOT be called)
        with patch('socket.gethostbyname', return_value='10.0.0.1') as mock_dns:
            with patch('netwalker.netwalker_app.logger'):
                result = app._resolve_ip_for_hostname('priority-test')

                # Verify result is from database
                assert result == '192.168.1.1', "Should return IP from database"

                # Verify DNS was NOT called (database succeeded)
                mock_dns.assert_not_called()

    def test_logging_includes_resolved_ip(self):
        """
        Test that log messages include the resolved IP address
        Validates Requirements: 4.4
        """
        # Create NetWalker app with minimal config
        app = NetWalkerApp()

        # Mock database manager
        app.db_manager = MagicMock()
        app.db_manager.enabled = True
        app.db_manager.get_primary_ip_by_hostname.return_value = '172.31.0.100'

        # Call the method
        with patch('netwalker.netwalker_app.logger') as mock_logger:
            result = app._resolve_ip_for_hostname('log-test-device')

            # Verify logging includes IP
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert '172.31.0.100' in log_message, "Log should include resolved IP"
            assert 'log-test-device' in log_message, "Log should include hostname"

    def test_logging_includes_resolution_source(self):
        """
        Test that log messages include the resolution source
        Validates Requirements: 4.1, 4.2
        """
        # Create NetWalker app with minimal config
        app = NetWalkerApp()

        # Test database source
        app.db_manager = MagicMock()
        app.db_manager.enabled = True
        app.db_manager.get_primary_ip_by_hostname.return_value = '10.0.0.1'

        with patch('netwalker.netwalker_app.logger') as mock_logger:
            app._resolve_ip_for_hostname('db-source-test')
            log_message = mock_logger.info.call_args[0][0]
            assert 'database' in log_message.lower(), "Should indicate database as source"

        # Test DNS source
        app.db_manager.get_primary_ip_by_hostname.return_value = None

        with patch('socket.gethostbyname', return_value='10.0.0.2'):
            with patch('netwalker.netwalker_app.logger') as mock_logger:
                app._resolve_ip_for_hostname('dns-source-test')
                log_message = mock_logger.info.call_args[0][0]
                assert 'dns' in log_message.lower(), "Should indicate DNS as source"

    def test_info_level_for_success(self):
        """
        Test that successful resolutions log at INFO level
        Validates Requirements: 4.5
        """
        # Create NetWalker app with minimal config
        app = NetWalkerApp()

        # Mock database manager
        app.db_manager = MagicMock()
        app.db_manager.enabled = True
        app.db_manager.get_primary_ip_by_hostname.return_value = '192.168.1.1'

        # Call the method
        with patch('netwalker.netwalker_app.logger') as mock_logger:
            app._resolve_ip_for_hostname('info-level-test')

            # Verify INFO level was used
            mock_logger.info.assert_called_once()
            mock_logger.warning.assert_not_called()
            mock_logger.error.assert_not_called()

    def test_warning_level_for_failure(self):
        """
        Test that resolution failures log at WARNING level
        Validates Requirements: 4.5
        """
        # Create NetWalker app with minimal config
        app = NetWalkerApp()

        # Mock database manager to return None
        app.db_manager = MagicMock()
        app.db_manager.enabled = True
        app.db_manager.get_primary_ip_by_hostname.return_value = None

        # Mock DNS to fail
        with patch('socket.gethostbyname', side_effect=socket.gaierror("Failed")):
            with patch('netwalker.netwalker_app.logger') as mock_logger:
                app._resolve_ip_for_hostname('warning-level-test')

                # Verify WARNING level was used
                mock_logger.warning.assert_called_once()
                mock_logger.info.assert_not_called()
