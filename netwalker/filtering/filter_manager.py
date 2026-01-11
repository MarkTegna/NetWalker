"""
Filter Manager for NetWalker

Provides filtering and boundary management for network discovery operations.
Supports wildcard name matching, CIDR range filtering, and various exclusion criteria.
"""

import fnmatch
import ipaddress
import logging
from typing import List, Set, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FilterCriteria:
    """Container for all filtering criteria"""
    hostname_excludes: List[str]  # Wildcard patterns like LUMT*, LUMV*
    ip_excludes: List[str]        # CIDR ranges like 10.70.0.0/16
    platform_excludes: List[str]  # Platform types like linux, windows, unix
    capability_excludes: List[str] # Capabilities like host, phone, camera, printer
    
    def __post_init__(self):
        """Normalize all criteria to lowercase for case-insensitive matching"""
        self.hostname_excludes = [pattern.lower() for pattern in self.hostname_excludes]
        self.platform_excludes = [platform.lower() for platform in self.platform_excludes]
        self.capability_excludes = [cap.lower() for cap in self.capability_excludes]


class FilterManager:
    """
    Manages filtering and boundary enforcement for network discovery.
    
    Provides methods to filter devices based on hostname patterns, IP ranges,
    platform types, and capabilities. Filtered devices are recorded but not
    used for further discovery, creating discovery boundaries.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize FilterManager with configuration.
        
        Args:
            config: Configuration dictionary containing filter settings
        """
        self.config = config
        self.criteria = self._load_filter_criteria()
        self.filtered_devices: Set[str] = set()
        self.boundary_devices: Set[str] = set()
        
        logger.info(f"FilterManager initialized with {len(self.criteria.hostname_excludes)} hostname patterns, "
                   f"{len(self.criteria.ip_excludes)} IP ranges, "
                   f"{len(self.criteria.platform_excludes)} platform excludes, "
                   f"{len(self.criteria.capability_excludes)} capability excludes")
    
    def _load_filter_criteria(self) -> FilterCriteria:
        """Load filter criteria from configuration"""
        return FilterCriteria(
            hostname_excludes=self._get_config_list('exclude_hostnames', ['LUMT*', 'LUMV*']),
            ip_excludes=self._get_config_list('exclude_ip_ranges', ['10.70.0.0/16']),
            platform_excludes=self._get_config_list('exclude_platforms', 
                                                   ['linux', 'windows', 'unix', 'server']),
            capability_excludes=self._get_config_list('exclude_capabilities', 
                                                     ['host', 'phone', 'camera', 'printer', 'ap'])
        )
    
    def _get_config_list(self, key: str, default: List[str]) -> List[str]:
        """Get a list configuration value with default"""
        value = self.config.get(key, default)
        if isinstance(value, str):
            # Handle comma-separated string values
            return [item.strip() for item in value.split(',') if item.strip()]
        return value if isinstance(value, list) else default
    
    def should_filter_device(self, hostname: str, ip_address: str, 
                           platform: Optional[str] = None, 
                           capabilities: Optional[List[str]] = None) -> bool:
        """
        Determine if a device should be filtered (excluded from discovery).
        
        Args:
            hostname: Device hostname
            ip_address: Device IP address
            platform: Device platform type (optional)
            capabilities: Device capabilities list (optional)
            
        Returns:
            True if device should be filtered, False otherwise
        """
        device_key = f"{hostname}:{ip_address}"
        
        # Check hostname patterns
        if self._matches_hostname_pattern(hostname):
            logger.debug(f"Device {device_key} filtered by hostname pattern")
            self.filtered_devices.add(device_key)
            return True
        
        # Check IP address ranges
        if self._matches_ip_range(ip_address):
            logger.debug(f"Device {device_key} filtered by IP range")
            self.filtered_devices.add(device_key)
            return True
        
        # Check platform exclusions
        if platform and self._matches_platform_exclusion(platform):
            logger.debug(f"Device {device_key} filtered by platform: {platform}")
            self.filtered_devices.add(device_key)
            return True
        
        # Check capability exclusions
        if capabilities and self._matches_capability_exclusion(capabilities):
            logger.debug(f"Device {device_key} filtered by capabilities: {capabilities}")
            self.filtered_devices.add(device_key)
            return True
        
        return False
    
    def _matches_hostname_pattern(self, hostname: str) -> bool:
        """Check if hostname matches any exclusion pattern"""
        hostname_lower = hostname.lower()
        for pattern in self.criteria.hostname_excludes:
            if fnmatch.fnmatch(hostname_lower, pattern):
                return True
        return False
    
    def _matches_ip_range(self, ip_address: str) -> bool:
        """Check if IP address falls within any excluded CIDR range"""
        try:
            ip = ipaddress.ip_address(ip_address)
            for cidr_range in self.criteria.ip_excludes:
                try:
                    network = ipaddress.ip_network(cidr_range, strict=False)
                    if ip in network:
                        return True
                except (ipaddress.AddressValueError, ValueError) as e:
                    logger.warning(f"Invalid CIDR range {cidr_range}: {e}")
                    continue
        except (ipaddress.AddressValueError, ValueError):
            # If it's not a valid IP address, it might be a hostname
            # Skip IP range filtering for hostnames
            logger.debug(f"Skipping IP range filtering for hostname: {ip_address}")
        
        return False
    
    def _matches_platform_exclusion(self, platform: str) -> bool:
        """Check if platform matches any exclusion"""
        platform_lower = platform.lower()
        for excluded_platform in self.criteria.platform_excludes:
            if excluded_platform in platform_lower:
                return True
        return False
    
    def _matches_capability_exclusion(self, capabilities: List[str]) -> bool:
        """Check if any capability matches exclusions"""
        capabilities_lower = [cap.lower() for cap in capabilities]
        for excluded_cap in self.criteria.capability_excludes:
            for cap in capabilities_lower:
                if excluded_cap in cap:
                    return True
        return False
    
    def mark_as_boundary(self, hostname: str, ip_address: str, reason: str):
        """
        Mark a device as a boundary device (filtered but recorded).
        
        Args:
            hostname: Device hostname
            ip_address: Device IP address
            reason: Reason for boundary marking
        """
        device_key = f"{hostname}:{ip_address}"
        self.boundary_devices.add(device_key)
        logger.info(f"Device {device_key} marked as boundary: {reason}")
    
    def is_boundary_device(self, hostname: str, ip_address: str) -> bool:
        """Check if device is marked as a boundary device"""
        device_key = f"{hostname}:{ip_address}"
        return device_key in self.boundary_devices
    
    def get_filter_stats(self) -> Dict[str, int]:
        """Get filtering statistics"""
        return {
            'filtered_devices': len(self.filtered_devices),
            'boundary_devices': len(self.boundary_devices),
            'hostname_patterns': len(self.criteria.hostname_excludes),
            'ip_ranges': len(self.criteria.ip_excludes),
            'platform_excludes': len(self.criteria.platform_excludes),
            'capability_excludes': len(self.criteria.capability_excludes)
        }
    
    def get_filtered_devices(self) -> Set[str]:
        """Get set of all filtered device keys"""
        return self.filtered_devices.copy()
    
    def get_boundary_devices(self) -> Set[str]:
        """Get set of all boundary device keys"""
        return self.boundary_devices.copy()