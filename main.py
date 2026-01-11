#!/usr/bin/env python3
"""
NetWalker - Network Topology Discovery Tool

Main entry point for the NetWalker application.
Provides command-line interface for network discovery and reporting.

Author: Mark Oldham
"""

import sys
import argparse
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from netwalker.netwalker_app import NetWalkerApp
from netwalker.version import __version__, __author__


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="NetWalker - Network Topology Discovery Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  {sys.argv[0]} --config netwalker.ini
  {sys.argv[0]} --seed-devices "router1:192.168.1.1,switch1:192.168.1.2"
  {sys.argv[0]} --max-depth 3 --reports-dir ./custom_reports

Author: {__author__}
Version: {__version__}
        """
    )
    
    # Configuration options
    parser.add_argument(
        '--config', '-c',
        default='netwalker.ini',
        help='Configuration file path (default: netwalker.ini)'
    )
    
    # Discovery options
    parser.add_argument(
        '--seed-devices',
        help='Comma-separated list of seed devices (hostname:ip or just hostname)'
    )
    
    parser.add_argument(
        '--max-depth',
        type=int,
        help='Maximum discovery depth (overrides config file)'
    )
    
    parser.add_argument(
        '--max-connections',
        type=int,
        help='Maximum concurrent connections (overrides config file)'
    )
    
    # Output options
    parser.add_argument(
        '--reports-dir',
        help='Reports output directory (overrides config file)'
    )
    
    parser.add_argument(
        '--logs-dir',
        help='Logs output directory (overrides config file)'
    )
    
    # Logging options
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (overrides config file)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress console output (logs only)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    # Information options
    parser.add_argument(
        '--version',
        action='version',
        version=f'NetWalker {__version__} by {__author__}'
    )
    
    return parser.parse_args()


def convert_args_to_config(args):
    """Convert command-line arguments to configuration dictionary"""
    config_overrides = {}
    
    # Discovery settings
    if args.seed_devices:
        config_overrides['seed_devices'] = args.seed_devices
    
    if args.max_depth is not None:
        config_overrides['max_discovery_depth'] = args.max_depth
    
    if args.max_connections is not None:
        config_overrides['max_concurrent_connections'] = args.max_connections
    
    # Output settings
    if args.reports_dir:
        config_overrides['reports_directory'] = args.reports_dir
    
    if args.logs_dir:
        config_overrides['logs_directory'] = args.logs_dir
    
    # Logging settings
    if args.log_level:
        config_overrides['log_level'] = args.log_level
    
    if args.quiet:
        config_overrides['console_logging'] = False
    
    if args.verbose:
        config_overrides['log_level'] = 'DEBUG'
        config_overrides['console_logging'] = True
    
    return config_overrides


def main():
    """Main application entry point"""
    try:
        # Parse command-line arguments
        args = parse_arguments()
        
        # Convert arguments to configuration overrides
        cli_config = convert_args_to_config(args)
        
        # Initialize and run NetWalker application
        with NetWalkerApp(config_file=args.config, cli_args=cli_config) as app:
            print(f"NetWalker {__version__} - Network Topology Discovery Tool")
            print(f"Author: {__author__}")
            print("-" * 60)
            
            # Run discovery process
            success = app.run_discovery()
            
            if success:
                print("\nDiscovery completed successfully!")
                return 0
            else:
                print("\nDiscovery failed!")
                return 1
    
    except KeyboardInterrupt:
        print("\nDiscovery interrupted by user")
        return 130
    
    except Exception as e:
        print(f"\nFatal error: {e}")
        logging.exception("Fatal error in main application")
        return 1


if __name__ == "__main__":
    sys.exit(main())