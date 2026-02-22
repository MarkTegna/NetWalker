"""
Normalizer Component for IPv4 Prefix Inventory Module

This module handles the normalization of IPv4 prefixes to CIDR notation,
ambiguity resolution, and deduplication of prefix entries.

Author: Mark Oldham
"""

import logging
import ipaddress
from typing import Optional, List, Dict
from collections import defaultdict

from netwalker.ipv4_prefix.data_models import (
    ParsedPrefix, NormalizedPrefix, DeduplicatedPrefix, CollectionException
)


class PrefixNormalizer:
    """
    Normalizes prefixes to CIDR notation.
    
    Converts all prefix formats (CIDR, mask notation) to standard CIDR format
    using Python's ipaddress library for validation and conversion.
    """
    
    def __init__(self):
        """Initialize prefix normalizer."""
        self.logger = logging.getLogger(__name__)
    
    def normalize(self, raw_prefix: str) -> Optional[str]:
        """
        Convert prefix to CIDR notation using ipaddress library.
        
        Handles:
        - 192.168.1.0/24 → 192.168.1.0/24 (validate)
        - 192.168.1.0 255.255.255.0 → 192.168.1.0/24 (convert)
        - 10.0.0.1/32 → 10.0.0.1/32 (preserve host routes)
        
        Args:
            raw_prefix: Prefix string in any supported format
            
        Returns:
            CIDR notation string or None if invalid
            
        Requirements:
            - 6.1: Convert mask format to CIDR
            - 6.2: Validate and preserve CIDR format
            - 6.3: Handle invalid formats gracefully
            - 6.4: Return valid IPv4 network in CIDR notation
            - 6.5: Preserve /32 host routes
        """
        if not raw_prefix or not raw_prefix.strip():
            return None
        
        raw_prefix = raw_prefix.strip()
        
        # Check if already in CIDR format
        if '/' in raw_prefix:
            return self.validate_cidr(raw_prefix)
        
        # Check if in mask format (IP + subnet mask)
        if ' ' in raw_prefix:
            parts = raw_prefix.split()
            if len(parts) == 2:
                return self.mask_to_cidr(parts[0], parts[1])
        
        # Single IP address without mask (ambiguous - should be resolved first)
        self.logger.warning(f"Cannot normalize ambiguous prefix without mask: {raw_prefix}")
        return None
    
    def mask_to_cidr(self, ip: str, mask: str) -> Optional[str]:
        """
        Convert IP + mask to CIDR notation.
        
        Uses ipaddress library for conversion and validation.
        
        Args:
            ip: IP address string
            mask: Subnet mask string
            
        Returns:
            CIDR notation string or None if invalid
            
        Requirements:
            - 6.1: Convert mask format to CIDR using ipaddress library
        """
        try:
            # Create IPv4Network from IP and netmask
            network = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
            return str(network)
            
        except (ValueError, ipaddress.AddressValueError, ipaddress.NetmaskValueError) as e:
            self.logger.warning(f"Invalid IP/mask format: {ip} {mask} - {str(e)}")
            return None
    
    def validate_cidr(self, cidr: str) -> Optional[str]:
        """
        Validate CIDR notation format.
        
        Args:
            cidr: CIDR notation string
            
        Returns:
            Validated CIDR string or None if invalid
            
        Requirements:
            - 6.2: Validate CIDR format and preserve if valid
            - 6.4: Ensure output is valid IPv4 network
        """
        try:
            # Parse and validate using ipaddress library
            network = ipaddress.IPv4Network(cidr, strict=False)
            return str(network)
            
        except (ValueError, ipaddress.AddressValueError, ipaddress.NetmaskValueError) as e:
            self.logger.warning(f"Invalid CIDR format: {cidr} - {str(e)}")
            return None
    
    def normalize_parsed_prefix(self, parsed: ParsedPrefix, 
                                exceptions: List[CollectionException]) -> Optional[NormalizedPrefix]:
        """
        Normalize a ParsedPrefix to NormalizedPrefix.
        
        Converts the prefix string to CIDR notation and creates a NormalizedPrefix
        object. If normalization fails, adds an exception and returns None.
        
        Args:
            parsed: ParsedPrefix object to normalize
            exceptions: List to append exceptions to
            
        Returns:
            NormalizedPrefix object or None if normalization failed
            
        Requirements:
            - 6.3: Log errors and add to exceptions report on failure
            - 6.4: Return valid IPv4 network in CIDR notation
        """
        # Normalize the prefix string
        normalized_str = self.normalize(parsed.prefix_str)
        
        if not normalized_str:
            # Normalization failed - add to exceptions
            exception = CollectionException(
                device=parsed.device,
                command='',  # Not command-specific
                error_type='normalization_failed',
                raw_token=parsed.prefix_str,
                error_message=f"Failed to normalize prefix: {parsed.prefix_str}",
                timestamp=parsed.timestamp
            )
            exceptions.append(exception)
            self.logger.error(f"Failed to normalize prefix on {parsed.device}: {parsed.prefix_str}")
            return None
        
        # Create NormalizedPrefix object
        normalized = NormalizedPrefix(
            device=parsed.device,
            platform=parsed.platform,
            vrf=parsed.vrf,
            prefix=normalized_str,
            source=parsed.source,
            protocol=parsed.protocol,
            raw_line=parsed.raw_line,
            timestamp=parsed.timestamp,
            vlan=parsed.vlan,
            interface=parsed.interface
        )
        
        return normalized


class AmbiguityResolver:
    """Resolves prefixes without explicit length."""
    
    def __init__(self, connection_manager):
        """
        Initialize ambiguity resolver.
        
        Args:
            connection_manager: NetWalker ConnectionManager instance
        """
        self.connection_manager = connection_manager
        self.logger = logging.getLogger(__name__)
        self.normalizer = PrefixNormalizer()
    
    def resolve(self, connection, prefix: str, vrf: str, platform: str) -> Optional[str]:
        """
        Resolve ambiguous prefix by querying device.
        
        Strategy:
        1. Try 'show ip bgp <prefix>' (or vrf variant)
        2. Try 'show ip route <prefix>' (or vrf variant)
        3. If both fail, mark as unresolved
        
        Args:
            connection: Active device connection
            prefix: Ambiguous prefix (IP without length)
            vrf: VRF name ("global" for global table)
            platform: Device platform (ios, iosxe, nxos)
            
        Returns:
            Resolved CIDR notation or None if unresolved
            
        Requirements:
            - 7.1: Try 'show ip bgp <prefix>' first
            - 7.2: Try 'show ip route <prefix>' second
            - 7.3: Mark as unresolved if both fail
            - 7.4: Normalize resolved prefix to CIDR
        """
        self.logger.debug(f"Resolving ambiguous prefix: {prefix} in VRF {vrf}")
        
        # Try BGP lookup first
        resolved = self._try_bgp_lookup(connection, prefix, vrf, platform)
        if resolved:
            self.logger.info(f"Resolved {prefix} via BGP: {resolved}")
            return resolved
        
        # Try routing table lookup second
        resolved = self._try_route_lookup(connection, prefix, vrf)
        if resolved:
            self.logger.info(f"Resolved {prefix} via routing table: {resolved}")
            return resolved
        
        # Both attempts failed
        self.logger.warning(f"Could not resolve ambiguous prefix: {prefix} in VRF {vrf}")
        return None
    
    def _try_bgp_lookup(self, connection, prefix: str, vrf: str, platform: str) -> Optional[str]:
        """
        Try to resolve prefix using BGP lookup.
        
        Args:
            connection: Active device connection
            prefix: Ambiguous prefix
            vrf: VRF name
            platform: Device platform
            
        Returns:
            Resolved CIDR notation or None
        """
        try:
            # Build platform-specific command
            if vrf == 'global':
                command = f"show ip bgp {prefix}"
            else:
                if platform.lower() in ['ios', 'iosxe', 'ios-xe']:
                    command = f"show ip bgp vpnv4 vrf {vrf} {prefix}"
                else:  # NX-OS
                    command = f"show ip bgp vrf {vrf} {prefix}"
            
            self.logger.debug(f"Trying BGP lookup: {command}")
            output = connection.send_command(command)
            
            # Extract prefix with length from output
            return self._extract_prefix_from_output(output)
            
        except Exception as e:
            self.logger.debug(f"BGP lookup failed: {str(e)}")
            return None
    
    def _try_route_lookup(self, connection, prefix: str, vrf: str) -> Optional[str]:
        """
        Try to resolve prefix using routing table lookup.
        
        Args:
            connection: Active device connection
            prefix: Ambiguous prefix
            vrf: VRF name
            
        Returns:
            Resolved CIDR notation or None
        """
        try:
            # Build command
            if vrf == 'global':
                command = f"show ip route {prefix}"
            else:
                command = f"show ip route vrf {vrf} {prefix}"
            
            self.logger.debug(f"Trying route lookup: {command}")
            output = connection.send_command(command)
            
            # Extract prefix with length from output
            return self._extract_prefix_from_output(output)
            
        except Exception as e:
            self.logger.debug(f"Route lookup failed: {str(e)}")
            return None
    
    def _extract_prefix_from_output(self, output: str) -> Optional[str]:
        """
        Extract prefix with length from command output.
        
        Looks for CIDR notation or IP/mask pairs in the output.
        
        Args:
            output: Command output
            
        Returns:
            Prefix in CIDR notation or None
        """
        if not output or not output.strip():
            return None
        
        # Use PrefixExtractor to find prefixes in output
        from netwalker.ipv4_prefix.parser import PrefixExtractor
        extractor = PrefixExtractor()
        
        lines = output.split('\n')
        for line in lines:
            # Try to extract prefix from line
            raw_prefix = extractor.extract_from_route_line(line)
            if raw_prefix and not raw_prefix.is_ambiguous:
                # Found a prefix with explicit length - normalize it
                normalized = self.normalizer.normalize(raw_prefix.prefix_str)
                if normalized:
                    return normalized
        
        return None


class PrefixDeduplicator:
    """Removes duplicate prefix entries."""
    
    def __init__(self):
        """Initialize prefix deduplicator."""
        self.logger = logging.getLogger(__name__)
    
    def deduplicate_by_device(self, prefixes: List[NormalizedPrefix]) -> List[NormalizedPrefix]:
        """
        Remove duplicates within device scope.
        
        Key: (device, vrf, prefix, source)
        Keeps first occurrence of duplicates.
        
        Args:
            prefixes: List of NormalizedPrefix objects
            
        Returns:
            Deduplicated list of NormalizedPrefix objects
            
        Requirements:
            - 9.1: Use (device, vrf, prefix, source) as unique key
            - 9.2: Keep first occurrence of duplicates
        """
        seen = set()
        deduplicated = []
        
        for prefix in prefixes:
            # Create unique key
            key = (prefix.device, prefix.vrf, prefix.prefix, prefix.source)
            
            if key not in seen:
                seen.add(key)
                deduplicated.append(prefix)
        
        duplicates_removed = len(prefixes) - len(deduplicated)
        if duplicates_removed > 0:
            self.logger.info(f"Removed {duplicates_removed} duplicate prefixes (by device)")
        
        return deduplicated
    
    def deduplicate_by_vrf(self, prefixes: List[NormalizedPrefix]) -> List[DeduplicatedPrefix]:
        """
        Create deduplicated view across devices.
        
        Key: (vrf, prefix)
        Aggregates: device_list, device_count
        
        Args:
            prefixes: List of NormalizedPrefix objects
            
        Returns:
            List of DeduplicatedPrefix objects
            
        Requirements:
            - 9.3: Group by (vrf, prefix) across all devices
            - 9.4: Include list of devices where each prefix appears
            - 9.5: Include count of devices for each prefix
        """
        # Group prefixes by (vrf, prefix)
        grouped: Dict[tuple, List[str]] = defaultdict(list)
        
        for prefix in prefixes:
            key = (prefix.vrf, prefix.prefix)
            if prefix.device not in grouped[key]:
                grouped[key].append(prefix.device)
        
        # Create DeduplicatedPrefix objects
        deduplicated = []
        for (vrf, prefix), devices in grouped.items():
            dedup = DeduplicatedPrefix(
                vrf=vrf,
                prefix=prefix,
                device_count=len(devices),
                device_list=sorted(devices)  # Sort for consistency
            )
            deduplicated.append(dedup)
        
        self.logger.info(f"Created deduplicated view with {len(deduplicated)} unique (vrf, prefix) pairs")
        return deduplicated
