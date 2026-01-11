"""
Data models for configuration
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DiscoveryConfig:
    """Configuration for discovery parameters"""
    max_depth: int = 10
    concurrent_connections: int = 5
    connection_timeout: int = 30
    protocols: List[str] = None
    
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
            self.exclude_hostnames = ['LUMT*', 'LUMV*']
        if self.exclude_ip_ranges is None:
            self.exclude_ip_ranges = ['10.70.0.0/16']
        if self.exclude_platforms is None:
            self.exclude_platforms = [
                'linux', 'windows', 'unix', 'freebsd', 'openbsd', 'netbsd', 
                'solaris', 'aix', 'hp-ux', 'vmware', 'docker', 'kubernetes', 
                'phone', 'host phone', 'camera', 'printer', 'access point', 
                'wireless', 'server'
            ]
        if self.exclude_capabilities is None:
            self.exclude_capabilities = ['host phone', 'phone', 'camera', 'printer', 'server']


@dataclass
class OutputConfig:
    """Configuration for output parameters"""
    reports_directory: str = "./reports"
    logs_directory: str = "./logs"
    excel_format: str = "xlsx"
    visio_enabled: bool = True


@dataclass
class ConnectionConfig:
    """Configuration for connection parameters"""
    ssh_port: int = 22
    telnet_port: int = 23
    preferred_method: str = "ssh"