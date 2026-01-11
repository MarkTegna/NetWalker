"""
NetWalker Main Application

The main NetWalker application class that coordinates all components for network discovery.
Provides the primary interface for network topology discovery and reporting.
"""

import logging
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from .config.config_manager import ConfigurationManager
from .config.credentials import CredentialManager
from .connection.connection_manager import ConnectionManager
from .filtering.filter_manager import FilterManager
from .discovery.discovery_engine import DiscoveryEngine
from .discovery.thread_manager import ThreadManager
from .reports.excel_generator import ExcelReportGenerator
from .output.output_manager import OutputManager
from .logging_config import setup_logging
from .version import __version__, __author__, __compile_date__

logger = logging.getLogger(__name__)


class NetWalkerApp:
    """
    Main NetWalker application class.
    
    Coordinates all components to perform network topology discovery:
    - Configuration management
    - Device connections
    - Protocol parsing and discovery
    - Filtering and boundary management
    - Report generation
    - Output management
    """
    
    def __init__(self, config_file: Optional[str] = None, cli_args: Optional[Dict[str, Any]] = None):
        """
        Initialize NetWalker application.
        
        Args:
            config_file: Path to configuration file (optional)
            cli_args: Command-line arguments (optional)
        """
        self.config_file = config_file or "netwalker.ini"
        self.cli_args = cli_args or {}
        
        # Initialize components
        self.config_manager: Optional[ConfigurationManager] = None
        self.credential_manager: Optional[CredentialManager] = None
        self.output_manager: Optional[OutputManager] = None
        self.connection_manager: Optional[ConnectionManager] = None
        self.filter_manager: Optional[FilterManager] = None
        self.discovery_engine: Optional[DiscoveryEngine] = None
        self.thread_manager: Optional[ThreadManager] = None
        self.excel_generator: Optional[ExcelReportGenerator] = None
        
        # Application state
        self.initialized = False
        self.discovery_results: Dict[str, Any] = {}
        self.seed_devices: List[str] = []
        
        logger.info(f"NetWalker v{__version__} by {__author__}")
        logger.info(f"Compile date: {__compile_date__}")
    
    def initialize(self) -> bool:
        """
        Initialize all application components.
        
        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing NetWalker application...")
            
            # Initialize configuration
            logger.info("Step 1: Initializing configuration...")
            self._initialize_configuration()
            
            # Initialize output management
            logger.info("Step 2: Initializing output management...")
            self._initialize_output_management()
            
            # Setup logging with output directories
            logger.info("Step 3: Setting up application logging...")
            self._setup_application_logging()
            
            # Initialize credentials
            logger.info("Step 4: Initializing credentials...")
            self._initialize_credentials()
            
            # Initialize connection management
            logger.info("Step 5: Initializing connection management...")
            self._initialize_connection_management()
            
            # Initialize filtering
            logger.info("Step 6: Initializing filtering...")
            self._initialize_filtering()
            
            # Initialize discovery engine
            logger.info("Step 7: Initializing discovery engine...")
            self._initialize_discovery_engine()
            
            # Initialize threading
            logger.info("Step 8: Initializing threading...")
            self._initialize_threading()
            
            # Initialize reporting
            logger.info("Step 9: Initializing reporting...")
            self._initialize_reporting()
            
            # Load seed devices
            logger.info("Step 10: Loading seed devices...")
            self._load_seed_devices()
            
            self.initialized = True
            logger.info("NetWalker application initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize NetWalker application: {e}")
            logger.exception("Initialization error details:")
            return False
    
    def _initialize_configuration(self):
        """Initialize configuration management"""
        # For now, create a simple flat configuration
        # TODO: Integrate with full ConfigurationManager later
        
        # Default configuration
        self.config = {
            'reports_directory': './reports',
            'logs_directory': './logs',
            'temp_directory': './temp',
            'backup_directory': './backup',
            'max_discovery_depth': 5,
            'discovery_timeout_seconds': 300,
            'max_concurrent_connections': 10,
            'connection_timeout_seconds': 30,
            'task_timeout_seconds': 60,
            'hostname_excludes': ['LUMT*', 'LUMV*'],
            'ip_excludes': ['10.70.0.0/16'],
            'platform_excludes': ['linux', 'windows', 'unix', 'server'],
            'capability_excludes': ['host', 'phone', 'camera', 'printer', 'ap'],
            'log_level': 'INFO',
            'console_logging': True
        }
        
        # Apply CLI overrides
        if self.cli_args:
            self.config.update({k: v for k, v in self.cli_args.items() if v is not None})
        
        logger.info(f"Configuration initialized with defaults and CLI overrides")
    
    def _initialize_output_management(self):
        """Initialize output directory management"""
        self.output_manager = OutputManager(self.config)
        
        # Validate output configuration
        if not self.output_manager.validate_configuration():
            raise RuntimeError("Output directory configuration validation failed")
    
    def _setup_application_logging(self):
        """Setup application logging with proper output directories"""
        log_directory = self.output_manager.get_logs_directory()
        
        # Update logging configuration with actual log directory
        setup_logging(
            logs_directory=log_directory,
            log_level=getattr(logging, self.config.get('log_level', 'INFO'))
        )
        
        logger.info(f"Logging configured - directory: {log_directory}")
    
    def _initialize_credentials(self):
        """Initialize credential management"""
        # CredentialManager expects a file path and CLI config
        credentials_file = self.config.get('credentials_file', 'secret_creds.ini')
        self.credential_manager = CredentialManager(credentials_file, self.config)
        logger.info("Credential management initialized")
    
    def _initialize_connection_management(self):
        """Initialize connection management"""
        self.credentials = self.credential_manager.get_credentials()
        
        # Extract connection parameters from config
        ssh_port = self.config.get('ssh_port', 22)
        telnet_port = self.config.get('telnet_port', 23)
        timeout = self.config.get('connection_timeout_seconds', 30)
        
        self.connection_manager = ConnectionManager(ssh_port, telnet_port, timeout)
        logger.info("Connection management initialized")
    
    def _initialize_filtering(self):
        """Initialize filtering and boundary management"""
        self.filter_manager = FilterManager(self.config)
        
        stats = self.filter_manager.get_filter_stats()
        logger.info(f"Filtering initialized - {stats['hostname_patterns']} hostname patterns, "
                   f"{stats['ip_ranges']} IP ranges")
    
    def _initialize_discovery_engine(self):
        """Initialize discovery engine"""
        self.discovery_engine = DiscoveryEngine(
            self.connection_manager,
            self.filter_manager,
            self.config,
            self.credentials
        )
        logger.info("Discovery engine initialized")
    
    def _initialize_threading(self):
        """Initialize thread management"""
        self.thread_manager = ThreadManager(self.config)
        logger.info(f"Thread management initialized - max connections: "
                   f"{self.config.get('max_concurrent_connections', 10)}")
    
    def _initialize_reporting(self):
        """Initialize report generation"""
        # Update config with output directory
        config_with_reports = self.config.copy()
        config_with_reports['reports_directory'] = self.output_manager.get_reports_directory()
        
        self.excel_generator = ExcelReportGenerator(config_with_reports)
        logger.info("Report generation initialized")
    
    def _load_seed_devices(self):
        """Load seed devices from configuration"""
        # First check for CLI-provided seed devices (highest priority)
        seed_config = self.config.get('seed_devices', '')
        if seed_config:
            self.seed_devices = [device.strip() for device in seed_config.split(',')]
            logger.info(f"Loaded {len(self.seed_devices)} seed devices from CLI arguments")
            return
        
        # If no CLI seed devices, try to load from seed_device.ini or seed_file.csv
        seed_files = ['seed_device.ini', 'seed_file.csv']
        
        for seed_file in seed_files:
            if os.path.exists(seed_file):
                self.seed_devices = self._parse_seed_file(seed_file)
                logger.info(f"Loaded {len(self.seed_devices)} seed devices from {seed_file}")
                break
        
        if not self.seed_devices:
            logger.warning("No seed devices configured")
    
    def _parse_seed_file(self, filename: str) -> List[str]:
        """Parse seed device file"""
        seed_devices = []
        
        try:
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Handle CSV format
                        if ',' in line:
                            parts = line.split(',')
                            hostname = parts[0].strip()
                            ip_address = parts[1].strip() if len(parts) > 1 else hostname
                        else:
                            # Simple hostname/IP format
                            hostname = line
                            ip_address = line
                        
                        seed_devices.append(f"{hostname}:{ip_address}")
        
        except Exception as e:
            logger.error(f"Failed to parse seed file {filename}: {e}")
        
        return seed_devices
    
    def discover_network(self) -> Dict[str, Any]:
        """
        Execute network topology discovery.
        
        Returns:
            Discovery results summary
        """
        if not self.initialized:
            raise RuntimeError("NetWalker application not initialized")
        
        if not self.seed_devices:
            raise RuntimeError("No seed devices configured")
        
        logger.info(f"Starting network discovery with {len(self.seed_devices)} seed devices")
        
        try:
            # Add seed devices to discovery engine
            for seed_device in self.seed_devices:
                if ':' in seed_device:
                    hostname, ip_address = seed_device.split(':', 1)
                else:
                    hostname = ip_address = seed_device
                
                self.discovery_engine.add_seed_device(hostname, ip_address)
            
            # Execute discovery
            self.discovery_results = self.discovery_engine.discover_topology()
            
            logger.info(f"Discovery completed - found {self.discovery_results.get('total_devices', 0)} devices")
            return self.discovery_results
            
        except Exception as e:
            logger.error(f"Network discovery failed: {e}")
            raise
    
    def generate_reports(self) -> List[str]:
        """
        Generate discovery reports.
        
        Returns:
            List of generated report file paths
        """
        if not self.discovery_results:
            raise RuntimeError("No discovery results available - run discover_network() first")
        
        logger.info("Generating discovery reports...")
        
        try:
            report_files = []
            
            # Get device inventory
            inventory = self.discovery_engine.get_inventory().get_all_devices()
            
            # Generate main discovery report and per-seed reports
            discovery_reports = self.excel_generator.generate_discovery_report(
                inventory,
                self.discovery_results,
                self.seed_devices
            )
            report_files.extend(discovery_reports)
            
            logger.info(f"Generated {len(discovery_reports)} discovery reports")
            
            # Always generate inventory workbook (separate from discovery report)
            inventory_path = self.excel_generator.generate_inventory_report(inventory)
            report_files.append(inventory_path)
            logger.info(f"Generated inventory report: {inventory_path}")
            
            return report_files
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise
    
    def run_discovery(self) -> bool:
        """
        Run complete discovery process (discover + report).
        
        Returns:
            True if successful
        """
        try:
            # Execute discovery
            results = self.discover_network()
            
            # Generate reports
            report_files = self.generate_reports()
            
            # Print summary
            self._print_discovery_summary(results, report_files)
            
            return True
            
        except Exception as e:
            logger.error(f"Discovery process failed: {e}")
            return False
    
    def _print_discovery_summary(self, results: Dict[str, Any], report_files: List[str]):
        """Print discovery summary to console"""
        print("\n" + "="*60)
        print("NetWalker Discovery Summary")
        print("="*60)
        print(f"Discovery Time: {results.get('discovery_time_seconds', 0):.2f} seconds")
        print(f"Total Devices: {results.get('total_devices', 0)}")
        print(f"Successful Connections: {results.get('successful_connections', 0)}")
        print(f"Failed Connections: {results.get('failed_connections', 0)}")
        print(f"Filtered Devices: {results.get('filtered_devices', 0)}")
        print(f"Maximum Depth: {results.get('max_depth_reached', 0)}")
        print("\nGenerated Reports:")
        for report_file in report_files:
            print(f"  - {report_file}")
        print("="*60)
    
    def cleanup(self):
        """Cleanup application resources"""
        try:
            if self.thread_manager:
                self.thread_manager.stop()
            
            if self.output_manager:
                self.output_manager.cleanup_temp_files()
            
            logger.info("NetWalker application cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_version_info(self) -> Dict[str, str]:
        """Get version information"""
        return {
            'version': __version__,
            'author': __author__,
            'compile_date': __compile_date__
        }
    
    def __enter__(self):
        """Context manager entry"""
        if not self.initialize():
            raise RuntimeError("Failed to initialize NetWalker application")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()