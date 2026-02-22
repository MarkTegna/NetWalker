"""
Data models for configuration
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DiscoveryConfig:
    """Configuration for discovery parameters"""
    max_depth: int = 1
    concurrent_connections: int = 5
    connection_timeout: int = 30
    discovery_timeout: int = 300  # Total discovery process timeout (5 minutes)
    protocols: List[str] = None
    enable_progress_tracking: bool = True
    
    def __post_init__(self):
        if self.protocols is None:
            self.protocols = ['CDP', 'LLDP']


@dataclass
class FilterConfig:
    """Configuration for filtering parameters"""
    include_wildcards: List[str] = None
    exclude_wildcards: List[str] = None
    include_cidrs: List[str] = None
    exclude_cidrs: List[str] = None
    
    def __post_init__(self):
        if self.include_wildcards is None:
            self.include_wildcards = ['*']
        if self.exclude_wildcards is None:
            self.exclude_wildcards = []
        if self.include_cidrs is None:
            self.include_cidrs = []
        if self.exclude_cidrs is None:
            self.exclude_cidrs = []


@dataclass
class ExclusionConfig:
    """Configuration for exclusion parameters"""
    exclude_hostnames: List[str] = None
    exclude_ip_ranges: List[str] = None
    exclude_platforms: List[str] = None
    exclude_capabilities: List[str] = None
    
    def __post_init__(self):
        if self.exclude_hostnames is None:
            self.exclude_hostnames = []  # No hardcoded defaults
        if self.exclude_ip_ranges is None:
            self.exclude_ip_ranges = []
        if self.exclude_platforms is None:
            self.exclude_platforms = []
        if self.exclude_capabilities is None:
            self.exclude_capabilities = []


@dataclass
class OutputConfig:
    """Configuration for output parameters"""
    reports_directory: str = "./reports"
    logs_directory: str = "./logs"
    excel_format: str = "xlsx"
    visio_enabled: bool = True
    site_boundary_pattern: Optional[str] = "*-CORE-*"
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        # Validate that None is accepted as a valid disabled state for site boundary pattern
        # This is intentional - None means site boundary detection is disabled
        if self.site_boundary_pattern is not None and not isinstance(self.site_boundary_pattern, str):
            raise ValueError("site_boundary_pattern must be a string or None")
        
        # If it's a string, ensure it's not just whitespace (should have been handled by ConfigurationBlankHandler)
        if isinstance(self.site_boundary_pattern, str) and self.site_boundary_pattern.strip() == "":
            # This should not happen if ConfigurationBlankHandler is used correctly
            # But we'll handle it gracefully by converting to None
            self.site_boundary_pattern = None
    
    def is_site_boundary_detection_enabled(self) -> bool:
        """
        Check if site boundary detection is enabled.
        
        Returns:
            bool: True if site boundary detection is enabled, False if disabled
        """
        return self.site_boundary_pattern is not None
    
    def get_effective_site_boundary_pattern(self) -> Optional[str]:
        """
        Get the effective site boundary pattern.
        
        Returns:
            Optional[str]: The pattern if enabled, None if disabled
        """
        return self.site_boundary_pattern


@dataclass
class ConnectionConfig:
    """Configuration for connection parameters"""
    ssh_port: int = 22
    telnet_port: int = 23
    preferred_method: str = "ssh"
    ssl_verify: bool = False
    ssl_cert_file: Optional[str] = None
    ssl_key_file: Optional[str] = None
    ssl_ca_bundle: Optional[str] = None
    skip_after_failures: int = 3


@dataclass
class VLANCollectionConfig:
    """Configuration for VLAN collection parameters"""
    enabled: bool = True
    command_timeout: int = 30
    max_retries: int = 2
    include_inactive_vlans: bool = True
    platforms_to_skip: List[str] = None
    
    def __post_init__(self):
        if self.platforms_to_skip is None:
            self.platforms_to_skip = []