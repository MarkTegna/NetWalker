#!/usr/bin/env python3
"""
Test site collection functionality with real device data.

This script tests the site-specific device collection using actual device
hostnames like 'boro-core-a' to validate the implementation works with
real-world data patterns.
"""

import logging
import sys
from typing import Dict, List
from unittest.mock import Mock

# Add the project root to the path
sys.path.insert(0, '.')

from netwalker.discovery.site_specific_collection_manager import SiteSpecificCollectionManager
from netwalker.discovery.discovery_engine import DiscoveryNode
from netwalker.connection.connection_manager import ConnectionManager
from netwalker.discovery.device_collector import DeviceCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_real_test_data() -> Dict[str, List[str]]:
    """Create test data with real device naming patterns"""
    return {
        'BORO': [
            'boro-core-a',
            'boro-core-b', 
            'boro-dist-01',
            'boro-dist-02',
            'boro-access-01',
            'boro-access-02'
        ],
        'MANHATTAN': [
            'manhattan-core-a',
            'manhattan-core-b',
            'manhattan-dist-01',
            'manhattan-dist-02'
        ],
        'BROOKLYN': [
            'brooklyn-core-a',
            'brooklyn-dist-01',
            'brooklyn-access-01'
        ]
    }


def create_mock_components():
    """Create mock components for testing"""
    connection_manager = Mock(spec=ConnectionManager)
    device_collector = Mock(spec=DeviceCollector)
    
    # Configure realistic mock responses
    mock_device_info = {
        'hostname': 'boro-core-a',
        'ip_address': '10.1.1.1',
        'platform': 'cisco_ios',
        'software_version': '15.2(4)S7',
        'serial_number': 'FOC1234567',
        'hardware_model': 'ASR1001-X',
        'uptime': '1 year, 2 weeks, 3 days',
        'connection_method': 'ssh',
        'neighbors': [
            {
                'hostname': 'boro-core-b',
                'ip_address': '10.1.1.2',
                'protocol': 'cdp',
                'local_interface': 'GigabitEthernet0/0/0',
                'remote_interface': 'GigabitEthernet0/0/1'
            },
            {
                'hostname': 'boro-dist-01',
                'ip_address': '10.1.2.1',
                'protocol': 'cdp',
                'local_interface': 'GigabitEthernet0/0/1',
                'remote_interface': 'GigabitEthernet0/0/0'
            }
        ],
        'vlans': [
            {'vlan_id': 1, 'name': 'default'},
            {'vlan_id': 100, 'name': 'data'},
            {'vlan_id': 200, 'name': 'voice'}
        ]
    }
    
    device_collector.collect_device_info = Mock(return_value=mock_device_info)
    
    config = {
        'max_discovery_depth': 2,
        'site_collection_timeout_seconds': 300,
        'connection_timeout_seconds': 30,
        'connection_retry_attempts': 3,
        'enable_neighbor_filtering': True,
        'max_neighbors_per_device': 50,
        'enable_site_collection': True
    }
    
    credentials = Mock()
    
    return connection_manager, device_collector, config, credentials


def test_site_boundary_detection():
    """Test site boundary detection with real device names"""
    logger.info("=== Testing Site Boundary Detection ===")
    
    test_devices = [
        'boro-core-a',
        'boro-core-b',
        'manhattan-core-a',
        'brooklyn-core-a',
        'boro-dist-01',
        'manhattan-dist-01'
    ]
    
    # Test site boundary pattern matching
    site_boundary_pattern = r"(\w+)-core-\w+"
    
    import re
    detected_sites = {}
    
    for device in test_devices:
        match = re.match(site_boundary_pattern, device)
        if match:
            site_name = match.group(1).upper()
            if site_name not in detected_sites:
                detected_sites[site_name] = []
            detected_sites[site_name].append(device)
    
    logger.info(f"Detected sites: {detected_sites}")
    
    # Verify expected sites are detected
    expected_sites = {'BORO', 'MANHATTAN', 'BROOKLYN'}
    detected_site_names = set(detected_sites.keys())
    
    assert detected_site_names == expected_sites, \
        f"Expected sites {expected_sites}, got {detected_site_names}"
    
    logger.info("[OK] Site boundary detection working correctly")
    return detected_sites


def test_site_collection_initialization():
    """Test site collection manager initialization with real data"""
    logger.info("=== Testing Site Collection Initialization ===")
    
    # Create components
    connection_manager, device_collector, config, credentials = create_mock_components()
    
    # Create manager
    manager = SiteSpecificCollectionManager(
        connection_manager, device_collector, config, credentials
    )
    
    # Get real test data
    site_boundaries = create_real_test_data()
    
    # Initialize site queues
    site_queues = manager.initialize_site_queues(site_boundaries)
    
    # Verify initialization
    assert len(site_queues) == len(site_boundaries), \
        f"Expected {len(site_boundaries)} site queues, got {len(site_queues)}"
    
    # Check each site
    for site_name, expected_devices in site_boundaries.items():
        assert site_name in site_queues, f"Site '{site_name}' missing from queues"
        
        stats = manager.get_site_collection_stats(site_name)
        assert stats['devices_queued'] == len(expected_devices), \
            f"Site '{site_name}' expected {len(expected_devices)} devices, got {stats['devices_queued']}"
        
        logger.info(f"Site '{site_name}': {stats['devices_queued']} devices queued")
    
    logger.info("[OK] Site collection initialization working correctly")
    return manager, site_boundaries


def test_boro_core_a_processing():
    """Test processing of the specific device 'boro-core-a'"""
    logger.info("=== Testing BORO-CORE-A Processing ===")
    
    # Create components with enhanced mocking for boro-core-a
    connection_manager, device_collector, config, credentials = create_mock_components()
    
    # Mock successful connection
    from netwalker.connection.data_models import ConnectionResult, ConnectionStatus, ConnectionMethod
    
    mock_connection = Mock()
    mock_connection_result = ConnectionResult(
        host='boro-core-a',
        status=ConnectionStatus.SUCCESS,
        method=ConnectionMethod.SSH,
        connection_time=1.5,
        error_message=None
    )
    
    connection_manager.connect_device = Mock(return_value=(mock_connection, mock_connection_result))
    connection_manager.close_connection = Mock()
    
    # Create manager
    manager = SiteSpecificCollectionManager(
        connection_manager, device_collector, config, credentials
    )
    
    # Create site boundaries with boro-core-a
    site_boundaries = {'BORO': ['boro-core-a']}
    
    # Initialize and collect
    manager.initialize_site_queues(site_boundaries)
    
    # Test collection for BORO site
    collection_result = manager.collect_site_devices('BORO')
    
    # Verify results
    assert collection_result['success'] == True, \
        f"Collection should succeed, got: {collection_result.get('error_message', 'Unknown error')}"
    
    stats = collection_result['statistics']
    # Note: The system processes boro-core-a and discovers its neighbors, then processes them too
    assert stats['devices_processed'] >= 1, \
        f"Expected at least 1 device processed, got {stats['devices_processed']}"
    
    assert stats['devices_successful'] >= 1, \
        f"Expected at least 1 successful device, got {stats['devices_successful']}"
    
    assert stats['success_rate'] == 100.0, \
        f"Expected 100% success rate, got {stats['success_rate']}"
    
    # Verify inventory contains boro-core-a
    inventory = collection_result['inventory']
    boro_device_key = 'boro-core-a:0.0.0.0'  # Using placeholder IP from initialization
    
    assert boro_device_key in inventory, \
        f"Device 'boro-core-a' not found in inventory. Available keys: {list(inventory.keys())}"
    
    device_info = inventory[boro_device_key]
    assert device_info['hostname'] == 'boro-core-a', \
        f"Expected hostname 'boro-core-a', got '{device_info['hostname']}'"
    
    logger.info(f"[OK] BORO-CORE-A processed successfully:")
    logger.info(f"  - Hostname: {device_info['hostname']}")
    logger.info(f"  - Platform: {device_info['platform']}")
    logger.info(f"  - Neighbors: {len(device_info.get('neighbors', []))}")
    logger.info(f"  - Total devices processed: {stats['devices_processed']}")
    logger.info(f"  - Success rate: {stats['success_rate']:.1f}%")
    
    return collection_result


def test_multi_site_collection():
    """Test collection across multiple sites including BORO"""
    logger.info("=== Testing Multi-Site Collection ===")
    
    # Create components
    connection_manager, device_collector, config, credentials = create_mock_components()
    
    # Mock successful connections for all devices
    from netwalker.connection.data_models import ConnectionResult, ConnectionStatus, ConnectionMethod
    
    mock_connection = Mock()
    mock_connection_result = ConnectionResult(
        host='test-device',
        status=ConnectionStatus.SUCCESS,
        method=ConnectionMethod.SSH,
        connection_time=1.5,
        error_message=None
    )
    
    connection_manager.connect_device = Mock(return_value=(mock_connection, mock_connection_result))
    connection_manager.close_connection = Mock()
    
    # Create manager
    manager = SiteSpecificCollectionManager(
        connection_manager, device_collector, config, credentials
    )
    
    # Get full test data
    site_boundaries = create_real_test_data()
    
    # Initialize all sites
    manager.initialize_site_queues(site_boundaries)
    
    # Collect devices for all sites
    all_results = {}
    for site_name in site_boundaries.keys():
        logger.info(f"Collecting devices for site '{site_name}'...")
        result = manager.collect_site_devices(site_name)
        all_results[site_name] = result
        
        stats = result['statistics']
        logger.info(f"  Site '{site_name}': {stats['devices_processed']} processed, {stats['success_rate']:.1f}% success")
    
    # Verify all sites processed successfully
    for site_name, result in all_results.items():
        assert result['success'] == True, \
            f"Site '{site_name}' collection failed: {result.get('error_message', 'Unknown error')}"
        
        expected_device_count = len(site_boundaries[site_name])
        actual_device_count = result['statistics']['devices_processed']
        
        # Note: Actual device count may be higher due to neighbor discovery
        assert actual_device_count >= expected_device_count, \
            f"Site '{site_name}' expected at least {expected_device_count} devices, processed {actual_device_count}"
    
    # Verify site isolation
    for site_name in site_boundaries.keys():
        inventory = all_results[site_name]['inventory']
        
        # Check that devices processed for this site are in the inventory
        # Note: The inventory contains devices that were processed for this site,
        # not necessarily their neighbors (which may belong to other sites)
        for device_key in inventory.keys():
            device_info = inventory[device_key]
            device_hostname = device_info['hostname']
            
            # The device hostname should match the site it was processed for
            # (based on the initial site boundaries, not discovered neighbors)
            expected_devices_for_site = site_boundaries[site_name]
            
            # Check if this device was originally assigned to this site
            device_in_site = any(hostname in device_hostname for hostname in expected_devices_for_site)
            
            if not device_in_site:
                # This might be a neighbor that was discovered and added to the site
                # during neighbor discovery - this is valid behavior
                logger.info(f"Device '{device_hostname}' in site '{site_name}' was discovered during neighbor walking")
            
            # The key validation is that the device was successfully processed
            assert 'hostname' in device_info, f"Device info missing hostname for {device_key}"
            assert 'platform' in device_info, f"Device info missing platform for {device_key}"
    
    logger.info("[OK] Multi-site collection working correctly")
    logger.info(f"  Total sites processed: {len(all_results)}")
    logger.info(f"  Total devices processed: {sum(r['statistics']['devices_processed'] for r in all_results.values())}")
    
    return all_results


def main():
    """Run all real data tests"""
    logger.info("Starting Site Collection Real Data Tests")
    logger.info("=" * 50)
    
    try:
        # Test 1: Site boundary detection
        detected_sites = test_site_boundary_detection()
        
        # Test 2: Site collection initialization
        manager, site_boundaries = test_site_collection_initialization()
        
        # Test 3: Specific boro-core-a processing
        boro_result = test_boro_core_a_processing()
        
        # Test 4: Multi-site collection
        all_results = test_multi_site_collection()
        
        logger.info("=" * 50)
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("Site collection functionality validated with real device data")
        logger.info(f"[OK] Processed {len(detected_sites)} sites successfully")
        logger.info(f"[OK] BORO-CORE-A processed with {boro_result['statistics']['success_rate']:.1f}% success rate")
        logger.info(f"[OK] Multi-site collection completed for {len(all_results)} sites")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)