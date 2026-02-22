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
    
    # Global options (available to all commands)
    parser.add_argument(
        '--config', '-c',
        default='netwalker.ini',
        help='Configuration file path (default: netwalker.ini)'
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Discovery command (default)
    discovery_parser = subparsers.add_parser('discover', help='Run network discovery')
    
    # Seed devices options
    discovery_parser.add_argument(
        "--seeds", "-s",
        default="seed_device.ini",
        help="Seed devices file path (default: seed_device.ini)"
    )
    
    discovery_parser.add_argument(
        '--seed-devices',
        help='Comma-separated list of seed devices (hostname:ip or just hostname)'
    )
    
    # Discovery options
    discovery_parser.add_argument(
        "--max-depth", "-d",
        type=int,
        help="Maximum discovery depth (overrides config file)"
    )
    
    discovery_parser.add_argument(
        '--max-connections',
        type=int,
        help='Maximum concurrent connections (overrides config file)'
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
    
    # Logging options
    discovery_parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (overrides config file)'
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
    
    # Credential options
    discovery_parser.add_argument(
        '--username', '-u',
        help='Device username for authentication'
    )
    
    discovery_parser.add_argument(
        '--password', '-p',
        help='Device password for authentication'
    )
    
    discovery_parser.add_argument(
        '--enable-password',
        action='store_true',
        help='Prompt for enable password'
    )
    
    # Database-driven discovery options
    discovery_parser.add_argument(
        '--rewalk-stale',
        type=int,
        metavar='DAYS',
        help='Walk devices not walked in X days (ignores seed file)'
    )
    
    discovery_parser.add_argument(
        '--rewalk-depth',
        type=int,
        default=1,
        metavar='DEPTH',
        help='Discovery depth for --rewalk-stale (default: 1)'
    )
    
    discovery_parser.add_argument(
        '--walk-unwalked',
        action='store_true',
        help='Walk devices discovered but never walked (Unwalked Neighbors, ignores seed file)'
    )
    
    discovery_parser.add_argument(
        '--walk-unwalked-depth',
        type=int,
        default=1,
        metavar='DEPTH',
        help='Discovery depth for --walk-unwalked (default: 1)'
    )
    
    # Database management commands (added to discovery for backward compatibility)
    discovery_parser.add_argument(
        '--db-init',
        action='store_true',
        help='Initialize database schema (create tables)'
    )
    
    discovery_parser.add_argument(
        '--db-purge',
        action='store_true',
        help='Purge all data from database (requires confirmation)'
    )
    
    discovery_parser.add_argument(
        '--db-purge-devices',
        action='store_true',
        help='Delete devices marked with status=purge'
    )
    
    discovery_parser.add_argument(
        '--db-status',
        action='store_true',
        help='Show database connection status and record counts'
    )
    
    # Visio generator command
    visio_parser = subparsers.add_parser('visio', help='Generate Visio topology diagrams from database')

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
    
    # IPv4 Prefix Inventory command
    ipv4_parser = subparsers.add_parser(
        'ipv4-prefix-inventory',
        help='Collect and inventory IPv4 prefixes from network devices'
    )
    
    ipv4_parser.add_argument(
        '--filter', '-f',
        help='Device name filter pattern (SQL wildcard: %% for multiple chars, _ for single char)'
    )
    
    ipv4_parser.add_argument(
        '--output', '-o',
        help='Output directory for reports (overrides config file)'
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