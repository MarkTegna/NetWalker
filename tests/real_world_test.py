#!/usr/bin/env python3
"""
Real-world testing with actual network devices
This script tests the NetWalker components against real Cisco devices
"""

import sys
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from netwalker.config import ConfigurationManager, CredentialManager
from netwalker.connection import ConnectionManager
from netwalker.discovery import DeviceCollector, ProtocolParser


def setup_logging():
    """Setup logging for real-world testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('real_world_test.log')
        ]
    )
    return logging.getLogger(__name__)


def load_seed_devices():
    """Load seed devices from seed_file.csv"""
    try:
        with open('seed_file.csv', 'r') as f:
            devices = [line.strip() for line in f if line.strip()]
        return devices
    except FileNotFoundError:
        return []


def test_real_device_connection(logger):
    """Test connection to real devices"""
    logger.info("=== Testing Real Device Connection ===")
    
    # Load configuration and credentials
    config_manager = ConfigurationManager()
    config = config_manager.load_configuration()
    
    cred_manager = CredentialManager()
    credentials = cred_manager.get_credentials()
    
    if not credentials:
        logger.error("No credentials available - cannot test real devices")
        return False
    
    # Load seed devices
    seed_devices = load_seed_devices()
    if not seed_devices:
        logger.error("No seed devices found in seed_file.csv")
        return False
    
    logger.info(f"Found {len(seed_devices)} seed devices: {seed_devices}")
    
    # Setup connection manager
    connection_manager = ConnectionManager(
        ssh_port=config['connection'].ssh_port,
        telnet_port=config['connection'].telnet_port,
        timeout=config['discovery'].connection_timeout
    )
    
    # Test connection to first seed device
    test_device = seed_devices[0]
    logger.info(f"Testing connection to {test_device}")
    
    try:
        connection, result = connection_manager.connect_device(test_device, credentials)
        
        if result.status.value == "success":
            logger.info(f"SUCCESS: Successfully connected to {test_device} via {result.method.value}")
            logger.info(f"  Connection time: {result.connection_time:.2f}s")
            
            # Test basic command execution
            version_output = connection_manager.execute_command(connection, "show version")
            if version_output:
                logger.info(f"SUCCESS: Successfully executed 'show version' command")
                logger.info(f"  Output length: {len(version_output)} characters")
            else:
                logger.warning("WARNING: Failed to execute 'show version' command")
            
            # Test platform detection
            platform = connection_manager.detect_platform(connection)
            logger.info(f"SUCCESS: Detected platform: {platform}")
            
            # Close connection properly
            connection_manager.close_connection(test_device)
            logger.info(f"SUCCESS: Connection to {test_device} closed properly")
            
            return True
            
        else:
            logger.error(f"FAILED: Failed to connect to {test_device}: {result.error_message}")
            return False
            
    except Exception as e:
        logger.error(f"FAILED: Exception during connection test: {str(e)}")
        return False


def test_real_device_discovery(logger):
    """Test device information collection from real devices"""
    logger.info("=== Testing Real Device Discovery ===")
    
    # Load configuration and credentials
    config_manager = ConfigurationManager()
    config = config_manager.load_configuration()
    
    cred_manager = CredentialManager()
    credentials = cred_manager.get_credentials()
    
    if not credentials:
        logger.error("No credentials available")
        return False
    
    # Load seed devices
    seed_devices = load_seed_devices()
    if not seed_devices:
        logger.error("No seed devices found")
        return False
    
    # Setup managers
    connection_manager = ConnectionManager(
        ssh_port=config['connection'].ssh_port,
        telnet_port=config['connection'].telnet_port,
        timeout=config['discovery'].connection_timeout
    )
    
    device_collector = DeviceCollector()
    
    # Test device discovery on first seed
    test_device = seed_devices[0]
    logger.info(f"Testing device discovery on {test_device}")
    
    try:
        # Connect to device
        connection, result = connection_manager.connect_device(test_device, credentials)
        
        if result.status.value != "success":
            logger.error(f"Cannot connect to {test_device} for discovery test")
            return False
        
        # Collect device information
        device_info = device_collector.collect_device_information(
            connection=connection,
            host=test_device,
            connection_method=result.method.value,
            discovery_depth=0,
            is_seed=True
        )
        
        if device_info and device_info.connection_status == "success":
            logger.info(f"SUCCESS: Successfully collected device information:")
            logger.info(f"  Hostname: {device_info.hostname}")
            logger.info(f"  Platform: {device_info.platform}")
            logger.info(f"  Software Version: {device_info.software_version}")
            logger.info(f"  Serial Number: {device_info.serial_number}")
            logger.info(f"  Hardware Model: {device_info.hardware_model}")
            logger.info(f"  Uptime: {device_info.uptime}")
            logger.info(f"  Capabilities: {device_info.capabilities}")
            logger.info(f"  Neighbors found: {len(device_info.neighbors)}")
            
            # Log neighbor information
            for i, neighbor in enumerate(device_info.neighbors):
                logger.info(f"  Neighbor {i+1}: {neighbor.device_id} ({neighbor.protocol})")
            
            # Close connection
            connection_manager.close_connection(test_device)
            return True
            
        else:
            logger.error(f"FAILED: Failed to collect device information: {device_info.error_details if device_info else 'Unknown error'}")
            connection_manager.close_connection(test_device)
            return False
            
    except Exception as e:
        logger.error(f"FAILED: Exception during discovery test: {str(e)}")
        return False


def test_protocol_parsing(logger):
    """Test protocol parsing with real device outputs"""
    logger.info("=== Testing Protocol Parsing ===")
    
    # Load configuration and credentials
    config_manager = ConfigurationManager()
    config = config_manager.load_configuration()
    
    cred_manager = CredentialManager()
    credentials = cred_manager.get_credentials()
    
    if not credentials:
        logger.error("No credentials available")
        return False
    
    # Load seed devices
    seed_devices = load_seed_devices()
    if not seed_devices:
        logger.error("No seed devices found")
        return False
    
    # Setup managers
    connection_manager = ConnectionManager()
    protocol_parser = ProtocolParser()
    
    test_device = seed_devices[0]
    logger.info(f"Testing protocol parsing on {test_device}")
    
    try:
        # Connect to device
        connection, result = connection_manager.connect_device(test_device, credentials)
        
        if result.status.value != "success":
            logger.error(f"Cannot connect to {test_device}")
            return False
        
        # Get CDP neighbors
        cdp_output = connection_manager.execute_command(connection, "show cdp neighbors detail")
        if cdp_output:
            logger.info(f"SUCCESS: Retrieved CDP output ({len(cdp_output)} characters)")
            cdp_neighbors = protocol_parser.parse_cdp_neighbors(cdp_output)
            logger.info(f"SUCCESS: Parsed {len(cdp_neighbors)} CDP neighbors")
        else:
            logger.info("No CDP output received")
            cdp_neighbors = []
        
        # Get LLDP neighbors
        lldp_output = connection_manager.execute_command(connection, "show lldp neighbors detail")
        if lldp_output:
            logger.info(f"SUCCESS: Retrieved LLDP output ({len(lldp_output)} characters)")
            lldp_neighbors = protocol_parser.parse_lldp_neighbors(lldp_output)
            logger.info(f"SUCCESS: Parsed {len(lldp_neighbors)} LLDP neighbors")
        else:
            logger.info("No LLDP output received")
            lldp_neighbors = []
        
        # Test combined parsing
        if cdp_output or lldp_output:
            combined_neighbors = protocol_parser.parse_multi_protocol_output(
                cdp_output or "", lldp_output or ""
            )
            logger.info(f"SUCCESS: Combined parsing found {len(combined_neighbors)} unique neighbors")
            
            # Log neighbor details
            for neighbor in combined_neighbors:
                hostname = protocol_parser.extract_hostname(neighbor)
                logger.info(f"  {neighbor.protocol} Neighbor: {hostname} via {neighbor.local_interface}")
        
        # Close connection
        connection_manager.close_connection(test_device)
        return True
        
    except Exception as e:
        logger.error(f"FAILED: Exception during protocol parsing test: {str(e)}")
        return False


def main():
    """Main test function"""
    logger = setup_logging()
    logger.info("Starting NetWalker Real-World Testing")
    
    # Run tests
    tests = [
        ("Connection Test", test_real_device_connection),
        ("Device Discovery Test", test_real_device_discovery),
        ("Protocol Parsing Test", test_protocol_parsing)
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            results[test_name] = test_func(logger)
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {str(e)}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = 0
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        logger.info("SUCCESS: All real-world tests PASSED!")
        return 0
    else:
        logger.error("FAILED: Some real-world tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())