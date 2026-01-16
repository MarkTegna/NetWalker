"""
Configuration Manager for NetWalker
"""

import configparser
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from .data_models import (
    DiscoveryConfig, FilterConfig, OutputConfig, 
    ExclusionConfig, ConnectionConfig, VLANCollectionConfig
)
from .blank_detection import ConfigurationBlankHandler


class ConfigurationManager:
    """Manages configuration loading, CLI overrides, and default generation"""
    
    def __init__(self, config_file: str = "netwalker.ini"):
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        self._config = configparser.ConfigParser()
        self._cli_overrides = {}
        
    def load_configuration(self, cli_args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load configuration from INI file with CLI overrides
        
        Args:
            cli_args: Dictionary of CLI arguments to override INI settings
            
        Returns:
            Dictionary containing all configuration sections
        """
        # Store CLI overrides
        if cli_args:
            self._cli_overrides = {k: v for k, v in cli_args.items() if v is not None}
        
        # Create default config if file doesn't exist
        if not os.path.exists(self.config_file):
            self.logger.warning(f"Configuration file {self.config_file} not found. Creating default configuration.")
            self.create_default_config()
        
        # Load configuration file
        self._config.read(self.config_file)
        
        # Build configuration objects with CLI overrides
        config = {
            'discovery': self._build_discovery_config(),
            'filtering': self._build_filter_config(),
            'exclusions': self._build_exclusion_config(),
            'output': self._build_output_config(),
            'connection': self._build_connection_config(),
            'vlan_collection': self._build_vlan_collection_config(),
            'database': self._build_database_config()
        }
        
        self.logger.info(f"Configuration loaded from {self.config_file}")
        if self._cli_overrides:
            self.logger.info(f"CLI overrides applied: {self._cli_overrides}")
            
        return config
    
    def create_default_config(self):
        """Generate default configuration file with all options and descriptions"""
        config_content = """# NetWalker Configuration File
# Author: Mark Oldham

[discovery]
# Maximum depth for recursive discovery
max_depth = 1
# Number of concurrent device connections
concurrent_connections = 5
# Connection timeout in seconds
connection_timeout = 30
# Total discovery process timeout in seconds
discovery_timeout = 300
# Discovery protocols to use (comma-separated)
discovery_protocols = CDP,LLDP
# Enable progress tracking display (true/false)
enable_progress_tracking = true

[filtering]
# Include devices matching these wildcards (comma-separated)
include_wildcards = *
# Exclude devices matching these wildcards (comma-separated)
exclude_wildcards = 
# Include devices in these CIDR ranges (comma-separated)
include_cidrs = 
# Exclude devices in these CIDR ranges (comma-separated)
exclude_cidrs = 

[exclusions]
# Exclude devices with these hostname patterns (comma-separated)
exclude_hostnames = 
# Exclude devices in these IP ranges (comma-separated)
exclude_ip_ranges = 
# Exclude devices with these platforms (comma-separated)
exclude_platforms = linux,windows,unix,freebsd,openbsd,netbsd,solaris,aix,hp-ux,vmware,docker,kubernetes,host phone,camera,printer,access point,wireless,server
# Exclude devices with these capabilities (comma-separated)
exclude_capabilities = host phone,camera,printer,server

[output]
# Directory for report files
reports_directory = ./reports
# Directory for log files
logs_directory = ./logs
# Excel file format
excel_format = xlsx
# Enable Visio diagram generation (true/false)
visio_enabled = true
# Site boundary pattern for creating separate workbooks (wildcard pattern)
site_boundary_pattern = *-CORE-*

[connection]
# SSH port number
ssh_port = 22
# Telnet port number
telnet_port = 23
# Preferred connection method (ssh/telnet)
preferred_method = ssh
# SSL certificate verification (true/false)
ssl_verify = false
# SSL certificate file path (optional)
ssl_cert_file = 
# SSL key file path (optional)
ssl_key_file = 
# SSL CA bundle file path (optional)
ssl_ca_bundle = 

[vlan_collection]
# Enable VLAN collection during discovery (true/false)
enabled = true
# Timeout for VLAN commands in seconds
command_timeout = 30
# Maximum retries for failed VLAN commands
max_retries = 2
# Include inactive VLANs in collection (true/false)
include_inactive_vlans = true
# Platforms to skip for VLAN collection (comma-separated)
# platforms_to_skip = 

[database]
# Enable database inventory tracking (true/false)
enabled = false
# SQL Server hostname or IP address
server = eit-prisqldb01.tgna.tegna.com
# SQL Server port number
port = 1433
# Database name
database = NetWalker
# SQL Server username
username = NetWalker
# SQL Server password
password = FluffyBunnyHitbyaBus
# Trust server certificate for internal networks (true/false)
trust_server_certificate = true
# Connection timeout in seconds
connection_timeout = 30
# Command timeout in seconds
command_timeout = 60
"""
        
        # Write configuration file
        with open(self.config_file, 'w') as f:
            f.write(config_content)
            
        self.logger.info(f"Default configuration created: {self.config_file}")
    
    def _build_discovery_config(self) -> DiscoveryConfig:
        """Build discovery configuration with CLI overrides"""
        config = DiscoveryConfig()
        
        if self._config.has_section('discovery'):
            config.max_depth = self._config.getint('discovery', 'max_depth', fallback=config.max_depth)
            config.concurrent_connections = self._config.getint('discovery', 'concurrent_connections', fallback=config.concurrent_connections)
            config.connection_timeout = self._config.getint('discovery', 'connection_timeout', fallback=config.connection_timeout)
            config.discovery_timeout = self._config.getint('discovery', 'discovery_timeout', fallback=config.discovery_timeout)
            config.enable_progress_tracking = self._config.getboolean('discovery', 'enable_progress_tracking', fallback=config.enable_progress_tracking)
            
            protocols_str = self._config.get('discovery', 'discovery_protocols', fallback='CDP,LLDP')
            config.protocols = [p.strip() for p in protocols_str.split(',') if p.strip()]
        
        # Apply CLI overrides
        if 'max_depth' in self._cli_overrides:
            config.max_depth = self._cli_overrides['max_depth']
        if 'concurrent_connections' in self._cli_overrides:
            config.concurrent_connections = self._cli_overrides['concurrent_connections']
        if 'timeout' in self._cli_overrides:
            config.connection_timeout = self._cli_overrides['timeout']
        if 'discovery_timeout' in self._cli_overrides:
            config.discovery_timeout = self._cli_overrides['discovery_timeout']
        if 'enable_progress_tracking' in self._cli_overrides:
            config.enable_progress_tracking = self._cli_overrides['enable_progress_tracking']
            
        return config
    
    def _build_filter_config(self) -> FilterConfig:
        """Build filter configuration"""
        config = FilterConfig()
        
        if self._config.has_section('filtering'):
            include_wildcards = self._config.get('filtering', 'include_wildcards', fallback='*')
            config.include_wildcards = [w.strip() for w in include_wildcards.split(',') if w.strip()]
            
            exclude_wildcards = self._config.get('filtering', 'exclude_wildcards', fallback='')
            config.exclude_wildcards = [w.strip() for w in exclude_wildcards.split(',') if w.strip()]
            
            include_cidrs = self._config.get('filtering', 'include_cidrs', fallback='')
            config.include_cidrs = [c.strip() for c in include_cidrs.split(',') if c.strip()]
            
            exclude_cidrs = self._config.get('filtering', 'exclude_cidrs', fallback='')
            config.exclude_cidrs = [c.strip() for c in exclude_cidrs.split(',') if c.strip()]
            
        return config
    
    def _build_exclusion_config(self) -> ExclusionConfig:
        """Build exclusion configuration"""
        config = ExclusionConfig()
        
        if self._config.has_section('exclusions'):
            exclude_hostnames = self._config.get('exclusions', 'exclude_hostnames', fallback='')
            if exclude_hostnames:
                config.exclude_hostnames = [h.strip() for h in exclude_hostnames.split(',') if h.strip()]
            else:
                config.exclude_hostnames = []  # Empty list if explicitly empty in INI
            
            exclude_ip_ranges = self._config.get('exclusions', 'exclude_ip_ranges', fallback='')
            if exclude_ip_ranges:
                config.exclude_ip_ranges = [r.strip() for r in exclude_ip_ranges.split(',') if r.strip()]
            else:
                config.exclude_ip_ranges = []  # Empty list if explicitly empty in INI
            
            exclude_platforms = self._config.get('exclusions', 'exclude_platforms', fallback='')
            if exclude_platforms:
                config.exclude_platforms = [p.strip() for p in exclude_platforms.split(',') if p.strip()]
            
            exclude_capabilities = self._config.get('exclusions', 'exclude_capabilities', fallback='')
            if exclude_capabilities:
                config.exclude_capabilities = [c.strip() for c in exclude_capabilities.split(',') if c.strip()]
                
        return config
    
    def _build_output_config(self) -> OutputConfig:
        """Build output configuration with CLI overrides"""
        config = OutputConfig()
        
        if self._config.has_section('output'):
            config.reports_directory = self._config.get('output', 'reports_directory', fallback=config.reports_directory)
            config.logs_directory = self._config.get('output', 'logs_directory', fallback=config.logs_directory)
            config.excel_format = self._config.get('output', 'excel_format', fallback=config.excel_format)
            config.visio_enabled = self._config.getboolean('output', 'visio_enabled', fallback=config.visio_enabled)
            
            # Handle site boundary pattern with proper blank detection and Unicode support
            # Use has_option to distinguish between missing and blank values
            raw_pattern = None
            if self._config.has_option('output', 'site_boundary_pattern'):
                # Option exists - get its value (could be blank)
                raw_pattern = self._config.get('output', 'site_boundary_pattern')
            # If option doesn't exist, raw_pattern remains None (missing)
            
            config.site_boundary_pattern = ConfigurationBlankHandler.process_site_boundary_pattern_with_unicode(
                raw_pattern, 
                default_pattern="*-CORE-*",
                logger=self.logger
            )
        
        # Apply CLI overrides
        if 'reports_dir' in self._cli_overrides:
            config.reports_directory = self._cli_overrides['reports_dir']
        if 'logs_dir' in self._cli_overrides:
            config.logs_directory = self._cli_overrides['logs_dir']
        if 'site_boundary_pattern' in self._cli_overrides:
            # CLI override for site boundary pattern - process through blank detection with Unicode support
            cli_pattern = self._cli_overrides['site_boundary_pattern']
            config.site_boundary_pattern = ConfigurationBlankHandler.process_site_boundary_pattern_with_unicode(
                cli_pattern,
                default_pattern="*-CORE-*",
                logger=self.logger
            )
            self.logger.info(f"Site boundary pattern overridden by CLI: {cli_pattern} -> {config.site_boundary_pattern}")
            
        return config
    
    def _build_connection_config(self) -> ConnectionConfig:
        """Build connection configuration"""
        config = ConnectionConfig()
        
        if self._config.has_section('connection'):
            config.ssh_port = self._config.getint('connection', 'ssh_port', fallback=config.ssh_port)
            config.telnet_port = self._config.getint('connection', 'telnet_port', fallback=config.telnet_port)
            config.preferred_method = self._config.get('connection', 'preferred_method', fallback=config.preferred_method)
            config.ssl_verify = self._config.getboolean('connection', 'ssl_verify', fallback=config.ssl_verify)
            config.ssl_cert_file = self._config.get('connection', 'ssl_cert_file', fallback=config.ssl_cert_file)
            config.ssl_key_file = self._config.get('connection', 'ssl_key_file', fallback=config.ssl_key_file)
            config.ssl_ca_bundle = self._config.get('connection', 'ssl_ca_bundle', fallback=config.ssl_ca_bundle)
            
            # Convert empty strings to None for optional SSL file paths
            if config.ssl_cert_file == '':
                config.ssl_cert_file = None
            if config.ssl_key_file == '':
                config.ssl_key_file = None
            if config.ssl_ca_bundle == '':
                config.ssl_ca_bundle = None
            
        return config
    
    def _build_vlan_collection_config(self) -> VLANCollectionConfig:
        """Build VLAN collection configuration with CLI overrides"""
        config = VLANCollectionConfig()
        
        if self._config.has_section('vlan_collection'):
            config.enabled = self._config.getboolean('vlan_collection', 'enabled', fallback=config.enabled)
            config.command_timeout = self._config.getint('vlan_collection', 'command_timeout', fallback=config.command_timeout)
            config.max_retries = self._config.getint('vlan_collection', 'max_retries', fallback=config.max_retries)
            config.include_inactive_vlans = self._config.getboolean('vlan_collection', 'include_inactive_vlans', fallback=config.include_inactive_vlans)
            
            platforms_to_skip = self._config.get('vlan_collection', 'platforms_to_skip', fallback='')
            if platforms_to_skip:
                config.platforms_to_skip = [p.strip() for p in platforms_to_skip.split(',') if p.strip()]
            else:
                config.platforms_to_skip = []
        
        # Apply CLI overrides
        if 'vlan_enabled' in self._cli_overrides:
            config.enabled = self._cli_overrides['vlan_enabled']
        if 'vlan_timeout' in self._cli_overrides:
            config.command_timeout = self._cli_overrides['vlan_timeout']
        if 'vlan_retries' in self._cli_overrides:
            config.max_retries = self._cli_overrides['vlan_retries']
        if 'vlan_include_inactive' in self._cli_overrides:
            config.include_inactive_vlans = self._cli_overrides['vlan_include_inactive']
            
        return config
    
    def _build_database_config(self) -> Dict[str, Any]:
        """Build database configuration with password encryption support"""
        config = {
            'enabled': False,
            'server': 'eit-prisqldb01.tgna.tegna.com',
            'port': 1433,
            'database': 'NetWalker',
            'username': 'NetWalker',
            'password': 'FluffyBunnyHitbyaBus',
            'trust_server_certificate': True,
            'connection_timeout': 30,
            'command_timeout': 60
        }
        
        if self._config.has_section('database'):
            config['enabled'] = self._config.getboolean('database', 'enabled', fallback=config['enabled'])
            config['server'] = self._config.get('database', 'server', fallback=config['server'])
            config['port'] = self._config.getint('database', 'port', fallback=config['port'])
            config['database'] = self._config.get('database', 'database', fallback=config['database'])
            config['username'] = self._config.get('database', 'username', fallback=config['username'])
            
            # Get password and handle encryption
            raw_password = self._config.get('database', 'password', fallback=config['password'])
            
            # Check if password needs encryption
            if raw_password and not self._is_encrypted(raw_password):
                self.logger.info("Database password is not encrypted - encrypting and updating config file")
                encrypted_password = self._encrypt_password(raw_password)
                
                # Update config file with encrypted password
                self._config.set('database', 'password', encrypted_password)
                try:
                    with open(self.config_file, 'w') as f:
                        self._config.write(f)
                    self.logger.info("Updated config file with encrypted database password")
                except Exception as e:
                    self.logger.warning(f"Could not update config file with encrypted password: {e}")
                
                config['password'] = raw_password  # Use decrypted password in config
            elif raw_password and self._is_encrypted(raw_password):
                # Decrypt password for use
                config['password'] = self._decrypt_password(raw_password)
            else:
                config['password'] = raw_password
            
            config['trust_server_certificate'] = self._config.getboolean('database', 'trust_server_certificate', fallback=config['trust_server_certificate'])
            config['connection_timeout'] = self._config.getint('database', 'connection_timeout', fallback=config['connection_timeout'])
            config['command_timeout'] = self._config.getint('database', 'command_timeout', fallback=config['command_timeout'])
        
        return config
    
    def _is_encrypted(self, password: str) -> bool:
        """Check if password is in encrypted format (ENC: prefix)"""
        return password.startswith('ENC:') if password else False
    
    def _encrypt_password(self, password: str) -> str:
        """Encrypt password using base64 encoding"""
        import base64
        encoded = base64.b64encode(password.encode('utf-8')).decode('utf-8')
        return f"ENC:{encoded}"
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt password from base64 encoding"""
        import base64
        try:
            if encrypted_password.startswith('ENC:'):
                encoded = encrypted_password[4:]  # Remove 'ENC:' prefix
                decoded = base64.b64decode(encoded).decode('utf-8')
                return decoded
            return encrypted_password
        except Exception as e:
            self.logger.error(f"Failed to decrypt password: {e}")
            return encrypted_password
    
    def get_site_boundary_pattern(self) -> Optional[str]:
        """
        Get site boundary pattern with proper blank handling and CLI override support.
        
        This method provides direct access to the site boundary pattern
        with proper blank value detection and handling. It distinguishes
        between missing values (which get fallback) and explicitly blank
        values (which disable the feature).
        
        Precedence order:
        1. CLI overrides (highest priority)
        2. Configuration file values
        3. Default values (lowest priority)
        
        Returns:
            Optional[str]: The site boundary pattern or None if disabled
                - None: Site boundary detection is disabled (blank pattern)
                - str: Site boundary detection is enabled with the pattern
        """
        # Check for CLI override first (highest precedence)
        if 'site_boundary_pattern' in self._cli_overrides:
            cli_pattern = self._cli_overrides['site_boundary_pattern']
            processed_pattern = ConfigurationBlankHandler.process_site_boundary_pattern_with_unicode(
                cli_pattern,
                default_pattern="*-CORE-*",
                logger=self.logger
            )
            self.logger.info(f"Using CLI override for site boundary pattern: {cli_pattern} -> {processed_pattern}")
            return processed_pattern
        
        # Ensure configuration is loaded
        if not self._config.sections():
            self._config.read(self.config_file)
        
        # Load the raw value without any fallback to distinguish missing vs blank
        raw_value = None
        if self._config.has_section('output') and self._config.has_option('output', 'site_boundary_pattern'):
            # Option exists - get its value (could be blank)
            raw_value = self._config.get('output', 'site_boundary_pattern')
        # If option doesn't exist, raw_value remains None (missing)
        
        # Process with blank detection and Unicode handling - this handles the distinction
        processed_pattern = ConfigurationBlankHandler.process_site_boundary_pattern_with_unicode(
            raw_value,
            default_pattern="*-CORE-*",
            logger=self.logger
        )
        
        # Log the final decision for debugging
        if processed_pattern is None:
            self.logger.info("Site boundary detection is DISABLED due to blank pattern")
        else:
            self.logger.info(f"Site boundary detection is ENABLED with pattern: {processed_pattern}")
        
        return processed_pattern