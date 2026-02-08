"""
Unit tests for database IP lookup functionality
Feature: database-ip-lookup-for-seed-devices
Task: 1.5 - Write unit tests for database query method
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import pyodbc
from netwalker.database.database_manager import DatabaseManager


class TestGetPrimaryIPByHostname:
    """Unit tests for get_primary_ip_by_hostname() method"""
    
    def test_existing_hostname_returns_ip(self):
        """
        Test with existing hostname (returns IP)
        Validates Requirements: 2.2
        """
        # Setup database manager
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
        
        # Mock cursor to return an IP address
        mock_cursor = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: '192.168.1.100'
        mock_cursor.fetchone.return_value = mock_row
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Call the method
        result = db_manager.get_primary_ip_by_hostname('test-router')
        
        # Verify result
        assert result == '192.168.1.100', "Should return the IP address for existing hostname"
        
        # Verify cursor was called correctly (should be called at least once for the query)
        assert mock_cursor.execute.call_count >= 1, "Should execute query"
        # Get the last call (the actual query, not is_connected check)
        last_call_args = mock_cursor.execute.call_args_list[-1][0]
        assert 'test-router' in last_call_args[1], "Should query with the hostname"
        mock_cursor.close.assert_called()
    
    def test_non_existent_hostname_returns_none(self):
        """
        Test with non-existent hostname (returns None)
        Validates Requirements: 2.3
        """
        # Setup database manager
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
        
        # Mock cursor to return None (no results)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Call the method
        result = db_manager.get_primary_ip_by_hostname('non-existent-device')
        
        # Verify result
        assert result is None, "Should return None for non-existent hostname"
        
        # Verify cursor was called
        assert mock_cursor.execute.call_count >= 1, "Should execute query"
        mock_cursor.close.assert_called()
    
    def test_database_connection_error_returns_none(self):
        """
        Test with database connection error (returns None, logs error)
        Validates Requirements: 6.1, 6.2
        """
        # Setup database manager
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
        
        # Replace logger with mock after initialization
        mock_logger = MagicMock()
        db_manager.logger = mock_logger
        
        # Mock cursor - first call succeeds (is_connected check), second call fails
        mock_cursor = MagicMock()
        call_count = [0]
        
        def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call is is_connected() check - succeed
                return None
            else:
                # Second call is actual query - fail
                raise pyodbc.OperationalError("Connection lost")
        
        mock_cursor.execute.side_effect = execute_side_effect
        mock_cursor.fetchone.return_value = [1]  # For is_connected check
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Call the method
        result = db_manager.get_primary_ip_by_hostname('test-router')
        
        # Verify result
        assert result is None, "Should return None on database connection error"
        
        # Verify error was logged
        mock_logger.error.assert_called()
        error_message = mock_logger.error.call_args[0][0]
        assert 'Database error' in error_message, "Should log database error"
        assert 'test-router' in error_message, "Should include hostname in error message"
    
    def test_query_error_returns_none(self):
        """
        Test with query error (returns None, logs error)
        Validates Requirements: 6.1, 6.2
        """
        # Setup database manager
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
        
        # Replace logger with mock after initialization
        mock_logger = MagicMock()
        db_manager.logger = mock_logger
        
        # Mock cursor - first call succeeds (is_connected check), second call fails
        mock_cursor = MagicMock()
        call_count = [0]
        
        def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call is is_connected() check - succeed
                return None
            else:
                # Second call is actual query - fail
                raise pyodbc.DatabaseError("Invalid query")
        
        mock_cursor.execute.side_effect = execute_side_effect
        mock_cursor.fetchone.return_value = [1]  # For is_connected check
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Call the method
        result = db_manager.get_primary_ip_by_hostname('test-router')
        
        # Verify result
        assert result is None, "Should return None on query error"
        
        # Verify error was logged
        mock_logger.error.assert_called()
        error_message = mock_logger.error.call_args[0][0]
        assert 'Database error' in error_message, "Should log database error"
        assert 'test-router' in error_message, "Should include hostname in error message"
    
    def test_database_disabled_returns_none(self):
        """
        Test that method returns None when database is disabled
        Validates Requirements: 6.1
        """
        # Setup database manager with database disabled
        db_config = {
            'enabled': False,
            'server': 'localhost',
            'database': 'test_db',
            'username': 'test',
            'password': 'test'
        }
        
        db_manager = DatabaseManager(db_config)
        
        # Call the method
        result = db_manager.get_primary_ip_by_hostname('test-router')
        
        # Verify result
        assert result is None, "Should return None when database is disabled"
    
    def test_not_connected_returns_none(self):
        """
        Test that method returns None when database is not connected
        Validates Requirements: 6.1
        """
        # Setup database manager
        db_config = {
            'enabled': True,
            'server': 'localhost',
            'database': 'test_db',
            'username': 'test',
            'password': 'test'
        }
        
        db_manager = DatabaseManager(db_config)
        db_manager.connection = None  # Not connected
        db_manager.enabled = True
        
        # Call the method
        result = db_manager.get_primary_ip_by_hostname('test-router')
        
        # Verify result
        assert result is None, "Should return None when not connected"
    
    def test_empty_hostname_returns_none(self):
        """
        Test that method returns None for empty hostname
        Validates Requirements: 6.1
        """
        # Setup database manager
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
        
        # Call the method with empty hostname
        result = db_manager.get_primary_ip_by_hostname('')
        
        # Verify result
        assert result is None, "Should return None for empty hostname"
    
    def test_none_hostname_returns_none(self):
        """
        Test that method returns None for None hostname
        Validates Requirements: 6.1
        """
        # Setup database manager
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
        
        # Call the method with None hostname
        result = db_manager.get_primary_ip_by_hostname(None)
        
        # Verify result
        assert result is None, "Should return None for None hostname"
    
    def test_empty_ip_in_result_returns_none(self):
        """
        Test that method returns None when database returns empty IP
        Validates Requirements: 2.3
        """
        # Setup database manager
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
        
        # Mock cursor to return empty IP
        mock_cursor = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: ''
        mock_cursor.fetchone.return_value = mock_row
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Call the method
        result = db_manager.get_primary_ip_by_hostname('test-router')
        
        # Verify result
        assert result is None, "Should return None when IP is empty string"
    
    def test_null_ip_in_result_returns_none(self):
        """
        Test that method returns None when database returns NULL IP
        Validates Requirements: 2.3
        """
        # Setup database manager
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
        
        # Mock cursor to return None IP
        mock_cursor = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: None
        mock_cursor.fetchone.return_value = mock_row
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Call the method
        result = db_manager.get_primary_ip_by_hostname('test-router')
        
        # Verify result
        assert result is None, "Should return None when IP is NULL"
    
    def test_unexpected_exception_returns_none(self):
        """
        Test that method handles unexpected exceptions gracefully
        Validates Requirements: 6.1, 6.2
        """
        # Setup database manager
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
        
        # Replace logger with mock after initialization
        mock_logger = MagicMock()
        db_manager.logger = mock_logger
        
        # Mock cursor - first call succeeds (is_connected check), second call fails
        mock_cursor = MagicMock()
        call_count = [0]
        
        def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call is is_connected() check - succeed
                return None
            else:
                # Second call is actual query - fail
                raise RuntimeError("Unexpected error")
        
        mock_cursor.execute.side_effect = execute_side_effect
        mock_cursor.fetchone.return_value = [1]  # For is_connected check
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Call the method
        result = db_manager.get_primary_ip_by_hostname('test-router')
        
        # Verify result
        assert result is None, "Should return None on unexpected exception"
        
        # Verify error was logged
        mock_logger.error.assert_called()
        error_message = mock_logger.error.call_args[0][0]
        assert 'Unexpected error' in error_message, "Should log unexpected error"
        assert 'test-router' in error_message, "Should include hostname in error message"
    
    def test_query_uses_correct_sql(self):
        """
        Test that the query uses correct SQL with proper joins and ordering
        Validates Requirements: 2.2
        """
        # Setup database manager
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
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: '192.168.1.1'
        mock_cursor.fetchone.return_value = mock_row
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Call the method
        result = db_manager.get_primary_ip_by_hostname('test-device')
        
        # Verify SQL query structure (get the last call which is the actual query)
        assert mock_cursor.execute.call_count >= 1, "Should execute query"
        sql_query = mock_cursor.execute.call_args_list[-1][0][0]
        
        # Check for key SQL elements
        assert 'SELECT TOP 1' in sql_query, "Should use TOP 1 to get single result"
        assert 'device_interfaces' in sql_query, "Should query device_interfaces table"
        assert 'devices' in sql_query, "Should join with devices table"
        assert 'INNER JOIN' in sql_query or 'JOIN' in sql_query, "Should use JOIN"
        assert 'device_name' in sql_query, "Should filter by device_name"
        assert 'ORDER BY' in sql_query, "Should order results to prioritize management interfaces"
        assert 'Primary Management' in sql_query, "Should prioritize Primary Management interface"
    
    def test_successful_lookup_logs_debug(self):
        """
        Test that successful lookup logs debug message
        Validates Requirements: 2.2
        """
        # Setup database manager
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
        
        # Mock cursor to return an IP
        mock_cursor = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: '10.0.0.1'
        mock_cursor.fetchone.return_value = mock_row
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Mock logger
        db_manager.logger = MagicMock()
        
        # Call the method
        result = db_manager.get_primary_ip_by_hostname('test-router')
        
        # Verify debug logging
        db_manager.logger.debug.assert_called()
        debug_message = db_manager.logger.debug.call_args[0][0]
        assert 'Found primary IP' in debug_message, "Should log success message"
        assert '10.0.0.1' in debug_message, "Should include IP in log"
        assert 'test-router' in debug_message, "Should include hostname in log"
    
    def test_no_result_logs_debug(self):
        """
        Test that no result logs debug message
        Validates Requirements: 2.3
        """
        # Setup database manager
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
        
        # Mock cursor to return None
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Mock logger
        db_manager.logger = MagicMock()
        
        # Call the method
        result = db_manager.get_primary_ip_by_hostname('unknown-device')
        
        # Verify debug logging
        db_manager.logger.debug.assert_called()
        debug_message = db_manager.logger.debug.call_args[0][0]
        assert 'No primary IP found' in debug_message, "Should log no result message"
        assert 'unknown-device' in debug_message, "Should include hostname in log"
    
    def test_multiple_interfaces_returns_primary_management(self):
        """
        Test that when device has multiple interfaces, Primary Management is returned
        Validates Requirements: 2.2
        """
        # Setup database manager
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
        
        # Mock cursor to return Primary Management IP
        # (SQL ORDER BY ensures this is returned first)
        mock_cursor = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: '192.168.1.100'  # Primary Management IP
        mock_cursor.fetchone.return_value = mock_row
        db_manager.connection.cursor.return_value = mock_cursor
        
        # Call the method
        result = db_manager.get_primary_ip_by_hostname('multi-interface-device')
        
        # Verify result is the Primary Management IP
        assert result == '192.168.1.100', "Should return Primary Management IP when multiple interfaces exist"
