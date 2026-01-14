"""
Test script to verify WTSP discovery fix

This script tests that the discovery timeout fix allows depth 3+ devices to be processed.
"""

import os
import sys
import configparser
from pathlib import Path

def test_config_changes():
    """Verify that configuration changes are correct"""
    print("=" * 80)
    print("WTSP Discovery Fix Verification")
    print("=" * 80)
    print()
    
    # Read configuration
    config_file = Path("netwalker.ini")
    if not config_file.exists():
        print("ERROR: netwalker.ini not found!")
        return False
    
    config = configparser.ConfigParser()
    config.read(config_file)
    
    # Check discovery settings
    print("Checking discovery configuration...")
    print()
    
    discovery_timeout = config.getint('discovery', 'discovery_timeout')
    concurrent_connections = config.getint('discovery', 'concurrent_connections')
    max_depth = config.getint('discovery', 'max_depth')
    
    print(f"  max_depth: {max_depth}")
    print(f"  discovery_timeout: {discovery_timeout} seconds ({discovery_timeout/60:.1f} minutes)")
    print(f"  concurrent_connections: {concurrent_connections}")
    print()
    
    # Verify recommended settings
    issues = []
    
    if max_depth < 99:
        issues.append(f"  - max_depth is {max_depth}, should be 99 for full network discovery")
    else:
        print("  ✓ max_depth is set to 99 (correct)")
    
    if discovery_timeout < 3600:
        issues.append(f"  - discovery_timeout is {discovery_timeout}s ({discovery_timeout/60:.1f}m), recommended 7200s (2 hours) for large networks")
    else:
        print(f"  ✓ discovery_timeout is set to {discovery_timeout}s ({discovery_timeout/60:.1f} minutes) (sufficient for large networks)")
    
    if concurrent_connections < 10:
        issues.append(f"  - concurrent_connections is {concurrent_connections}, recommended 10+ for faster discovery")
    else:
        print(f"  ✓ concurrent_connections is set to {concurrent_connections} (good for large networks)")
    
    print()
    
    if issues:
        print("WARNINGS:")
        for issue in issues:
            print(issue)
        print()
        print("These settings may work but are not optimal for large network discovery.")
        print()
    else:
        print("All settings are optimal for large network discovery!")
        print()
    
    # Calculate expected discovery time
    print("Expected Discovery Performance:")
    print()
    
    # Assumptions based on log analysis
    avg_device_time = 4  # seconds per device (from log analysis)
    total_devices = 1059  # from WTSP discovery log
    
    # Sequential time
    sequential_time = total_devices * avg_device_time
    print(f"  Sequential processing time: {sequential_time}s ({sequential_time/60:.1f} minutes)")
    
    # Parallel time (with concurrency)
    parallel_time = sequential_time / concurrent_connections
    print(f"  With {concurrent_connections} concurrent connections: {parallel_time}s ({parallel_time/60:.1f} minutes)")
    
    # Add overhead (20%)
    estimated_time = parallel_time * 1.2
    print(f"  Estimated time (with 20% overhead): {estimated_time}s ({estimated_time/60:.1f} minutes)")
    print()
    
    if estimated_time > discovery_timeout:
        print(f"  WARNING: Estimated time ({estimated_time/60:.1f}m) exceeds timeout ({discovery_timeout/60:.1f}m)")
        print(f"  Discovery may not complete!")
        print()
        return False
    else:
        print(f"  ✓ Timeout ({discovery_timeout/60:.1f}m) is sufficient for estimated time ({estimated_time/60:.1f}m)")
        print()
    
    return True

def print_test_instructions():
    """Print instructions for testing the fix"""
    print("=" * 80)
    print("Testing Instructions")
    print("=" * 80)
    print()
    print("To test the fix, run NetWalker with WTSP-CORE-A as seed device:")
    print()
    print("  1. Clean the seed file status entries:")
    print("     - Open seed_file.csv")
    print("     - Remove any status entries for previous runs")
    print()
    print("  2. Run NetWalker:")
    print("     .\\dist\\NetWalker_v0.3.35\\NetWalker.exe")
    print()
    print("  3. Monitor the discovery:")
    print("     - Watch for depth 3+ devices being processed (not just queued)")
    print("     - Check that discovery completes without timeout")
    print("     - Verify all queued devices are processed")
    print()
    print("  4. Check the results:")
    print("     - Open the Discovery report")
    print("     - Look for KARE-NEWS-SW1 in 'Discovered Devices' sheet")
    print("     - Verify 'Neighbor-only Devices' sheet is empty or minimal")
    print("     - Check that total devices discovered matches queue size")
    print()
    print("Expected Results:")
    print("  - Discovery time: 60-90 minutes")
    print("  - Devices discovered: 1000+ (all queued devices processed)")
    print("  - No timeout warnings in log")
    print("  - All depth 3+ devices in 'Discovered Devices' sheet")
    print()

if __name__ == "__main__":
    success = test_config_changes()
    print_test_instructions()
    
    if success:
        print("Configuration is ready for testing!")
        sys.exit(0)
    else:
        print("Configuration needs adjustment before testing.")
        sys.exit(1)
