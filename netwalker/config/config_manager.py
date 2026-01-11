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
    ExclusionConfig, ConnectionConfig
)


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
            'connection': self._build_connection_config()
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
max_depth = 10
# Number of concurrent device connections
concurrent_connections = 5
# Connection timeout in seconds
connection_timeout = 30
# Discovery protocols to use (comma-separated)
discovery_protocols = CDP,LLDP

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
exclude_hostnames = LUMT*,LUMV*
# Exclude devices in these IP ranges (comma-separated)
exclude_ip_ranges = 10.70.0.0/16
# Exclude devices with these platforms (comma-separated)
exclude_platforms = linux,windows,unix,freebsd,openbsd,netbsd,solaris,aix,hp-ux,vmware,docker,kubernetes,phone,host phone,camera,printer,access point,wireless,server
# Exclude devices with these capabilities (comma-separated)
exclude_capabilities = host phone,phone,camera,printer,server

[output]
# Directory for report files
reports_directory = ./reports
# Directory for log files
logs_directory = ./logs
# Excel file format
excel_format = xlsx
# Enable Visio diagram generation (true/false)
visio_enabled = true

[connection]
# SSH port number
ssh_port = 22
# Telnet port number
telnet_port = 23
# Preferred connection method (ssh/telnet)
preferred_method = ssh
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
            
            protocols_str = self._config.get('discovery', 'discovery_protocols', fallback='CDP,LLDP')
            config.protocols = [p.strip() for p in protocols_str.split(',') if p.strip()]
        
        # Apply CLI overrides
        if 'max_depth' in self._cli_overrides:
            config.max_depth = self._cli_overrides['max_depth']
        if 'concurrent_connections' in self._cli_overrides:
            config.concurrent_connections = self._cli_overrides['concurrent_connections']
        if 'timeout' in self._cli_overrides:
            config.connection_timeout = self._cli_overrides['timeout']
            
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
            exclude_hostnames = self._config.get('exclusions', 'exclude_hostnames', fallback='LUMT*,LUMV*')
            config.exclude_hostnames = [h.strip() for h in exclude_hostnames.split(',') if h.strip()]
            
            exclude_ip_ranges = self._config.get('exclusions', 'exclude_ip_ranges', fallback='10.70.0.0/16')
            config.exclude_ip_ranges = [r.strip() for r in exclude_ip_ranges.split(',') if r.strip()]
            
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
        
        # Apply CLI overrides
        if 'reports_dir' in self._cli_overrides:
            config.reports_directory = self._cli_overrides['reports_dir']
        if 'logs_dir' in self._cli_overrides:
            config.logs_directory = self._cli_overrides['logs_dir']
            
        return config
    
    def _build_connection_config(self) -> ConnectionConfig:
        """Build connection configuration"""
        config = ConnectionConfig()
        
        if self._config.has_section('connection'):
            config.ssh_port = self._config.getint('connection', 'ssh_port', fallback=config.ssh_port)
            config.telnet_port = self._config.getint('connection', 'telnet_port', fallback=config.telnet_port)
            config.preferred_method = self._config.get('connection', 'preferred_method', fallback=config.preferred_method)
            
        return config