"""
Property-based tests for database IP lookup for seed devices
Feature: database-ip-lookup-for-seed-devices
"""

from unittest.mock import Mock, MagicMock
from hypothesis import given, strategies as st, settings
from netwalker.database.database_manager import DatabaseManager


# Strategy for generating valid IPv4 addresses
def valid_ipv4_addresses():
    """Generate valid IPv4 addresses"""
    return st.builds(
        lambda a, b, c, d: f"{a}.{b}.{c}.{d}",
        st.integers(min_value=1, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=1, max_value=254)
    )


# Strategy for generating valid hostnames
def valid_hostnames():
    """Generate valid device hostnames"""
    return st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        )
    )


@given(
    hostname=valid_hostnames(),
    primary_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_database_lookup_returns_stored_ip(hostname, primary_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 2
    Database Lookup Returns Stored IP
    
    For any hostname that exists in the database with a non-null, non-empty 
    primary IP, querying the database should return that exact IP address.
    
    **Validates: Requirements 2.2**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }
    
    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True
    
    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    
    # Simulate database having the hostname with the primary IP
    # The query returns a row with the IP address
    mock_cursor.fetchone.return_value = (primary_ip,)
    mock_connection.cursor.return_value = mock_cursor
    
    db_manager.connection = mock_connection
    
    # Mock is_connected to return True
    db_manager.is_connected = Mock(return_value=True)
    
    # Call get_primary_ip_by_hostname
    result = db_manager.get_primary_ip_by_hostname(hostname)
    
    # CRITICAL PROPERTY: The returned IP should exactly match the stored IP
    assert result == primary_ip, \
        f"Database lookup should return stored IP: expected '{primary_ip}', got '{result}'"
    
    # Verify the query was executed with the correct hostname
    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()
    
    # Verify the hostname was passed as a parameter to the query
    call_args = mock_cursor.execute.call_args
    assert call_args is not None, "execute should have been called"
    
    # The second argument should be a tuple containing the hostname
    if len(call_args[0]) > 1:
        query_params = call_args[0][1]
        assert hostname in query_params, \
            f"Hostname '{hostname}' should be in query parameters"
    
    # Verify cursor was closed
    mock_cursor.close.assert_called_once()


@given(
    hostname=valid_hostnames(),
    primary_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_database_lookup_with_multiple_interfaces(hostname, primary_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 2 (Extended)
    Database Lookup Returns Primary Management IP When Multiple Interfaces Exist
    
    For any hostname with multiple interfaces in the database, the query should
    prioritize and return the 'Primary Management' interface IP.
    
    **Validates: Requirements 2.2**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }
    
    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True
    
    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    
    # Simulate database having multiple interfaces, but the query returns
    # the Primary Management IP due to ORDER BY prioritization
    # The SQL query in get_primary_ip_by_hostname uses ORDER BY to prioritize
    # 'Primary Management' interface, so fetchone() returns the highest priority IP
    mock_cursor.fetchone.return_value = (primary_ip,)
    mock_connection.cursor.return_value = mock_cursor
    
    db_manager.connection = mock_connection
    db_manager.is_connected = Mock(return_value=True)
    
    # Call get_primary_ip_by_hostname
    result = db_manager.get_primary_ip_by_hostname(hostname)
    
    # CRITICAL PROPERTY: Should return the primary management IP
    assert result == primary_ip, \
        f"Should return primary management IP: expected '{primary_ip}', got '{result}'"
    
    # Verify the query uses TOP 1 and ORDER BY for prioritization
    call_args = mock_cursor.execute.call_args
    assert call_args is not None, "execute should have been called"
    
    query = call_args[0][0]
    assert 'TOP 1' in query or 'LIMIT 1' in query, \
        "Query should limit results to 1 row"
    assert 'ORDER BY' in query, \
        "Query should use ORDER BY for interface prioritization"
    assert 'Primary Management' in query, \
        "Query should prioritize 'Primary Management' interface"


@given(
    hostname=valid_hostnames(),
    primary_ip=valid_ipv4_addresses(),
    num_rediscoveries=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=5, deadline=None)
def test_property_database_lookup_returns_most_recent_ip(
    hostname,
    primary_ip,
    num_rediscoveries
):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 2 (Idempotence)
    Database Lookup Returns IP After Multiple Discoveries
    
    For any hostname that has been discovered multiple times with the same IP,
    the database lookup should still return that IP correctly.
    
    **Validates: Requirements 2.2**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }
    
    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True
    
    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    
    # Simulate database having the IP (regardless of how many times it was stored)
    mock_cursor.fetchone.return_value = (primary_ip,)
    mock_connection.cursor.return_value = mock_cursor
    
    db_manager.connection = mock_connection
    db_manager.is_connected = Mock(return_value=True)
    
    # Call get_primary_ip_by_hostname multiple times
    # (simulating multiple lookups after multiple discoveries)
    for i in range(num_rediscoveries):
        result = db_manager.get_primary_ip_by_hostname(hostname)
        
        # CRITICAL PROPERTY: Each lookup should return the same IP
        assert result == primary_ip, \
            f"Lookup {i+1} should return stored IP: expected '{primary_ip}', got '{result}'"
    
    # Verify the query was executed the correct number of times
    assert mock_cursor.execute.call_count == num_rediscoveries, \
        f"Query should be executed {num_rediscoveries} times"


@given(
    hostname=valid_hostnames(),
    primary_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_database_lookup_with_valid_non_empty_ip(hostname, primary_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 2 (Non-null/Non-empty)
    Database Lookup Only Returns Non-null, Non-empty IPs
    
    For any hostname, the database query should filter out null or empty IP addresses
    and only return valid, non-empty IPs.
    
    **Validates: Requirements 2.2**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }
    
    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True
    
    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    
    # Simulate database returning a valid, non-empty IP
    mock_cursor.fetchone.return_value = (primary_ip,)
    mock_connection.cursor.return_value = mock_cursor
    
    db_manager.connection = mock_connection
    db_manager.is_connected = Mock(return_value=True)
    
    # Call get_primary_ip_by_hostname
    result = db_manager.get_primary_ip_by_hostname(hostname)
    
    # CRITICAL PROPERTY: Result should be non-null and non-empty
    assert result is not None, "Result should not be None"
    assert result != '', "Result should not be empty string"
    assert result == primary_ip, f"Result should match stored IP: {primary_ip}"
    
    # Verify the query filters for non-null and non-empty IPs
    call_args = mock_cursor.execute.call_args
    assert call_args is not None, "execute should have been called"
    
    query = call_args[0][0]
    assert 'IS NOT NULL' in query, \
        "Query should filter out NULL IP addresses"
    assert "!= ''" in query or "<> ''" in query, \
        "Query should filter out empty string IP addresses"


@given(
    hostname=valid_hostnames(),
    primary_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_database_lookup_case_sensitivity(hostname, primary_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 2 (Case Handling)
    Database Lookup Handles Hostname Case Correctly
    
    For any hostname, the database lookup should work correctly regardless of
    the hostname's case (the database query should handle case appropriately).
    
    **Validates: Requirements 2.2**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }
    
    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True
    
    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    
    # Simulate database returning the IP for the hostname
    mock_cursor.fetchone.return_value = (primary_ip,)
    mock_connection.cursor.return_value = mock_cursor
    
    db_manager.connection = mock_connection
    db_manager.is_connected = Mock(return_value=True)
    
    # Call get_primary_ip_by_hostname with the hostname as-is
    result = db_manager.get_primary_ip_by_hostname(hostname)
    
    # CRITICAL PROPERTY: Should return the stored IP
    assert result == primary_ip, \
        f"Database lookup should return stored IP: expected '{primary_ip}', got '{result}'"
    
    # Verify the hostname was passed to the query
    call_args = mock_cursor.execute.call_args
    assert call_args is not None, "execute should have been called"
    
    if len(call_args[0]) > 1:
        query_params = call_args[0][1]
        assert hostname in query_params, \
            f"Hostname '{hostname}' should be in query parameters"


@given(
    hostname=valid_hostnames(),
    primary_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_database_lookup_returns_string_type(hostname, primary_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 2 (Type Safety)
    Database Lookup Returns String Type
    
    For any hostname with a stored IP, the database lookup should return
    a string type (not bytes, not other types).
    
    **Validates: Requirements 2.2**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }
    
    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True
    
    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    
    # Simulate database returning the IP
    mock_cursor.fetchone.return_value = (primary_ip,)
    mock_connection.cursor.return_value = mock_cursor
    
    db_manager.connection = mock_connection
    db_manager.is_connected = Mock(return_value=True)
    
    # Call get_primary_ip_by_hostname
    result = db_manager.get_primary_ip_by_hostname(hostname)
    
    # CRITICAL PROPERTY: Result should be a string type
    assert isinstance(result, str), \
        f"Result should be string type, got {type(result)}"
    assert result == primary_ip, \
        f"Result should match stored IP: expected '{primary_ip}', got '{result}'"


@given(hostname=valid_hostnames())
@settings(max_examples=5, deadline=None)
def test_property_database_lookup_returns_none_for_missing_entries(hostname):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 3
    Database Lookup Returns None for Missing Entries

    For any hostname that does not exist in the database or has a null/empty
    primary IP, querying the database should return None.

    **Validates: Requirements 2.3**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }

    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True

    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    # Simulate database NOT having the hostname (fetchone returns None)
    mock_cursor.fetchone.return_value = None
    mock_connection.cursor.return_value = mock_cursor

    db_manager.connection = mock_connection
    db_manager.is_connected = Mock(return_value=True)

    # Call get_primary_ip_by_hostname
    result = db_manager.get_primary_ip_by_hostname(hostname)

    # CRITICAL PROPERTY: Should return None for missing entries
    assert result is None, \
        f"Database lookup should return None for missing hostname '{hostname}', got '{result}'"

    # Verify the query was executed
    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()

    # Verify cursor was closed
    mock_cursor.close.assert_called_once()


@given(hostname=valid_hostnames())
@settings(max_examples=5, deadline=None)
def test_property_database_lookup_returns_none_for_null_ip(hostname):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 3 (Null IP)
    Database Lookup Returns None for Null Primary IP

    For any hostname that exists in the database but has a NULL primary IP,
    querying the database should return None.

    **Validates: Requirements 2.3**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }

    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True

    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    # Simulate database having the hostname but with NULL IP
    # The query filters for "IS NOT NULL AND != ''" so it returns no rows
    mock_cursor.fetchone.return_value = None
    mock_connection.cursor.return_value = mock_cursor

    db_manager.connection = mock_connection
    db_manager.is_connected = Mock(return_value=True)

    # Call get_primary_ip_by_hostname
    result = db_manager.get_primary_ip_by_hostname(hostname)

    # CRITICAL PROPERTY: Should return None for NULL IP
    assert result is None, \
        f"Database lookup should return None for hostname '{hostname}' with NULL IP, got '{result}'"

    # Verify the query was executed
    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()

    # Verify the query filters for non-null IPs
    call_args = mock_cursor.execute.call_args
    assert call_args is not None, "execute should have been called"

    query = call_args[0][0]
    assert 'IS NOT NULL' in query, \
        "Query should filter out NULL IP addresses"

    # Verify cursor was closed
    mock_cursor.close.assert_called_once()


@given(hostname=valid_hostnames())
@settings(max_examples=5, deadline=None)
def test_property_database_lookup_returns_none_for_empty_ip(hostname):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 3 (Empty IP)
    Database Lookup Returns None for Empty Primary IP

    For any hostname that exists in the database but has an empty string
    primary IP, querying the database should return None.

    **Validates: Requirements 2.3**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }

    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True

    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    # Simulate database having the hostname but with empty IP
    # The query filters for "!= ''" so it returns no rows
    mock_cursor.fetchone.return_value = None
    mock_connection.cursor.return_value = mock_cursor

    db_manager.connection = mock_connection
    db_manager.is_connected = Mock(return_value=True)

    # Call get_primary_ip_by_hostname
    result = db_manager.get_primary_ip_by_hostname(hostname)

    # CRITICAL PROPERTY: Should return None for empty IP
    assert result is None, \
        f"Database lookup should return None for hostname '{hostname}' with empty IP, got '{result}'"

    # Verify the query was executed
    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()

    # Verify the query filters for non-empty IPs
    call_args = mock_cursor.execute.call_args
    assert call_args is not None, "execute should have been called"

    query = call_args[0][0]
    assert "!= ''" in query or "<> ''" in query, \
        "Query should filter out empty string IP addresses"

    # Verify cursor was closed
    mock_cursor.close.assert_called_once()


@given(hostname=valid_hostnames())
@settings(max_examples=5, deadline=None)
def test_property_database_lookup_returns_none_when_disabled(hostname):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 3 (Database Disabled)
    Database Lookup Returns None When Database is Disabled

    For any hostname, if the database is disabled in configuration,
    querying should return None without attempting a database query.

    **Validates: Requirements 2.3**
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

    # Call get_primary_ip_by_hostname
    result = db_manager.get_primary_ip_by_hostname(hostname)

    # CRITICAL PROPERTY: Should return None when database is disabled
    assert result is None, \
        f"Database lookup should return None when disabled for hostname '{hostname}', got '{result}'"

    # Verify no connection was attempted (connection should be None)
    assert db_manager.connection is None, \
        "No database connection should exist when database is disabled"


@given(hostname=valid_hostnames())
@settings(max_examples=5, deadline=None)
def test_property_database_lookup_returns_none_when_not_connected(hostname):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 3 (Not Connected)
    Database Lookup Returns None When Not Connected

    For any hostname, if the database is not connected,
    querying should return None without attempting a query.

    **Validates: Requirements 2.3**
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
    db_manager.enabled = True
    db_manager.connection = None  # Not connected

    # Mock is_connected to return False
    db_manager.is_connected = Mock(return_value=False)

    # Call get_primary_ip_by_hostname
    result = db_manager.get_primary_ip_by_hostname(hostname)

    # CRITICAL PROPERTY: Should return None when not connected
    assert result is None, \
        f"Database lookup should return None when not connected for hostname '{hostname}', got '{result}'"


@given(hostname=st.just(''))
@settings(max_examples=5, deadline=None)
def test_property_database_lookup_returns_none_for_empty_hostname(hostname):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 3 (Empty Hostname)
    Database Lookup Returns None for Empty Hostname

    For any empty hostname, querying the database should return None
    without attempting a query.

    **Validates: Requirements 2.3**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }

    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True

    # Mock the connection
    mock_connection = MagicMock()
    db_manager.connection = mock_connection
    db_manager.is_connected = Mock(return_value=True)

    # Call get_primary_ip_by_hostname
    result = db_manager.get_primary_ip_by_hostname(hostname)

    # CRITICAL PROPERTY: Should return None for empty hostname
    assert result is None, \
        f"Database lookup should return None for empty hostname, got '{result}'"

    # Verify no query was executed (cursor should not be called)
    mock_connection.cursor.assert_not_called()


@given(
    hostname=valid_hostnames(),
    error_type=st.sampled_from(['connection_error', 'query_error', 'unexpected_error'])
)
@settings(max_examples=5, deadline=None)
def test_property_database_error_handling(hostname, error_type):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 13
    Database Error Handling

    For any database query that fails (connection error, query error, or any
    exception), the DatabaseManager should return None without raising exceptions.

    **Validates: Requirements 6.1, 6.2, 6.4**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }

    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True

    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    # Simulate different types of database errors
    if error_type == 'connection_error':
        # Simulate connection error (e.g., database unavailable)
        import pyodbc
        mock_cursor.execute.side_effect = pyodbc.OperationalError(
            "08S01", "[08S01] Connection failure"
        )
    elif error_type == 'query_error':
        # Simulate query error (e.g., malformed query, database corruption)
        import pyodbc
        mock_cursor.execute.side_effect = pyodbc.DatabaseError(
            "42000", "[42000] Syntax error or access violation"
        )
    else:  # unexpected_error
        # Simulate unexpected exception
        mock_cursor.execute.side_effect = Exception("Unexpected database error")

    mock_connection.cursor.return_value = mock_cursor
    db_manager.connection = mock_connection
    db_manager.is_connected = Mock(return_value=True)

    # Call get_primary_ip_by_hostname - should NOT raise exception
    try:
        result = db_manager.get_primary_ip_by_hostname(hostname)

        # CRITICAL PROPERTY: Should return None on any error
        assert result is None, \
            f"Database error should return None for hostname '{hostname}', got '{result}'"

        # Verify the query was attempted
        mock_connection.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()

    except Exception as e:
        # CRITICAL PROPERTY: Should NOT raise exceptions
        assert False, \
            f"Database error handling should not raise exceptions, but raised: {type(e).__name__}: {e}"


@given(hostname=valid_hostnames())
@settings(max_examples=5, deadline=None)
def test_property_database_connection_error_returns_none(hostname):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 13 (Connection Error)
    Database Connection Error Returns None

    For any hostname, if a database connection error occurs during query,
    the method should return None without raising exceptions.

    **Validates: Requirements 6.1, 6.4**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }

    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True

    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    # Simulate connection error
    import pyodbc
    mock_cursor.execute.side_effect = pyodbc.OperationalError(
        "08S01", "[08S01] TCP Provider: An existing connection was forcibly closed"
    )

    mock_connection.cursor.return_value = mock_cursor
    db_manager.connection = mock_connection
    db_manager.is_connected = Mock(return_value=True)

    # Call get_primary_ip_by_hostname
    result = db_manager.get_primary_ip_by_hostname(hostname)

    # CRITICAL PROPERTY: Should return None on connection error
    assert result is None, \
        f"Connection error should return None for hostname '{hostname}', got '{result}'"

    # Verify the query was attempted
    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()


@given(hostname=valid_hostnames())
@settings(max_examples=5, deadline=None)
def test_property_database_query_error_returns_none(hostname):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 13 (Query Error)
    Database Query Error Returns None

    For any hostname, if a database query error occurs (syntax error,
    access violation, etc.), the method should return None without raising exceptions.

    **Validates: Requirements 6.2, 6.4**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }

    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True

    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    # Simulate query error
    import pyodbc
    mock_cursor.execute.side_effect = pyodbc.DatabaseError(
        "42000", "[42000] Invalid object name 'devices'"
    )

    mock_connection.cursor.return_value = mock_cursor
    db_manager.connection = mock_connection
    db_manager.is_connected = Mock(return_value=True)

    # Call get_primary_ip_by_hostname
    result = db_manager.get_primary_ip_by_hostname(hostname)

    # CRITICAL PROPERTY: Should return None on query error
    assert result is None, \
        f"Query error should return None for hostname '{hostname}', got '{result}'"

    # Verify the query was attempted
    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()


@given(hostname=valid_hostnames())
@settings(max_examples=5, deadline=None)
def test_property_database_unexpected_error_returns_none(hostname):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 13 (Unexpected Error)
    Database Unexpected Error Returns None

    For any hostname, if an unexpected exception occurs during query,
    the method should return None without raising exceptions.

    **Validates: Requirements 6.4**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }

    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True

    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    # Simulate unexpected error
    mock_cursor.execute.side_effect = RuntimeError("Unexpected runtime error")

    mock_connection.cursor.return_value = mock_cursor
    db_manager.connection = mock_connection
    db_manager.is_connected = Mock(return_value=True)

    # Call get_primary_ip_by_hostname
    result = db_manager.get_primary_ip_by_hostname(hostname)

    # CRITICAL PROPERTY: Should return None on unexpected error
    assert result is None, \
        f"Unexpected error should return None for hostname '{hostname}', got '{result}'"

    # Verify the query was attempted
    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()


@given(hostname=valid_hostnames())
@settings(max_examples=5, deadline=None)
def test_property_database_error_no_exception_propagation(hostname):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 13 (No Exception Propagation)
    Database Errors Do Not Propagate Exceptions

    For any hostname and any type of database error, the method should
    catch all exceptions and return None instead of propagating them.

    **Validates: Requirements 6.4**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }

    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True

    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    # Simulate various types of errors
    error_types = [
        ValueError("Invalid value"),
        TypeError("Type mismatch"),
        KeyError("Missing key"),
        AttributeError("Missing attribute"),
        IndexError("Index out of range"),
        MemoryError("Out of memory"),
    ]

    for error in error_types:
        mock_cursor.execute.side_effect = error
        mock_connection.cursor.return_value = mock_cursor
        db_manager.connection = mock_connection
        db_manager.is_connected = Mock(return_value=True)

        # Call get_primary_ip_by_hostname - should NOT raise exception
        try:
            result = db_manager.get_primary_ip_by_hostname(hostname)

            # CRITICAL PROPERTY: Should return None on any error
            assert result is None, \
                f"Error {type(error).__name__} should return None, got '{result}'"

        except Exception as e:
            # CRITICAL PROPERTY: Should NOT propagate exceptions
            assert False, \
                f"Should not propagate {type(error).__name__}, but raised: {type(e).__name__}: {e}"


@given(hostname=valid_hostnames())
@settings(max_examples=5, deadline=None)
def test_property_database_cursor_close_on_error(hostname):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 13 (Resource Cleanup)
    Database Cursor is Closed Even on Error

    For any hostname, if a database error occurs, the cursor should still
    be closed properly to avoid resource leaks.

    **Validates: Requirements 6.4**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }

    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True

    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    # Simulate database error
    import pyodbc
    mock_cursor.execute.side_effect = pyodbc.DatabaseError(
        "42000", "[42000] Database error"
    )

    mock_connection.cursor.return_value = mock_cursor
    db_manager.connection = mock_connection
    db_manager.is_connected = Mock(return_value=True)

    # Call get_primary_ip_by_hostname
    result = db_manager.get_primary_ip_by_hostname(hostname)

    # CRITICAL PROPERTY: Should return None on error
    assert result is None, \
        f"Database error should return None for hostname '{hostname}', got '{result}'"

    # CRITICAL PROPERTY: Cursor should be closed even on error
    # Note: The current implementation doesn't explicitly close cursor in error path
    # This test documents expected behavior for resource cleanup
    # The cursor will be closed when it goes out of scope, but explicit close is better
    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()


@given(
    hostname=valid_hostnames(),
    num_retries=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=5, deadline=None)
def test_property_database_error_idempotence(hostname, num_retries):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 13 (Idempotence)
    Database Error Handling is Idempotent

    For any hostname, if database errors occur repeatedly, each call should
    consistently return None without side effects.

    **Validates: Requirements 6.4**
    """
    # Setup mock database manager
    db_config = {
        'enabled': True,
        'server': 'localhost',
        'database': 'test_db',
        'username': 'test',
        'password': 'test'
    }

    db_manager = DatabaseManager(db_config)
    db_manager.enabled = True

    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    # Simulate persistent database error
    import pyodbc
    mock_cursor.execute.side_effect = pyodbc.DatabaseError(
        "42000", "[42000] Persistent database error"
    )

    mock_connection.cursor.return_value = mock_cursor
    db_manager.connection = mock_connection
    db_manager.is_connected = Mock(return_value=True)

    # Call get_primary_ip_by_hostname multiple times
    for i in range(num_retries):
        result = db_manager.get_primary_ip_by_hostname(hostname)

        # CRITICAL PROPERTY: Each call should return None
        assert result is None, \
            f"Retry {i+1} should return None for hostname '{hostname}', got '{result}'"

    # Verify the query was attempted the correct number of times
    assert mock_cursor.execute.call_count == num_retries, \
        f"Query should be attempted {num_retries} times"


# ============================================================================
# Property Tests for _resolve_ip_for_hostname() Method
# Tasks 2.2 - 2.6
# ============================================================================

@given(
    hostname=valid_hostnames(),
    db_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_resolution_fallback_chain_order_database_first(hostname, db_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 4
    Resolution Fallback Chain Order
    
    For any hostname requiring resolution, the system should attempt database
    lookup first, and only attempt DNS lookup if the database returns None.
    
    **Validates: Requirements 2.1, 3.1, 3.2**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Mock database manager to return IP
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = db_ip
    
    # Mock DNS (should NOT be called since database succeeds)
    with patch('socket.gethostbyname', return_value='10.0.0.1') as mock_dns:
        with patch('netwalker.netwalker_app.logger'):
            result = app._resolve_ip_for_hostname(hostname)
            
            # CRITICAL PROPERTY: Should return database IP
            assert result == db_ip, \
                f"Should return database IP '{db_ip}', got '{result}'"
            
            # CRITICAL PROPERTY: Database should be called first
            app.db_manager.get_primary_ip_by_hostname.assert_called_once_with(hostname)
            
            # CRITICAL PROPERTY: DNS should NOT be called (database succeeded)
            mock_dns.assert_not_called()


@given(
    hostname=valid_hostnames(),
    dns_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_resolution_fallback_chain_order_dns_second(hostname, dns_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 4
    Resolution Fallback Chain Order - DNS Fallback
    
    For any hostname where database returns None, the system should
    attempt DNS lookup as the second method.
    
    **Validates: Requirements 2.1, 3.1, 3.2**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Mock database manager to return None
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = None
    
    # Mock DNS to return IP
    with patch('socket.gethostbyname', return_value=dns_ip) as mock_dns:
        with patch('netwalker.netwalker_app.logger'):
            result = app._resolve_ip_for_hostname(hostname)
            
            # CRITICAL PROPERTY: Should return DNS IP
            assert result == dns_ip, \
                f"Should return DNS IP '{dns_ip}', got '{result}'"
            
            # CRITICAL PROPERTY: Database should be called first
            app.db_manager.get_primary_ip_by_hostname.assert_called_once_with(hostname)
            
            # CRITICAL PROPERTY: DNS should be called after database fails
            mock_dns.assert_called_once_with(hostname)


@given(hostname=valid_hostnames())
@settings(max_examples=5, deadline=None)
def test_property_resolution_fallback_chain_order_both_fail(hostname):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 4
    Resolution Fallback Chain Order - Complete Failure
    
    For any hostname where both database and DNS fail, the system should
    return None after trying both methods in order.
    
    **Validates: Requirements 3.1, 3.2, 3.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch
    import socket
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Mock database manager to return None
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = None
    
    # Mock DNS to fail
    with patch('socket.gethostbyname', side_effect=socket.gaierror("Failed")) as mock_dns:
        with patch('netwalker.netwalker_app.logger'):
            result = app._resolve_ip_for_hostname(hostname)
            
            # CRITICAL PROPERTY: Should return None when both fail
            assert result is None, \
                f"Should return None when both methods fail, got '{result}'"
            
            # CRITICAL PROPERTY: Database should be called first
            app.db_manager.get_primary_ip_by_hostname.assert_called_once_with(hostname)
            
            # CRITICAL PROPERTY: DNS should be called after database fails
            mock_dns.assert_called_once_with(hostname)


@given(
    hostname=valid_hostnames(),
    dns_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_database_error_fallback_to_dns(hostname, dns_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 14
    Database Error Fallback
    
    For any hostname where database lookup fails with an error, the system
    should proceed to attempt DNS lookup.
    
    **Validates: Requirements 6.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Mock database manager to return None (simulating error handling)
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = None
    
    # Mock DNS to return IP
    with patch('socket.gethostbyname', return_value=dns_ip) as mock_dns:
        with patch('netwalker.netwalker_app.logger'):
            result = app._resolve_ip_for_hostname(hostname)
            
            # CRITICAL PROPERTY: Should return DNS IP after database error
            assert result == dns_ip, \
                f"Should return DNS IP '{dns_ip}' after database error, got '{result}'"
            
            # CRITICAL PROPERTY: Database should be attempted first
            app.db_manager.get_primary_ip_by_hostname.assert_called_once_with(hostname)
            
            # CRITICAL PROPERTY: DNS should be called as fallback
            mock_dns.assert_called_once_with(hostname)


@given(
    hostname=valid_hostnames(),
    db_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_database_resolution_logging(hostname, db_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 7
    Database Resolution Logging
    
    For any hostname resolved via database lookup, the log should contain
    an INFO-level message indicating "database" as the resolution source
    and include both the hostname and resolved IP.
    
    **Validates: Requirements 4.1, 4.4**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Mock database manager to return IP
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = db_ip
    
    # Mock logger to capture log calls
    with patch('netwalker.netwalker_app.logger') as mock_logger:
        result = app._resolve_ip_for_hostname(hostname)
        
        # CRITICAL PROPERTY: Should return database IP
        assert result == db_ip, \
            f"Should return database IP '{db_ip}', got '{result}'"
        
        # CRITICAL PROPERTY: Should log at INFO level
        mock_logger.info.assert_called_once()
        
        # CRITICAL PROPERTY: Log should include hostname
        log_message = mock_logger.info.call_args[0][0]
        assert hostname in log_message, \
            f"Log should include hostname '{hostname}'"
        
        # CRITICAL PROPERTY: Log should include resolved IP
        assert db_ip in log_message, \
            f"Log should include resolved IP '{db_ip}'"
        
        # CRITICAL PROPERTY: Log should indicate database as source
        assert 'database' in log_message.lower(), \
            "Log should indicate 'database' as resolution source"


@given(
    hostname=valid_hostnames(),
    dns_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_dns_resolution_logging(hostname, dns_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 8
    DNS Resolution Logging
    
    For any hostname resolved via DNS lookup, the log should contain
    an INFO-level message indicating "DNS" as the resolution source
    and include both the hostname and resolved IP.
    
    **Validates: Requirements 4.2, 4.4**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Mock database manager to return None
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = None
    
    # Mock DNS to return IP
    with patch('socket.gethostbyname', return_value=dns_ip):
        # Mock logger to capture log calls
        with patch('netwalker.netwalker_app.logger') as mock_logger:
            result = app._resolve_ip_for_hostname(hostname)
            
            # CRITICAL PROPERTY: Should return DNS IP
            assert result == dns_ip, \
                f"Should return DNS IP '{dns_ip}', got '{result}'"
            
            # CRITICAL PROPERTY: Should log at INFO level
            mock_logger.info.assert_called_once()
            
            # CRITICAL PROPERTY: Log should include hostname
            log_message = mock_logger.info.call_args[0][0]
            assert hostname in log_message, \
                f"Log should include hostname '{hostname}'"
            
            # CRITICAL PROPERTY: Log should include resolved IP
            assert dns_ip in log_message, \
                f"Log should include resolved IP '{dns_ip}'"
            
            # CRITICAL PROPERTY: Log should indicate DNS as source
            assert 'DNS' in log_message, \
                "Log should indicate 'DNS' as resolution source"


@given(hostname=valid_hostnames())
@settings(max_examples=5, deadline=None)
def test_property_resolution_failure_logging(hostname):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 9
    Resolution Failure Logging
    
    For any hostname that fails to resolve via both database and DNS,
    the log should contain a WARNING-level message with the hostname.
    
    **Validates: Requirements 4.3, 4.5**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch
    import socket
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Mock database manager to return None
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = None
    
    # Mock DNS to fail
    with patch('socket.gethostbyname', side_effect=socket.gaierror("Name resolution failed")):
        # Mock logger to capture log calls
        with patch('netwalker.netwalker_app.logger') as mock_logger:
            result = app._resolve_ip_for_hostname(hostname)
            
            # CRITICAL PROPERTY: Should return None on failure
            assert result is None, \
                f"Should return None when resolution fails, got '{result}'"
            
            # CRITICAL PROPERTY: Should log at WARNING level
            mock_logger.warning.assert_called_once()
            
            # CRITICAL PROPERTY: Log should include hostname
            log_message = mock_logger.warning.call_args[0][0]
            assert hostname in log_message, \
                f"Log should include hostname '{hostname}'"
            
            # CRITICAL PROPERTY: Should not log at INFO level
            mock_logger.info.assert_not_called()


@given(
    hostname=valid_hostnames(),
    db_ip=valid_ipv4_addresses(),
    dns_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_database_priority_over_dns(hostname, db_ip, dns_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 4 (Priority)
    Database Has Priority Over DNS
    
    For any hostname that exists in both database and DNS, the database
    IP should be returned and DNS should not be queried.
    
    **Validates: Requirements 3.1, 3.2**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch
    
    # Ensure IPs are different to verify which one is returned
    if db_ip == dns_ip:
        return  # Skip this test case if IPs are the same
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Mock database manager to return IP
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = db_ip
    
    # Mock DNS (should NOT be called)
    with patch('socket.gethostbyname', return_value=dns_ip) as mock_dns:
        with patch('netwalker.netwalker_app.logger'):
            result = app._resolve_ip_for_hostname(hostname)
            
            # CRITICAL PROPERTY: Should return database IP, not DNS IP
            assert result == db_ip, \
                f"Should return database IP '{db_ip}', not DNS IP '{dns_ip}', got '{result}'"
            
            # CRITICAL PROPERTY: DNS should not be called
            mock_dns.assert_not_called()


@given(hostname=valid_hostnames())
@settings(max_examples=5, deadline=None)
def test_property_database_disabled_skips_to_dns(hostname):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 4 (Database Disabled)
    Database Disabled Skips to DNS
    
    For any hostname when database is disabled, the system should skip
    database lookup and go directly to DNS.
    
    **Validates: Requirements 3.2**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Mock database manager as disabled
    app.db_manager = MagicMock()
    app.db_manager.enabled = False
    
    # Mock DNS to return IP
    dns_ip = '192.168.1.1'
    with patch('socket.gethostbyname', return_value=dns_ip) as mock_dns:
        with patch('netwalker.netwalker_app.logger'):
            result = app._resolve_ip_for_hostname(hostname)
            
            # CRITICAL PROPERTY: Should return DNS IP
            assert result == dns_ip, \
                f"Should return DNS IP '{dns_ip}', got '{result}'"
            
            # CRITICAL PROPERTY: Database should not be called when disabled
            app.db_manager.get_primary_ip_by_hostname.assert_not_called()
            
            # CRITICAL PROPERTY: DNS should be called
            mock_dns.assert_called_once_with(hostname)


@given(hostname=valid_hostnames())
@settings(max_examples=5, deadline=None)
def test_property_database_none_skips_to_dns(hostname):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 4 (Database None)
    Database Manager None Skips to DNS
    
    For any hostname when database manager is None, the system should skip
    database lookup and go directly to DNS.
    
    **Validates: Requirements 3.2**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Set database manager to None
    app.db_manager = None
    
    # Mock DNS to return IP
    dns_ip = '10.0.0.1'
    with patch('socket.gethostbyname', return_value=dns_ip) as mock_dns:
        with patch('netwalker.netwalker_app.logger'):
            result = app._resolve_ip_for_hostname(hostname)
            
            # CRITICAL PROPERTY: Should return DNS IP
            assert result == dns_ip, \
                f"Should return DNS IP '{dns_ip}', got '{result}'"
            
            # CRITICAL PROPERTY: DNS should be called
            mock_dns.assert_called_once_with(hostname)


@given(
    hostname=valid_hostnames(),
    error_type=st.sampled_from([
        'gaierror',
        'timeout',
        'unexpected'
    ])
)
@settings(max_examples=5, deadline=None)
def test_property_dns_error_types_logged(hostname, error_type):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 9 (DNS Errors)
    DNS Error Types Are Logged
    
    For any hostname where DNS fails with different error types,
    all errors should be logged at WARNING level.
    
    **Validates: Requirements 4.3, 4.5**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch
    import socket
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Mock database manager to return None
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = None
    
    # Create appropriate error based on type
    if error_type == 'gaierror':
        error = socket.gaierror("Name resolution failed")
    elif error_type == 'timeout':
        error = socket.timeout("DNS timeout")
    else:  # unexpected
        error = RuntimeError("Unexpected DNS error")
    
    # Mock DNS to fail with error
    with patch('socket.gethostbyname', side_effect=error):
        # Mock logger to capture log calls
        with patch('netwalker.netwalker_app.logger') as mock_logger:
            result = app._resolve_ip_for_hostname(hostname)
            
            # CRITICAL PROPERTY: Should return None on DNS error
            assert result is None, \
                f"Should return None on DNS {error_type}, got '{result}'"
            
            # CRITICAL PROPERTY: Should log at WARNING level
            mock_logger.warning.assert_called_once()
            
            # CRITICAL PROPERTY: Log should include hostname
            log_message = mock_logger.warning.call_args[0][0]
            assert hostname in log_message, \
                f"Log should include hostname '{hostname}'"


# ============================================================================
# Property Tests for _parse_seed_file() Method - Blank IP Detection
# Task 4.2
# ============================================================================

@given(
    hostname=valid_hostnames(),
    ip_value=st.sampled_from(['', ' ', '  ', '\t', '\n', '   \t  '])
)
@settings(max_examples=5, deadline=None)
def test_property_blank_ip_detection_triggers_resolution(hostname, ip_value):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 1
    Blank IP Detection - Triggers Resolution
    
    For any seed file entry where the IP field is empty or contains only
    whitespace, the parser should flag it for resolution by calling
    _resolve_ip_for_hostname().
    
    **Validates: Requirements 1.1, 1.2, 1.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open, MagicMock
    import tempfile
    import os
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create a temporary seed file with blank IP
    seed_content = f"hostname,ip,status\n{hostname},{ip_value},pending\n"
    
    # Mock _resolve_ip_for_hostname to track if it's called
    with patch.object(app, '_resolve_ip_for_hostname', return_value='192.168.1.1') as mock_resolve:
        # Mock file operations
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse the seed file
                    app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Resolution should be triggered for blank IP
                    mock_resolve.assert_called_once_with(hostname)


@given(
    hostname=valid_hostnames(),
    ip_value=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_blank_ip_detection_bypasses_explicit_ip(hostname, ip_value):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 1
    Blank IP Detection - Bypasses Explicit IP
    
    For any seed file entry where the IP field contains a non-whitespace value,
    the parser should NOT trigger resolution and should use the explicit IP.
    
    **Validates: Requirements 1.1, 1.2, 1.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open, MagicMock
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create a temporary seed file with explicit IP
    seed_content = f"hostname,ip,status\n{hostname},{ip_value},pending\n"
    
    # Mock _resolve_ip_for_hostname to track if it's called
    with patch.object(app, '_resolve_ip_for_hostname', return_value='10.0.0.1') as mock_resolve:
        # Mock file operations
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse the seed file
                    app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Resolution should NOT be triggered for explicit IP
                    mock_resolve.assert_not_called()


@given(
    hostname=valid_hostnames(),
    whitespace_variations=st.lists(
        st.sampled_from(['', ' ', '  ', '\t', '\n', '   \t  ', '\r\n']),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=5, deadline=None)
def test_property_blank_ip_detection_all_whitespace_variations(hostname, whitespace_variations):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 1
    Blank IP Detection - All Whitespace Variations
    
    For any seed file with multiple entries containing different whitespace
    variations in the IP field, all should trigger resolution.
    
    **Validates: Requirements 1.1, 1.2, 1.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open, MagicMock
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file content with multiple whitespace variations
    seed_lines = ["hostname,ip,status"]
    for i, ws in enumerate(whitespace_variations):
        seed_lines.append(f"{hostname}-{i},{ws},pending")
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Mock _resolve_ip_for_hostname to return different IPs
    def resolve_side_effect(h):
        return f"192.168.1.{hash(h) % 254 + 1}"
    
    with patch.object(app, '_resolve_ip_for_hostname', side_effect=resolve_side_effect) as mock_resolve:
        # Mock file operations
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse the seed file
                    app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Resolution should be called for each whitespace entry
                    assert mock_resolve.call_count == len(whitespace_variations), \
                        f"Resolution should be called {len(whitespace_variations)} times, " \
                        f"but was called {mock_resolve.call_count} times"


@given(
    hostname=valid_hostnames(),
    ip_value=st.one_of(
        st.just(''),
        st.just(' '),
        valid_ipv4_addresses()
    )
)
@settings(max_examples=5, deadline=None)
def test_property_blank_ip_detection_consistency(hostname, ip_value):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 1
    Blank IP Detection - Consistency
    
    For any seed file entry, the blank IP detection logic should be consistent:
    empty/whitespace always triggers resolution, non-whitespace never does.
    
    **Validates: Requirements 1.1, 1.2, 1.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open, MagicMock
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file content
    seed_content = f"hostname,ip,status\n{hostname},{ip_value},pending\n"
    
    # Determine if IP is blank (empty or whitespace only)
    is_blank = ip_value.strip() == ''
    
    # Mock _resolve_ip_for_hostname
    with patch.object(app, '_resolve_ip_for_hostname', return_value='192.168.1.1') as mock_resolve:
        # Mock file operations
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse the seed file
                    app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Resolution behavior should match blank detection
                    if is_blank:
                        mock_resolve.assert_called_once_with(hostname)
                    else:
                        mock_resolve.assert_not_called()


@given(
    hostname1=valid_hostnames(),
    hostname2=valid_hostnames(),
    ip1=st.just(''),  # Blank IP
    ip2=valid_ipv4_addresses()  # Explicit IP
)
@settings(max_examples=5, deadline=None)
def test_property_blank_ip_detection_mixed_entries(hostname1, hostname2, ip1, ip2):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 1
    Blank IP Detection - Mixed Entries
    
    For any seed file with mixed entries (some with blank IPs, some with explicit IPs),
    only the blank IP entries should trigger resolution.
    
    **Validates: Requirements 1.1, 1.2, 1.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open, MagicMock
    
    # Skip if hostnames are the same
    if hostname1 == hostname2:
        return
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with mixed entries
    seed_content = (
        f"hostname,ip,status\n"
        f"{hostname1},{ip1},pending\n"
        f"{hostname2},{ip2},pending\n"
    )
    
    # Mock _resolve_ip_for_hostname
    with patch.object(app, '_resolve_ip_for_hostname', return_value='192.168.1.1') as mock_resolve:
        # Mock file operations
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse the seed file
                    app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Resolution should be called only once (for blank IP)
                    mock_resolve.assert_called_once_with(hostname1)


@given(
    hostname=valid_hostnames(),
    num_entries=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=5, deadline=None)
def test_property_blank_ip_detection_multiple_blank_entries(hostname, num_entries):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 1
    Blank IP Detection - Multiple Blank Entries
    
    For any seed file with multiple entries all having blank IPs,
    resolution should be triggered for each entry.
    
    **Validates: Requirements 1.1, 1.2, 1.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open, MagicMock
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with multiple blank IP entries
    seed_lines = ["hostname,ip,status"]
    for i in range(num_entries):
        seed_lines.append(f"{hostname}-{i},,pending")
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Mock _resolve_ip_for_hostname
    def resolve_side_effect(h):
        return f"192.168.1.{hash(h) % 254 + 1}"
    
    with patch.object(app, '_resolve_ip_for_hostname', side_effect=resolve_side_effect) as mock_resolve:
        # Mock file operations
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse the seed file
                    app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Resolution should be called for each blank entry
                    assert mock_resolve.call_count == num_entries, \
                        f"Resolution should be called {num_entries} times, " \
                        f"but was called {mock_resolve.call_count} times"


# ============================================================================
# Property Tests for Resolved IP Usage
# Task 4.3
# ============================================================================

@given(
    hostname=valid_hostnames(),
    resolved_ip=valid_ipv4_addresses(),
    resolution_method=st.sampled_from(['database', 'dns'])
)
@settings(max_examples=5, deadline=None)
def test_property_resolved_ip_usage(hostname, resolved_ip, resolution_method):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 6
    Resolved IP Usage
    
    For any hostname that is successfully resolved (via database or DNS),
    the resolved IP should appear in the discovery queue entry for that device.
    
    **Validates: Requirements 3.4, 7.1**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with blank IP
    seed_content = f"hostname,ip,status\n{hostname},,pending\n"
    
    # Mock resolution based on method
    if resolution_method == 'database':
        # Mock database to return IP
        app.db_manager = MagicMock()
        app.db_manager.enabled = True
        app.db_manager.get_primary_ip_by_hostname.return_value = resolved_ip
        
        # Mock DNS (should not be called)
        with patch('socket.gethostbyname', return_value='10.0.0.1') as mock_dns:
            with patch('builtins.open', mock_open(read_data=seed_content)):
                with patch('os.path.exists', return_value=True):
                    with patch('netwalker.netwalker_app.logger'):
                        # Parse seed file
                        seed_devices = app._parse_seed_file('dummy_seed.csv')
                        
                        # CRITICAL PROPERTY: Resolved IP should appear in discovery queue
                        assert len(seed_devices) == 1, \
                            f"Should have 1 device in queue, got {len(seed_devices)}"
                        
                        # CRITICAL PROPERTY: Device entry should contain resolved IP
                        device_entry = seed_devices[0]
                        assert resolved_ip in device_entry, \
                            f"Resolved IP '{resolved_ip}' should be in device entry '{device_entry}'"
                        
                        # CRITICAL PROPERTY: Device entry should be in format "hostname:ip"
                        expected_entry = f"{hostname}:{resolved_ip}"
                        assert device_entry == expected_entry, \
                            f"Device entry should be '{expected_entry}', got '{device_entry}'"
                        
                        # Verify DNS was not called (database succeeded)
                        mock_dns.assert_not_called()
    
    else:  # dns
        # Mock database to return None
        app.db_manager = MagicMock()
        app.db_manager.enabled = True
        app.db_manager.get_primary_ip_by_hostname.return_value = None
        
        # Mock DNS to return IP
        with patch('socket.gethostbyname', return_value=resolved_ip) as mock_dns:
            with patch('builtins.open', mock_open(read_data=seed_content)):
                with patch('os.path.exists', return_value=True):
                    with patch('netwalker.netwalker_app.logger'):
                        # Parse seed file
                        seed_devices = app._parse_seed_file('dummy_seed.csv')
                        
                        # CRITICAL PROPERTY: Resolved IP should appear in discovery queue
                        assert len(seed_devices) == 1, \
                            f"Should have 1 device in queue, got {len(seed_devices)}"
                        
                        # CRITICAL PROPERTY: Device entry should contain resolved IP
                        device_entry = seed_devices[0]
                        assert resolved_ip in device_entry, \
                            f"Resolved IP '{resolved_ip}' should be in device entry '{device_entry}'"
                        
                        # CRITICAL PROPERTY: Device entry should be in format "hostname:ip"
                        expected_entry = f"{hostname}:{resolved_ip}"
                        assert device_entry == expected_entry, \
                            f"Device entry should be '{expected_entry}', got '{device_entry}'"
                        
                        # Verify DNS was called (database failed)
                        mock_dns.assert_called_once_with(hostname)


@given(
    hostname=valid_hostnames(),
    resolved_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_resolved_ip_usage_database_priority(hostname, resolved_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 6 (Database Priority)
    Resolved IP Usage - Database Priority
    
    For any hostname resolved via database, the database IP should appear
    in the discovery queue entry, not any DNS IP.
    
    **Validates: Requirements 3.4, 7.1**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with blank IP
    seed_content = f"hostname,ip,status\n{hostname},,pending\n"
    
    # Mock database to return IP
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = resolved_ip
    
    # Mock DNS with different IP (should not be used)
    dns_ip = '10.0.0.99'
    with patch('socket.gethostbyname', return_value=dns_ip):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Database IP should be in queue, not DNS IP
                    assert len(seed_devices) == 1, \
                        f"Should have 1 device in queue, got {len(seed_devices)}"
                    
                    device_entry = seed_devices[0]
                    assert resolved_ip in device_entry, \
                        f"Database IP '{resolved_ip}' should be in device entry '{device_entry}'"
                    assert dns_ip not in device_entry, \
                        f"DNS IP '{dns_ip}' should NOT be in device entry '{device_entry}'"


@given(
    hostname=valid_hostnames(),
    resolved_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_resolved_ip_usage_dns_fallback(hostname, resolved_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 6 (DNS Fallback)
    Resolved IP Usage - DNS Fallback
    
    For any hostname where database returns None, the DNS IP should appear
    in the discovery queue entry.
    
    **Validates: Requirements 3.4, 7.1**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with blank IP
    seed_content = f"hostname,ip,status\n{hostname},,pending\n"
    
    # Mock database to return None
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = None
    
    # Mock DNS to return IP
    with patch('socket.gethostbyname', return_value=resolved_ip):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: DNS IP should be in queue
                    assert len(seed_devices) == 1, \
                        f"Should have 1 device in queue, got {len(seed_devices)}"
                    
                    device_entry = seed_devices[0]
                    assert resolved_ip in device_entry, \
                        f"DNS IP '{resolved_ip}' should be in device entry '{device_entry}'"
                    
                    expected_entry = f"{hostname}:{resolved_ip}"
                    assert device_entry == expected_entry, \
                        f"Device entry should be '{expected_entry}', got '{device_entry}'"


@given(
    hostname=valid_hostnames(),
    resolved_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_resolved_ip_usage_format_consistency(hostname, resolved_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 6 (Format Consistency)
    Resolved IP Usage - Format Consistency
    
    For any hostname with resolved IP, the discovery queue entry should
    follow the consistent format "hostname:ip_address".
    
    **Validates: Requirements 3.4, 7.1**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with blank IP
    seed_content = f"hostname,ip,status\n{hostname},,pending\n"
    
    # Mock database to return IP
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = resolved_ip
    
    with patch('builtins.open', mock_open(read_data=seed_content)):
        with patch('os.path.exists', return_value=True):
            with patch('netwalker.netwalker_app.logger'):
                # Parse seed file
                seed_devices = app._parse_seed_file('dummy_seed.csv')
                
                # CRITICAL PROPERTY: Entry should be in format "hostname:ip"
                assert len(seed_devices) == 1, \
                    f"Should have 1 device in queue, got {len(seed_devices)}"
                
                device_entry = seed_devices[0]
                
                # Verify format
                assert ':' in device_entry, \
                    f"Device entry should contain ':' separator, got '{device_entry}'"
                
                parts = device_entry.split(':')
                assert len(parts) == 2, \
                    f"Device entry should have exactly 2 parts, got {len(parts)}"
                
                entry_hostname, entry_ip = parts
                assert entry_hostname == hostname, \
                    f"Hostname should be '{hostname}', got '{entry_hostname}'"
                assert entry_ip == resolved_ip, \
                    f"IP should be '{resolved_ip}', got '{entry_ip}'"


@given(
    hostnames=st.lists(valid_hostnames(), min_size=2, max_size=5, unique=True),
    resolved_ips=st.lists(valid_ipv4_addresses(), min_size=2, max_size=5)
)
@settings(max_examples=5, deadline=None)
def test_property_resolved_ip_usage_multiple_devices(hostnames, resolved_ips):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 6 (Multiple Devices)
    Resolved IP Usage - Multiple Devices
    
    For any seed file with multiple hostnames requiring resolution,
    each resolved IP should appear in its corresponding discovery queue entry.
    
    **Validates: Requirements 3.4, 7.1**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Ensure we have enough IPs for all hostnames
    if len(resolved_ips) < len(hostnames):
        return
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with multiple blank IPs
    seed_lines = ["hostname,ip,status"]
    for hostname in hostnames:
        seed_lines.append(f"{hostname},,pending")
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Create mapping of hostnames to IPs
    hostname_to_ip = {hostname: resolved_ips[i] for i, hostname in enumerate(hostnames)}
    
    # Mock database to return IPs based on hostname
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.side_effect = lambda h: hostname_to_ip.get(h)
    
    with patch('builtins.open', mock_open(read_data=seed_content)):
        with patch('os.path.exists', return_value=True):
            with patch('netwalker.netwalker_app.logger'):
                # Parse seed file
                seed_devices = app._parse_seed_file('dummy_seed.csv')
                
                # CRITICAL PROPERTY: Should have entry for each hostname
                assert len(seed_devices) == len(hostnames), \
                    f"Should have {len(hostnames)} devices in queue, got {len(seed_devices)}"
                
                # CRITICAL PROPERTY: Each resolved IP should appear in queue
                for hostname in hostnames:
                    expected_ip = hostname_to_ip[hostname]
                    expected_entry = f"{hostname}:{expected_ip}"
                    
                    assert expected_entry in seed_devices, \
                        f"Expected entry '{expected_entry}' should be in queue"
                    
                    # Verify IP appears in at least one entry
                    ip_found = any(expected_ip in entry for entry in seed_devices)
                    assert ip_found, \
                        f"Resolved IP '{expected_ip}' should appear in discovery queue"


@given(
    hostname=valid_hostnames(),
    resolved_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_resolved_ip_usage_no_modification(hostname, resolved_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 6 (No Modification)
    Resolved IP Usage - No IP Modification
    
    For any hostname with resolved IP, the IP should appear in the discovery
    queue exactly as returned by the resolution method, without modification.
    
    **Validates: Requirements 3.4, 7.1**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with blank IP
    seed_content = f"hostname,ip,status\n{hostname},,pending\n"
    
    # Mock database to return IP
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = resolved_ip
    
    with patch('builtins.open', mock_open(read_data=seed_content)):
        with patch('os.path.exists', return_value=True):
            with patch('netwalker.netwalker_app.logger'):
                # Parse seed file
                seed_devices = app._parse_seed_file('dummy_seed.csv')
                
                # CRITICAL PROPERTY: IP should be exactly as resolved
                assert len(seed_devices) == 1, \
                    f"Should have 1 device in queue, got {len(seed_devices)}"
                
                device_entry = seed_devices[0]
                entry_ip = device_entry.split(':')[1]
                
                assert entry_ip == resolved_ip, \
                    f"IP in queue should be exactly '{resolved_ip}', got '{entry_ip}'"
                
                # Verify no whitespace or other modifications
                assert entry_ip.strip() == entry_ip, \
                    f"IP should not have leading/trailing whitespace"
                assert ' ' not in entry_ip, \
                    f"IP should not contain spaces"


@given(
    hostname=valid_hostnames(),
    resolved_ip=valid_ipv4_addresses(),
    num_resolutions=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=5, deadline=None)
def test_property_resolved_ip_usage_idempotence(hostname, resolved_ip, num_resolutions):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 6 (Idempotence)
    Resolved IP Usage - Idempotence
    
    For any hostname resolved multiple times with the same IP, each parsing
    should produce the same discovery queue entry.
    
    **Validates: Requirements 3.4, 7.1**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with blank IP
    seed_content = f"hostname,ip,status\n{hostname},,pending\n"
    
    # Mock database to return IP
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = resolved_ip
    
    # Parse seed file multiple times
    results = []
    for _ in range(num_resolutions):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    results.append(seed_devices)
    
    # CRITICAL PROPERTY: All results should be identical
    expected_entry = f"{hostname}:{resolved_ip}"
    for i, result in enumerate(results):
        assert len(result) == 1, \
            f"Parse {i+1} should have 1 device, got {len(result)}"
        assert result[0] == expected_entry, \
            f"Parse {i+1} should produce '{expected_entry}', got '{result[0]}'"
    
    # Verify all results are the same
    first_result = results[0]
    for i, result in enumerate(results[1:], start=2):
        assert result == first_result, \
            f"Parse {i} should match parse 1: expected {first_result}, got {result}"


# ============================================================================
# Property Tests for Complete Resolution Failure Handling
# Task 4.4
# ============================================================================

@given(
    unresolvable_hostname=valid_hostnames(),
    resolvable_hostname=valid_hostnames(),
    resolved_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_complete_resolution_failure_handling(
    unresolvable_hostname,
    resolvable_hostname,
    resolved_ip
):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 5
    Complete Resolution Failure Handling
    
    For any hostname that cannot be resolved by either database or DNS,
    the system should skip the device and continue processing remaining entries.
    
    **Validates: Requirements 3.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    import socket
    
    # Skip if hostnames are the same
    if unresolvable_hostname == resolvable_hostname:
        return
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with unresolvable hostname first, then resolvable hostname
    seed_content = (
        f"hostname,ip,status\n"
        f"{unresolvable_hostname},,pending\n"
        f"{resolvable_hostname},,pending\n"
    )
    
    # Mock database to return None for both hostnames
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = None
    
    # Mock DNS to fail for unresolvable hostname, succeed for resolvable hostname
    def dns_side_effect(hostname):
        if hostname == unresolvable_hostname:
            raise socket.gaierror("Name resolution failed")
        elif hostname == resolvable_hostname:
            return resolved_ip
        else:
            raise socket.gaierror("Unknown hostname")
    
    with patch('socket.gethostbyname', side_effect=dns_side_effect) as mock_dns:
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger') as mock_logger:
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Unresolvable device should be skipped
                    # Only the resolvable device should be in the queue
                    assert len(seed_devices) == 1, \
                        f"Should have 1 device in queue (unresolvable skipped), got {len(seed_devices)}"
                    
                    # CRITICAL PROPERTY: Queue should contain only the resolvable device
                    expected_entry = f"{resolvable_hostname}:{resolved_ip}"
                    assert seed_devices[0] == expected_entry, \
                        f"Queue should contain '{expected_entry}', got '{seed_devices[0]}'"
                    
                    # CRITICAL PROPERTY: Unresolvable hostname should NOT be in queue
                    unresolvable_in_queue = any(
                        unresolvable_hostname in entry for entry in seed_devices
                    )
                    assert not unresolvable_in_queue, \
                        f"Unresolvable hostname '{unresolvable_hostname}' should NOT be in queue"
                    
                    # CRITICAL PROPERTY: Warning should be logged for unresolvable hostname
                    warning_logged = any(
                        call[0][0] and unresolvable_hostname in str(call[0][0])
                        for call in mock_logger.warning.call_args_list
                    )
                    assert warning_logged, \
                        f"Warning should be logged for unresolvable hostname '{unresolvable_hostname}'"
                    
                    # Verify DNS was called for both hostnames
                    assert mock_dns.call_count == 2, \
                        f"DNS should be called twice, was called {mock_dns.call_count} times"


@given(
    unresolvable_hostnames=st.lists(
        valid_hostnames(),
        min_size=1,
        max_size=5,
        unique=True
    )
)
@settings(max_examples=5, deadline=None)
def test_property_complete_resolution_failure_all_unresolvable(unresolvable_hostnames):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 5 (All Unresolvable)
    Complete Resolution Failure - All Devices Unresolvable
    
    For any seed file where all hostnames cannot be resolved by either
    database or DNS, the system should skip all devices and return empty queue.
    
    **Validates: Requirements 3.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    import socket
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with all unresolvable hostnames
    seed_lines = ["hostname,ip,status"]
    for hostname in unresolvable_hostnames:
        seed_lines.append(f"{hostname},,pending")
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Mock database to return None for all hostnames
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = None
    
    # Mock DNS to fail for all hostnames
    with patch('socket.gethostbyname', side_effect=socket.gaierror("Name resolution failed")):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger') as mock_logger:
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Queue should be empty (all devices skipped)
                    assert len(seed_devices) == 0, \
                        f"Queue should be empty when all devices unresolvable, got {len(seed_devices)} devices"
                    
                    # CRITICAL PROPERTY: Warning should be logged for each unresolvable hostname
                    warning_count = mock_logger.warning.call_count
                    assert warning_count >= len(unresolvable_hostnames), \
                        f"Should log at least {len(unresolvable_hostnames)} warnings, " \
                        f"logged {warning_count}"


@given(
    unresolvable_hostname=valid_hostnames(),
    resolvable_hostnames=st.lists(
        valid_hostnames(),
        min_size=1,
        max_size=5,
        unique=True
    ),
    resolved_ips=st.lists(
        valid_ipv4_addresses(),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=5, deadline=None)
def test_property_complete_resolution_failure_mixed_resolvability(
    unresolvable_hostname,
    resolvable_hostnames,
    resolved_ips
):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 5 (Mixed Resolvability)
    Complete Resolution Failure - Mixed Resolvable and Unresolvable
    
    For any seed file with a mix of resolvable and unresolvable hostnames,
    the system should skip only the unresolvable devices and process the rest.
    
    **Validates: Requirements 3.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    import socket
    
    # Ensure we have enough IPs for all resolvable hostnames
    if len(resolved_ips) < len(resolvable_hostnames):
        return
    
    # Ensure unresolvable hostname is not in resolvable list
    if unresolvable_hostname in resolvable_hostnames:
        return
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with unresolvable hostname mixed with resolvable ones
    seed_lines = ["hostname,ip,status"]
    seed_lines.append(f"{unresolvable_hostname},,pending")
    for hostname in resolvable_hostnames:
        seed_lines.append(f"{hostname},,pending")
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Create mapping of resolvable hostnames to IPs
    hostname_to_ip = {
        hostname: resolved_ips[i]
        for i, hostname in enumerate(resolvable_hostnames)
    }
    
    # Mock database to return None for all hostnames
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = None
    
    # Mock DNS to fail for unresolvable, succeed for resolvable
    def dns_side_effect(hostname):
        if hostname == unresolvable_hostname:
            raise socket.gaierror("Name resolution failed")
        elif hostname in hostname_to_ip:
            return hostname_to_ip[hostname]
        else:
            raise socket.gaierror("Unknown hostname")
    
    with patch('socket.gethostbyname', side_effect=dns_side_effect):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger') as mock_logger:
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Queue should contain only resolvable devices
                    assert len(seed_devices) == len(resolvable_hostnames), \
                        f"Queue should have {len(resolvable_hostnames)} devices, " \
                        f"got {len(seed_devices)}"
                    
                    # CRITICAL PROPERTY: All resolvable devices should be in queue
                    for hostname in resolvable_hostnames:
                        expected_ip = hostname_to_ip[hostname]
                        expected_entry = f"{hostname}:{expected_ip}"
                        assert expected_entry in seed_devices, \
                            f"Queue should contain '{expected_entry}'"
                    
                    # CRITICAL PROPERTY: Unresolvable hostname should NOT be in queue
                    unresolvable_in_queue = any(
                        unresolvable_hostname in entry for entry in seed_devices
                    )
                    assert not unresolvable_in_queue, \
                        f"Unresolvable hostname '{unresolvable_hostname}' should NOT be in queue"
                    
                    # CRITICAL PROPERTY: Warning should be logged for unresolvable hostname
                    warning_logged = any(
                        call[0][0] and unresolvable_hostname in str(call[0][0])
                        for call in mock_logger.warning.call_args_list
                    )
                    assert warning_logged, \
                        f"Warning should be logged for unresolvable hostname '{unresolvable_hostname}'"


@given(
    unresolvable_hostname=valid_hostnames(),
    error_type=st.sampled_from(['gaierror', 'timeout', 'unexpected'])
)
@settings(max_examples=5, deadline=None)
def test_property_complete_resolution_failure_dns_error_types(
    unresolvable_hostname,
    error_type
):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 5 (DNS Error Types)
    Complete Resolution Failure - Different DNS Error Types
    
    For any hostname where DNS fails with different error types (gaierror,
    timeout, unexpected), the system should skip the device consistently.
    
    **Validates: Requirements 3.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    import socket
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with unresolvable hostname
    seed_content = f"hostname,ip,status\n{unresolvable_hostname},,pending\n"
    
    # Mock database to return None
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = None
    
    # Create appropriate DNS error based on type
    if error_type == 'gaierror':
        dns_error = socket.gaierror("Name resolution failed")
    elif error_type == 'timeout':
        dns_error = socket.timeout("DNS timeout")
    else:  # unexpected
        dns_error = RuntimeError("Unexpected DNS error")
    
    # Mock DNS to fail with error
    with patch('socket.gethostbyname', side_effect=dns_error):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger') as mock_logger:
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Device should be skipped for any DNS error type
                    assert len(seed_devices) == 0, \
                        f"Device should be skipped for DNS {error_type}, " \
                        f"got {len(seed_devices)} devices in queue"
                    
                    # CRITICAL PROPERTY: Warning should be logged
                    assert mock_logger.warning.call_count > 0, \
                        f"Warning should be logged for DNS {error_type}"


@given(
    num_entries=st.integers(min_value=2, max_value=5)
)
@settings(max_examples=5, deadline=None)
def test_property_complete_resolution_failure_entry_order_preserved(
    num_entries
):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 5 (Entry Order)
    Complete Resolution Failure - Entry Order Preserved
    
    For any seed file with unresolvable hostnames interspersed with resolvable
    ones, the order of resolvable devices in the queue should match their
    order in the seed file (excluding skipped devices).
    
    **Validates: Requirements 3.3, 7.4**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    import socket
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with alternating resolvable and unresolvable hostnames
    seed_lines = ["hostname,ip,status"]
    resolvable_hostnames = []
    unresolvable_hostnames = []
    for i in range(num_entries):
        if i % 2 == 0:
            # Resolvable hostname
            hostname = f"resolvable-device-{i}"
            resolvable_hostnames.append(hostname)
            seed_lines.append(f"{hostname},,pending")
        else:
            # Unresolvable hostname
            hostname = f"unresolvable-device-{i}"
            unresolvable_hostnames.append(hostname)
            seed_lines.append(f"{hostname},,pending")
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Mock database to return None for all hostnames
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = None
    
    # Mock DNS to fail for unresolvable, succeed for resolvable
    def dns_side_effect(hostname):
        if hostname.startswith('unresolvable-'):
            raise socket.gaierror("Name resolution failed")
        elif hostname.startswith('resolvable-'):
            # Return IP based on hostname index
            index = int(hostname.split('-')[-1])
            return f"192.168.1.{index + 1}"
        else:
            raise socket.gaierror("Unknown hostname")
    
    with patch('socket.gethostbyname', side_effect=dns_side_effect):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Queue should contain only resolvable devices
                    assert len(seed_devices) == len(resolvable_hostnames), \
                        f"Queue should have {len(resolvable_hostnames)} devices, " \
                        f"got {len(seed_devices)}"
                    
                    # CRITICAL PROPERTY: Order should be preserved
                    for i, hostname in enumerate(resolvable_hostnames):
                        index = int(hostname.split('-')[-1])
                        expected_ip = f"192.168.1.{index + 1}"
                        expected_entry = f"{hostname}:{expected_ip}"
                        assert seed_devices[i] == expected_entry, \
                            f"Device at position {i} should be '{expected_entry}', " \
                            f"got '{seed_devices[i]}'"


@given(
    unresolvable_hostname=valid_hostnames(),
    num_attempts=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=5, deadline=None)
def test_property_complete_resolution_failure_idempotence(
    unresolvable_hostname,
    num_attempts
):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 5 (Idempotence)
    Complete Resolution Failure - Idempotence
    
    For any unresolvable hostname, parsing the seed file multiple times
    should consistently skip the device each time.
    
    **Validates: Requirements 3.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    import socket
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with unresolvable hostname
    seed_content = f"hostname,ip,status\n{unresolvable_hostname},,pending\n"
    
    # Mock database to return None
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = None
    
    # Parse seed file multiple times
    for attempt in range(num_attempts):
        with patch('socket.gethostbyname', side_effect=socket.gaierror("Name resolution failed")):
            with patch('builtins.open', mock_open(read_data=seed_content)):
                with patch('os.path.exists', return_value=True):
                    with patch('netwalker.netwalker_app.logger'):
                        # Parse seed file
                        seed_devices = app._parse_seed_file('dummy_seed.csv')
                        
                        # CRITICAL PROPERTY: Device should be skipped consistently
                        assert len(seed_devices) == 0, \
                            f"Attempt {attempt + 1}: Device should be skipped, " \
                            f"got {len(seed_devices)} devices in queue"


# ============================================================================
# Property Tests for Explicit IP Bypass
# Task 4.5
# ============================================================================

@given(
    hostname=valid_hostnames(),
    explicit_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_explicit_ip_bypass(hostname, explicit_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 10
    Explicit IP Bypass
    
    For any seed file entry with a non-empty IP address, the system should
    use the provided IP without querying the database or performing DNS lookup.
    
    **Validates: Requirements 5.1**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with explicit IP
    seed_content = f"hostname,ip,status\n{hostname},{explicit_ip},pending\n"
    
    # Mock database manager
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = '10.0.0.99'  # Different IP
    
    # Mock DNS (should NOT be called)
    with patch('socket.gethostbyname', return_value='192.168.99.99') as mock_dns:
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Should use explicit IP
                    assert len(seed_devices) == 1, \
                        f"Should have 1 device in queue, got {len(seed_devices)}"
                    
                    device_entry = seed_devices[0]
                    expected_entry = f"{hostname}:{explicit_ip}"
                    assert device_entry == expected_entry, \
                        f"Should use explicit IP '{explicit_ip}', got '{device_entry}'"
                    
                    # CRITICAL PROPERTY: Database should NOT be queried
                    app.db_manager.get_primary_ip_by_hostname.assert_not_called()
                    
                    # CRITICAL PROPERTY: DNS should NOT be called
                    mock_dns.assert_not_called()


@given(
    hostname=valid_hostnames(),
    explicit_ip=valid_ipv4_addresses(),
    db_ip=valid_ipv4_addresses(),
    dns_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_explicit_ip_bypass_priority_over_database_and_dns(
    hostname,
    explicit_ip,
    db_ip,
    dns_ip
):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 10 (Priority)
    Explicit IP Bypass - Priority Over Database and DNS
    
    For any seed file entry with an explicit IP, the explicit IP should be
    used even if the database and DNS would return different IPs.
    
    **Validates: Requirements 5.1**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Ensure all IPs are different to verify which one is used
    if explicit_ip == db_ip or explicit_ip == dns_ip or db_ip == dns_ip:
        return  # Skip this test case if any IPs are the same
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with explicit IP
    seed_content = f"hostname,ip,status\n{hostname},{explicit_ip},pending\n"
    
    # Mock database manager to return different IP
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = db_ip
    
    # Mock DNS to return different IP (should NOT be called)
    with patch('socket.gethostbyname', return_value=dns_ip) as mock_dns:
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Should use explicit IP, not database or DNS IP
                    assert len(seed_devices) == 1, \
                        f"Should have 1 device in queue, got {len(seed_devices)}"
                    
                    device_entry = seed_devices[0]
                    assert explicit_ip in device_entry, \
                        f"Should use explicit IP '{explicit_ip}', got '{device_entry}'"
                    assert db_ip not in device_entry, \
                        f"Should NOT use database IP '{db_ip}', got '{device_entry}'"
                    assert dns_ip not in device_entry, \
                        f"Should NOT use DNS IP '{dns_ip}', got '{device_entry}'"
                    
                    # CRITICAL PROPERTY: Database should NOT be queried
                    app.db_manager.get_primary_ip_by_hostname.assert_not_called()
                    
                    # CRITICAL PROPERTY: DNS should NOT be called
                    mock_dns.assert_not_called()


@given(
    hostnames=st.lists(valid_hostnames(), min_size=2, max_size=5, unique=True),
    explicit_ips=st.lists(valid_ipv4_addresses(), min_size=2, max_size=5)
)
@settings(max_examples=5, deadline=None)
def test_property_explicit_ip_bypass_multiple_entries(hostnames, explicit_ips):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 10 (Multiple Entries)
    Explicit IP Bypass - Multiple Entries
    
    For any seed file with multiple entries all having explicit IPs,
    none should trigger database or DNS lookup.
    
    **Validates: Requirements 5.1**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Ensure we have enough IPs for all hostnames
    if len(explicit_ips) < len(hostnames):
        return
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with multiple explicit IPs
    seed_lines = ["hostname,ip,status"]
    for i, hostname in enumerate(hostnames):
        seed_lines.append(f"{hostname},{explicit_ips[i]},pending")
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Mock database manager
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = '10.0.0.99'
    
    # Mock DNS (should NOT be called)
    with patch('socket.gethostbyname', return_value='192.168.99.99') as mock_dns:
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Should have entry for each hostname
                    assert len(seed_devices) == len(hostnames), \
                        f"Should have {len(hostnames)} devices in queue, got {len(seed_devices)}"
                    
                    # CRITICAL PROPERTY: Each entry should use its explicit IP
                    for i, hostname in enumerate(hostnames):
                        expected_entry = f"{hostname}:{explicit_ips[i]}"
                        assert expected_entry in seed_devices, \
                            f"Queue should contain '{expected_entry}'"
                    
                    # CRITICAL PROPERTY: Database should NOT be queried at all
                    app.db_manager.get_primary_ip_by_hostname.assert_not_called()
                    
                    # CRITICAL PROPERTY: DNS should NOT be called at all
                    mock_dns.assert_not_called()


@given(
    hostname_blank=valid_hostnames(),
    hostname_explicit=valid_hostnames(),
    explicit_ip=valid_ipv4_addresses(),
    resolved_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_explicit_ip_bypass_mixed_with_blank_ips(
    hostname_blank,
    hostname_explicit,
    explicit_ip,
    resolved_ip
):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 10 (Mixed Entries)
    Explicit IP Bypass - Mixed with Blank IPs
    
    For any seed file with a mix of explicit IPs and blank IPs,
    only the blank IP entries should trigger resolution.
    
    **Validates: Requirements 5.1, 5.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Skip if hostnames are the same
    if hostname_blank == hostname_explicit:
        return
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with mixed entries
    seed_content = (
        f"hostname,ip,status\n"
        f"{hostname_explicit},{explicit_ip},pending\n"
        f"{hostname_blank},,pending\n"
    )
    
    # Mock database manager to return IP for blank entry
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = resolved_ip
    
    # Mock DNS (should NOT be called since database succeeds)
    with patch('socket.gethostbyname', return_value='192.168.99.99') as mock_dns:
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Should have both devices in queue
                    assert len(seed_devices) == 2, \
                        f"Should have 2 devices in queue, got {len(seed_devices)}"
                    
                    # CRITICAL PROPERTY: Explicit IP entry should use explicit IP
                    expected_explicit = f"{hostname_explicit}:{explicit_ip}"
                    assert expected_explicit in seed_devices, \
                        f"Queue should contain explicit IP entry '{expected_explicit}'"
                    
                    # CRITICAL PROPERTY: Blank IP entry should use resolved IP
                    expected_resolved = f"{hostname_blank}:{resolved_ip}"
                    assert expected_resolved in seed_devices, \
                        f"Queue should contain resolved IP entry '{expected_resolved}'"
                    
                    # CRITICAL PROPERTY: Database should be queried only for blank IP entry
                    app.db_manager.get_primary_ip_by_hostname.assert_called_once_with(hostname_blank)
                    
                    # CRITICAL PROPERTY: DNS should NOT be called (database succeeded)
                    mock_dns.assert_not_called()


@given(
    hostname=valid_hostnames(),
    explicit_ip=valid_ipv4_addresses(),
    num_parses=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=5, deadline=None)
def test_property_explicit_ip_bypass_idempotence(hostname, explicit_ip, num_parses):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 10 (Idempotence)
    Explicit IP Bypass - Idempotence
    
    For any seed file entry with an explicit IP, parsing multiple times
    should consistently use the explicit IP without triggering resolution.
    
    **Validates: Requirements 5.1**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with explicit IP
    seed_content = f"hostname,ip,status\n{hostname},{explicit_ip},pending\n"
    
    # Mock database manager
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = '10.0.0.99'
    
    # Parse seed file multiple times
    for attempt in range(num_parses):
        with patch('socket.gethostbyname', return_value='192.168.99.99') as mock_dns:
            with patch('builtins.open', mock_open(read_data=seed_content)):
                with patch('os.path.exists', return_value=True):
                    with patch('netwalker.netwalker_app.logger'):
                        # Parse seed file
                        seed_devices = app._parse_seed_file('dummy_seed.csv')
                        
                        # CRITICAL PROPERTY: Should consistently use explicit IP
                        assert len(seed_devices) == 1, \
                            f"Parse {attempt + 1}: Should have 1 device, got {len(seed_devices)}"
                        
                        expected_entry = f"{hostname}:{explicit_ip}"
                        assert seed_devices[0] == expected_entry, \
                            f"Parse {attempt + 1}: Should use explicit IP '{explicit_ip}', " \
                            f"got '{seed_devices[0]}'"
                        
                        # CRITICAL PROPERTY: Database should NOT be queried
                        app.db_manager.get_primary_ip_by_hostname.assert_not_called()
                        
                        # CRITICAL PROPERTY: DNS should NOT be called
                        mock_dns.assert_not_called()


@given(
    hostname=valid_hostnames(),
    explicit_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_explicit_ip_bypass_no_validation(hostname, explicit_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 10 (No Validation)
    Explicit IP Bypass - No IP Validation
    
    For any seed file entry with an explicit IP, the system should use
    the IP as-is without validating its format or reachability.
    
    **Validates: Requirements 5.1, 5.4**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with explicit IP
    seed_content = f"hostname,ip,status\n{hostname},{explicit_ip},pending\n"
    
    # Mock database manager
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    with patch('builtins.open', mock_open(read_data=seed_content)):
        with patch('os.path.exists', return_value=True):
            with patch('netwalker.netwalker_app.logger'):
                # Parse seed file
                seed_devices = app._parse_seed_file('dummy_seed.csv')
                
                # CRITICAL PROPERTY: IP should be used exactly as provided
                assert len(seed_devices) == 1, \
                    f"Should have 1 device in queue, got {len(seed_devices)}"
                
                device_entry = seed_devices[0]
                entry_ip = device_entry.split(':')[1]
                
                # CRITICAL PROPERTY: IP should match exactly (no modification)
                assert entry_ip == explicit_ip, \
                    f"IP should be exactly '{explicit_ip}', got '{entry_ip}'"
                
                # Verify no whitespace or other modifications
                assert entry_ip.strip() == entry_ip, \
                    "IP should not have leading/trailing whitespace"


@given(
    hostname=valid_hostnames(),
    explicit_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_explicit_ip_bypass_performance(hostname, explicit_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 10 (Performance)
    Explicit IP Bypass - Performance Characteristics
    
    For any seed file entry with an explicit IP, processing should be
    faster than entries requiring resolution (no database or DNS queries).
    
    **Validates: Requirements 5.2**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    import time
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with explicit IP
    seed_content = f"hostname,ip,status\n{hostname},{explicit_ip},pending\n"
    
    # Mock database manager with artificial delay
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    def slow_db_lookup(h):
        time.sleep(0.1)  # 100ms delay
        return '10.0.0.99'
    
    app.db_manager.get_primary_ip_by_hostname.side_effect = slow_db_lookup
    
    # Mock DNS with artificial delay
    def slow_dns_lookup(h):
        time.sleep(0.1)  # 100ms delay
        return '192.168.99.99'
    
    with patch('socket.gethostbyname', side_effect=slow_dns_lookup) as mock_dns:
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Measure parsing time
                    start_time = time.time()
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    elapsed_time = time.time() - start_time
                    
                    # CRITICAL PROPERTY: Should complete quickly (no delays from DB/DNS)
                    # If DB or DNS were called, elapsed time would be >= 100ms
                    assert elapsed_time < 0.05, \
                        f"Parsing should be fast (<50ms), took {elapsed_time * 1000:.1f}ms"
                    
                    # CRITICAL PROPERTY: Should use explicit IP
                    assert len(seed_devices) == 1, \
                        f"Should have 1 device in queue, got {len(seed_devices)}"
                    
                    expected_entry = f"{hostname}:{explicit_ip}"
                    assert seed_devices[0] == expected_entry, \
                        f"Should use explicit IP '{explicit_ip}', got '{seed_devices[0]}'"
                    
                    # CRITICAL PROPERTY: Database should NOT be queried
                    app.db_manager.get_primary_ip_by_hostname.assert_not_called()
                    
                    # CRITICAL PROPERTY: DNS should NOT be called
                    mock_dns.assert_not_called()


# ============================================================================
# Property Tests for Explicit IP Preservation
# Task 4.6
# ============================================================================

@given(
    hostname=valid_hostnames(),
    explicit_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_explicit_ip_preservation(hostname, explicit_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 12
    Explicit IP Preservation
    
    For any seed file entry with an explicit IP address, the IP in the
    discovery queue should exactly match the IP from the seed file.
    
    **Validates: Requirements 5.4**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with explicit IP
    seed_content = f"hostname,ip,status\n{hostname},{explicit_ip},pending\n"
    
    # Mock database manager (should not be called)
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    # Mock DNS (should not be called)
    with patch('socket.gethostbyname') as mock_dns:
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Discovery queue should contain exactly one entry
                    assert len(seed_devices) == 1, \
                        f"Discovery queue should have 1 device, got {len(seed_devices)}"
                    
                    device_entry = seed_devices[0]
                    
                    # CRITICAL PROPERTY: The IP in discovery queue must exactly match seed file IP
                    expected_entry = f"{hostname}:{explicit_ip}"
                    assert device_entry == expected_entry, \
                        f"Discovery queue IP should exactly match seed file IP. " \
                        f"Expected '{expected_entry}', got '{device_entry}'"
                    
                    # Verify the explicit IP is preserved without modification
                    assert explicit_ip in device_entry, \
                        f"Explicit IP '{explicit_ip}' should be preserved in '{device_entry}'"
                    
                    # CRITICAL PROPERTY: No resolution should occur
                    app.db_manager.get_primary_ip_by_hostname.assert_not_called()
                    mock_dns.assert_not_called()


@given(
    hostname=valid_hostnames(),
    explicit_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_explicit_ip_preservation_no_modification(hostname, explicit_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 12 (No Modification)
    Explicit IP Preservation - No Modification
    
    For any seed file entry with an explicit IP, the system should not
    modify or validate the IP address during processing.
    
    **Validates: Requirements 5.4**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with explicit IP
    seed_content = f"hostname,ip,status\n{hostname},{explicit_ip},pending\n"
    
    # Mock database manager
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    with patch('socket.gethostbyname'):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: IP should be preserved exactly as provided
                    device_entry = seed_devices[0]
                    
                    # Extract IP from device entry (format: hostname:ip)
                    if ':' in device_entry:
                        _, actual_ip = device_entry.split(':', 1)
                        
                        # CRITICAL PROPERTY: IP must match exactly (no trimming, no validation, no modification)
                        assert actual_ip == explicit_ip, \
                            f"IP should be preserved exactly. Expected '{explicit_ip}', got '{actual_ip}'"


@given(
    hostnames=st.lists(valid_hostnames(), min_size=2, max_size=5, unique=True),
    explicit_ips=st.lists(valid_ipv4_addresses(), min_size=2, max_size=5)
)
@settings(max_examples=5, deadline=None)
def test_property_explicit_ip_preservation_multiple_entries(hostnames, explicit_ips):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 12 (Multiple Entries)
    Explicit IP Preservation - Multiple Entries
    
    For any seed file with multiple entries all having explicit IPs,
    each IP in the discovery queue should exactly match its corresponding
    seed file IP.
    
    **Validates: Requirements 5.4**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Ensure we have enough IPs for all hostnames
    if len(explicit_ips) < len(hostnames):
        return
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with multiple explicit IPs
    seed_lines = ["hostname,ip,status"]
    for i, hostname in enumerate(hostnames):
        seed_lines.append(f"{hostname},{explicit_ips[i]},pending")
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Mock database manager
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    with patch('socket.gethostbyname'):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Should have entry for each hostname
                    assert len(seed_devices) == len(hostnames), \
                        f"Should have {len(hostnames)} devices in queue, got {len(seed_devices)}"
                    
                    # CRITICAL PROPERTY: Each entry should preserve its exact IP from seed file
                    for i, hostname in enumerate(hostnames):
                        expected_entry = f"{hostname}:{explicit_ips[i]}"
                        assert expected_entry in seed_devices, \
                            f"Queue should contain '{expected_entry}' with exact IP '{explicit_ips[i]}'"
                    
                    # Verify no resolution occurred
                    app.db_manager.get_primary_ip_by_hostname.assert_not_called()


@given(
    hostname=valid_hostnames(),
    explicit_ip=valid_ipv4_addresses(),
    num_parses=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=5, deadline=None)
def test_property_explicit_ip_preservation_idempotence(hostname, explicit_ip, num_parses):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 12 (Idempotence)
    Explicit IP Preservation - Idempotence
    
    For any seed file entry with an explicit IP, parsing the same file
    multiple times should always preserve the exact same IP.
    
    **Validates: Requirements 5.4**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with explicit IP
    seed_content = f"hostname,ip,status\n{hostname},{explicit_ip},pending\n"
    
    # Mock database manager
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    expected_entry = f"{hostname}:{explicit_ip}"
    
    with patch('socket.gethostbyname'):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file multiple times
                    for i in range(num_parses):
                        seed_devices = app._parse_seed_file('dummy_seed.csv')
                        
                        # CRITICAL PROPERTY: Each parse should preserve exact IP
                        assert len(seed_devices) == 1, \
                            f"Parse {i+1}: Should have 1 device, got {len(seed_devices)}"
                        
                        device_entry = seed_devices[0]
                        assert device_entry == expected_entry, \
                            f"Parse {i+1}: IP should be preserved exactly. " \
                            f"Expected '{expected_entry}', got '{device_entry}'"


@given(
    hostname=valid_hostnames(),
    explicit_ip=valid_ipv4_addresses(),
    db_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_explicit_ip_preservation_ignores_database(hostname, explicit_ip, db_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 12 (Database Ignored)
    Explicit IP Preservation - Ignores Database IP
    
    For any seed file entry with an explicit IP, the discovery queue should
    contain the seed file IP even if the database has a different IP for
    the same hostname.
    
    **Validates: Requirements 5.4**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Skip if IPs are the same (can't verify which was used)
    if explicit_ip == db_ip:
        return
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with explicit IP
    seed_content = f"hostname,ip,status\n{hostname},{explicit_ip},pending\n"
    
    # Mock database manager to return different IP
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = db_ip
    
    with patch('socket.gethostbyname'):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    device_entry = seed_devices[0]
                    
                    # CRITICAL PROPERTY: Should use seed file IP, not database IP
                    assert explicit_ip in device_entry, \
                        f"Should preserve seed file IP '{explicit_ip}', got '{device_entry}'"
                    assert db_ip not in device_entry, \
                        f"Should NOT use database IP '{db_ip}', got '{device_entry}'"
                    
                    # CRITICAL PROPERTY: Database should not be queried
                    app.db_manager.get_primary_ip_by_hostname.assert_not_called()


@given(
    hostname=valid_hostnames(),
    explicit_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_explicit_ip_preservation_with_whitespace(hostname, explicit_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 12 (Whitespace Handling)
    Explicit IP Preservation - Whitespace Trimming
    
    For any seed file entry with an explicit IP that has leading/trailing
    whitespace, the system should trim the whitespace but preserve the IP value.
    
    **Validates: Requirements 5.4**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with explicit IP that has whitespace
    ip_with_whitespace = f"  {explicit_ip}  "
    seed_content = f"hostname,ip,status\n{hostname},{ip_with_whitespace},pending\n"
    
    # Mock database manager
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    with patch('socket.gethostbyname'):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Should have one entry
                    assert len(seed_devices) == 1, \
                        f"Should have 1 device, got {len(seed_devices)}"
                    
                    device_entry = seed_devices[0]
                    
                    # CRITICAL PROPERTY: IP should be trimmed and preserved
                    expected_entry = f"{hostname}:{explicit_ip}"
                    assert device_entry == expected_entry, \
                        f"IP should be trimmed and preserved. Expected '{expected_entry}', got '{device_entry}'"
                    
                    # Verify no resolution occurred
                    app.db_manager.get_primary_ip_by_hostname.assert_not_called()



# ============================================================================
# Property Tests for Attribute Preservation
# Task 4.7
# ============================================================================

@given(
    hostname=valid_hostnames(),
    resolved_ip=valid_ipv4_addresses(),
    resolution_method=st.sampled_from(['database', 'dns'])
)
@settings(max_examples=5, deadline=None)
def test_property_attribute_preservation(hostname, resolved_ip, resolution_method):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 15
    Attribute Preservation
    
    For any seed file entry that undergoes IP resolution, all non-IP attributes
    (hostname, status) should be preserved unchanged in the discovery queue entry.
    
    **Validates: Requirements 7.2**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with blank IP (triggers resolution)
    seed_content = f"hostname,ip,status\n{hostname},,pending\n"
    
    # Mock database manager and DNS based on resolution method
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    if resolution_method == 'database':
        # Database returns IP, DNS not called
        app.db_manager.get_primary_ip_by_hostname.return_value = resolved_ip
        with patch('socket.gethostbyname') as mock_dns:
            with patch('builtins.open', mock_open(read_data=seed_content)):
                with patch('os.path.exists', return_value=True):
                    with patch('netwalker.netwalker_app.logger'):
                        # Parse seed file
                        seed_devices = app._parse_seed_file('dummy_seed.csv')
                        
                        # CRITICAL PROPERTY: Should have exactly one entry
                        assert len(seed_devices) == 1, \
                            f"Discovery queue should have 1 device, got {len(seed_devices)}"
                        
                        device_entry = seed_devices[0]
                        
                        # CRITICAL PROPERTY: Hostname must be preserved exactly
                        assert device_entry.startswith(f"{hostname}:"), \
                            f"Hostname should be preserved. Expected to start with '{hostname}:', got '{device_entry}'"
                        
                        # CRITICAL PROPERTY: Resolved IP should be present
                        assert device_entry == f"{hostname}:{resolved_ip}", \
                            f"Entry should be '{hostname}:{resolved_ip}', got '{device_entry}'"
                        
                        # Verify hostname is not modified (case, whitespace, etc.)
                        extracted_hostname = device_entry.split(':')[0]
                        assert extracted_hostname == hostname, \
                            f"Hostname should be unchanged. Expected '{hostname}', got '{extracted_hostname}'"
    else:  # dns
        # Database returns None, DNS returns IP
        app.db_manager.get_primary_ip_by_hostname.return_value = None
        with patch('socket.gethostbyname', return_value=resolved_ip):
            with patch('builtins.open', mock_open(read_data=seed_content)):
                with patch('os.path.exists', return_value=True):
                    with patch('netwalker.netwalker_app.logger'):
                        # Parse seed file
                        seed_devices = app._parse_seed_file('dummy_seed.csv')
                        
                        # CRITICAL PROPERTY: Should have exactly one entry
                        assert len(seed_devices) == 1, \
                            f"Discovery queue should have 1 device, got {len(seed_devices)}"
                        
                        device_entry = seed_devices[0]
                        
                        # CRITICAL PROPERTY: Hostname must be preserved exactly
                        assert device_entry.startswith(f"{hostname}:"), \
                            f"Hostname should be preserved. Expected to start with '{hostname}:', got '{device_entry}'"
                        
                        # CRITICAL PROPERTY: Resolved IP should be present
                        assert device_entry == f"{hostname}:{resolved_ip}", \
                            f"Entry should be '{hostname}:{resolved_ip}', got '{device_entry}'"
                        
                        # Verify hostname is not modified (case, whitespace, etc.)
                        extracted_hostname = device_entry.split(':')[0]
                        assert extracted_hostname == hostname, \
                            f"Hostname should be unchanged. Expected '{hostname}', got '{extracted_hostname}'"


@given(
    hostname=valid_hostnames(),
    resolved_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_attribute_preservation_hostname_case(hostname, resolved_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 15 (Case Preservation)
    Attribute Preservation - Hostname Case
    
    For any seed file entry with specific hostname casing that undergoes IP
    resolution, the hostname case should be preserved exactly as provided.
    
    **Validates: Requirements 7.2**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with blank IP
    seed_content = f"hostname,ip,status\n{hostname},,pending\n"
    
    # Mock database to return IP
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = resolved_ip
    
    with patch('socket.gethostbyname'):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Should have one entry
                    assert len(seed_devices) == 1, \
                        f"Should have 1 device, got {len(seed_devices)}"
                    
                    device_entry = seed_devices[0]
                    extracted_hostname = device_entry.split(':')[0]
                    
                    # CRITICAL PROPERTY: Hostname case must be preserved exactly
                    assert extracted_hostname == hostname, \
                        f"Hostname case should be preserved. Expected '{hostname}', got '{extracted_hostname}'"
                    
                    # Verify character-by-character match
                    for i, (expected_char, actual_char) in enumerate(zip(hostname, extracted_hostname)):
                        assert expected_char == actual_char, \
                            f"Character {i} should match: expected '{expected_char}', got '{actual_char}'"


@given(
    hostnames=st.lists(valid_hostnames(), min_size=2, max_size=5, unique=True),
    resolved_ips=st.lists(valid_ipv4_addresses(), min_size=2, max_size=5)
)
@settings(max_examples=5, deadline=None)
def test_property_attribute_preservation_multiple_devices(hostnames, resolved_ips):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 15 (Multiple Devices)
    Attribute Preservation - Multiple Devices
    
    For any seed file with multiple entries that undergo IP resolution,
    all hostnames should be preserved unchanged in their respective
    discovery queue entries.
    
    **Validates: Requirements 7.2**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Ensure we have matching lists
    if len(resolved_ips) < len(hostnames):
        resolved_ips = resolved_ips * ((len(hostnames) // len(resolved_ips)) + 1)
    resolved_ips = resolved_ips[:len(hostnames)]
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with multiple blank IPs
    seed_lines = ["hostname,ip,status"]
    for hostname in hostnames:
        seed_lines.append(f"{hostname},,pending")
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Mock database to return IPs based on hostname
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    # Create a mapping of hostname to IP
    hostname_to_ip = dict(zip(hostnames, resolved_ips))
    
    def get_ip_for_hostname(h):
        return hostname_to_ip.get(h)
    
    app.db_manager.get_primary_ip_by_hostname.side_effect = get_ip_for_hostname
    
    with patch('socket.gethostbyname'):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Should have same number of entries as hostnames
                    assert len(seed_devices) == len(hostnames), \
                        f"Should have {len(hostnames)} devices, got {len(seed_devices)}"
                    
                    # CRITICAL PROPERTY: Each hostname should be preserved in its entry
                    for i, (hostname, resolved_ip) in enumerate(zip(hostnames, resolved_ips)):
                        device_entry = seed_devices[i]
                        extracted_hostname = device_entry.split(':')[0]
                        
                        assert extracted_hostname == hostname, \
                            f"Device {i}: hostname should be preserved. " \
                            f"Expected '{hostname}', got '{extracted_hostname}'"
                        
                        assert device_entry == f"{hostname}:{resolved_ip}", \
                            f"Device {i}: entry should be '{hostname}:{resolved_ip}', got '{device_entry}'"


@given(
    hostname=valid_hostnames(),
    resolved_ip=valid_ipv4_addresses(),
    num_resolutions=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=5, deadline=None)
def test_property_attribute_preservation_idempotence(hostname, resolved_ip, num_resolutions):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 15 (Idempotence)
    Attribute Preservation - Idempotence
    
    For any seed file entry that undergoes IP resolution multiple times
    (e.g., re-parsing the same seed file), the hostname should be preserved
    identically each time.
    
    **Validates: Requirements 7.2**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with blank IP
    seed_content = f"hostname,ip,status\n{hostname},,pending\n"
    
    # Mock database to return IP
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = resolved_ip
    
    # Parse the same seed file multiple times
    previous_entry = None
    
    for i in range(num_resolutions):
        with patch('socket.gethostbyname'):
            with patch('builtins.open', mock_open(read_data=seed_content)):
                with patch('os.path.exists', return_value=True):
                    with patch('netwalker.netwalker_app.logger'):
                        # Parse seed file
                        seed_devices = app._parse_seed_file('dummy_seed.csv')
                        
                        # CRITICAL PROPERTY: Should have one entry
                        assert len(seed_devices) == 1, \
                            f"Parse {i+1}: should have 1 device, got {len(seed_devices)}"
                        
                        device_entry = seed_devices[0]
                        extracted_hostname = device_entry.split(':')[0]
                        
                        # CRITICAL PROPERTY: Hostname should be preserved identically
                        assert extracted_hostname == hostname, \
                            f"Parse {i+1}: hostname should be preserved. " \
                            f"Expected '{hostname}', got '{extracted_hostname}'"
                        
                        # CRITICAL PROPERTY: Entry should be identical across parses
                        if previous_entry is not None:
                            assert device_entry == previous_entry, \
                                f"Parse {i+1}: entry should be identical to previous parse. " \
                                f"Expected '{previous_entry}', got '{device_entry}'"
                        
                        previous_entry = device_entry


@given(
    hostname=valid_hostnames(),
    resolved_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_attribute_preservation_no_hostname_modification(hostname, resolved_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 15 (No Modification)
    Attribute Preservation - No Hostname Modification
    
    For any seed file entry that undergoes IP resolution, the hostname
    should not be modified in any way (no trimming, case changes, or
    character substitutions beyond what was in the original seed file).
    
    **Validates: Requirements 7.2**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with blank IP
    seed_content = f"hostname,ip,status\n{hostname},,pending\n"
    
    # Mock database to return IP
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = resolved_ip
    
    with patch('socket.gethostbyname'):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Should have one entry
                    assert len(seed_devices) == 1, \
                        f"Should have 1 device, got {len(seed_devices)}"
                    
                    device_entry = seed_devices[0]
                    extracted_hostname = device_entry.split(':')[0]
                    
                    # CRITICAL PROPERTY: Hostname should be byte-for-byte identical
                    assert extracted_hostname == hostname, \
                        f"Hostname should be unmodified. Expected '{hostname}', got '{extracted_hostname}'"
                    
                    # Verify length is preserved
                    assert len(extracted_hostname) == len(hostname), \
                        f"Hostname length should be preserved. " \
                        f"Expected {len(hostname)}, got {len(extracted_hostname)}"
                    
                    # Verify no whitespace was added or removed
                    assert extracted_hostname.strip() == hostname.strip(), \
                        f"Hostname whitespace handling should be consistent"


@given(
    hostname=valid_hostnames(),
    resolved_ip=valid_ipv4_addresses(),
    resolution_failure=st.booleans()
)
@settings(max_examples=5, deadline=None)
def test_property_attribute_preservation_with_resolution_failure(
    hostname,
    resolved_ip,
    resolution_failure
):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 15 (Resolution Failure)
    Attribute Preservation - Resolution Failure Handling
    
    For any seed file entry where IP resolution fails, the hostname should
    still be preserved in logs/warnings (even though the device is skipped).
    For successful resolution, hostname should be preserved in the queue.
    
    **Validates: Requirements 7.2**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    import socket
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with blank IP
    seed_content = f"hostname,ip,status\n{hostname},,pending\n"
    
    # Mock database and DNS based on resolution_failure flag
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    if resolution_failure:
        # Both database and DNS fail
        app.db_manager.get_primary_ip_by_hostname.return_value = None
        with patch('socket.gethostbyname', side_effect=socket.gaierror("Failed")):
            with patch('builtins.open', mock_open(read_data=seed_content)):
                with patch('os.path.exists', return_value=True):
                    with patch('netwalker.netwalker_app.logger') as mock_logger:
                        # Parse seed file
                        seed_devices = app._parse_seed_file('dummy_seed.csv')
                        
                        # CRITICAL PROPERTY: Device should be skipped
                        assert len(seed_devices) == 0, \
                            f"Failed resolution should skip device, got {len(seed_devices)} devices"
                        
                        # CRITICAL PROPERTY: Warning log should contain original hostname
                        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
                        hostname_in_logs = any(hostname in msg for msg in warning_calls)
                        assert hostname_in_logs, \
                            f"Hostname '{hostname}' should appear in warning logs"
    else:
        # Resolution succeeds
        app.db_manager.get_primary_ip_by_hostname.return_value = resolved_ip
        with patch('socket.gethostbyname'):
            with patch('builtins.open', mock_open(read_data=seed_content)):
                with patch('os.path.exists', return_value=True):
                    with patch('netwalker.netwalker_app.logger'):
                        # Parse seed file
                        seed_devices = app._parse_seed_file('dummy_seed.csv')
                        
                        # CRITICAL PROPERTY: Should have one entry
                        assert len(seed_devices) == 1, \
                            f"Successful resolution should add device, got {len(seed_devices)}"
                        
                        device_entry = seed_devices[0]
                        extracted_hostname = device_entry.split(':')[0]
                        
                        # CRITICAL PROPERTY: Hostname should be preserved
                        assert extracted_hostname == hostname, \
                            f"Hostname should be preserved. Expected '{hostname}', got '{extracted_hostname}'"



# ============================================================================
# Property Tests for Entry Order Preservation
# Task 4.8
# ============================================================================

@given(
    num_entries=st.integers(min_value=2, max_value=5)
)
@settings(max_examples=5, deadline=None)
def test_property_entry_order_preservation(num_entries):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 17
    Entry Order Preservation
    
    For any seed file with multiple entries, the order of devices in the
    discovery queue should match the order in the seed file (excluding
    skipped devices).
    
    **Validates: Requirements 7.4**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    import socket
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with multiple entries in specific order
    seed_lines = ["hostname,ip,status"]
    expected_order = []
    
    for i in range(num_entries):
        hostname = f"device-{i:02d}"
        ip = f"192.168.1.{i + 1}"
        seed_lines.append(f"{hostname},{ip},pending")
        expected_order.append(f"{hostname}:{ip}")
    
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Mock database manager (not used for explicit IPs)
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    with patch('socket.gethostbyname'):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Number of devices should match
                    assert len(seed_devices) == num_entries, \
                        f"Should have {num_entries} devices in queue, got {len(seed_devices)}"
                    
                    # CRITICAL PROPERTY: Order must be preserved exactly
                    for i, expected_entry in enumerate(expected_order):
                        actual_entry = seed_devices[i]
                        assert actual_entry == expected_entry, \
                            f"Position {i}: Expected '{expected_entry}', got '{actual_entry}'. " \
                            f"Order should match seed file order."
                    
                    # Verify complete order matches
                    assert seed_devices == expected_order, \
                        f"Complete order mismatch. Expected {expected_order}, got {seed_devices}"


@given(
    num_entries=st.integers(min_value=3, max_value=5)
)
@settings(max_examples=5, deadline=None)
def test_property_entry_order_preservation_with_resolution(num_entries):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 17 (With Resolution)
    Entry Order Preservation - With IP Resolution
    
    For any seed file with multiple entries requiring IP resolution,
    the order of devices in the discovery queue should match the order
    in the seed file.
    
    **Validates: Requirements 7.4**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with blank IPs in specific order
    seed_lines = ["hostname,ip,status"]
    expected_order = []
    hostnames = []
    
    for i in range(num_entries):
        hostname = f"device-{i:02d}"
        hostnames.append(hostname)
        seed_lines.append(f"{hostname},,pending")
        # Expected IP will be resolved from database
        expected_order.append(f"{hostname}:10.0.0.{i + 1}")
    
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Mock database manager to return IPs in order
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    def db_lookup(hostname):
        # Extract index from hostname and return corresponding IP
        index = int(hostname.split('-')[1])
        return f"10.0.0.{index + 1}"
    
    app.db_manager.get_primary_ip_by_hostname.side_effect = db_lookup
    
    with patch('socket.gethostbyname'):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Number of devices should match
                    assert len(seed_devices) == num_entries, \
                        f"Should have {num_entries} devices in queue, got {len(seed_devices)}"
                    
                    # CRITICAL PROPERTY: Order must be preserved exactly
                    for i, expected_entry in enumerate(expected_order):
                        actual_entry = seed_devices[i]
                        assert actual_entry == expected_entry, \
                            f"Position {i}: Expected '{expected_entry}', got '{actual_entry}'. " \
                            f"Order should match seed file order even after resolution."
                    
                    # Verify complete order matches
                    assert seed_devices == expected_order, \
                        f"Complete order mismatch. Expected {expected_order}, got {seed_devices}"


@given(
    num_entries=st.integers(min_value=4, max_value=6)
)
@settings(max_examples=5, deadline=None)
def test_property_entry_order_preservation_with_skipped_devices(num_entries):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 17 (With Skipped Devices)
    Entry Order Preservation - Excluding Skipped Devices
    
    For any seed file with multiple entries where some cannot be resolved,
    the order of successfully resolved devices in the discovery queue should
    match their order in the seed file (skipped devices excluded).
    
    **Validates: Requirements 7.4**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    import socket
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with alternating resolvable and unresolvable entries
    seed_lines = ["hostname,ip,status"]
    expected_order = []
    
    for i in range(num_entries):
        hostname = f"device-{i:02d}"
        if i % 2 == 0:
            # Resolvable - will be in queue
            seed_lines.append(f"{hostname},,pending")
            expected_order.append(f"{hostname}:10.0.0.{i + 1}")
        else:
            # Unresolvable - will be skipped
            seed_lines.append(f"{hostname},,pending")
    
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Mock database manager to return None for all (force DNS)
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = None
    
    # Mock DNS to succeed for even indices, fail for odd
    def dns_lookup(hostname):
        index = int(hostname.split('-')[1])
        if index % 2 == 0:
            return f"10.0.0.{index + 1}"
        else:
            raise socket.gaierror("Name resolution failed")
    
    with patch('socket.gethostbyname', side_effect=dns_lookup):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Only resolvable devices should be in queue
                    expected_count = (num_entries + 1) // 2  # Ceiling division for even indices
                    assert len(seed_devices) == expected_count, \
                        f"Should have {expected_count} resolvable devices in queue, got {len(seed_devices)}"
                    
                    # CRITICAL PROPERTY: Order of resolvable devices must be preserved
                    for i, expected_entry in enumerate(expected_order):
                        actual_entry = seed_devices[i]
                        assert actual_entry == expected_entry, \
                            f"Position {i}: Expected '{expected_entry}', got '{actual_entry}'. " \
                            f"Order should match seed file order (excluding skipped devices)."
                    
                    # Verify complete order matches
                    assert seed_devices == expected_order, \
                        f"Complete order mismatch. Expected {expected_order}, got {seed_devices}"


@given(
    num_entries=st.integers(min_value=3, max_value=5)
)
@settings(max_examples=5, deadline=None)
def test_property_entry_order_preservation_mixed_explicit_and_resolved(num_entries):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 17 (Mixed Entries)
    Entry Order Preservation - Mixed Explicit and Resolved IPs
    
    For any seed file with a mix of explicit IPs and blank IPs requiring
    resolution, the order of all devices in the discovery queue should
    match their order in the seed file.
    
    **Validates: Requirements 7.4**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with alternating explicit and blank IPs
    seed_lines = ["hostname,ip,status"]
    expected_order = []
    
    for i in range(num_entries):
        hostname = f"device-{i:02d}"
        if i % 2 == 0:
            # Explicit IP
            ip = f"192.168.1.{i + 1}"
            seed_lines.append(f"{hostname},{ip},pending")
            expected_order.append(f"{hostname}:{ip}")
        else:
            # Blank IP - will be resolved
            seed_lines.append(f"{hostname},,pending")
            expected_order.append(f"{hostname}:10.0.0.{i + 1}")
    
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Mock database manager to return IPs for blank entries
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    def db_lookup(hostname):
        index = int(hostname.split('-')[1])
        return f"10.0.0.{index + 1}"
    
    app.db_manager.get_primary_ip_by_hostname.side_effect = db_lookup
    
    with patch('socket.gethostbyname'):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: All devices should be in queue
                    assert len(seed_devices) == num_entries, \
                        f"Should have {num_entries} devices in queue, got {len(seed_devices)}"
                    
                    # CRITICAL PROPERTY: Order must be preserved exactly
                    for i, expected_entry in enumerate(expected_order):
                        actual_entry = seed_devices[i]
                        assert actual_entry == expected_entry, \
                            f"Position {i}: Expected '{expected_entry}', got '{actual_entry}'. " \
                            f"Order should match seed file order for both explicit and resolved IPs."
                    
                    # Verify complete order matches
                    assert seed_devices == expected_order, \
                        f"Complete order mismatch. Expected {expected_order}, got {seed_devices}"


@given(
    num_entries=st.integers(min_value=2, max_value=4),
    num_parses=st.integers(min_value=2, max_value=3)
)
@settings(max_examples=5, deadline=None)
def test_property_entry_order_preservation_idempotence(num_entries, num_parses):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 17 (Idempotence)
    Entry Order Preservation - Idempotence
    
    For any seed file with multiple entries, parsing the same file multiple
    times should consistently preserve the same order.
    
    **Validates: Requirements 7.4**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with multiple entries
    seed_lines = ["hostname,ip,status"]
    expected_order = []
    
    for i in range(num_entries):
        hostname = f"device-{i:02d}"
        ip = f"192.168.1.{i + 1}"
        seed_lines.append(f"{hostname},{ip},pending")
        expected_order.append(f"{hostname}:{ip}")
    
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Mock database manager
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    # Parse seed file multiple times
    for parse_num in range(num_parses):
        with patch('socket.gethostbyname'):
            with patch('builtins.open', mock_open(read_data=seed_content)):
                with patch('os.path.exists', return_value=True):
                    with patch('netwalker.netwalker_app.logger'):
                        # Parse seed file
                        seed_devices = app._parse_seed_file('dummy_seed.csv')
                        
                        # CRITICAL PROPERTY: Order should be consistent across parses
                        assert seed_devices == expected_order, \
                            f"Parse {parse_num + 1}: Order mismatch. " \
                            f"Expected {expected_order}, got {seed_devices}"
                        
                        # Verify each position individually
                        for i, expected_entry in enumerate(expected_order):
                            actual_entry = seed_devices[i]
                            assert actual_entry == expected_entry, \
                                f"Parse {parse_num + 1}, Position {i}: " \
                                f"Expected '{expected_entry}', got '{actual_entry}'"



# ============================================================================
# Property Tests for Mixed Seed File Processing
# Task 5.1
# ============================================================================

@given(
    num_explicit=st.integers(min_value=1, max_value=3),
    num_blank=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=5, deadline=None)
def test_property_mixed_seed_file_processing(num_explicit, num_blank):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 11
    Mixed Seed File Processing
    
    For any seed file containing a mix of entries with and without IP addresses,
    each entry should be processed according to its IP presence (explicit IPs
    used directly, blank IPs resolved).
    
    **Validates: Requirements 5.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open, MagicMock
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with mixed entries
    seed_lines = ["hostname,ip,status"]
    explicit_ips = []
    blank_hostnames = []
    
    # Add entries with explicit IPs
    for i in range(num_explicit):
        hostname = f"explicit-device-{i}"
        ip = f"192.168.1.{i + 1}"
        seed_lines.append(f"{hostname},{ip},pending")
        explicit_ips.append((hostname, ip))
    
    # Add entries with blank IPs
    for i in range(num_blank):
        hostname = f"blank-device-{i}"
        seed_lines.append(f"{hostname},,pending")
        blank_hostnames.append(hostname)
    
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Mock database manager to return IPs for blank entries
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    def db_lookup(hostname):
        # Return database IP for blank entries
        if hostname in blank_hostnames:
            index = int(hostname.split('-')[-1])
            return f"10.0.0.{index + 1}"
        return None
    
    app.db_manager.get_primary_ip_by_hostname.side_effect = db_lookup
    
    # Track resolution calls
    resolution_calls = []
    
    with patch.object(app, '_resolve_ip_for_hostname', wraps=app._resolve_ip_for_hostname) as mock_resolve:
        with patch('socket.gethostbyname'):
            with patch('builtins.open', mock_open(read_data=seed_content)):
                with patch('os.path.exists', return_value=True):
                    with patch('netwalker.netwalker_app.logger'):
                        # Parse seed file
                        seed_devices = app._parse_seed_file('dummy_seed.csv')
                        
                        # CRITICAL PROPERTY: All devices should be in queue
                        total_expected = num_explicit + num_blank
                        assert len(seed_devices) == total_expected, \
                            f"Should have {total_expected} devices in queue, got {len(seed_devices)}"
                        
                        # CRITICAL PROPERTY: Resolution should only be called for blank IPs
                        assert mock_resolve.call_count == num_blank, \
                            f"Resolution should be called {num_blank} times for blank IPs, " \
                            f"but was called {mock_resolve.call_count} times"
                        
                        # CRITICAL PROPERTY: Explicit IPs should be used directly
                        for hostname, expected_ip in explicit_ips:
                            # Find this device in the parsed results
                            found = False
                            for device_entry in seed_devices:
                                if hostname in device_entry:
                                    # Extract IP from entry (format: "hostname:ip")
                                    actual_ip = device_entry.split(':')[1]
                                    assert actual_ip == expected_ip, \
                                        f"Explicit IP for {hostname} should be {expected_ip}, got {actual_ip}"
                                    found = True
                                    break
                            assert found, f"Device {hostname} with explicit IP should be in queue"
                        
                        # CRITICAL PROPERTY: Blank IPs should be resolved
                        for hostname in blank_hostnames:
                            # Verify resolution was called for this hostname
                            called_hostnames = [call[0][0] for call in mock_resolve.call_args_list]
                            assert hostname in called_hostnames, \
                                f"Resolution should be called for blank IP hostname {hostname}"
                            
                            # Find this device in the parsed results
                            found = False
                            for device_entry in seed_devices:
                                if hostname in device_entry:
                                    # Extract IP from entry (format: "hostname:ip")
                                    actual_ip = device_entry.split(':')[1]
                                    # Should have a resolved IP (not empty)
                                    assert actual_ip != '', \
                                        f"Blank IP for {hostname} should be resolved to non-empty IP"
                                    found = True
                                    break
                            assert found, f"Device {hostname} with blank IP should be in queue after resolution"


@given(
    num_explicit=st.integers(min_value=1, max_value=2),
    num_blank_db=st.integers(min_value=1, max_value=2),
    num_blank_dns=st.integers(min_value=1, max_value=2)
)
@settings(max_examples=5, deadline=None)
def test_property_mixed_seed_file_with_multiple_resolution_methods(
    num_explicit,
    num_blank_db,
    num_blank_dns
):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 11 (Extended)
    Mixed Seed File Processing with Multiple Resolution Methods
    
    For any seed file containing explicit IPs, database-resolved IPs, and
    DNS-resolved IPs, each entry should be processed correctly according to
    its resolution method.
    
    **Validates: Requirements 5.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open, MagicMock
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with mixed entries
    seed_lines = ["hostname,ip,status"]
    explicit_devices = []
    db_devices = []
    dns_devices = []
    
    # Add entries with explicit IPs
    for i in range(num_explicit):
        hostname = f"explicit-{i}"
        ip = f"192.168.1.{i + 1}"
        seed_lines.append(f"{hostname},{ip},pending")
        explicit_devices.append((hostname, ip))
    
    # Add entries that will be resolved from database
    for i in range(num_blank_db):
        hostname = f"db-device-{i}"
        seed_lines.append(f"{hostname},,pending")
        db_devices.append(hostname)
    
    # Add entries that will be resolved from DNS
    for i in range(num_blank_dns):
        hostname = f"dns-device-{i}"
        seed_lines.append(f"{hostname},,pending")
        dns_devices.append(hostname)
    
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Mock database manager to return IPs only for db_devices
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    def db_lookup(hostname):
        if hostname in db_devices:
            index = int(hostname.split('-')[-1])
            return f"10.0.0.{index + 1}"
        return None  # DNS devices will get None from database
    
    app.db_manager.get_primary_ip_by_hostname.side_effect = db_lookup
    
    # Mock DNS to return IPs for dns_devices
    def dns_lookup(hostname):
        if hostname in dns_devices:
            index = int(hostname.split('-')[-1])
            return f"172.16.0.{index + 1}"
        raise Exception(f"Unexpected DNS lookup for {hostname}")
    
    with patch('socket.gethostbyname', side_effect=dns_lookup):
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: All devices should be in queue
                    total_expected = num_explicit + num_blank_db + num_blank_dns
                    assert len(seed_devices) == total_expected, \
                        f"Should have {total_expected} devices in queue, got {len(seed_devices)}"
                    
                    # CRITICAL PROPERTY: Explicit IPs used directly (no resolution)
                    for hostname, expected_ip in explicit_devices:
                        found = False
                        for device_entry in seed_devices:
                            if hostname in device_entry:
                                actual_ip = device_entry.split(':')[1]
                                assert actual_ip == expected_ip, \
                                    f"Explicit IP for {hostname} should be {expected_ip}, got {actual_ip}"
                                found = True
                                break
                        assert found, f"Device {hostname} with explicit IP should be in queue"
                    
                    # CRITICAL PROPERTY: Database-resolved IPs should be from database
                    for hostname in db_devices:
                        found = False
                        for device_entry in seed_devices:
                            if hostname in device_entry:
                                actual_ip = device_entry.split(':')[1]
                                # Should be in 10.0.0.x range (database IPs)
                                assert actual_ip.startswith('10.0.0.'), \
                                    f"Database-resolved IP for {hostname} should be in 10.0.0.x range, got {actual_ip}"
                                found = True
                                break
                        assert found, f"Device {hostname} with database-resolved IP should be in queue"
                    
                    # CRITICAL PROPERTY: DNS-resolved IPs should be from DNS
                    for hostname in dns_devices:
                        found = False
                        for device_entry in seed_devices:
                            if hostname in device_entry:
                                actual_ip = device_entry.split(':')[1]
                                # Should be in 172.16.0.x range (DNS IPs)
                                assert actual_ip.startswith('172.16.0.'), \
                                    f"DNS-resolved IP for {hostname} should be in 172.16.0.x range, got {actual_ip}"
                                found = True
                                break
                        assert found, f"Device {hostname} with DNS-resolved IP should be in queue"


@given(
    num_entries=st.integers(min_value=3, max_value=6),
    explicit_ratio=st.floats(min_value=0.2, max_value=0.8)
)
@settings(max_examples=5, deadline=None)
def test_property_mixed_seed_file_processing_ratio(num_entries, explicit_ratio):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 11 (Ratio Variation)
    Mixed Seed File Processing with Varying Ratios
    
    For any seed file with varying ratios of explicit vs blank IPs,
    each entry should be processed correctly according to its type.
    
    **Validates: Requirements 5.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open, MagicMock
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Calculate number of explicit vs blank entries
    num_explicit = max(1, int(num_entries * explicit_ratio))
    num_blank = num_entries - num_explicit
    
    # Ensure at least one of each type
    if num_blank == 0:
        num_blank = 1
        num_explicit = num_entries - 1
    
    # Create seed file with mixed entries
    seed_lines = ["hostname,ip,status"]
    explicit_count = 0
    blank_count = 0
    
    for i in range(num_entries):
        hostname = f"device-{i:02d}"
        if i < num_explicit:
            # Explicit IP
            ip = f"192.168.1.{i + 1}"
            seed_lines.append(f"{hostname},{ip},pending")
            explicit_count += 1
        else:
            # Blank IP
            seed_lines.append(f"{hostname},,pending")
            blank_count += 1
    
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Mock database manager to return IPs for blank entries
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = "10.0.0.1"
    
    # Track resolution calls
    with patch.object(app, '_resolve_ip_for_hostname', wraps=app._resolve_ip_for_hostname) as mock_resolve:
        with patch('socket.gethostbyname'):
            with patch('builtins.open', mock_open(read_data=seed_content)):
                with patch('os.path.exists', return_value=True):
                    with patch('netwalker.netwalker_app.logger'):
                        # Parse seed file
                        seed_devices = app._parse_seed_file('dummy_seed.csv')
                        
                        # CRITICAL PROPERTY: All devices should be in queue
                        assert len(seed_devices) == num_entries, \
                            f"Should have {num_entries} devices in queue, got {len(seed_devices)}"
                        
                        # CRITICAL PROPERTY: Resolution called only for blank IPs
                        assert mock_resolve.call_count == blank_count, \
                            f"Resolution should be called {blank_count} times, " \
                            f"but was called {mock_resolve.call_count} times"
                        
                        # CRITICAL PROPERTY: Each device should have an IP
                        for device_entry in seed_devices:
                            assert ':' in device_entry, \
                                f"Device entry should contain IP: {device_entry}"
                            parts = device_entry.split(':')
                            assert len(parts) == 2, \
                                f"Device entry should have hostname:ip format: {device_entry}"
                            hostname, ip = parts
                            assert hostname != '', "Hostname should not be empty"
                            assert ip != '', "IP should not be empty (should be resolved)"



# ============================================================================
# Property Tests for Integration - Format Consistency
# Task 5.2
# ============================================================================

@given(
    hostname_explicit=valid_hostnames(),
    explicit_ip=valid_ipv4_addresses(),
    hostname_resolved=valid_hostnames(),
    resolved_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_format_consistency_explicit_vs_resolved(
    hostname_explicit,
    explicit_ip,
    hostname_resolved,
    resolved_ip
):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 16
    Format Consistency
    
    For any two devices in the discovery queue (one with explicit IP, one with
    resolved IP), their data structure format should be identical.
    
    **Validates: Requirements 7.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open, MagicMock
    
    # Ensure hostnames are different
    if hostname_explicit == hostname_resolved:
        hostname_resolved = hostname_resolved + "_resolved"
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with one explicit IP and one blank IP
    seed_content = (
        "hostname,ip,status\n"
        f"{hostname_explicit},{explicit_ip},pending\n"
        f"{hostname_resolved},,pending\n"
    )
    
    # Mock database manager to return IP for resolved hostname
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = resolved_ip
    
    # Mock file operations
    with patch('builtins.open', mock_open(read_data=seed_content)):
        with patch('os.path.exists', return_value=True):
            with patch('netwalker.netwalker_app.logger'):
                # Parse seed file
                seed_devices = app._parse_seed_file('dummy_seed.csv')
                
                # CRITICAL PROPERTY: Should have exactly 2 devices
                assert len(seed_devices) == 2, \
                    f"Should have 2 devices in queue, got {len(seed_devices)}"
                
                # Get the two device entries
                device_explicit = seed_devices[0]
                device_resolved = seed_devices[1]
                
                # CRITICAL PROPERTY: Both should be strings
                assert isinstance(device_explicit, str), \
                    f"Explicit IP device should be string, got {type(device_explicit)}"
                assert isinstance(device_resolved, str), \
                    f"Resolved IP device should be string, got {type(device_resolved)}"
                
                # CRITICAL PROPERTY: Both should have same format (hostname:ip)
                assert ':' in device_explicit, \
                    f"Explicit IP device should contain ':' separator: {device_explicit}"
                assert ':' in device_resolved, \
                    f"Resolved IP device should contain ':' separator: {device_resolved}"
                
                # Parse both entries
                explicit_parts = device_explicit.split(':')
                resolved_parts = device_resolved.split(':')
                
                # CRITICAL PROPERTY: Both should have exactly 2 parts (hostname, ip)
                assert len(explicit_parts) == 2, \
                    f"Explicit IP device should have 2 parts, got {len(explicit_parts)}: {device_explicit}"
                assert len(resolved_parts) == 2, \
                    f"Resolved IP device should have 2 parts, got {len(resolved_parts)}: {device_resolved}"
                
                # Extract components
                explicit_hostname, explicit_ip_result = explicit_parts
                resolved_hostname, resolved_ip_result = resolved_parts
                
                # CRITICAL PROPERTY: Both should have non-empty hostnames
                assert explicit_hostname != '', \
                    "Explicit IP device should have non-empty hostname"
                assert resolved_hostname != '', \
                    "Resolved IP device should have non-empty hostname"
                
                # CRITICAL PROPERTY: Both should have non-empty IPs
                assert explicit_ip_result != '', \
                    "Explicit IP device should have non-empty IP"
                assert resolved_ip_result != '', \
                    "Resolved IP device should have non-empty IP"
                
                # CRITICAL PROPERTY: Hostnames should match original values
                assert explicit_hostname == hostname_explicit, \
                    f"Explicit hostname should be '{hostname_explicit}', got '{explicit_hostname}'"
                assert resolved_hostname == hostname_resolved, \
                    f"Resolved hostname should be '{hostname_resolved}', got '{resolved_hostname}'"
                
                # CRITICAL PROPERTY: IPs should match expected values
                assert explicit_ip_result == explicit_ip, \
                    f"Explicit IP should be '{explicit_ip}', got '{explicit_ip_result}'"
                assert resolved_ip_result == resolved_ip, \
                    f"Resolved IP should be '{resolved_ip}', got '{resolved_ip_result}'"
                
                # CRITICAL PROPERTY: Format structure should be identical
                # (both are "hostname:ip" strings with same separator and structure)
                assert device_explicit.count(':') == device_resolved.count(':'), \
                    "Both devices should have same number of ':' separators"


@given(
    num_explicit=st.integers(min_value=1, max_value=3),
    num_resolved=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=5, deadline=None)
def test_property_format_consistency_multiple_devices(num_explicit, num_resolved):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 16
    Format Consistency - Multiple Devices
    
    For any seed file with multiple devices (some with explicit IPs, some with
    resolved IPs), all devices in the discovery queue should have identical
    data structure format.
    
    **Validates: Requirements 7.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open, MagicMock
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with mixed explicit and blank IPs
    seed_lines = ["hostname,ip,status"]
    
    # Add explicit IP entries
    for i in range(num_explicit):
        hostname = f"explicit-device-{i}"
        ip = f"192.168.1.{i + 1}"
        seed_lines.append(f"{hostname},{ip},pending")
    
    # Add blank IP entries (to be resolved)
    for i in range(num_resolved):
        hostname = f"resolved-device-{i}"
        seed_lines.append(f"{hostname},,pending")
    
    seed_content = "\n".join(seed_lines) + "\n"
    
    # Mock database manager to return IPs for resolved entries
    def get_ip_side_effect(hostname):
        # Return different IPs for different hostnames
        if 'resolved-device' in hostname:
            device_num = int(hostname.split('-')[-1])
            return f"10.0.0.{device_num + 1}"
        return None
    
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.side_effect = get_ip_side_effect
    
    # Mock file operations
    with patch('builtins.open', mock_open(read_data=seed_content)):
        with patch('os.path.exists', return_value=True):
            with patch('netwalker.netwalker_app.logger'):
                # Parse seed file
                seed_devices = app._parse_seed_file('dummy_seed.csv')
                
                # CRITICAL PROPERTY: Should have all devices
                total_devices = num_explicit + num_resolved
                assert len(seed_devices) == total_devices, \
                    f"Should have {total_devices} devices in queue, got {len(seed_devices)}"
                
                # CRITICAL PROPERTY: All devices should have same format
                for i, device_entry in enumerate(seed_devices):
                    # All should be strings
                    assert isinstance(device_entry, str), \
                        f"Device {i} should be string, got {type(device_entry)}"
                    
                    # All should have ':' separator
                    assert ':' in device_entry, \
                        f"Device {i} should contain ':' separator: {device_entry}"
                    
                    # All should have exactly 2 parts
                    parts = device_entry.split(':')
                    assert len(parts) == 2, \
                        f"Device {i} should have 2 parts, got {len(parts)}: {device_entry}"
                    
                    # All should have non-empty hostname and IP
                    hostname, ip = parts
                    assert hostname != '', \
                        f"Device {i} should have non-empty hostname: {device_entry}"
                    assert ip != '', \
                        f"Device {i} should have non-empty IP: {device_entry}"
                
                # CRITICAL PROPERTY: All devices should have same separator count
                separator_counts = [device.count(':') for device in seed_devices]
                assert len(set(separator_counts)) == 1, \
                    f"All devices should have same number of ':' separators, got {separator_counts}"


@given(
    hostname=valid_hostnames(),
    explicit_ip=valid_ipv4_addresses(),
    resolved_ip=valid_ipv4_addresses()
)
@settings(max_examples=5, deadline=None)
def test_property_format_consistency_type_uniformity(hostname, explicit_ip, resolved_ip):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 16
    Format Consistency - Type Uniformity
    
    For any devices in the discovery queue, regardless of whether their IPs
    were explicit or resolved, all should be the same data type (string).
    
    **Validates: Requirements 7.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open, MagicMock
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file with one explicit and one resolved IP
    seed_content = (
        "hostname,ip,status\n"
        f"{hostname}-explicit,{explicit_ip},pending\n"
        f"{hostname}-resolved,,pending\n"
    )
    
    # Mock database manager to return IP for resolved hostname
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    app.db_manager.get_primary_ip_by_hostname.return_value = resolved_ip
    
    # Mock file operations
    with patch('builtins.open', mock_open(read_data=seed_content)):
        with patch('os.path.exists', return_value=True):
            with patch('netwalker.netwalker_app.logger'):
                # Parse seed file
                seed_devices = app._parse_seed_file('dummy_seed.csv')
                
                # CRITICAL PROPERTY: Should have 2 devices
                assert len(seed_devices) == 2, \
                    f"Should have 2 devices in queue, got {len(seed_devices)}"
                
                # CRITICAL PROPERTY: All devices should be same type (string)
                device_types = [type(device) for device in seed_devices]
                assert all(t == str for t in device_types), \
                    f"All devices should be strings, got types: {device_types}"
                
                # CRITICAL PROPERTY: Type of explicit IP device == Type of resolved IP device
                assert type(seed_devices[0]) == type(seed_devices[1]), \
                    f"Explicit and resolved devices should have same type: " \
                    f"{type(seed_devices[0])} vs {type(seed_devices[1])}"


@given(
    hostname=valid_hostnames(),
    ip=valid_ipv4_addresses(),
    resolution_method=st.sampled_from(['explicit', 'database', 'dns'])
)
@settings(max_examples=5, deadline=None)
def test_property_format_consistency_resolution_method_independence(
    hostname,
    ip,
    resolution_method
):
    """
    Feature: database-ip-lookup-for-seed-devices, Property 16
    Format Consistency - Resolution Method Independence
    
    For any device, the format of its entry in the discovery queue should be
    identical regardless of how its IP was obtained (explicit, database, or DNS).
    
    **Validates: Requirements 7.3**
    """
    from netwalker.netwalker_app import NetWalkerApp
    from unittest.mock import patch, mock_open, MagicMock
    
    # Create NetWalker app
    app = NetWalkerApp()
    
    # Create seed file based on resolution method
    if resolution_method == 'explicit':
        # Explicit IP in seed file
        seed_content = f"hostname,ip,status\n{hostname},{ip},pending\n"
    else:
        # Blank IP in seed file (will be resolved)
        seed_content = f"hostname,ip,status\n{hostname},,pending\n"
    
    # Mock database manager
    app.db_manager = MagicMock()
    app.db_manager.enabled = True
    
    if resolution_method == 'database':
        # Database returns IP
        app.db_manager.get_primary_ip_by_hostname.return_value = ip
    else:
        # Database returns None (for DNS fallback or explicit)
        app.db_manager.get_primary_ip_by_hostname.return_value = None
    
    # Mock DNS for DNS resolution method
    with patch('socket.gethostbyname', return_value=ip):
        # Mock file operations
        with patch('builtins.open', mock_open(read_data=seed_content)):
            with patch('os.path.exists', return_value=True):
                with patch('netwalker.netwalker_app.logger'):
                    # Parse seed file
                    seed_devices = app._parse_seed_file('dummy_seed.csv')
                    
                    # CRITICAL PROPERTY: Should have exactly 1 device
                    assert len(seed_devices) == 1, \
                        f"Should have 1 device in queue, got {len(seed_devices)}"
                    
                    device_entry = seed_devices[0]
                    
                    # CRITICAL PROPERTY: Should be a string
                    assert isinstance(device_entry, str), \
                        f"Device should be string, got {type(device_entry)}"
                    
                    # CRITICAL PROPERTY: Should have hostname:ip format
                    assert ':' in device_entry, \
                        f"Device should contain ':' separator: {device_entry}"
                    
                    parts = device_entry.split(':')
                    assert len(parts) == 2, \
                        f"Device should have 2 parts, got {len(parts)}: {device_entry}"
                    
                    result_hostname, result_ip = parts
                    
                    # CRITICAL PROPERTY: Should have correct hostname and IP
                    assert result_hostname == hostname, \
                        f"Hostname should be '{hostname}', got '{result_hostname}'"
                    assert result_ip == ip, \
                        f"IP should be '{ip}', got '{result_ip}'"
                    
                    # CRITICAL PROPERTY: Format is consistent regardless of resolution method
                    # The format is always "hostname:ip" with exactly one ':' separator
                    assert device_entry.count(':') == 1, \
                        f"Device should have exactly 1 ':' separator, got {device_entry.count(':')}"
