#!/usr/bin/env python3
"""
Diagnostic script to identify configuration issues
"""

import configparser
import os

def check_config_file(config_path):
    """Check a config file and report its settings"""
    print(f"\n{'='*80}")
    print(f"Checking: {config_path}")
    print(f"{'='*80}")
    
    if not os.path.exists(config_path):
        print(f"  [NOT FOUND] File does not exist")
        return
    
    print(f"  [EXISTS] File found")
    
    config = configparser.ConfigParser()
    config.read(config_path)
    
    # Check discovery section
    if config.has_section('discovery'):
        print(f"\n  [discovery] section:")
        max_depth = config.get('discovery', 'max_depth', fallback='NOT SET')
        print(f"    max_depth = {max_depth}")
        concurrent = config.get('discovery', 'concurrent_connections', fallback='NOT SET')
        print(f"    concurrent_connections = {concurrent}")
        timeout = config.get('discovery', 'discovery_timeout', fallback='NOT SET')
        print(f"    discovery_timeout = {timeout}")
    else:
        print(f"\n  [WARNING] No [discovery] section found!")
    
    # Check exclusions section
    if config.has_section('exclusions'):
        print(f"\n  [exclusions] section:")
        platforms = config.get('exclusions', 'exclude_platforms', fallback='NOT SET')
        print(f"    exclude_platforms = {platforms}")
        capabilities = config.get('exclusions', 'exclude_capabilities', fallback='NOT SET')
        print(f"    exclude_capabilities = {capabilities}")
    else:
        print(f"\n  [WARNING] No [exclusions] section found!")

def main():
    print("NetWalker Configuration Diagnostic")
    print("="*80)
    
    # Check all possible config locations
    config_files = [
        'netwalker.ini',
        'dist/NetWalker_v0.3.30/netwalker.ini',
        'dist/NetWalker_v0.3.29/netwalker.ini',
    ]
    
    for config_file in config_files:
        check_config_file(config_file)
    
    print(f"\n{'='*80}")
    print("DIAGNOSIS COMPLETE")
    print(f"{'='*80}")
    print("\nExpected values for correct operation:")
    print("  max_depth = 99")
    print("  exclude_capabilities = camera,printer  (NOT including 'phone')")
    print("\nIf max_depth = 1, the config file is using old defaults.")
    print("If exclude_capabilities includes 'phone', LUM* devices will be filtered.")

if __name__ == '__main__':
    main()
