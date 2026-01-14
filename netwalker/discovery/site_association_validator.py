"""
Site Association Validator for NetWalker

Determines correct site associations for discovered devices based on hostname patterns
and site boundary configurations.
"""

import logging
import re
import fnmatch
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class SiteAssociationValidator:
    """
    Validates and determines site associations for discovered devices.
    
    Features:
    - Device site determination based on hostname patterns
    - Site membership validation logic
    - Multi-site conflict resolution
    - Hostname cleaning and normalization
    """
    
    def __init__(self, site_boundary_pattern: str):
        """
        Initialize SiteAssociationValidator.
        
        Args:
            site_boundary_pattern: Pattern for identifying site boundary devices (e.g., '*-CORE-*')
        """
        self.site_boundary_pattern = site_boundary_pattern
        self._site_cache: Dict[str, str] = {}  # Cache for hostname -> site mappings
        
        logger.info(f"SiteAssociationValidator initialized with pattern: {site_boundary_pattern}")
    
    def determine_device_site(self, device_hostname: str, device_ip: str, 
                             parent_site: Optional[str] = None) -> str:
        """
        Determine the correct site association for a device.
        
        Args:
            device_hostname: Device hostname (may contain serial numbers)
            device_ip: Device IP address
            parent_site: Site of the parent device that discovered this device
            
        Returns:
            Site name or 'GLOBAL' if device doesn't belong to any specific site
        """
        if not device_hostname and not device_ip:
            logger.warning("Cannot determine site for device with no hostname or IP")
            return 'GLOBAL'
        
        # Use hostname for site determination, fallback to IP if needed
        identifier = device_hostname if device_hostname else device_ip
        
        # Check cache first
        cache_key = f"{identifier}:{parent_site or 'None'}"
        if cache_key in self._site_cache:
            logger.debug(f"Site cache hit for {identifier}: {self._site_cache[cache_key]}")
            return self._site_cache[cache_key]
        
        # Clean hostname for pattern matching
        clean_hostname = self._clean_hostname(device_hostname) if device_hostname else device_ip
        
        logger.debug(f"Determining site for device: {device_hostname} (cleaned: {clean_hostname}), IP: {device_ip}, parent_site: {parent_site}")
        
        # Method 1: Check if device matches site boundary pattern directly
        if fnmatch.fnmatch(clean_hostname, self.site_boundary_pattern):
            site_name = self._extract_site_name(clean_hostname)
            logger.info(f"Device {clean_hostname} matches site boundary pattern, assigned to site: {site_name}")
            self._site_cache[cache_key] = site_name
            return site_name
        
        # Method 2: If parent site is provided, check if device belongs to same site
        if parent_site and parent_site != 'GLOBAL':
            # Check if device hostname suggests it belongs to parent site
            if self._hostname_suggests_site_membership(clean_hostname, parent_site):
                logger.info(f"Device {clean_hostname} belongs to parent site: {parent_site}")
                self._site_cache[cache_key] = parent_site
                return parent_site
        
        # Method 3: Try to extract site from hostname using common patterns
        inferred_site = self._infer_site_from_hostname(clean_hostname)
        if inferred_site and inferred_site != 'UNKNOWN':
            logger.info(f"Device {clean_hostname} inferred to belong to site: {inferred_site}")
            self._site_cache[cache_key] = inferred_site
            return inferred_site
        
        # Method 4: Default to GLOBAL if no site can be determined
        logger.debug(f"Device {clean_hostname} assigned to GLOBAL (no specific site determined)")
        self._site_cache[cache_key] = 'GLOBAL'
        return 'GLOBAL'
    
    def validate_site_membership(self, device_info: Dict[str, Any], site_name: str) -> bool:
        """
        Validate if a device belongs to a specific site.
        
        Args:
            device_info: Device information dictionary
            site_name: Site name to validate against
            
        Returns:
            True if device belongs to the site, False otherwise
        """
        if not device_info or not site_name:
            return False
        
        device_hostname = device_info.get('hostname', '')
        device_ip = device_info.get('ip_address', '') or device_info.get('primary_ip', '')
        
        # Determine the device's actual site
        determined_site = self.determine_device_site(device_hostname, device_ip)
        
        # Check if determined site matches the requested site
        is_member = determined_site == site_name
        
        logger.debug(f"Site membership validation: device {device_hostname} -> determined_site: {determined_site}, requested_site: {site_name}, is_member: {is_member}")
        
        return is_member
    
    def resolve_multi_site_conflicts(self, device_info: Dict[str, Any], 
                                   candidate_sites: List[str]) -> str:
        """
        Resolve conflicts when a device could belong to multiple sites.
        
        Args:
            device_info: Device information dictionary
            candidate_sites: List of potential sites for the device
            
        Returns:
            The most appropriate site name
        """
        if not candidate_sites:
            return 'GLOBAL'
        
        if len(candidate_sites) == 1:
            return candidate_sites[0]
        
        device_hostname = device_info.get('hostname', '')
        device_ip = device_info.get('ip_address', '') or device_info.get('primary_ip', '')
        clean_hostname = self._clean_hostname(device_hostname) if device_hostname else device_ip
        
        logger.info(f"Resolving multi-site conflict for device {clean_hostname}: candidates {candidate_sites}")
        
        # Priority 1: Site boundary pattern match
        for site in candidate_sites:
            if fnmatch.fnmatch(clean_hostname, self.site_boundary_pattern):
                extracted_site = self._extract_site_name(clean_hostname)
                if extracted_site == site:
                    logger.info(f"Conflict resolved: {clean_hostname} assigned to {site} (boundary pattern match)")
                    return site
        
        # Priority 2: Hostname prefix match
        for site in candidate_sites:
            if clean_hostname.upper().startswith(site.upper()):
                logger.info(f"Conflict resolved: {clean_hostname} assigned to {site} (hostname prefix match)")
                return site
        
        # Priority 3: Most specific site name (longest match)
        best_site = max(candidate_sites, key=len)
        logger.info(f"Conflict resolved: {clean_hostname} assigned to {best_site} (longest site name)")
        return best_site
    
    def get_site_devices(self, inventory: Dict[str, Dict[str, Any]], 
                        site_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all devices that belong to a specific site.
        
        Args:
            inventory: Complete device inventory
            site_name: Site name to filter by
            
        Returns:
            Dictionary of devices belonging to the site
        """
        site_devices = {}
        
        for device_key, device_info in inventory.items():
            if self.validate_site_membership(device_info, site_name):
                site_devices[device_key] = device_info
        
        logger.info(f"Found {len(site_devices)} devices for site '{site_name}'")
        return site_devices
    
    def get_all_sites(self, inventory: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Get list of all unique sites from the inventory.
        
        Args:
            inventory: Complete device inventory
            
        Returns:
            List of unique site names
        """
        sites = set()
        
        for device_key, device_info in inventory.items():
            device_hostname = device_info.get('hostname', '')
            device_ip = device_info.get('ip_address', '') or device_info.get('primary_ip', '')
            
            site = self.determine_device_site(device_hostname, device_ip)
            if site != 'GLOBAL':
                sites.add(site)
        
        site_list = sorted(list(sites))
        logger.info(f"Identified {len(site_list)} unique sites: {site_list}")
        return site_list
    
    def _clean_hostname(self, hostname: str) -> str:
        """
        Clean hostname by removing serial numbers and special characters.
        
        Args:
            hostname: Raw hostname that may contain serial numbers
            
        Returns:
            Cleaned hostname
        """
        if not hostname:
            return ''
        
        # Handle FQDN by taking only the hostname part
        if '.' in hostname:
            hostname = hostname.split('.')[0]
        
        # Remove serial numbers in parentheses (e.g., "DEVICE(FOX123)" -> "DEVICE")
        hostname = re.sub(r'\([^)]*\)', '', hostname)
        
        # Normalize Unicode characters to ASCII equivalents where possible
        import unicodedata
        try:
            # Normalize to NFD (decomposed form) then remove combining characters
            hostname = unicodedata.normalize('NFD', hostname)
            hostname = ''.join(c for c in hostname if unicodedata.category(c) != 'Mn')
            # Convert to ASCII, ignoring non-ASCII characters
            hostname = hostname.encode('ascii', 'ignore').decode('ascii')
        except (UnicodeError, UnicodeDecodeError):
            # Fallback: keep only ASCII alphanumeric and hyphens
            hostname = re.sub(r'[^A-Za-z0-9-]', '', hostname)
        
        # Remove any remaining special characters except word chars and hyphens
        hostname = re.sub(r'[^\w-]', '', hostname)
        
        # Remove leading/trailing whitespace and hyphens
        hostname = hostname.strip().strip('-')
        
        # Ensure hostname is not longer than 36 characters
        if len(hostname) > 36:
            hostname = hostname[:36]
            
        return hostname.upper()  # Normalize to uppercase for consistent matching
    
    def _extract_site_name(self, hostname: str) -> str:
        """
        Extract site name from hostname based on the site boundary pattern.
        
        Args:
            hostname: Device hostname (should be cleaned)
            
        Returns:
            Site name extracted from hostname
        """
        if not hostname:
            return "UNKNOWN"
            
        # Handle the default pattern '*-CORE-*'
        if '-CORE-' in hostname:
            site_name = hostname.split('-CORE-')[0]
            # Ensure site name is valid
            site_name = re.sub(r'[^\w-]', '', site_name)
            return site_name if site_name else "UNKNOWN"
        
        # For other patterns, use a more generic approach
        # Extract the first part before any delimiter that might indicate device type
        common_delimiters = ['-CORE-', '-MDF-', '-IDF-', '-SW-', '-RTR-', '-FW-']
        
        for delimiter in common_delimiters:
            if delimiter in hostname:
                site_name = hostname.split(delimiter)[0]
                site_name = re.sub(r'[^\w-]', '', site_name)
                return site_name if site_name else "UNKNOWN"
        
        # Fallback: use first part before first hyphen
        parts = hostname.split('-')
        if len(parts) >= 2:
            site_name = parts[0]
            site_name = re.sub(r'[^\w-]', '', site_name)
            return site_name if site_name else "UNKNOWN"
        
        # Final fallback to cleaned hostname
        site_name = re.sub(r'[^\w-]', '', hostname)
        return site_name if site_name else "UNKNOWN"
    
    def _hostname_suggests_site_membership(self, hostname: str, site_name: str) -> bool:
        """
        Check if hostname suggests membership in a specific site.
        
        Args:
            hostname: Cleaned hostname
            site_name: Site name to check against
            
        Returns:
            True if hostname suggests site membership
        """
        if not hostname or not site_name:
            return False
        
        hostname_upper = hostname.upper()
        site_upper = site_name.upper()
        
        # Check if hostname starts with site name
        if hostname_upper.startswith(site_upper):
            return True
        
        # Check if hostname contains site name as a prefix with delimiter
        if hostname_upper.startswith(f"{site_upper}-"):
            return True
        
        # Check if site name appears in hostname with common delimiters
        site_patterns = [
            f"{site_upper}-",
            f"-{site_upper}-",
            f"_{site_upper}_",
            f".{site_upper}."
        ]
        
        for pattern in site_patterns:
            if pattern in hostname_upper:
                return True
        
        return False
    
    def _infer_site_from_hostname(self, hostname: str) -> str:
        """
        Infer site name from hostname using common naming patterns.
        
        Args:
            hostname: Cleaned hostname
            
        Returns:
            Inferred site name or 'UNKNOWN'
        """
        if not hostname:
            return 'UNKNOWN'
        
        # Common patterns for network device naming
        # Pattern 1: SITE-DEVICETYPE-NUMBER (e.g., NYC-SW-01, LAX-RTR-02)
        parts = hostname.split('-')
        if len(parts) >= 2:
            potential_site = parts[0]
            # Check if second part looks like a device type
            device_types = ['SW', 'SWITCH', 'RTR', 'ROUTER', 'FW', 'FIREWALL', 
                           'CORE', 'MDF', 'IDF', 'AP', 'WLC', 'ASA']
            if len(parts) >= 2 and parts[1].upper() in device_types:
                return potential_site
        
        # Pattern 2: SITEDEVICETYPE-NUMBER (e.g., NYCSW01, LAXRTR02)
        # Look for common device type suffixes
        for device_type in ['SW', 'RTR', 'FW', 'CORE']:
            if device_type in hostname:
                site_part = hostname.split(device_type)[0]
                if site_part and len(site_part) >= 2:
                    return site_part
        
        # Pattern 3: Geographic codes (3-4 letter codes)
        if len(hostname) >= 3:
            # Check if first 3-4 characters could be a site code
            potential_site = hostname[:4] if len(hostname) >= 4 else hostname[:3]
            # Simple heuristic: if it's all letters, it might be a site code
            if potential_site.isalpha():
                return potential_site
        
        return 'UNKNOWN'
    
    def clear_cache(self):
        """Clear the site association cache"""
        self._site_cache.clear()
        logger.debug("Site association cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'cache_size': len(self._site_cache),
            'cached_sites': len(set(self._site_cache.values()))
        }