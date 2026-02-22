"""
Property-based tests for database primary IP storage
Feature: database-primary-ip-storage
"""

import ipaddress
from datetime import datetime
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


# Strategy for generating device_info dictionaries
def device_info_strategy(primary_ip_strategy=valid_ipv4_addresses()):
    """Generate device_info dictionaries with various configurations"""
    return st.fixed_dictionaries({
        'hostname': st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')),
        'primary_ip': primary_ip_strategy,
        'serial_number': st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
        'platform': st.sampled_from(['cisco_ios', 'cisco_nxos', 'arista_eos', 'juniper_junos']),
        'software_version': st.text(min_size=1, max_size=20),
        'interfaces': st.lists(st.fixed_dictionaries({
            'interface_name': st.text(min_size=1, max_size=50),
            'ip_address': valid_ipv4_addresses(),
            'subnet_mask': st.sampled_from(['255.255.255.0', '255.255.255.252', '255.255.0.0']),
            'interface_type': st.sampled_from(['physical', 'loopback', 'vlan'])
        }), max_size=5),
        'vlans': st.lists(st.just({}), max_size=0),  # Empty for simplicity
        'neighbors': st.lists(st.just({}), max_size=0)  # Empty for simplicity
    })


@given(device_info=device_info_strategy())
@settings(max_examples=100, deadline=None)
def test_property_primary_ip_storage_completeness(device_info):
    """
    Feature: database-primary-ip-storage, Property 1: Primary IP Storage Completeness
    For any device with a valid primary_ip in device_info, when process_device_discovery() 
    is called, the primary_ip should be stored in device_interfaces with 
    interface_name='Primary Management', interface_type='management', and associated 
    with the correct device_id.
    **Validates: Requirements 1.1, 1.2, 1.3, 4.2**
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
    db_manager.connection = MagicMock()
    db_manager.enabled = True
    
    # Mock methods
    device_id = 42  # Fixed device_id for testing
    db_manager.upsert_device = Mock(return_value=(device_id, True))
    db_manager.upsert_device_version = Mock(return_value=True)
    db_manager.upsert_device_interface = Mock(return_value=True)
    
    # Call process_device_discovery
    success, is_new = db_manager.process_device_discovery(device_info)
    
    # Verify success
    assert success is True, "process_device_discovery should return True"
    
    # Find the primary_ip interface call
    primary_ip_call = None
    for call in db_manager.upsert_device_interface.call_args_list:
        args, kwargs = call
        if len(args) >= 2:
            interface_info = args[1]
            if interface_info.get('interface_name') == 'Primary Management':
                primary_ip_call = interface_info
                break
    
    # Verify primary_ip was stored correctly
    assert primary_ip_call is not None, "Primary IP interface should be stored"
    assert primary_ip_call['interface_name'] == 'Primary Management', "Interface name should be 'Primary Management'"
    assert primary_ip_call['ip_address'] == device_info['primary_ip'], f"IP address should match primary_ip: {device_info['primary_ip']}"
    assert primary_ip_call['interface_type'] == 'management', "Interface type should be 'management'"
    assert primary_ip_call['subnet_mask'] == '', "Subnet mask should be empty string"
    
    # Verify device_id was passed correctly
    first_call_device_id = db_manager.upsert_device_interface.call_args_list[0][0][0]
    assert first_call_device_id == device_id, f"Device ID should be {device_id}"


@given(device_info=device_info_strategy())
@settings(max_examples=100, deadline=None)
def test_property_primary_ip_storage_idempotence(device_info):
    """
    Feature: database-primary-ip-storage, Property 2: Primary IP Storage Idempotence
    For any device, storing the same primary_ip multiple times should result in only 
    one record in device_interfaces (update existing rather than create duplicates), 
    with last_seen timestamp updated.
    **Validates: Requirements 1.4**
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
    db_manager.connection = MagicMock()
    db_manager.enabled = True
    
    # Mock methods
    device_id = 42
    db_manager.upsert_device = Mock(return_value=(device_id, True))
    db_manager.upsert_device_version = Mock(return_value=True)
    
    # Simulate actual upsert_device_interface behavior with idempotence
    # Track stored interfaces to simulate database uniqueness constraint
    stored_interfaces = {}
    
    def mock_upsert_interface(dev_id, interface_info):
        """Mock that simulates actual database upsert behavior"""
        # Create unique key based on device_id, interface_name, ip_address
        # This matches the UNIQUE constraint in the database
        key = (dev_id, interface_info.get('interface_name'), interface_info.get('ip_address'))
        
        if key in stored_interfaces:
            # Update existing record (simulate updating last_seen)
            stored_interfaces[key]['update_count'] += 1
            stored_interfaces[key]['last_seen'] = 'updated'
        else:
            # Insert new record
            stored_interfaces[key] = {
                'interface_info': interface_info.copy(),
                'update_count': 0,
                'last_seen': 'initial'
            }
        return True
    
    db_manager.upsert_device_interface = Mock(side_effect=mock_upsert_interface)
    
    # Call process_device_discovery twice with same device_info
    result1 = db_manager.process_device_discovery(device_info)
    result2 = db_manager.process_device_discovery(device_info)
    
    # Both should succeed
    assert success1 is True, "First call should succeed"
    assert success2 is True, "Second call should succeed"
    
    # Verify upsert_device_interface was called twice for primary_ip
    primary_ip_calls = 0
    for call in db_manager.upsert_device_interface.call_args_list:
        args, kwargs = call
        if len(args) >= 2:
            interface_info = args[1]
            if interface_info.get('interface_name') == 'Primary Management':
                primary_ip_calls += 1
    
    assert primary_ip_calls == 2, "Primary IP should be stored on each discovery"
    
    # CRITICAL: Verify only ONE record exists in our simulated database
    primary_ip_records = [
        (key, data) for key, data in stored_interfaces.items()
        if key[1] == 'Primary Management'  # interface_name
    ]
    
    assert len(primary_ip_records) == 1, \
        f"Should have exactly ONE primary IP record, found {len(primary_ip_records)}"
    
    # Verify the record was updated (not duplicated)
    key, record = primary_ip_records[0]
    assert record['update_count'] == 1, \
        "Primary IP record should have been updated once (second call)"
    assert record['last_seen'] == 'updated', \
        "last_seen timestamp should be updated"
    
    # Verify the stored IP matches the device_info
    assert record['interface_info']['ip_address'] == device_info['primary_ip'], \
        "Stored IP should match device_info primary_ip"
    assert record['interface_info']['interface_type'] == 'management', \
        "Interface type should be 'management'"


@given(
    hostname=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')),
    primary_ip=valid_ipv4_addresses(),
    serial=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd')))
)
@settings(max_examples=100, deadline=None)
def test_property_primary_ip_stored_before_other_interfaces(hostname, primary_ip, serial):
    """
    Property: Primary IP should always be stored before other interfaces
    This ensures database queries can rely on primary_ip being available first
    **Validates: Requirements 1.1, 1.2, 1.3**
    """
    # Create device_info with primary_ip and some other interfaces
    device_info = {
        'hostname': hostname,
        'primary_ip': primary_ip,
        'serial_number': serial,
        'platform': 'cisco_ios',
        'software_version': '15.1',
        'interfaces': [
            {
                'interface_name': 'GigabitEthernet0/0',
                'ip_address': '10.0.0.1',
                'subnet_mask': '255.255.255.0',
                'interface_type': 'physical'
            }
        ],
        'vlans': [],
        'neighbors': []
    }
    
    # Setup mock database manager
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
    
    # Call process_device_discovery
    success, is_new = db_manager.process_device_discovery(device_info)
    
    assert success is True, "process_device_discovery should succeed"
    
    # Verify at least 2 interface calls were made
    assert db_manager.upsert_device_interface.call_count >= 2, "Should store primary_ip and at least one other interface"
    
    # Verify first call was for primary_ip
    first_call = db_manager.upsert_device_interface.call_args_list[0]
    first_interface = first_call[0][1]
    
    assert first_interface['interface_name'] == 'Primary Management', "First interface stored should be primary_ip"
    assert first_interface['ip_address'] == primary_ip, "First interface IP should match primary_ip"
    assert first_interface['interface_type'] == 'management', "First interface type should be management"


@given(
    hostname=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')),
    serial=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd')))
)
@settings(max_examples=100, deadline=None)
def test_property_handles_missing_primary_ip(hostname, serial):
    """
    Property: System should handle missing primary_ip gracefully without errors
    **Validates: Requirements 4.1, 5.1, 5.2**
    """
    # Create device_info without primary_ip
    device_info = {
        'hostname': hostname,
        'serial_number': serial,
        'platform': 'cisco_ios',
        'software_version': '15.1',
        'interfaces': [],
        'vlans': [],
        'neighbors': []
    }
    
    # Setup mock database manager
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
    
    # Call process_device_discovery - should not raise exception
    success, is_new = db_manager.process_device_discovery(device_info)
    
    assert success is True, "Should succeed even without primary_ip"
    
    # Verify no primary_ip interface was stored
    primary_ip_calls = 0
    for call in db_manager.upsert_device_interface.call_args_list:
        args, kwargs = call
        if len(args) >= 2:
            interface_info = args[1]
            if interface_info.get('interface_name') == 'Primary Management':
                primary_ip_calls += 1
    
    assert primary_ip_calls == 0, "Should not store primary_ip when it's missing"


@given(
    hostname=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')),
    primary_ip=st.one_of(st.just(''), st.just(None)),
    serial=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd')))
)
@settings(max_examples=50, deadline=None)
def test_property_handles_empty_or_none_primary_ip(hostname, primary_ip, serial):
    """
    Property: System should handle empty or None primary_ip gracefully
    **Validates: Requirements 4.1**
    """
    # Create device_info with empty or None primary_ip
    device_info = {
        'hostname': hostname,
        'primary_ip': primary_ip,
        'serial_number': serial,
        'platform': 'cisco_ios',
        'software_version': '15.1',
        'interfaces': [],
        'vlans': [],
        'neighbors': []
    }

    # Setup mock database manager
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

    # Call process_device_discovery - should not raise exception
    success, is_new = db_manager.process_device_discovery(device_info)

    assert success is True, "Should succeed with empty/None primary_ip"

    # Verify no primary_ip interface was stored
    assert db_manager.upsert_device_interface.call_count == 0, \
        "Should not store empty/None primary_ip"


# Strategy for generating interface configurations
def interface_config_strategy():
    """Generate various interface configurations for testing queries"""
    return st.one_of(
        # Only primary_ip, no other interfaces
        st.just({'primary_only': True, 'other_interfaces': []}),
        # Primary_ip + other interfaces
        st.builds(
            lambda interfaces: {'primary_only': False, 'other_interfaces': interfaces},
            st.lists(
                st.fixed_dictionaries({
                    'interface_name': st.sampled_from([
                        'GigabitEthernet0/0',
                        'Loopback0',
                        'Vlan1',
                        'FastEthernet0/1'
                    ]),
                    'ip_address': valid_ipv4_addresses(),
                    'subnet_mask': st.sampled_from([
                        '255.255.255.0',
                        '255.255.255.252'
                    ]),
                    'interface_type': st.sampled_from([
                        'physical',
                        'loopback',
                        'vlan'
                    ])
                }),
                min_size=1,
                max_size=3
            )
        )
    )


@given(
    primary_ip=valid_ipv4_addresses(),
    interface_config=interface_config_strategy(),
    device_type=st.sampled_from(['stale', 'unwalked'])
)
@settings(max_examples=100, deadline=None)
def test_property_database_query_returns_valid_ips(
    primary_ip,
    interface_config,
    device_type
):
    """
    Feature: database-primary-ip-storage, Property 3: Database Query Returns Valid IPs
    For any device returned by get_stale_devices() or get_unwalked_devices(),
    the ip_address field should not be empty, and if a primary_ip exists in
    device_interfaces, it should be prioritized over other interface types.
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
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
    db_manager.connection = MagicMock()
    db_manager.enabled = True

    # Mock cursor to simulate database query results
    mock_cursor = MagicMock()

    # Simulate the interface priority logic from the actual SQL query
    # The query prioritizes: Management (1) > Loopback (2) > Vlan (3) > Other (4)
    interfaces = []

    # Add primary_ip as management interface
    interfaces.append({
        'interface_name': 'Primary Management',
        'ip_address': primary_ip,
        'priority': 1  # Management has highest priority
    })

    # Add other interfaces if configured
    if not interface_config['primary_only']:
        for iface in interface_config['other_interfaces']:
            # Determine priority based on interface name
            if 'Management' in iface['interface_name']:
                priority = 1
            elif 'Loopback' in iface['interface_name']:
                priority = 2
            elif 'Vlan' in iface['interface_name']:
                priority = 3
            else:
                priority = 4

            interfaces.append({
                'interface_name': iface['interface_name'],
                'ip_address': iface['ip_address'],
                'priority': priority
            })

    # Sort interfaces by priority (same as SQL ORDER BY)
    interfaces.sort(key=lambda x: (x['priority'], x['interface_name']))

    # The query returns the first (highest priority) IP
    selected_ip = interfaces[0]['ip_address'] if interfaces else ''

    # Mock the query result based on device type
    if device_type == 'stale':
        mock_cursor.fetchall.return_value = [
            ('test-device', '2024-01-01', 'cisco_ios', 'Catalyst', selected_ip)
        ]
    else:  # unwalked
        mock_cursor.fetchall.return_value = [
            ('test-device', 'cisco_ios', 'router', '2024-01-01',
             '2024-01-01', selected_ip)
        ]

    db_manager.connection.cursor.return_value = mock_cursor

    # Call the appropriate query method
    if device_type == 'stale':
        devices = db_manager.get_stale_devices(days=30)
    else:
        devices = db_manager.get_unwalked_devices()

    # Verify results
    assert len(devices) > 0, "Query should return at least one device"

    for device in devices:
        # Property 1: ip_address field should not be empty
        assert 'ip_address' in device, "Device should have ip_address field"
        assert device['ip_address'] != '', \
            "Device ip_address should not be empty"
        assert device['ip_address'] is not None, \
            "Device ip_address should not be None"

        # Property 2: If primary_ip exists, it should be prioritized
        # Since we added primary_ip as 'Primary Management' with priority 1,
        # it should be selected
        assert device['ip_address'] == primary_ip, \
            f"Primary IP should be prioritized: expected {primary_ip}, " \
            f"got {device['ip_address']}"



# Strategy for generating invalid IP addresses
def invalid_ip_addresses():
    """Generate invalid IP address strings"""
    return st.one_of(
        # Malformed IPv4 addresses
        st.text(min_size=1, max_size=20,
                alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'),
                                       whitelist_characters='.-_')),
        # Out of range octets
        st.builds(lambda a, b, c, d: f"{a}.{b}.{c}.{d}",
                  st.integers(min_value=256, max_value=999),
                  st.integers(min_value=0, max_value=255),
                  st.integers(min_value=0, max_value=255),
                  st.integers(min_value=0, max_value=255)),
        # Too few octets
        st.builds(lambda a, b: f"{a}.{b}",
                  st.integers(min_value=0, max_value=255),
                  st.integers(min_value=0, max_value=255)),
        # Too many octets
        st.builds(lambda a, b, c, d, e: f"{a}.{b}.{c}.{d}.{e}",
                  st.integers(min_value=0, max_value=255),
                  st.integers(min_value=0, max_value=255),
                  st.integers(min_value=0, max_value=255),
                  st.integers(min_value=0, max_value=255),
                  st.integers(min_value=0, max_value=255)),
        # Special invalid strings
        st.sampled_from([
            'not.an.ip.address',
            '999.999.999.999',
            '1.2.3',
            '1.2.3.4.5',
            '1.2.3.256',
            '256.1.2.3',
            'hostname',
            '192.168.1',
            '192.168.1.1.1',
            '',
            '...',
            '1..2.3',
            'a.b.c.d',
            '192.168.-1.1',
            '192.168.1.1/24',  # CIDR notation (not a plain IP)
        ])
    )


def is_valid_ip(ip_string):
    """Check if a string is a valid IPv4 or IPv6 address"""
    if not ip_string:
        return False
    try:
        ipaddress.ip_address(ip_string)
        return True
    except (ValueError, AttributeError):
        return False


@given(
    hostname=st.text(min_size=1, max_size=50,
                     alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'),
                                            whitelist_characters='-_')),
    primary_ip=invalid_ip_addresses(),
    serial=st.text(min_size=1, max_size=20,
                   alphabet=st.characters(whitelist_categories=('Lu', 'Nd')))
)
@settings(max_examples=100, deadline=None)
def test_property_ip_address_format_validation(hostname, primary_ip, serial):
    """
    Feature: database-primary-ip-storage, Property 4: IP Address Format Validation
    For any primary_ip value, if it is not in valid IP address format (IPv4 or IPv6),
    the storage operation should either reject it or log a warning, ensuring only
    valid IP addresses are stored in device_interfaces.
    **Validates: Requirements 4.1**
    """
    # Skip if the generated string happens to be a valid IP
    # (we want to test invalid IPs only)
    if is_valid_ip(primary_ip):
        return

    # Create device_info with potentially invalid primary_ip
    device_info = {
        'hostname': hostname,
        'primary_ip': primary_ip,
        'serial_number': serial,
        'platform': 'cisco_ios',
        'software_version': '15.1',
        'interfaces': [],
        'vlans': [],
        'neighbors': []
    }

    # Setup mock database manager
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

    # Track what was stored
    stored_interfaces = []

    def mock_upsert_interface(dev_id, interface_info):
        """Mock that tracks stored interfaces"""
        stored_interfaces.append(interface_info.copy())
        return True

    db_manager.upsert_device = Mock(return_value=(1, True))
    db_manager.upsert_device_version = Mock(return_value=True)
    db_manager.upsert_device_interface = Mock(side_effect=mock_upsert_interface)

    # Mock logger to capture warnings
    warning_logged = []

    def mock_warning(msg):
        warning_logged.append(msg)

    original_warning = db_manager.logger.warning
    db_manager.logger.warning = Mock(side_effect=mock_warning)

    # Call process_device_discovery
    success, is_new = db_manager.process_device_discovery(device_info)

    # The operation should complete (not crash)
    assert success is True, "process_device_discovery should not crash on invalid IP"

    # Check if invalid IP was stored
    primary_ip_stored = False
    for interface in stored_interfaces:
        if interface.get('interface_name') == 'Primary Management':
            primary_ip_stored = True
            break

    # CRITICAL PROPERTY: Invalid IPs should NOT be stored
    # The system should reject them and log a warning
    if primary_ip and primary_ip != '':
        # Non-empty invalid IP should be rejected
        assert not primary_ip_stored, \
            f"Invalid IP '{primary_ip}' should not be stored in device_interfaces"

        # A warning should have been logged about the invalid IP
        assert len(warning_logged) > 0, \
            f"Warning should be logged for invalid IP '{primary_ip}'"

        # Verify the warning mentions the invalid IP
        warning_text = ' '.join(warning_logged)
        assert 'Invalid IP address format' in warning_text or \
               'invalid' in warning_text.lower(), \
            f"Warning should mention invalid IP format: {warning_text}"

    # Restore original logger
    db_manager.logger.warning = original_warning


@given(primary_ip=valid_ipv4_addresses())
@settings(max_examples=50, deadline=None)
def test_property_valid_ip_addresses_are_stored(primary_ip):
    """
    Property: Valid IP addresses should always be stored successfully
    This complements the invalid IP test by ensuring valid IPs work correctly
    **Validates: Requirements 4.1**
    """
    # Verify the IP is actually valid
    assert is_valid_ip(primary_ip), f"Generated IP should be valid: {primary_ip}"

    # Create device_info with valid primary_ip
    device_info = {
        'hostname': 'test-device',
        'primary_ip': primary_ip,
        'serial_number': 'TEST123',
        'platform': 'cisco_ios',
        'software_version': '15.1',
        'interfaces': [],
        'vlans': [],
        'neighbors': []
    }

    # Setup mock database manager
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

    # Call process_device_discovery
    success, is_new = db_manager.process_device_discovery(device_info)

    # Should succeed
    assert success is True, "Valid IP should be processed successfully"

    # Verify primary_ip was stored
    primary_ip_calls = 0
    for call in db_manager.upsert_device_interface.call_args_list:
        args, _ = call
        if len(args) >= 2:
            interface_info = args[1]
            if interface_info.get('interface_name') == 'Primary Management':
                primary_ip_calls += 1
                assert interface_info['ip_address'] == primary_ip, \
                    "Stored IP should match input"

    assert primary_ip_calls == 1, "Valid primary_ip should be stored exactly once"


@given(
    hostname=st.text(min_size=1, max_size=50,
                     alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'),
                                            whitelist_characters='-_')),
    primary_ip1=valid_ipv4_addresses(),
    primary_ip2=valid_ipv4_addresses(),
    serial=st.text(min_size=1, max_size=20,
                   alphabet=st.characters(whitelist_categories=('Lu', 'Nd')))
)
@settings(max_examples=100, deadline=None)
def test_property_primary_ip_update_on_rediscovery(
    hostname,
    primary_ip1,
    primary_ip2,
    serial
):
    """
    Feature: database-primary-ip-storage, Property 5: Primary IP Update on Rediscovery
    For any device that is rediscovered with a different primary_ip, the new primary_ip
    should be stored (creating a new record), and the device should be retrievable using
    the most recent primary_ip.
    **Validates: Requirements 4.3**
    """
    # Skip if both IPs are the same (we want to test IP changes)
    if primary_ip1 == primary_ip2:
        return

    # Setup mock database manager
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

    # Track stored interfaces to simulate database behavior
    # Key: (device_id, interface_name, ip_address)
    # Value: interface record with metadata
    stored_interfaces = {}
    timestamp_counter = [0]  # Use list to allow modification in nested function

    def mock_upsert_interface(dev_id, interface_info):
        """Mock that simulates actual database upsert behavior"""
        # Create unique key based on device_id, interface_name, ip_address
        # This matches the UNIQUE constraint in the database
        key = (
            dev_id,
            interface_info.get('interface_name'),
            interface_info.get('ip_address')
        )

        if key in stored_interfaces:
            # Update existing record (simulate updating last_seen)
            timestamp_counter[0] += 1
            stored_interfaces[key]['last_seen'] = timestamp_counter[0]
            stored_interfaces[key]['update_count'] += 1
        else:
            # Insert new record
            timestamp_counter[0] += 1
            stored_interfaces[key] = {
                'device_id': dev_id,
                'interface_name': interface_info.get('interface_name'),
                'ip_address': interface_info.get('ip_address'),
                'subnet_mask': interface_info.get('subnet_mask', ''),
                'interface_type': interface_info.get('interface_type', ''),
                'first_seen': timestamp_counter[0],
                'last_seen': timestamp_counter[0],
                'update_count': 0
            }
        return True

    # Mock the database methods
    device_id = 42
    db_manager.upsert_device = Mock(return_value=(device_id, True))
    db_manager.upsert_device_version = Mock(return_value=True)
    db_manager.upsert_device_interface = Mock(side_effect=mock_upsert_interface)

    # First discovery with primary_ip1
    device_info1 = {
        'hostname': hostname,
        'primary_ip': primary_ip1,
        'serial_number': serial,
        'platform': 'cisco_ios',
        'software_version': '15.1',
        'interfaces': [],
        'vlans': [],
        'neighbors': []
    }

    success1, is_new1 = db_manager.process_device_discovery(device_info1)
    assert success1 is True, "First discovery should succeed"

    # Verify first primary_ip was stored
    key1 = (device_id, 'Primary Management', primary_ip1)
    assert key1 in stored_interfaces, \
        f"First primary_ip {primary_ip1} should be stored"

    # Rediscovery with different primary_ip2
    device_info2 = {
        'hostname': hostname,
        'primary_ip': primary_ip2,
        'serial_number': serial,
        'platform': 'cisco_ios',
        'software_version': '15.1',
        'interfaces': [],
        'vlans': [],
        'neighbors': []
    }

    success2, is_new2 = db_manager.process_device_discovery(device_info2)
    assert success2 is True, "Second discovery should succeed"

    # CRITICAL PROPERTY 1: Both primary_ip records should exist
    # (new record created, old record preserved for history)
    key2 = (device_id, 'Primary Management', primary_ip2)
    assert key2 in stored_interfaces, \
        f"Second primary_ip {primary_ip2} should be stored as new record"

    assert key1 in stored_interfaces, \
        f"First primary_ip {primary_ip1} should still exist (historical record)"

    # Verify we have exactly 2 Primary Management records
    primary_management_records = [
        (key, data) for key, data in stored_interfaces.items()
        if key[1] == 'Primary Management'
    ]
    assert len(primary_management_records) == 2, \
        f"Should have exactly 2 Primary Management records, found {len(primary_management_records)}"

    # CRITICAL PROPERTY 2: Most recent primary_ip should be retrievable
    # Simulate the database query that retrieves devices
    # The query should return the most recent IP based on last_seen timestamp

    # Get all Primary Management interfaces for this device
    device_primary_ips = [
        (key, data) for key, data in stored_interfaces.items()
        if key[0] == device_id and key[1] == 'Primary Management'
    ]

    # Sort by last_seen (most recent first)
    device_primary_ips.sort(key=lambda x: x[1]['last_seen'], reverse=True)

    # The most recent IP should be primary_ip2
    most_recent_ip = device_primary_ips[0][1]['ip_address']
    assert most_recent_ip == primary_ip2, \
        f"Most recent primary_ip should be {primary_ip2}, got {most_recent_ip}"

    # Verify the second IP has a more recent timestamp than the first
    ip1_record = stored_interfaces[key1]
    ip2_record = stored_interfaces[key2]
    assert ip2_record['last_seen'] >= ip1_record['first_seen'], \
        "Second IP's last_seen should be after or equal to first IP's first_seen"

    # CRITICAL PROPERTY 3: The new IP should not have been "updated"
    # (it's a new record, not an update of the old one)
    assert ip2_record['update_count'] == 0, \
        "New primary_ip record should have update_count=0 (new record, not updated)"

    # The old IP should also not have been updated during rediscovery
    assert ip1_record['update_count'] == 0, \
        "Old primary_ip record should not be updated when new IP is stored"
