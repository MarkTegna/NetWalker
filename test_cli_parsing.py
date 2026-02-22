#!/usr/bin/env python3
"""Test CLI argument parsing"""

import sys
import argparse

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Test CLI parsing")
    
    parser.add_argument('--config', '-c', default='netwalker.ini')
    parser.add_argument('--seed-devices', help='Seed devices')
    parser.add_argument('--max-depth', type=int, help='Maximum discovery depth')
    
    return parser.parse_args()

def convert_args_to_config(args):
    """Convert command-line arguments to configuration dictionary"""
    config_overrides = {}
    
    if args.seed_devices:
        config_overrides['seed_devices'] = args.seed_devices
    
    if args.max_depth is not None:
        config_overrides['max_discovery_depth'] = args.max_depth
    
    return config_overrides

# Test with the command line the user used
test_args = ['--seed-devices', 'KARE-CORE-A', '--max-depth', '9', '--config', './netwalker.ini']
print(f"Testing with args: {test_args}\n")

sys.argv = ['test_cli_parsing.py'] + test_args
args = parse_arguments()

print(f"Parsed args:")
print(f"  config: {args.config}")
print(f"  seed_devices: {args.seed_devices}")
print(f"  max_depth: {args.max_depth}")
print(f"  max_depth type: {type(args.max_depth)}")
print(f"  max_depth is not None: {args.max_depth is not None}")

config_overrides = convert_args_to_config(args)
print(f"\nConfig overrides:")
for key, value in config_overrides.items():
    print(f"  {key}: {value}")
