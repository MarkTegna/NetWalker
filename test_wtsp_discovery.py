#!/usr/bin/env python3
"""
Test to investigate why WTSP-CORE-A is not being walked at depth 2.

This script will help diagnose if WTSP-CORE-A is being filtered as a site boundary.
"""

import sys
import logging
import fnmatch

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

def test_site_boundary_matching():
    """Test if WTSP-CORE-A matches the site boundary pattern"""
    logger = setup_logging()
    
    logger.info("=" * 80)
    logger.info("TESTING WTSP-CORE-A SITE BOUNDARY MATCHING")
    logger.info("=" * 80)
    
    # Test configuration
    site_boundary_pattern = "*-CORE-*"
    test_devices = [
        "BORO-CORE-A",
        "WTSP-CORE-A",
        "LUMT-CORE-A",
        "WTSP-SW01",
        "BORO-MDF-SW01"
    ]
    
    logger.info(f"\nSite boundary pattern: {site_boundary_pattern}")
    logger.info(f"Testing {len(test_devices)} devices:\n")
    
    for device in test_devices:
        matches = fnmatch.fnmatch(device, site_boundary_pattern)
        status = "[BOUNDARY]" if matches else "[NORMAL]"
        logger.info(f"  {status} {device} - matches pattern: {matches}")
    
    logger.info("\n" + "=" * 80)
    logger.info("ANALYSIS")
    logger.info("=" * 80)
    
    logger.info("\nWTSP-CORE-A matches the site boundary pattern *-CORE-*")
    logger.info("This means it will be treated as a site boundary device.")
    logger.info("\nIn NetWalker's discovery logic:")
    logger.info("1. BORO-CORE-A (seed) is discovered at depth 0")
    logger.info("2. WTSP-CORE-A is discovered as a neighbor at depth 1")
    logger.info("3. WTSP-CORE-A matches *-CORE-* pattern")
    logger.info("4. WTSP-CORE-A is marked as a site boundary")
    logger.info("5. Site boundary devices are NOT walked further")
    logger.info("\nThis is the expected behavior when site boundary detection is enabled.")
    logger.info("Site boundary devices define the edge of a site and are not traversed.")
    
    logger.info("\n" + "=" * 80)
    logger.info("SOLUTION OPTIONS")
    logger.info("=" * 80)
    
    logger.info("\nOption 1: Disable site boundary detection")
    logger.info("  - Set site_boundary_pattern = (blank) in netwalker.ini")
    logger.info("  - This will walk ALL devices regardless of hostname pattern")
    
    logger.info("\nOption 2: Change the site boundary pattern")
    logger.info("  - Use a more specific pattern that doesn't match WTSP-CORE-A")
    logger.info("  - Example: BORO-CORE-* (only matches BORO site boundaries)")
    
    logger.info("\nOption 3: Enable site collection mode")
    logger.info("  - Set enable_site_collection = true in netwalker.ini")
    logger.info("  - This will walk devices within each site boundary")
    logger.info("  - WTSP-CORE-A will be walked as part of the WTSP site")
    
    return True

def check_discovery_logs():
    """Check if we can find evidence in recent discovery logs"""
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "=" * 80)
    logger.info("CHECKING RECENT DISCOVERY LOGS")
    logger.info("=" * 80)
    
    try:
        from pathlib import Path
        
        logs_dir = Path("logs")
        if not logs_dir.exists():
            logger.info("No logs directory found")
            return False
        
        # Find most recent log file
        log_files = list(logs_dir.glob("netwalker_*.log"))
        if not log_files:
            logger.info("No log files found")
            return False
        
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"Analyzing: {latest_log}")
        
        # Search for WTSP-CORE-A mentions
        wtsp_mentions = []
        with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if 'WTSP-CORE-A' in line.upper():
                    wtsp_mentions.append((line_num, line.strip()))
        
        if wtsp_mentions:
            logger.info(f"\nFound {len(wtsp_mentions)} mentions of WTSP-CORE-A:")
            for line_num, line in wtsp_mentions[:20]:  # Show first 20
                logger.info(f"  Line {line_num}: {line[:150]}")
        else:
            logger.info("\nNo mentions of WTSP-CORE-A found in log")
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking logs: {e}")
        return False

def main():
    """Main test function"""
    logger = setup_logging()
    
    logger.info("NetWalker WTSP-CORE-A Discovery Investigation")
    
    # Test site boundary matching
    test_site_boundary_matching()
    
    # Check logs for evidence
    check_discovery_logs()
    
    logger.info("\n" + "=" * 80)
    logger.info("INVESTIGATION COMPLETE")
    logger.info("=" * 80)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)