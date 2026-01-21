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
import signal
import threading
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from netwalker.netwalker_app import NetWalkerApp
from netwalker.version import __version__, __author__

# Global variable to track the app instance for signal handling
_app_instance = None
_shutdown_event = threading.Event()


def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    global _app_instance, _shutdown_event
    
    print(f"\nReceived signal {signum} - initiating graceful shutdown...")
    logging.info(f"Received signal {signum} - initiating graceful shutdown")
    
    _shutdown_event.set()
    
    if _app_instance:
        try:
            # Force cleanup with shorter timeout for signal handling
            _app_instance.cleanup()
        except Exception as e:
            print(f"Error during signal cleanup: {e}")
            logging.error(f"Error during signal cleanup: {e}")
    
    print("Shutdown complete")
    sys.exit(128 + signum)


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
    
    # Credential options
    parser.add_argument(
        '--username', '-u',
        help='Device username for authentication'
    )
    
    parser.add_argument(
        '--password', '-p',
        help='Device password for authentication'
    )
    
    parser.add_argument(
        '--enable-password',
        action='store_true',
        help='Prompt for enable password'
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
    
    # Visio generator options
    parser.add_argument(
        '--visio',
        action='store_true',
        help='Generate Visio topology diagrams from database'
    )
    
    parser.add_argument(
        '--visio-output',
        default='./visio_diagrams',
        help='Output directory for Visio files (default: ./visio_diagrams)'
    )
    
    parser.add_argument(
        '--visio-site',
        help='Generate diagram for specific site only (e.g., BORO)'
    )
    
    parser.add_argument(
        '--visio-all-in-one',
        action='store_true',
        help='Generate single diagram with all devices'
    )
    
    # Database options
    parser.add_argument(
        '--db-init',
        action='store_true',
        help='Initialize database schema (create tables)'
    )
    
    parser.add_argument(
        '--db-purge',
        action='store_true',
        help='Purge all data from database (requires confirmation)'
    )
    
    parser.add_argument(
        '--db-purge-devices',
        action='store_true',
        help='Delete devices marked with status=purge'
    )
    
    parser.add_argument(
        '--db-status',
        action='store_true',
        help='Show database connection status and record counts'
    )
    
    return parser.parse_args()


def convert_args_to_config(args):
    """Convert command-line arguments to configuration dictionary"""
    config_overrides = {}
    
    # Credential settings
    if args.username:
        config_overrides['username'] = args.username
    
    if args.password:
        config_overrides['password'] = args.password
    
    if args.enable_password:
        config_overrides['enable_password'] = args.enable_password
    
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
    global _app_instance
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Parse command-line arguments
        args = parse_arguments()
        
        # Handle Visio generation command
        if args.visio:
            from netwalker.config.config_manager import ConfigurationManager
            from netwalker.database import DatabaseManager
            import pyodbc
            import logging
            
            # Try to import COM generator, fall back to vsdx if not available
            try:
                from netwalker.reports.visio_generator_com import VisioGeneratorCOM
                use_com = True
                logger_msg = "Using COM automation (requires Microsoft Visio)"
            except ImportError:
                from netwalker.reports.visio_generator import VisioGenerator
                use_com = False
                logger_msg = "Using vsdx library (limited connector support)"
            
            # Setup logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
            logger = logging.getLogger(__name__)
            logger.info(logger_msg)
            
            print("=" * 70)
            print(f"NetWalker Visio Diagram Generator v{__version__}")
            print(f"Author: {__author__}")
            print("=" * 70)
            print()
            
            try:
                # Load configuration
                config_manager = ConfigurationManager(args.config)
                parsed_config = config_manager.load_configuration()
                db_config = parsed_config.get('database', {})
                
                # Initialize database manager
                logger.info("Initializing database manager...")
                db_manager = DatabaseManager(db_config)
                
                if not db_manager.connect():
                    logger.error("Failed to connect to database")
                    print("\n[FAIL] Could not connect to database")
                    return 1
                
                # Get devices from database
                logger.info("Querying devices from database...")
                connection = db_manager.connection
                cursor = connection.cursor()
                query = """
                    SELECT device_name, platform, hardware_model, serial_number
                    FROM devices
                    WHERE status = 'active'
                    ORDER BY device_name
                """
                cursor.execute(query)
                
                devices = []
                for row in cursor.fetchall():
                    devices.append({
                        'device_name': row[0],
                        'platform': row[1] or 'Unknown',
                        'hardware_model': row[2] or '',
                        'serial_number': row[3] or ''
                    })
                cursor.close()
                
                logger.info(f"Retrieved {len(devices)} active devices from database")
                
                # Group devices by site
                devices_by_site = {}
                for device in devices:
                    device_name = device['device_name']
                    if len(device_name) >= 4:
                        site_code = device_name[:4].upper()
                    else:
                        site_code = 'UNKNOWN'
                    
                    if site_code not in devices_by_site:
                        devices_by_site[site_code] = []
                    devices_by_site[site_code].append(device)
                
                logger.info(f"Grouped devices into {len(devices_by_site)} sites")
                
                # Initialize Visio generator with database manager
                logger.info(f"Initializing Visio generator (output: {args.visio_output})...")
                if use_com:
                    visio_gen = VisioGeneratorCOM(args.visio_output, database_manager=db_manager)
                else:
                    visio_gen = VisioGenerator(args.visio_output, database_manager=db_manager)
                
                # Generate diagrams (connections will be queried from database automatically)
                
                if args.visio_all_in_one:
                    # Generate single diagram with all devices
                    logger.info("Generating single diagram with all devices...")
                    filepath = visio_gen.generate_topology_diagram(
                        devices,
                        site_name="Complete Network"
                    )
                    
                    if filepath:
                        print(f"\n[OK] Generated diagram: {filepath}")
                    else:
                        print("\n[FAIL] Failed to generate diagram")
                        return 1
                
                elif args.visio_site:
                    # Generate diagram for specific site
                    logger.info(f"Generating diagram for site: {args.visio_site}...")
                    
                    if args.visio_site not in devices_by_site:
                        logger.error(f"Site not found: {args.visio_site}")
                        logger.info(f"Available sites: {', '.join(devices_by_site.keys())}")
                        return 1
                    
                    site_devices = devices_by_site[args.visio_site]
                    filepath = visio_gen.generate_topology_diagram(
                        site_devices,
                        site_name=args.visio_site
                    )
                    
                    if filepath:
                        print(f"\n[OK] Generated diagram: {filepath}")
                    else:
                        print("\n[FAIL] Failed to generate diagram")
                        return 1
                
                else:
                    # Generate separate diagrams for each site
                    logger.info("Generating diagrams for all sites...")
                    
                    generated_files = []
                    for site_name, site_devices in devices_by_site.items():
                        filepath = visio_gen.generate_topology_diagram(
                            site_devices,
                            site_name=site_name
                        )
                        if filepath:
                            generated_files.append(filepath)
                    
                    print(f"\n[OK] Generated {len(generated_files)} diagram(s):")
                    for filepath in generated_files:
                        print(f"  - {filepath}")
                
                # Disconnect from database
                db_manager.disconnect()
                logger.info("Database connection closed")
                
                print("\nVisio diagram generation complete!")
                return 0
                
            except Exception as e:
                logger.error(f"Visio generation failed: {e}")
                logger.exception("Full exception details:")
                return 1
        
        # Handle database commands (these don't require full app initialization)
        if args.db_init or args.db_purge or args.db_purge_devices or args.db_status:
            from netwalker.config.config_manager import ConfigurationManager
            from netwalker.database import DatabaseManager
            
            # Load configuration
            config_manager = ConfigurationManager(args.config)
            parsed_config = config_manager.load_configuration()
            
            # Initialize database manager
            db_config = parsed_config.get('database', {})
            db_manager = DatabaseManager(db_config)
            
            if args.db_init:
                print("Initializing database schema...")
                if db_manager.initialize_database():
                    print("[OK] Database initialized successfully")
                    return 0
                else:
                    print("[FAIL] Database initialization failed")
                    return 1
            
            elif args.db_purge:
                print("WARNING: This will delete ALL data from the database!")
                response = input("Type 'YES' to confirm: ")
                if response == 'YES':
                    print("Purging database...")
                    if db_manager.purge_database():
                        print("[OK] Database purged successfully")
                        return 0
                    else:
                        print("[FAIL] Database purge failed")
                        return 1
                else:
                    print("Purge cancelled")
                    return 0
            
            elif args.db_purge_devices:
                print("Purging devices marked for deletion...")
                count = db_manager.purge_marked_devices()
                if count >= 0:
                    print(f"[OK] Purged {count} devices")
                    return 0
                else:
                    print("[FAIL] Purge failed")
                    return 1
            
            elif args.db_status:
                print("Database Status:")
                print("-" * 60)
                status = db_manager.get_database_status()
                print(f"Enabled: {status['enabled']}")
                print(f"Connected: {status['connected']}")
                if status['enabled']:
                    print(f"Server: {status['server']}")
                    print(f"Database: {status['database']}")
                    if status['connected']:
                        print("\nRecord Counts:")
                        for table, count in status['record_counts'].items():
                            print(f"  {table}: {count}")
                return 0
        
        # Convert arguments to configuration overrides
        cli_config = convert_args_to_config(args)
        
        # Initialize and run NetWalker application
        with NetWalkerApp(config_file=args.config, cli_args=cli_config) as app:
            _app_instance = app  # Store for signal handler
            
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
    
    finally:
        _app_instance = None


if __name__ == "__main__":
    sys.exit(main())