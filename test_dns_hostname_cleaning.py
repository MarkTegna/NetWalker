#!/usr/bin/env python3
"""
Test script for DNS hostname cleaning fix.

This script tests that hostnames with serial numbers in parentheses
are properly cleaned before DNS validation.
"""

import sys
import os
import logging
from unittest.mock import Mock, MagicMock

# Add the netwalker package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from netwalker.netwalker_app import NetWalkerApp
from netwalker.reports.excel_generator import ExcelReportGenerator

def setup_logging():
    """Setup logging for the test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def test_hostname_cleaning_in_dns_validation():
    """Test that hostnames are properly cleaned before DNS validation"""
    logger = setup_logging()
    
    logger.info("=" * 80)
    logger.info("TESTING DNS HOSTNAME CLEANING FIX")
    logger.info("Testing that LUMT-CORE-A(FOX1849GQKY) becomes LUMT-CORE-A")
    logger.info("=" * 80)
    
    try:
        # Test the Excel generator's _clean_hostname method directly
        logger.info("\n1. Testing _clean_hostname method directly...")
        
        config = {'reports_directory': './test_reports'}
        excel_generator = ExcelReportGenerator(config)
        
        test_cases = [
            ("LUMT-CORE-A(FOX1849GQKY)", "LUMT-CORE-A"),
            ("BORO-CORE-B(ABC123DEF)", "BORO-CORE-B"),
            ("KREM-RTR-01(XYZ789)", "KREM-RTR-01"),
            ("NORMAL-HOSTNAME", "NORMAL-HOSTNAME"),
            ("HOST.DOMAIN.COM(SERIAL)", "HOST.DOMAIN.COM"),
            ("", ""),
        ]
        
        for raw_hostname, expected_clean in test_cases:
            cleaned = excel_generator._clean_hostname(raw_hostname)
            logger.info(f"  '{raw_hostname}' -> '{cleaned}' (expected: '{expected_clean}')")
            
            if cleaned == expected_clean:
                logger.info(f"    ✓ PASS")
            else:
                logger.error(f"    ✗ FAIL: Expected '{expected_clean}', got '{cleaned}'")
                return False
        
        # Test the NetWalker app's DNS validation hostname extraction
        logger.info("\n2. Testing DNS validation hostname extraction...")
        
        # Create mock inventory with hostname containing serial number
        mock_inventory = {
            'LUMT-CORE-A:192.168.1.1': {
                'hostname': 'LUMT-CORE-A(FOX1849GQKY)',
                'primary_ip': '192.168.1.1',
                'platform': 'cisco_ios',
                'software_version': '15.1(4)M12a',
                'serial_number': 'FOX1849GQKY',
                'hardware_model': 'CISCO2911/K9',
                'uptime': '1 day, 2 hours',
                'discovery_depth': 2,
                'discovery_method': 'neighbor',
                'parent_device': 'BORO-CORE-A',
                'discovery_timestamp': '2026-01-13T10:30:00',
                'connection_method': 'ssh',
                'status': 'active'
            },
            'BORO-CORE-A:10.1.1.1': {
                'hostname': 'BORO-CORE-A',
                'primary_ip': '10.1.1.1',
                'platform': 'cisco_ios',
                'software_version': '16.9.04',
                'serial_number': 'FOC1111111',
                'hardware_model': 'ISR4331/K9',
                'uptime': '10 days, 3 hours',
                'discovery_depth': 0,
                'discovery_method': 'seed',
                'parent_device': None,
                'discovery_timestamp': '2026-01-13T10:25:00',
                'connection_method': 'ssh',
                'status': 'active'
            }
        }
        
        # Create a mock NetWalker app
        mock_config = {
            'reports_directory': './test_reports',
            'enable_dns_validation': True
        }
        
        # Create NetWalker app instance (we'll mock the DNS validator)
        app = NetWalkerApp()
        app.config = mock_config
        app.excel_generator = ExcelReportGenerator(mock_config)
        
        # Mock the DNS validator to capture what hostnames are passed to it
        captured_devices = []
        
        def mock_validate_devices_concurrent(devices):
            nonlocal captured_devices
            captured_devices = devices
            # Return mock results
            results = {}
            for hostname, ip in devices:
                device_key = f"{hostname}:{ip}"
                mock_result = Mock()
                mock_result.hostname = hostname
                mock_result.ip_address = ip
                mock_result.forward_dns_success = True
                mock_result.reverse_dns_success = True
                mock_result.is_public_ip = False
                mock_result.rfc1918_conflict = False
                mock_result.ping_success = True
                mock_result.forward_dns_resolved_ip = ip
                mock_result.reverse_dns_resolved_hostname = hostname
                mock_result.ping_resolved_ip = ip
                mock_result.resolved_private_ip = None
                mock_result.validation_timestamp = Mock()
                mock_result.validation_timestamp.strftime = Mock(return_value="2026-01-13 10:30:00")
                mock_result.error_details = None
                results[device_key] = mock_result
            return results
        
        app.dns_validator = Mock()
        app.dns_validator.validate_devices_concurrent = mock_validate_devices_concurrent
        app.dns_validator.get_validation_summary = Mock(return_value={
            'total_devices': 2,
            'forward_dns_success': 2,
            'reverse_dns_success': 2,
            'rfc1918_conflicts': 0
        })
        
        # Mock the Excel generator's generate_dns_report method
        app.excel_generator.generate_dns_report = Mock(return_value="test_dns_report.xlsx")
        
        # Call perform_dns_validation
        logger.info("  Calling perform_dns_validation with mock inventory...")
        result = app.perform_dns_validation(mock_inventory)
        
        # Check what devices were passed to DNS validation
        logger.info(f"  Devices passed to DNS validation: {captured_devices}")
        
        # Verify hostnames were cleaned
        expected_devices = [
            ('LUMT-CORE-A', '192.168.1.1'),  # Should be cleaned from LUMT-CORE-A(FOX1849GQKY)
            ('BORO-CORE-A', '10.1.1.1')     # Should remain unchanged
        ]
        
        if set(captured_devices) == set(expected_devices):
            logger.info("  ✓ PASS: Hostnames properly cleaned before DNS validation")
            
            # Check specifically for the problematic hostname
            lumt_found = False
            for hostname, ip in captured_devices:
                if hostname == 'LUMT-CORE-A' and ip == '192.168.1.1':
                    lumt_found = True
                    logger.info(f"  ✓ PASS: LUMT-CORE-A(FOX1849GQKY) correctly cleaned to LUMT-CORE-A")
                    break
            
            if not lumt_found:
                logger.error("  ✗ FAIL: LUMT-CORE-A not found in cleaned devices")
                return False
                
        else:
            logger.error(f"  ✗ FAIL: Expected devices {expected_devices}, got {captured_devices}")
            return False
        
        # Test edge cases
        logger.info("\n3. Testing edge cases...")
        
        edge_case_inventory = {
            'DEVICE1:1.1.1.1': {
                'hostname': 'DEVICE1(SERIAL123)',
                'primary_ip': '1.1.1.1'
            },
            'DEVICE2:2.2.2.2': {
                'hostname': 'DEVICE2(ABC)(DEF)',  # Multiple parentheses
                'primary_ip': '2.2.2.2'
            },
            'DEVICE3:3.3.3.3': {
                'hostname': 'DEVICE3',  # No parentheses
                'primary_ip': '3.3.3.3'
            }
        }
        
        captured_devices = []
        result = app.perform_dns_validation(edge_case_inventory)
        
        expected_edge_devices = [
            ('DEVICE1', '1.1.1.1'),
            ('DEVICE2', '2.2.2.2'),  # Should remove both sets of parentheses
            ('DEVICE3', '3.3.3.3')
        ]
        
        logger.info(f"  Edge case devices: {captured_devices}")
        
        if set(captured_devices) == set(expected_edge_devices):
            logger.info("  ✓ PASS: Edge cases handled correctly")
        else:
            logger.error(f"  ✗ FAIL: Expected {expected_edge_devices}, got {captured_devices}")
            return False
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 ALL DNS HOSTNAME CLEANING TESTS PASSED!")
        logger.info("✅ LUMT-CORE-A(FOX1849GQKY) will now appear as LUMT-CORE-A in DNS validation")
        logger.info("✅ Serial numbers in parentheses are properly removed")
        logger.info("✅ Edge cases with multiple parentheses handled correctly")
        logger.info("✅ Normal hostnames without parentheses remain unchanged")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"✗ FAIL: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to run the DNS hostname cleaning test"""
    logger = setup_logging()
    
    logger.info("NetWalker DNS Hostname Cleaning Fix Test")
    logger.info("Testing fix for hostname cleaning in DNS validation reports")
    
    success = test_hostname_cleaning_in_dns_validation()
    
    if success:
        logger.info("\n🎉 DNS HOSTNAME CLEANING FIX VERIFIED!")
        logger.info("The fix will resolve the issue where LUMT-CORE-A(FOX1849GQKY)")
        logger.info("appears in DNS validation reports instead of clean LUMT-CORE-A")
        return True
    else:
        logger.error("\n❌ DNS HOSTNAME CLEANING FIX FAILED!")
        logger.error("The issue with hostname cleaning in DNS validation needs attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)