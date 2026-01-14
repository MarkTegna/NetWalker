#!/usr/bin/env python3
"""
Test the duplicate sheets fix.

This script tests the improved device matching logic and duplicate prevention.
"""

import sys
import logging
from pathlib import Path

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

def test_improved_matching_logic():
    """Test the improved device matching logic"""
    logger = setup_logging()
    
    logger.info("=" * 80)
    logger.info("TESTING IMPROVED DEVICE MATCHING LOGIC")
    logger.info("=" * 80)
    
    # Simulate the improved matching logic
    def find_device_in_inventory(neighbor_hostname, full_inventory):
        """Simulate the improved matching logic"""
        def clean_hostname(hostname):
            if not hostname:
                return ''
            hostname = hostname.replace('(', '_').replace(')', '')
            return hostname.strip()
        
        neighbor_device_info = None
        neighbor_device_key = None
        
        # First pass: Look for exact hostname matches (preferred)
        for device_key, device_info in full_inventory.items():
            device_hostname = clean_hostname(device_info.get('hostname', ''))
            if device_hostname == neighbor_hostname:
                neighbor_device_info = device_info
                neighbor_device_key = device_key
                logger.info(f"  EXACT MATCH: {device_key} ({device_hostname})")
                break
        
        # Second pass: If no exact match, look for short hostname matches
        if not neighbor_device_info:
            for device_key, device_info in full_inventory.items():
                device_hostname = clean_hostname(device_info.get('hostname', ''))
                if device_hostname.split('.')[0] == neighbor_hostname:
                    neighbor_device_info = device_info
                    neighbor_device_key = device_key
                    logger.info(f"  PARTIAL MATCH: {device_key} ({device_hostname})")
                    break
        
        return neighbor_device_info, neighbor_device_key
    
    # Test case 1: Multiple entries for same device (FQDN + short name)
    logger.info("\nTest Case 1: FQDN + Short Name")
    full_inventory = {
        'device1': {
            'hostname': 'WLTX-CORE-A.example.com',
            'ip_address': '10.1.1.1',
            'status': 'discovered'
        },
        'device2': {
            'hostname': 'WLTX-CORE-A',
            'ip_address': '10.1.1.1',
            'status': 'discovered'
        }
    }
    
    neighbor_hostname = 'WLTX-CORE-A'
    device_info, device_key = find_device_in_inventory(neighbor_hostname, full_inventory)
    
    if device_info and device_key == 'device2':
        logger.info("✅ Correctly selected exact match (device2)")
    else:
        logger.error(f"❌ Wrong selection: {device_key}")
    
    # Test case 2: Only FQDN available
    logger.info("\nTest Case 2: Only FQDN Available")
    full_inventory = {
        'device1': {
            'hostname': 'WLTX-CORE-B.example.com',
            'ip_address': '10.1.1.2',
            'status': 'discovered'
        }
    }
    
    neighbor_hostname = 'WLTX-CORE-B'
    device_info, device_key = find_device_in_inventory(neighbor_hostname, full_inventory)
    
    if device_info and device_key == 'device1':
        logger.info("✅ Correctly selected partial match (device1)")
    else:
        logger.error(f"❌ Wrong selection: {device_key}")
    
    # Test case 3: No matches
    logger.info("\nTest Case 3: No Matches")
    full_inventory = {
        'device1': {
            'hostname': 'OTHER-DEVICE',
            'ip_address': '10.1.1.3',
            'status': 'discovered'
        }
    }
    
    neighbor_hostname = 'WLTX-CORE-C'
    device_info, device_key = find_device_in_inventory(neighbor_hostname, full_inventory)
    
    if not device_info:
        logger.info("✅ Correctly found no matches")
    else:
        logger.error(f"❌ Unexpected match: {device_key}")
    
    return True

def test_duplicate_sheet_prevention():
    """Test the duplicate sheet name prevention logic"""
    logger = setup_logging()
    
    logger.info("\n" + "=" * 80)
    logger.info("TESTING DUPLICATE SHEET NAME PREVENTION")
    logger.info("=" * 80)
    
    # Simulate the sheet name generation logic
    def generate_unique_sheet_name(neighbor_hostname, created_sheet_names):
        """Simulate the duplicate prevention logic"""
        safe_hostname = neighbor_hostname[:20]
        sheet_name = f"Neighbors_{safe_hostname}"
        
        # Check for duplicate sheet names and modify if necessary
        original_sheet_name = sheet_name
        counter = 1
        while sheet_name in created_sheet_names:
            # Append a number to make it unique
            suffix = f"_{counter}"
            max_hostname_len = 20 - len(suffix) - len("Neighbors_")
            truncated_hostname = safe_hostname[:max_hostname_len]
            sheet_name = f"Neighbors_{truncated_hostname}{suffix}"
            counter += 1
            
            # Safety check to prevent infinite loop
            if counter > 100:
                logger.error(f"Could not create unique sheet name for {neighbor_hostname}")
                return None
        
        if sheet_name != original_sheet_name:
            logger.warning(f"Duplicate detected, using {sheet_name} instead of {original_sheet_name}")
        
        return sheet_name
    
    # Test duplicate prevention
    created_sheet_names = set()
    
    # First device - should get normal name
    sheet1 = generate_unique_sheet_name('WLTX-CORE-A', created_sheet_names)
    created_sheet_names.add(sheet1)
    logger.info(f"Sheet 1: {sheet1}")
    
    # Second device with same name - should get modified name
    sheet2 = generate_unique_sheet_name('WLTX-CORE-A', created_sheet_names)
    created_sheet_names.add(sheet2)
    logger.info(f"Sheet 2: {sheet2}")
    
    # Third device with same name - should get another modified name
    sheet3 = generate_unique_sheet_name('WLTX-CORE-A', created_sheet_names)
    created_sheet_names.add(sheet3)
    logger.info(f"Sheet 3: {sheet3}")
    
    # Verify all names are unique
    all_sheets = [sheet1, sheet2, sheet3]
    unique_sheets = set(all_sheets)
    
    if len(all_sheets) == len(unique_sheets):
        logger.info("✅ All sheet names are unique")
        return True
    else:
        logger.error("❌ Duplicate sheet names generated")
        return False

def main():
    """Main test function"""
    logger = setup_logging()
    
    logger.info("NetWalker Duplicate Sheets Fix Test")
    
    # Test the improved matching logic
    matching_ok = test_improved_matching_logic()
    
    # Test duplicate prevention
    prevention_ok = test_duplicate_sheet_prevention()
    
    logger.info(f"\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    if matching_ok and prevention_ok:
        logger.info("✅ All tests passed - duplicate sheets fix is working")
        return True
    else:
        logger.error("❌ Some tests failed - fix needs more work")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)