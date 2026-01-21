"""
Test script to verify neighbor storage functionality
"""

import sys
from netwalker.config.config_manager import ConfigurationManager
from netwalker.database import DatabaseManager
from netwalker.connection.data_models import NeighborInfo

def main():
    print("=" * 70)
    print("Testing neighbor storage functionality")
    print("=" * 70)
    print()
    
    # Load configuration
    config_manager = ConfigurationManager('netwalker.ini')
    parsed_config = config_manager.load_configuration()
    db_config = parsed_config.get('database', {})
    
    # Initialize database manager
    print("Connecting to database...")
    db_manager = DatabaseManager(db_config)
    
    if not db_manager.connect():
        print("[FAIL] Could not connect to database")
        return 1
    
    print("[OK] Connected to database")
    print()
    
    # Initialize database
    print("Initializing database...")
    if not db_manager.initialize_database():
        print("[FAIL] Failed to initialize database")
        return 1
    
    print("[OK] Database initialized")
    print()
    
    # Create test devices if they don't exist
    print("Creating test devices...")
    
    test_device1 = {
        'hostname': 'TEST-CORE-A',
        'serial_number': 'TEST001',
        'platform': 'IOS',
        'hardware_model': 'Catalyst 3850',
        'software_version': '16.9.1'
    }
    
    test_device2 = {
        'hostname': 'TEST-DIST-A',
        'serial_number': 'TEST002',
        'platform': 'IOS',
        'hardware_model': 'Catalyst 3750',
        'software_version': '15.2.4'
    }
    
    device1_id = db_manager.upsert_device(test_device1)
    device2_id = db_manager.upsert_device(test_device2)
    
    if not device1_id or not device2_id:
        print("[FAIL] Failed to create test devices")
        return 1
    
    print(f"[OK] Created test devices: {device1_id}, {device2_id}")
    print()
    
    # Test hostname resolution
    print("Testing hostname resolution...")
    resolved_id = db_manager.resolve_hostname_to_device_id('TEST-CORE-A')
    
    if resolved_id == device1_id:
        print(f"[OK] Resolved 'TEST-CORE-A' to device_id {resolved_id}")
    else:
        print(f"[FAIL] Hostname resolution failed: expected {device1_id}, got {resolved_id}")
        return 1
    
    print()
    
    # Create test neighbor data
    print("Creating test neighbor data...")
    
    neighbors = [
        NeighborInfo(
            device_id='TEST-DIST-A',
            local_interface='Gi1/0/1',
            remote_interface='Gi1/0/24',
            platform='Catalyst 3750',
            capabilities=['Switch', 'Router'],
            ip_address='10.0.0.2',
            protocol='CDP'
        )
    ]
    
    # Store neighbors
    print("Storing neighbors...")
    count = db_manager.upsert_device_neighbors(device1_id, neighbors)
    
    if count == 1:
        print(f"[OK] Stored {count} neighbor connection")
    else:
        print(f"[FAIL] Expected to store 1 neighbor, stored {count}")
        return 1
    
    print()
    
    # Query neighbors
    print("Querying neighbors...")
    device_neighbors = db_manager.get_device_neighbors(device1_id)
    
    if len(device_neighbors) == 1:
        print(f"[OK] Found {len(device_neighbors)} neighbor connection")
        
        neighbor = device_neighbors[0]
        print(f"  Source: {neighbor['source_name']} ({neighbor['source_interface']})")
        print(f"  Destination: {neighbor['dest_name']} ({neighbor['destination_interface']})")
        print(f"  Protocol: {neighbor['protocol']}")
    else:
        print(f"[FAIL] Expected 1 neighbor, found {len(device_neighbors)}")
        return 1
    
    print()
    
    # Test deduplication - try to store reverse connection
    print("Testing deduplication...")
    
    reverse_neighbors = [
        NeighborInfo(
            device_id='TEST-CORE-A',
            local_interface='Gi1/0/24',
            remote_interface='Gi1/0/1',
            platform='Catalyst 3850',
            capabilities=['Switch', 'Router'],
            ip_address='10.0.0.1',
            protocol='CDP'
        )
    ]
    
    count = db_manager.upsert_device_neighbors(device2_id, reverse_neighbors)
    
    if count == 1:
        print(f"[OK] Reverse connection handled (updated existing)")
    else:
        print(f"[FAIL] Deduplication failed: stored {count} connections")
        return 1
    
    # Verify still only one connection in database
    cursor = db_manager.connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM device_neighbors")
    total_count = cursor.fetchone()[0]
    cursor.close()
    
    if total_count == 1:
        print(f"[OK] Only 1 connection in database (deduplication working)")
    else:
        print(f"[FAIL] Expected 1 connection, found {total_count}")
        return 1
    
    print()
    
    # Test interface normalization
    print("Testing interface normalization...")
    from netwalker.discovery.protocol_parser import ProtocolParser
    
    parser = ProtocolParser()
    
    test_cases = [
        ('Gi1/0/1', 'GigabitEthernet1/0/1', 'IOS'),
        ('Te1/0/1', 'TenGigabitEthernet1/0/1', 'IOS'),
        ('Po1', 'Port-channel1', 'IOS'),
        ('mgmt0', 'Management0', 'IOS'),
        ('Ethernet1/1', 'Ethernet1/1', 'NX-OS'),
    ]
    
    all_passed = True
    for input_if, expected, platform in test_cases:
        result = parser.normalize_interface_name(input_if, platform)
        if result == expected:
            print(f"  [OK] {input_if} -> {result}")
        else:
            print(f"  [FAIL] {input_if} -> {result} (expected {expected})")
            all_passed = False
    
    if not all_passed:
        return 1
    
    print()
    
    # Cleanup test data
    print("Cleaning up test data...")
    cursor = db_manager.connection.cursor()
    cursor.execute("DELETE FROM device_neighbors WHERE source_device_id IN (?, ?)", (device1_id, device2_id))
    cursor.execute("DELETE FROM devices WHERE device_id IN (?, ?)", (device1_id, device2_id))
    db_manager.connection.commit()
    cursor.close()
    
    print("[OK] Test data cleaned up")
    print()
    
    # Disconnect
    db_manager.disconnect()
    
    print("=" * 70)
    print("[OK] All tests passed!")
    print("=" * 70)
    return 0

if __name__ == '__main__':
    sys.exit(main())
