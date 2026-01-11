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
    
    # Configuration options
    parser.add_argument(
        "--config", "-c",
        default="netwalker.ini",
        help="Configuration file path (default: netwalker.ini)"
    )
    
    parser.add_argument(
        "--seeds", "-s",
        default="seed_device.ini",
        help="Seed devices file path (default: seed_device.ini)"
    )
    
    # Discovery options
    parser.add_argument(
        "--max-depth", "-d",
        type=int,
        help="Maximum discovery depth (overrides config file)"
    )
    
    parser.add_argument(
        "--concurrent-connections", "-j",
        type=int,
        help="Number of concurrent connections (overrides config file)"
    )
    
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        help="Connection timeout in seconds (overrides config file)"
    )
    
    # Output options
    parser.add_argument(
        "--reports-dir", "-r",
        help="Reports output directory (overrides config file)"
    )
    
    parser.add_argument(
        "--logs-dir", "-l",
        help="Logs output directory (overrides config file)"
    )
    
    # Verbosity
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress console output (log file only)"
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