#!/usr/bin/env python3
"""
Test script to verify config loading
"""

import sys
sys.path.insert(0, '.')

from netwalker.config.config_manager import ConfigurationManager

def main():
    print("Testing Configuration Loading")
    print("="*80)
    
    # Load configuration
    config_manager = ConfigurationManager('netwalker.ini')
    config = config_manager.load_configuration()
    
    print("\nLoaded configuration:")
    print(f"  Config type: {type(config)}")
    print(f"  Config keys: {config.keys()}")
    
    print("\nDiscovery config:")
    discovery = config['discovery']
    print(f"  Type: {type(discovery)}")
    print(f"  max_depth: {discovery.max_depth}")
    print(f"  concurrent_connections: {discovery.concurrent_connections}")
    print(f"  discovery_timeout: {discovery.discovery_timeout}")
    
    print("\nFlattened config (as passed to DiscoveryEngine):")
    flat_config = {
        'max_discovery_depth': discovery.max_depth,
        'discovery_timeout_seconds': discovery.discovery_timeout,
        'max_concurrent_connections': discovery.concurrent_connections,
    }
    print(f"  max_discovery_depth: {flat_config['max_discovery_depth']}")
    print(f"  discovery_timeout_seconds: {flat_config['discovery_timeout_seconds']}")
    
    print("\n" + "="*80)
    print("RESULT:")
    if flat_config['max_discovery_depth'] == 99:
        print("  [OK] max_discovery_depth is correctly set to 99")
    else:
        print(f"  [FAIL] max_discovery_depth is {flat_config['max_discovery_depth']}, expected 99")

if __name__ == '__main__':
    main()
