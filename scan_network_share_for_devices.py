"""
Scan Network Share for Device Names
Extracts device names from filenames and adds new devices to found_seed.csv

Author: Mark Oldham
"""

import os
import sys
import logging
import csv
import base64
from pathlib import Path
from typing import Set, List
import pyodbc
import configparser

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class NetworkShareScanner:
    """Scans network share for device names"""
    
    def __init__(self, config_file: str = "netwalker.ini"):
        """Initialize scanner with database config"""
        self.config = self._load_config(config_file)
        self.connection = None
    
    def _load_config(self, config_file: str) -> dict:
        """Load database configuration from INI file"""
        config = configparser.ConfigParser()
        
        if not Path(config_file).exists():
            logger.error(f"Config file not found: {config_file}")
            sys.exit(1)
        
        config.read(config_file)
        
        # Extract database config
        db_config = {
            'server': config.get('database', 'server'),
            'port': config.get('database', 'port'),
            'database': config.get('database', 'database'),
            'username': config.get('database', 'username'),
            'password': config.get('database', 'password'),
        }
        
        # Decrypt password if encrypted
        if db_config['password'].startswith('ENC:'):
            encoded = db_config['password'][4:]
            db_config['password'] = base64.b64decode(encoded.encode()).decode()
        
        return db_config
    
    def connect_database(self) -> bool:
        """Connect to NetWalker database"""
        try:
            connection_string = (
                f"DRIVER={{SQL Server}};"
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
    
    def disconnect_database(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def get_existing_devices(self) -> Set[str]:
        """Get all device names from database"""
        try:
            cursor = self.connection.cursor()
            
            query = "SELECT DISTINCT device_name FROM devices"
            cursor.execute(query)
            
            devices = {row[0].upper() for row in cursor.fetchall()}
            cursor.close()
            
            logger.info(f"Retrieved {len(devices)} existing devices from database")
            return devices
            
        except Exception as e:
            logger.error(f"Failed to retrieve devices: {e}")
            return set()
    
    def scan_network_share(self, share_path: str) -> List[str]:
        """
        Scan network share and extract device names from filenames
        
        Args:
            share_path: UNC path to network share
            
        Returns:
            List of device names extracted from filenames
        """
        device_names = []
        
        try:
            logger.info(f"Scanning network share: {share_path}")
            
            # Check if path exists
            if not os.path.exists(share_path):
                logger.error(f"Network share not accessible: {share_path}")
                return device_names
            
            # List all files in directory
            files = os.listdir(share_path)
            logger.info(f"Found {len(files)} files in share")
            
            # Extract device names
            for filename in files:
                # Skip directories
                full_path = os.path.join(share_path, filename)
                if os.path.isdir(full_path):
                    continue
                
                # Extract device name (part before "__")
                if "__" in filename:
                    device_name = filename.split("__")[0]
                    device_names.append(device_name.upper())
                    logger.debug(f"Extracted device name: {device_name}")
                else:
                    logger.debug(f"Skipping file (no '__' delimiter): {filename}")
            
            logger.info(f"Extracted {len(device_names)} device names from filenames")
            return device_names
            
        except Exception as e:
            logger.error(f"Failed to scan network share: {e}")
            return device_names
    
    def write_new_devices_to_csv(self, new_devices: List[str], output_file: str = "found_seed.csv"):
        """
        Write new devices to CSV file
        
        Args:
            new_devices: List of device names not in database
            output_file: Output CSV filename
        """
        try:
            # Check if file exists
            file_exists = Path(output_file).exists()
            
            # Open file in append mode
            with open(output_file, 'a', newline='') as f:
                writer = csv.writer(f)
                
                # Write header if new file
                if not file_exists:
                    writer.writerow(['hostname', 'ip_address', 'status'])
                    logger.info(f"Created new file: {output_file}")
                
                # Write device names
                for device_name in sorted(new_devices):
                    writer.writerow([device_name, '', 'pending'])
                
            logger.info(f"Wrote {len(new_devices)} new devices to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to write CSV file: {e}")


def main():
    """Main program entry point"""
    
    # Configuration
    NETWORK_SHARE = r"\\EIT-PRINWUTIL01\TestTest$"
    OUTPUT_FILE = "found_seed.csv"
    
    print("=" * 70)
    print("Network Share Device Scanner")
    print("=" * 70)
    print()
    
    try:
        # Initialize scanner
        scanner = NetworkShareScanner()
        
        # Connect to database
        logger.info("Connecting to database...")
        if not scanner.connect_database():
            logger.error("Failed to connect to database")
            return 1
        
        # Get existing devices from database
        logger.info("Retrieving existing devices from database...")
        existing_devices = scanner.get_existing_devices()
        
        # Scan network share
        logger.info(f"Scanning network share: {NETWORK_SHARE}")
        found_devices = scanner.scan_network_share(NETWORK_SHARE)
        
        if not found_devices:
            logger.warning("No devices found in network share")
            scanner.disconnect_database()
            return 0
        
        # Find new devices (not in database)
        new_devices = [d for d in found_devices if d not in existing_devices]
        
        # Remove duplicates
        new_devices = list(set(new_devices))
        
        logger.info(f"Found {len(found_devices)} total devices in share")
        logger.info(f"Found {len(existing_devices)} existing devices in database")
        logger.info(f"Found {len(new_devices)} NEW devices not in database")
        
        if new_devices:
            # Write new devices to CSV
            logger.info(f"Writing new devices to {OUTPUT_FILE}...")
            scanner.write_new_devices_to_csv(new_devices, OUTPUT_FILE)
            
            print()
            print(f"[OK] Found {len(new_devices)} new devices")
            print(f"[OK] Saved to: {OUTPUT_FILE}")
            print()
            print("New devices:")
            for device in sorted(new_devices):
                print(f"  - {device}")
        else:
            print()
            print("[INFO] No new devices found - all devices already in database")
        
        # Disconnect
        scanner.disconnect_database()
        
        print()
        print("Scan complete!")
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
