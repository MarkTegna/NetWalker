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
        # Handle both structured and flat configuration formats
        if 'exclusions' in self.config:
            # Structured configuration format
            exclusions_config = self.config.get('exclusions')
            if exclusions_config is None:
                return FilterCriteria(
                    hostname_excludes=[],
                    ip_excludes=[],
                    platform_excludes=[],
                    capability_excludes=[]
                )
            return FilterCriteria(
                hostname_excludes=exclusions_config.exclude_hostnames or [],
                ip_excludes=exclusions_config.exclude_ip_ranges or [],
                platform_excludes=exclusions_config.exclude_platforms or [],
                capability_excludes=exclusions_config.exclude_capabilities or []
            )
        else:
            # Flat configuration format (backward compatibility)
            return FilterCriteria(
                hostname_excludes=self.config.get('hostname_excludes', []),
                ip_excludes=self.config.get('ip_excludes', []),
                platform_excludes=self.config.get('platform_excludes', []),
                capability_excludes=self.config.get('capability_excludes', [])
            )

    
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
        
        try:
            logger.info(f"FILTER DECISION: Evaluating device {device_key}")
            logger.info(f"  Device details: hostname='{hostname}', ip='{ip_address}', platform='{platform}', capabilities={capabilities}")
            
            # Check hostname patterns
            if self._matches_hostname_pattern(hostname):
                logger.info(f"  [FILTERED] by hostname pattern - matches one of: {self.criteria.hostname_excludes}")
                self.filtered_devices.add(device_key)
                return True
            else:
                logger.info(f"  [PASSED] hostname check - no match in patterns: {self.criteria.hostname_excludes}")
            
            # Check IP address ranges
            if self._matches_ip_range(ip_address):
                logger.info(f"  [FILTERED] by IP range - matches one of: {self.criteria.ip_excludes}")
                self.filtered_devices.add(device_key)
                return True
            else:
                logger.info(f"  [PASSED] IP range check - no match in ranges: {self.criteria.ip_excludes}")
            
            # Check platform exclusions
            if platform and self._matches_platform_exclusion(platform):
                logger.info(f"  [FILTERED] by platform - '{platform}' matches one of: {self.criteria.platform_excludes}")
                self.filtered_devices.add(device_key)
                return True
            else:
                if platform:
                    logger.info(f"  [PASSED] platform check - '{platform}' not in exclusions")
                else:
                    logger.info(f"  [PASSED] platform check - no platform specified")
            
            # Check capability exclusions
            if capabilities and self._matches_capability_exclusion(capabilities):
                logger.info(f"  [FILTERED] by capabilities - {capabilities} matches one of: {self.criteria.capability_excludes}")
                self.filtered_devices.add(device_key)
                return True
            else:
                if capabilities:
                    logger.info(f"  [PASSED] capability check - {capabilities} not in exclusions")
                else:
                    logger.info(f"  [PASSED] capability check - no capabilities specified")
            
            logger.info(f"  [FINAL DECISION] Device {device_key} will NOT be filtered - proceeding to discovery")
            return False
            
        except Exception as e:
            logger.error(f"  [ERROR] in filtering evaluation for {device_key}: {e}")
            logger.exception("Full exception details:")
            # Default to not filtering on error to avoid blocking discovery
            return False
    
    def _matches_hostname_pattern(self, hostname: str) -> bool:
        """Check if hostname matches any exclusion pattern"""
        hostname_lower = hostname.lower()
        logger.debug(f"    Checking hostname '{hostname_lower}' against patterns: {self.criteria.hostname_excludes}")
        
        for pattern in self.criteria.hostname_excludes:
            if fnmatch.fnmatch(hostname_lower, pattern):
                logger.debug(f"    [MATCH] Hostname '{hostname_lower}' matches pattern '{pattern}'")
                return True
            else:
                logger.debug(f"    [NO MATCH] Hostname '{hostname_lower}' does not match pattern '{pattern}'")
        
        return False
    
    def _matches_ip_range(self, ip_address: str) -> bool:
        """Check if IP address falls within any excluded CIDR range"""
        logger.debug(f"    Checking IP '{ip_address}' against ranges: {self.criteria.ip_excludes}")
        
        try:
            ip = ipaddress.ip_address(ip_address)
            for cidr_range in self.criteria.ip_excludes:
                try:
                    network = ipaddress.ip_network(cidr_range, strict=False)
                    if ip in network:
                        logger.debug(f"    [MATCH] IP '{ip_address}' is within range '{cidr_range}'")
                        return True
                    else:
                        logger.debug(f"    [NO MATCH] IP '{ip_address}' is not within range '{cidr_range}'")
                except (ipaddress.AddressValueError, ValueError) as e:
                    logger.warning(f"Invalid CIDR range {cidr_range}: {e}")
                    continue
        except (ipaddress.AddressValueError, ValueError):
            # If it's not a valid IP address, it might be a hostname
            # Skip IP range filtering for hostnames
            logger.debug(f"    [INFO] Skipping IP range filtering for hostname: {ip_address}")
        
        return False
    
    def _matches_platform_exclusion(self, platform: str) -> bool:
        """Check if platform matches any exclusion"""
        try:
            platform_lower = platform.lower()
            logger.debug(f"    Checking platform '{platform_lower}' against exclusions: {self.criteria.platform_excludes}")
            
            for excluded_platform in self.criteria.platform_excludes:
                if excluded_platform in platform_lower:
                    logger.debug(f"    [MATCH] Platform '{platform_lower}' contains excluded substring '{excluded_platform}'")
                    return True
                else:
                    logger.debug(f"    [NO MATCH] Platform '{platform_lower}' does not contain '{excluded_platform}'")
            
            return False
        except Exception as e:
            logger.error(f"    [ERROR] in platform matching for '{platform}': {e}")
            return False
    
    def _matches_capability_exclusion(self, capabilities: List[str]) -> bool:
        """Check if any capability matches exclusions"""
        import re
        capabilities_lower = [cap.lower() for cap in capabilities]
        logger.debug(f"    Checking capabilities {capabilities_lower} against exclusions: {self.criteria.capability_excludes}")
        
        for excluded_cap in self.criteria.capability_excludes:
            for cap in capabilities_lower:
                # Use word boundary matching to avoid false positives
                # This ensures "phone" matches "phone" or "ip phone" but not "phone port"
                pattern = r'\b' + re.escape(excluded_cap) + r'\b'
                if re.search(pattern, cap):
                    logger.debug(f"    [MATCH] Capability '{cap}' matches excluded pattern '{excluded_cap}' (regex: {pattern})")
                    return True
                else:
                    logger.debug(f"    [NO MATCH] Capability '{cap}' does not match excluded pattern '{excluded_cap}'")
        
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