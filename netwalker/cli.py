"""
Command Line Interface for NetWalker
"""

import argparse
import sys
from .version import __version__, __author__


def create_parser():
    """Create and configure the command line argument parser"""
    parser = argparse.ArgumentParser(
        description="NetWalker - Network Topology Discovery Tool",
        epilog=f"Author: {__author__} | Version: {__version__}"
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Discovery command (default)
    discovery_parser = subparsers.add_parser('discover', help='Run network discovery')
    
    # Configuration options
    discovery_parser.add_argument(
        "--config", "-c",
        default="netwalker.ini",
        help="Configuration file path (default: netwalker.ini)"
    )
    
    discovery_parser.add_argument(
        "--seeds", "-s",
        default="seed_device.ini",
        help="Seed devices file path (default: seed_device.ini)"
    )
    
    # Discovery options
    discovery_parser.add_argument(
        "--max-depth", "-d",
        type=int,
        help="Maximum discovery depth (overrides config file)"
    )
    
    discovery_parser.add_argument(
        "--concurrent-connections", "-j",
        type=int,
        help="Number of concurrent connections (overrides config file)"
    )
    
    discovery_parser.add_argument(
        "--timeout", "-t",
        type=int,
        help="Connection timeout in seconds (overrides config file)"
    )
    
    # Output options
    discovery_parser.add_argument(
        "--reports-dir", "-r",
        help="Reports output directory (overrides config file)"
    )
    
    discovery_parser.add_argument(
        "--logs-dir", "-l",
        help="Logs output directory (overrides config file)"
    )
    
    # Verbosity
    discovery_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    discovery_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress console output (log file only)"
    )
    
    # Visio generator command
    visio_parser = subparsers.add_parser('visio', help='Generate Visio topology diagrams from database')

    visio_parser.add_argument(
        '--config',
        default='netwalker.ini',
        help='Configuration file path (default: netwalker.ini)'
    )

    visio_parser.add_argument(
        '--output',
        default='./visio_diagrams',
        help='Output directory for Visio files (default: ./visio_diagrams)'
    )

    visio_parser.add_argument(
        '--site',
        help='Generate diagram for specific site only (e.g., BORO)'
    )

    visio_parser.add_argument(
        '--all-in-one',
        action='store_true',
        help='Generate single diagram with all devices instead of per-site diagrams'
    )

    # Execute command
    execute_parser = subparsers.add_parser(
        'execute',
        help='Execute commands on filtered devices'
    )

    execute_parser.add_argument(
        '--config', '-c',
        default='netwalker.ini',
        help='Configuration file path (default: netwalker.ini)'
    )

    execute_parser.add_argument(
        '--filter', '-f',
        required=True,
        help='Device name filter pattern (SQL wildcard: %% for multiple chars, _ for single char)'
    )

    execute_parser.add_argument(
        '--command', '-cmd',
        required=True,
        help='Command to execute on devices'
    )

    execute_parser.add_argument(
        '--output', '-o',
        default='.',
        help='Output directory for Excel file (default: current directory)'
    )
    
    # Version
    parser.add_argument(
        "--version",
        action="version",
        version=f"NetWalker {__version__} by {__author__}"
    )
    
    return parser


def parse_args(args=None):
    """Parse command line arguments"""
    parser = create_parser()
    return parser.parse_args(args)