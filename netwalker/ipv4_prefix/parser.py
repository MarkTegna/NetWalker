"""
Parser Component for IPv4 Prefix Inventory Module

This module handles the extraction and parsing of IPv4 prefixes from command outputs,
including routing tables and BGP outputs. It supports multiple prefix formats (CIDR,
mask notation) and identifies ambiguous prefixes that require resolution.

Author: Mark Oldham
"""

import logging
import re
from typing import Optional, List
from datetime import datetime

from netwalker.ipv4_prefix.data_models import RawPrefix, ParsedPrefix


class PrefixExtractor:
    """
    Extracts prefixes from command output lines.
    
    Handles multiple prefix formats:
    - CIDR format: 192.168.1.0/24
    - Mask format: 192.168.1.0 255.255.255.0
    - Ambiguous format: 10.0.0.0 (no length)
    - Local routes: L    10.0.0.1/32
    """
    
    def __init__(self):
        """Initialize prefix extractor."""
        self.logger = logging.getLogger(__name__)
        
        # Regex patterns for prefix extraction
        # CIDR format: 192.168.1.0/24
        self.cidr_pattern = re.compile(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})\b')
        
        # Mask format: 192.168.1.0 255.255.255.0
        self.mask_pattern = re.compile(
            r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        )
        
        # IP address without mask (potentially ambiguous)
        self.ip_pattern = re.compile(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b')
    
    def extract_from_route_line(self, line: str) -> Optional[RawPrefix]:
        """
        Extract prefix from routing table line.
        
        Handles formats:
        - 192.168.1.0/24
        - 192.168.1.0 255.255.255.0
        - L    10.0.0.1/32 (local route)
        
        Args:
            line: Single line from routing table output
            
        Returns:
            RawPrefix object if prefix found, None otherwise
            
        Requirements:
            - 5.1: Extract prefixes in CIDR format
            - 5.2: Extract prefixes in mask format
            - 5.4: Extract /32 local routes (L route code)
            - 5.6: Preserve raw output line
        """
        if not line or not line.strip():
            return None
        
        # Try CIDR format first (most common and unambiguous)
        cidr_match = self.cidr_pattern.search(line)
        if cidr_match:
            prefix_str = cidr_match.group(1)
            return RawPrefix(
                prefix_str=prefix_str,
                raw_line=line,
                is_ambiguous=False
            )
        
        # Try mask format (IP + subnet mask)
        mask_match = self.mask_pattern.search(line)
        if mask_match:
            ip_addr = mask_match.group(1)
            subnet_mask = mask_match.group(2)
            
            # Validate that second part looks like a subnet mask
            if self._is_subnet_mask(subnet_mask):
                prefix_str = f"{ip_addr} {subnet_mask}"
                return RawPrefix(
                    prefix_str=prefix_str,
                    raw_line=line,
                    is_ambiguous=False
                )
        
        return None
    
    def extract_from_bgp_line(self, line: str) -> Optional[RawPrefix]:
        """
        Extract prefix from BGP output line.
        
        Handles formats:
        - 10.0.0.0/24 (with length - unambiguous)
        - 10.0.0.0 (without length - ambiguous)
        
        Args:
            line: Single line from BGP output
            
        Returns:
            RawPrefix object if prefix found, None otherwise
            
        Requirements:
            - 5.3: Extract BGP prefixes with or without explicit length
            - 5.6: Preserve raw output line
        """
        if not line or not line.strip():
            return None
        
        # Try CIDR format first (unambiguous)
        cidr_match = self.cidr_pattern.search(line)
        if cidr_match:
            prefix_str = cidr_match.group(1)
            return RawPrefix(
                prefix_str=prefix_str,
                raw_line=line,
                is_ambiguous=False
            )
        
        # Look for IP address without length (ambiguous)
        # BGP output typically has network addresses in specific columns
        # We need to be careful not to match IP addresses that are not networks
        ip_match = self.ip_pattern.search(line)
        if ip_match:
            ip_addr = ip_match.group(1)
            
            # Basic validation - don't match obviously non-network IPs
            # (like 0.0.0.0 or 255.255.255.255 unless they're actually networks)
            if self._looks_like_network_address(ip_addr, line):
                return RawPrefix(
                    prefix_str=ip_addr,
                    raw_line=line,
                    is_ambiguous=True  # No length specified
                )
        
        return None
    
    def _is_subnet_mask(self, mask: str) -> bool:
        """
        Check if a string looks like a valid subnet mask.
        
        Valid subnet masks have contiguous 1 bits followed by contiguous 0 bits.
        Examples: 255.255.255.0, 255.255.0.0, 255.0.0.0
        
        Args:
            mask: String to check
            
        Returns:
            True if it looks like a subnet mask
        """
        # Common subnet masks
        valid_masks = [
            '255.255.255.255', '255.255.255.254', '255.255.255.252',
            '255.255.255.248', '255.255.255.240', '255.255.255.224',
            '255.255.255.192', '255.255.255.128', '255.255.255.0',
            '255.255.254.0', '255.255.252.0', '255.255.248.0',
            '255.255.240.0', '255.255.224.0', '255.255.192.0',
            '255.255.128.0', '255.255.0.0', '255.254.0.0',
            '255.252.0.0', '255.248.0.0', '255.240.0.0',
            '255.224.0.0', '255.192.0.0', '255.128.0.0',
            '255.0.0.0', '254.0.0.0', '252.0.0.0',
            '248.0.0.0', '240.0.0.0', '224.0.0.0',
            '192.0.0.0', '128.0.0.0', '0.0.0.0'
        ]
        
        return mask in valid_masks
    
    def _looks_like_network_address(self, ip: str, line: str) -> bool:
        """
        Heuristic to determine if an IP address looks like a network address.
        
        This is used for BGP output where network addresses may not have
        explicit length indicators.
        
        Args:
            ip: IP address string
            line: Full line context
            
        Returns:
            True if it looks like a network address
        """
        # Skip obviously invalid addresses
        if ip in ['0.0.0.0', '255.255.255.255']:
            # These could be valid in some contexts, check line context
            if 'default' in line.lower() or 'route' in line.lower():
                return True
            return False
        
        # In BGP output, network addresses are typically at the start of the line
        # or after specific markers like '*' or '>'
        line_stripped = line.strip()
        
        # Check if IP is near the beginning of the line (after route status markers)
        # BGP lines typically look like: "*> 10.0.0.0          ..."
        if line_stripped.startswith('*') or line_stripped.startswith('>'):
            # Remove status markers and check if IP is next
            cleaned = line_stripped.lstrip('*> ')
            if cleaned.startswith(ip):
                return True
        
        # Check if line contains BGP-specific keywords
        bgp_keywords = ['network', 'bgp', 'next hop', 'metric', 'locprf', 'weight', 'path']
        if any(keyword in line.lower() for keyword in bgp_keywords):
            return True
        
        return False


class RoutingTableParser:
    """Parses 'show ip route' output."""
    
    def __init__(self):
        """Initialize routing table parser."""
        self.logger = logging.getLogger(__name__)
        self.extractor = PrefixExtractor()
        
        # Route code mapping (Cisco IOS/IOS-XE/NX-OS)
        self.route_codes = {
            'C': 'C',  # Connected
            'L': 'L',  # Local
            'S': 'S',  # Static
            'R': 'R',  # RIP
            'M': 'M',  # Mobile
            'B': 'B',  # BGP
            'D': 'D',  # EIGRP
            'EX': 'D',  # EIGRP external
            'O': 'O',  # OSPF
            'IA': 'O',  # OSPF inter area
            'N1': 'O',  # OSPF NSSA external type 1
            'N2': 'O',  # OSPF NSSA external type 2
            'E1': 'O',  # OSPF external type 1
            'E2': 'O',  # OSPF external type 2
            'i': 'i',  # IS-IS
            'su': 'i',  # IS-IS summary
            'L1': 'i',  # IS-IS level-1
            'L2': 'i',  # IS-IS level-2
            'ia': 'i',  # IS-IS inter area
        }
    
    def parse(self, output: str, device: str, platform: str, vrf: str) -> List[ParsedPrefix]:
        """
        Parse routing table output and extract all prefixes.
        
        Args:
            output: Raw command output from 'show ip route'
            device: Device hostname
            platform: Device platform (ios, iosxe, nxos)
            vrf: VRF name ("global" for global table)
            
        Returns:
            List of ParsedPrefix objects with metadata
            
        Requirements:
            - 5.1: Extract prefixes in CIDR format
            - 5.2: Extract prefixes in mask format
            - 5.4: Extract /32 local routes
            - 5.5: Extract loopback interface addresses
            - 5.6: Preserve raw output lines
            - 8.1-8.7: Tag with complete metadata
        """
        prefixes = []
        timestamp = datetime.now()
        
        if not output or not output.strip():
            self.logger.warning(f"Empty routing table output for {device}")
            return prefixes
        
        lines = output.split('\n')
        
        for line in lines:
            # Skip empty lines and header lines
            if not line.strip():
                continue
            
            # Skip lines that are clearly headers or legends
            if any(keyword in line for keyword in ['Codes:', 'Gateway', 'Legend:', 'Route Source']):
                continue
            
            # Extract prefix from line
            raw_prefix = self.extractor.extract_from_route_line(line)
            if not raw_prefix:
                continue
            
            # Determine routing protocol from route code
            protocol = self._extract_protocol(line)
            
            # Determine source (rib or connected)
            # Connected routes have 'C' or 'L' codes
            if protocol in ['C', 'L']:
                source = 'connected'
            else:
                source = 'rib'
            
            # Extract interface and VLAN information
            interface = self._extract_interface(line)
            vlan = self._extract_vlan(interface) if interface else None
            
            # Create ParsedPrefix object
            parsed = ParsedPrefix(
                device=device,
                platform=platform,
                vrf=vrf,
                prefix_str=raw_prefix.prefix_str,
                source=source,
                protocol=protocol,
                raw_line=raw_prefix.raw_line,
                is_ambiguous=raw_prefix.is_ambiguous,
                timestamp=timestamp,
                vlan=vlan,
                interface=interface
            )
            
            prefixes.append(parsed)
        
        self.logger.info(f"Parsed {len(prefixes)} prefixes from routing table on {device}")
        return prefixes
    
    def _extract_protocol(self, line: str) -> str:
        """
        Extract routing protocol code from route line.
        
        Cisco routing table lines typically start with a route code:
        C    192.168.1.0/24 is directly connected, GigabitEthernet0/0
        L    192.168.1.1/32 is directly connected, GigabitEthernet0/0
        B    10.0.0.0/8 [20/0] via 192.168.1.254, 00:01:23
        
        Args:
            line: Route line from routing table
            
        Returns:
            Protocol code (B, D, C, L, S, O, etc.) or empty string
        """
        line_stripped = line.strip()
        
        # Check for route codes at the beginning of the line
        for code in self.route_codes.keys():
            if line_stripped.startswith(code + ' ') or line_stripped.startswith(code + '\t'):
                return self.route_codes[code]
        
        # Check for codes with asterisks (like "B*" for BGP best path)
        for code in self.route_codes.keys():
            if line_stripped.startswith(code + '*'):
                return self.route_codes[code]
        
        return ''
    
    def _extract_interface(self, line: str) -> Optional[str]:
        """
        Extract interface name from routing table line.
        
        Cisco routing table lines with interfaces typically look like:
        C    192.168.1.0/24 is directly connected, GigabitEthernet0/0
        L    192.168.1.1/32 is directly connected, Vlan100
        O    10.0.0.0/8 [110/2] via 192.168.1.254, 00:01:23, GigabitEthernet0/1
        
        Args:
            line: Route line from routing table
            
        Returns:
            Interface name or None if not found
        """
        # Look for "directly connected" pattern
        if 'directly connected' in line.lower():
            # Interface name typically follows "directly connected,"
            match = re.search(r'directly connected,\s+(\S+)', line, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Look for interface at end of line (after via clause)
        # Pattern: via <ip>, <time>, <interface>
        match = re.search(r'via\s+[\d\.]+,\s+[\d:]+,\s+(\S+)', line)
        if match:
            return match.group(1)
        
        # Look for common interface patterns anywhere in the line
        interface_patterns = [
            r'\b(GigabitEthernet\d+/\d+(?:/\d+)?)\b',
            r'\b(FastEthernet\d+/\d+(?:/\d+)?)\b',
            r'\b(TenGigabitEthernet\d+/\d+(?:/\d+)?)\b',
            r'\b(Ethernet\d+/\d+(?:/\d+)?)\b',
            r'\b(Vlan\d+)\b',
            r'\b(Loopback\d+)\b',
            r'\b(Port-channel\d+)\b',
            r'\b(Tunnel\d+)\b',
        ]
        
        for pattern in interface_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_vlan(self, interface: str) -> Optional[int]:
        """
        Extract VLAN number from interface name.
        
        Args:
            interface: Interface name (e.g., "Vlan100", "GigabitEthernet0/0")
            
        Returns:
            VLAN number or None if interface is not a VLAN interface
        """
        if not interface:
            return None
        
        # Match "Vlan" followed by digits
        match = re.match(r'Vlan(\d+)', interface, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        return None


class BGPParser:
    """Parses 'show ip bgp' output."""
    
    def __init__(self):
        """Initialize BGP parser."""
        self.logger = logging.getLogger(__name__)
        self.extractor = PrefixExtractor()
    
    def parse(self, output: str, device: str, platform: str, vrf: str) -> List[ParsedPrefix]:
        """
        Parse BGP output and extract all prefixes.
        
        Marks ambiguous prefixes (without explicit length) for resolution.
        
        Args:
            output: Raw command output from 'show ip bgp'
            device: Device hostname
            platform: Device platform (ios, iosxe, nxos)
            vrf: VRF name ("global" for global table)
            
        Returns:
            List of ParsedPrefix objects with metadata
            
        Requirements:
            - 5.3: Extract BGP prefixes with or without explicit length
            - 5.6: Preserve raw output lines
            - 8.1-8.7: Tag with complete metadata
        """
        prefixes = []
        timestamp = datetime.now()
        
        if not output or not output.strip():
            self.logger.warning(f"Empty BGP output for {device}")
            return prefixes
        
        lines = output.split('\n')
        
        for line in lines:
            # Skip empty lines and header lines
            if not line.strip():
                continue
            
            # Skip lines that are clearly headers
            if any(keyword in line for keyword in ['Network', 'Next Hop', 'Metric', 'LocPrf', 
                                                     'Weight', 'Path', 'Route Distinguisher']):
                continue
            
            # Extract prefix from line
            raw_prefix = self.extractor.extract_from_bgp_line(line)
            if not raw_prefix:
                continue
            
            # Create ParsedPrefix object
            # All BGP prefixes have protocol 'B' and source 'bgp'
            parsed = ParsedPrefix(
                device=device,
                platform=platform,
                vrf=vrf,
                prefix_str=raw_prefix.prefix_str,
                source='bgp',
                protocol='B',
                raw_line=raw_prefix.raw_line,
                is_ambiguous=raw_prefix.is_ambiguous,
                timestamp=timestamp
            )
            
            prefixes.append(parsed)
        
        self.logger.info(f"Parsed {len(prefixes)} BGP prefixes from {device} "
                        f"({sum(1 for p in prefixes if p.is_ambiguous)} ambiguous)")
        return prefixes


class CommandOutputParser:
    """Main parser orchestrator."""
    
    def __init__(self):
        """Initialize command output parser."""
        self.logger = logging.getLogger(__name__)
        self.route_parser = RoutingTableParser()
        self.bgp_parser = BGPParser()
    
    def parse_collection_result(self, result) -> List[ParsedPrefix]:
        """
        Parse all command outputs from a device collection.
        
        Args:
            result: DeviceCollectionResult with raw command outputs
            
        Returns:
            List of all parsed prefixes with metadata
            
        Requirements:
            - 5.1-5.6: Extract all prefix formats
            - 8.1-8.7: Tag with complete metadata
        """
        all_prefixes = []
        
        if not result.success:
            self.logger.warning(f"Skipping parsing for failed device: {result.device}")
            return all_prefixes
        
        # Parse each command output
        for command, output in result.raw_outputs.items():
            if not output:
                continue
            
            # Determine which parser to use based on command
            if 'show ip route' in command:
                # Determine VRF from command
                vrf = self._extract_vrf_from_command(command)
                
                # Parse routing table
                prefixes = self.route_parser.parse(
                    output, result.device, result.platform, vrf
                )
                all_prefixes.extend(prefixes)
                
            elif 'show ip bgp' in command:
                # Determine VRF from command
                vrf = self._extract_vrf_from_command(command)
                
                # Parse BGP output
                prefixes = self.bgp_parser.parse(
                    output, result.device, result.platform, vrf
                )
                all_prefixes.extend(prefixes)
        
        self.logger.info(f"Parsed total of {len(all_prefixes)} prefixes from {result.device}")
        return all_prefixes
    
    def _extract_vrf_from_command(self, command: str) -> str:
        """
        Extract VRF name from command string.
        
        Args:
            command: Command string (e.g., "show ip route vrf WAN")
            
        Returns:
            VRF name or "global" if no VRF specified
        """
        # Look for "vrf <name>" pattern
        vrf_match = re.search(r'vrf\s+["\']?([^\s"\']+)["\']?', command, re.IGNORECASE)
        if vrf_match:
            return vrf_match.group(1)
        
        # Look for "vpnv4 vrf <name>" pattern (IOS BGP)
        vpnv4_match = re.search(r'vpnv4\s+vrf\s+["\']?([^\s"\']+)["\']?', command, re.IGNORECASE)
        if vpnv4_match:
            return vpnv4_match.group(1)
        
        return 'global'
