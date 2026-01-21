"""
NetWalker Visio Diagram Generator
Standalone program to generate network topology diagrams from NetWalker database

Author: Mark Oldham
"""

import sys
import logging
import argparse
import configparser
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pyodbc

from netwalker.reports.visio_generator import VisioGenerator
from netwalker.version import __version__, __author__

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class NetWalkerVisioDB:
    """Database interface for NetWalker Visio diagram generation"""
    
    def __init__(self, config: Dict[str, str]):
        """
        Initialize database connection
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config
        self.connection = None
        
    def connect(self) -> bool:
        """
        Connect to NetWalker database
        
        Returns:
            True if connection successful
        """
        try:
            connection_string = (
                f"DRIVER={{{self.config['driver']}}};"
                f"SERVER={self.config['server']},{self.config['port']};"
                f"DATABASE={self.config['database']};"
                f"UID={self.config['username']};"
                f"PWD={self.config['password']};"
                "TrustServerCertificate=yes;"
                "Connection Timeout=30;"
            )
            
            self.connection = pyodbc.connect(connection_string)
            logger.info(f"Connected to database: {self.config['server']}/{self.config['database']}")
            return True
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def get_active_devices(self) -> List[Dict]:
        """
        Get all active devices from database
        
        Returns:
            List of device dictionaries
        """
        try:
            cursor = self.connection.cursor()
            
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
            return devices
            
        except Exception as e:
            logger.error(f"Failed to retrieve devices: {e}")
            return []
    
    def get_device_connections(self) -> List[Tuple[str, str, str, str]]:
        """
        Get device connections from database
        
        NOTE: Currently NetWalker database does not store connection/neighbor data.
        This method returns an empty list. To add connections, you would need to:
        1. Add a connections/neighbors table to the database
        2. Update NetWalker to store neighbor information during discovery
        3. Update this query to retrieve that data
        
        Returns:
            List of tuples (source_device, source_port, dest_device, dest_port)
        """
        logger.warning("Connection data not available in database - diagrams will show devices only")
        return []
    
    def get_devices_by_site(self) -> Dict[str, List[Dict]]:
        """
        Get devices grouped by site (based on hostname prefix)
        
        Returns:
            Dictionary mapping site names to device lists
        """
        devices = self.get_active_devices()
        devices_by_site = {}
        
        for device in devices:
            device_name = device['device_name']
            
            # Extract site code (first 4 characters of hostname)
            # Adjust this logic based on your naming convention
            if len(device_name) >= 4:
                site_code = device_name[:4].upper()
            else:
                site_code = 'UNKNOWN'
            
            if site_code not in devices_by_site:
                devices_by_site[site_code] = []
            
            devices_by_site[site_code].append(device)
        
        logger.info(f"Grouped devices into {len(devices_by_site)} sites")
        return devices_by_site
    
    def get_connections_by_site(self, devices_by_site: Dict[str, List[Dict]]) -> Dict[str, List[Tuple]]:
        """
        Get connections grouped by site
        
        Args:
            devices_by_site: Dictionary of devices grouped by site
            
        Returns:
            Dictionary mapping site names to connection lists
        """
        all_connections = self.get_device_connections()
        connections_by_site = {}
        
        # Create device to site mapping
        device_to_site = {}
        for site, devices in devices_by_site.items():
            for device in devices:
                device_to_site[device['device_name']] = site
        
        # Group connections by site
        for source_dev, source_port, dest_dev, dest_port in all_connections:
            source_site = device_to_site.get(source_dev)
            dest_site = device_to_site.get(dest_dev)
            
            # Only include connections where both devices are in the same site
            if source_site and source_site == dest_site:
                if source_site not in connections_by_site:
                    connections_by_site[source_site] = []
                
                connections_by_site[source_site].append((
                    source_dev, source_port, dest_dev, dest_port
                ))
        
        return connections_by_site


def load_config(config_file: str) -> Dict[str, str]:
    """
    Load database configuration from INI file
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Database configuration dictionary
    """
    config = configparser.ConfigParser()
    
    # Default configuration
    db_config = {
        'server': 'eit-prisqldb01.tgna.tegna.com',
        'port': '1433',
        'database': 'NetWalker',
        'username': 'NetWalker',
        'password': 'FluffyBunnyHitbyaBus',
        'driver': 'SQL Server'
    }
    
    # Try to load from config file
    if Path(config_file).exists():
        config.read(config_file)
        
        if 'database' in config:
            db_config['server'] = config.get('database', 'server', fallback=db_config['server'])
            db_config['port'] = config.get('database', 'port', fallback=db_config['port'])
            db_config['database'] = config.get('database', 'database', fallback=db_config['database'])
            db_config['username'] = config.get('database', 'username', fallback=db_config['username'])
            db_config['password'] = config.get('database', 'password', fallback=db_config['password'])
            
            # Handle encrypted password
            password = db_config['password']
            if password.startswith('ENC:'):
                import base64
                encoded_part = password[4:]
                db_config['password'] = base64.b64decode(encoded_part.encode()).decode()
        
        logger.info(f"Loaded configuration from {config_file}")
    else:
        logger.warning(f"Configuration file not found: {config_file}, using defaults")
    
    return db_config


def main():
    """Main program entry point"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='NetWalker Visio Diagram Generator - Generate network topology diagrams from database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Generate diagrams for all sites
  python netwalker_visio.py
  
  # Generate diagram for specific site
  python netwalker_visio.py --site BORO
  
  # Specify custom output directory
  python netwalker_visio.py --output ./diagrams
  
  # Use custom config file
  python netwalker_visio.py --config custom.ini

Author: {__author__}
Version: {__version__}
        """
    )
    
    parser.add_argument(
        '--config',
        default='netwalker.ini',
        help='Configuration file path (default: netwalker.ini)'
    )
    
    parser.add_argument(
        '--output',
        default='./visio_diagrams',
        help='Output directory for Visio files (default: ./visio_diagrams)'
    )
    
    parser.add_argument(
        '--site',
        help='Generate diagram for specific site (e.g., BORO) or "EVERYTHING" for all sites'
    )
    
    parser.add_argument(
        '--all-in-one',
        action='store_true',
        help='Generate single diagram with all devices instead of per-site diagrams'
    )
    
    args = parser.parse_args()
    
    # Display banner
    print("=" * 70)
    print(f"NetWalker Visio Diagram Generator v{__version__}")
    print(f"Author: {__author__}")
    print("=" * 70)
    print()
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        db_config = load_config(args.config)
        
        # Connect to database
        logger.info("Connecting to NetWalker database...")
        db = NetWalkerVisioDB(db_config)
        
        if not db.connect():
            logger.error("Failed to connect to database")
            return 1
        
        # Initialize Visio generator
        logger.info(f"Initializing Visio generator (output: {args.output})...")
        visio_gen = VisioGenerator(args.output)
        
        # Generate diagrams
        if args.all_in_one:
            # Generate single diagram with all devices
            logger.info("Generating single diagram with all devices...")
            devices = db.get_active_devices()
            connections = db.get_device_connections()
            
            filepath = visio_gen.generate_topology_diagram(
                devices,
                connections,
                "Complete Network"
            )
            
            if filepath:
                print(f"\n[OK] Generated diagram: {filepath}")
            else:
                print("\n[FAIL] Failed to generate diagram")
                return 1
        
        elif args.site:
            # Check if user wants all sites
            if args.site.upper() == "EVERYTHING":
                # Generate separate diagrams for each site
                logger.info("Generating diagrams for all sites (EVERYTHING specified)...")
                devices_by_site = db.get_devices_by_site()
                connections_by_site = db.get_connections_by_site(devices_by_site)
                
                generated_files = visio_gen.generate_site_diagrams(
                    devices_by_site,
                    connections_by_site
                )
                
                print(f"\n[OK] Generated {len(generated_files)} diagram(s):")
                for filepath in generated_files:
                    print(f"  - {filepath}")
            else:
                # Generate diagram for specific site
                logger.info(f"Generating diagram for site: {args.site}...")
                devices_by_site = db.get_devices_by_site()
                
                if args.site not in devices_by_site:
                    logger.error(f"Site not found: {args.site}")
                    logger.info(f"Available sites: {', '.join(devices_by_site.keys())}")
                    return 1
                
                devices = devices_by_site[args.site]
                connections_by_site = db.get_connections_by_site(devices_by_site)
                connections = connections_by_site.get(args.site, [])
                
                filepath = visio_gen.generate_topology_diagram(
                    devices,
                    connections,
                    args.site
                )
                
                if filepath:
                    print(f"\n[OK] Generated diagram: {filepath}")
                else:
                    print("\n[FAIL] Failed to generate diagram")
                    return 1
        
        else:
            # Generate separate diagrams for each site
            logger.info("Generating diagrams for all sites...")
            devices_by_site = db.get_devices_by_site()
            connections_by_site = db.get_connections_by_site(devices_by_site)
            
            generated_files = visio_gen.generate_site_diagrams(
                devices_by_site,
                connections_by_site
            )
            
            print(f"\n[OK] Generated {len(generated_files)} diagram(s):")
            for filepath in generated_files:
                print(f"  - {filepath}")
        
        # Disconnect from database
        db.disconnect()
        
        print("\nVisio diagram generation complete!")
        return 0
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        return 130
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.exception("Full exception details:")
        return 1


if __name__ == '__main__':
    sys.exit(main())
