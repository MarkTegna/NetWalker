"""
VLAN Parser for extracting VLAN information from command output

Parses VLAN command output to extract structured VLAN information 
including port and PortChannel counts.
"""

import re
import logging
from typing import List, Tuple, Optional
from datetime import datetime

from netwalker.connection.data_models import VLANInfo


class VLANParser:
    """Parses VLAN command output to extract structured VLAN information"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Regex patterns for parsing VLAN information
        self.ios_vlan_pattern = re.compile(
            r'^(\d+)\s+(\S+)\s+\S+\s+(.*)$', 
            re.MULTILINE
        )
        
        self.nxos_vlan_pattern = re.compile(
            r'^(\d+)\s+(\S+)\s+\S+\s+(.*)$', 
            re.MULTILINE
        )
        
        # Pattern for port interfaces (Fa, Gi, Te, Eth, etc.)
        self.port_pattern = re.compile(
            r'\b(?:Fa|Gi|Te|Eth|Se|Hu)\d+/\d+(?:/\d+)?(?:\.\d+)?\b', 
            re.IGNORECASE
        )
        
        # Pattern for PortChannel interfaces
        self.portchannel_pattern = re.compile(
            r'\bPo\d+(?:\.\d+)?\b', 
            re.IGNORECASE
        )
        
        self.logger.debug("VLANParser initialized with parsing patterns")
    
    def parse_vlan_output(self, output: str, platform: str, device_hostname: str = "", device_ip: str = "") -> List[VLANInfo]:
        """
        Parse VLAN output based on platform
        
        Args:
            output: VLAN command output
            platform: Device platform (IOS, IOS-XE, NX-OS)
            device_hostname: Source device hostname
            device_ip: Source device IP address
            
        Returns:
            List of VLANInfo objects
        """
        if not output or not output.strip():
            self.logger.debug("Empty VLAN output provided")
            return []
        
        platform = platform.upper() if platform else 'UNKNOWN'
        
        try:
            if platform in ['IOS', 'IOS-XE']:
                vlans = self._parse_ios_vlan_brief(output, device_hostname, device_ip)
            elif platform == 'NX-OS':
                vlans = self._parse_nxos_vlan(output, device_hostname, device_ip)
            else:
                # Try both parsers for unknown platforms
                vlans = self._parse_ios_vlan_brief(output, device_hostname, device_ip)
                if not vlans:
                    vlans = self._parse_nxos_vlan(output, device_hostname, device_ip)
            
            self.logger.info(f"Parsed {len(vlans)} VLANs from {platform} output for device {device_hostname}")
            return vlans
            
        except Exception as e:
            error_msg = f"Error parsing VLAN output for {platform}: {str(e)}"
            self.logger.error(error_msg)
            self.logger.debug(f"Problematic output: {output[:500]}...")  # Log first 500 chars
            return []
    
    def _parse_ios_vlan_brief(self, output: str, device_hostname: str, device_ip: str) -> List[VLANInfo]:
        """
        Parse IOS/IOS-XE 'show vlan brief' output
        
        Expected format:
        VLAN Name                             Status    Ports
        ---- -------------------------------- --------- -------------------------------
        1    default                          active    Fa0/1, Fa0/2, Fa0/3, Po1
        10   VLAN0010                         active    Gi0/1, Gi0/2
        """
        vlans = []
        lines = output.split('\n')
        
        # Skip header lines and find data section
        data_started = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip headers - look for the dashed line or "VLAN Name" header
            if 'VLAN Name' in line or '----' in line:
                data_started = True
                continue
            
            if not data_started:
                continue
            
            # Parse VLAN line using regex
            match = self.ios_vlan_pattern.match(line)
            if match:
                try:
                    vlan_id = int(match.group(1))
                    vlan_name = match.group(2)
                    ports_str = match.group(3).strip()
                    
                    # Validate VLAN ID range
                    if not (1 <= vlan_id <= 4094):
                        self.logger.warning(f"VLAN ID {vlan_id} outside valid range (1-4094), skipping")
                        continue
                    
                    # Count ports and PortChannels (ignore status field)
                    port_count, portchannel_count = self._count_ports_and_portchannels(ports_str)
                    
                    vlan_info = VLANInfo(
                        vlan_id=vlan_id,
                        vlan_name=vlan_name,
                        port_count=port_count,
                        portchannel_count=portchannel_count,
                        device_hostname=device_hostname,
                        device_ip=device_ip,
                        collection_timestamp=datetime.now()
                    )
                    vlans.append(vlan_info)
                    
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Error parsing VLAN line '{line}': {e}")
                    continue
        
        return vlans
    
    def _parse_nxos_vlan(self, output: str, device_hostname: str, device_ip: str) -> List[VLANInfo]:
        """
        Parse NX-OS 'show vlan' output
        
        Expected format:
        VLAN Name                             Status    Ports
        ---- -------------------------------- --------- -------------------------------
        1    default                          active    Eth1/1, Eth1/2, Po10
        10   VLAN0010                         active    Eth1/3, Eth1/4
        """
        vlans = []
        lines = output.split('\n')
        
        # Skip header lines and find data section
        data_started = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip headers - look for the dashed line or "VLAN Name" header
            if 'VLAN Name' in line or '----' in line:
                data_started = True
                continue
            
            if not data_started:
                continue
            
            # Parse VLAN line using regex
            match = self.nxos_vlan_pattern.match(line)
            if match:
                try:
                    vlan_id = int(match.group(1))
                    vlan_name = match.group(2)
                    ports_str = match.group(3).strip()
                    
                    # Validate VLAN ID range
                    if not (1 <= vlan_id <= 4094):
                        self.logger.warning(f"VLAN ID {vlan_id} outside valid range (1-4094), skipping")
                        continue
                    
                    # Count ports and PortChannels (ignore status field)
                    port_count, portchannel_count = self._count_ports_and_portchannels(ports_str)
                    
                    vlan_info = VLANInfo(
                        vlan_id=vlan_id,
                        vlan_name=vlan_name,
                        port_count=port_count,
                        portchannel_count=portchannel_count,
                        device_hostname=device_hostname,
                        device_ip=device_ip,
                        collection_timestamp=datetime.now()
                    )
                    vlans.append(vlan_info)
                    
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Error parsing VLAN line '{line}': {e}")
                    continue
        
        return vlans
    
    def _count_ports_and_portchannels(self, ports_str: str) -> Tuple[int, int]:
        """
        Count physical ports and PortChannels from port assignment string
        
        Args:
            ports_str: String containing port assignments (e.g., "Fa0/1, Fa0/2, Po1")
            
        Returns:
            Tuple of (port_count, portchannel_count)
        """
        if not ports_str or ports_str.strip() == '':
            return 0, 0
        
        try:
            # Find all physical port interfaces
            ports = self.port_pattern.findall(ports_str)
            port_count = len(ports)
            
            # Find all PortChannel interfaces
            portchannels = self.portchannel_pattern.findall(ports_str)
            portchannel_count = len(portchannels)
            
            self.logger.debug(f"Counted {port_count} ports and {portchannel_count} PortChannels in: {ports_str}")
            
            return port_count, portchannel_count
            
        except Exception as e:
            self.logger.warning(f"Error counting ports in '{ports_str}': {e}")
            return 0, 0
    
    def validate_vlan_data(self, vlan_info: VLANInfo) -> bool:
        """
        Validate VLAN data for consistency and correctness
        
        Args:
            vlan_info: VLAN information to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Validate VLAN ID range
            if not (1 <= vlan_info.vlan_id <= 4094):
                self.logger.warning(f"Invalid VLAN ID: {vlan_info.vlan_id}")
                return False
            
            # Validate VLAN name
            if not vlan_info.vlan_name or len(vlan_info.vlan_name.strip()) == 0:
                self.logger.warning(f"Invalid VLAN name: '{vlan_info.vlan_name}'")
                return False
            
            # Validate port counts are non-negative
            if vlan_info.port_count < 0 or vlan_info.portchannel_count < 0:
                self.logger.warning(f"Invalid port counts: ports={vlan_info.port_count}, portchannels={vlan_info.portchannel_count}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating VLAN data: {e}")
            return False
    
    def handle_parsing_error(self, output: str, error: Exception, device_hostname: str) -> None:
        """
        Handle parsing errors with appropriate logging
        
        Args:
            output: The problematic output
            error: The exception that occurred
            device_hostname: Device that generated the output
        """
        error_msg = f"VLAN parsing error for device {device_hostname}: {str(error)}"
        self.logger.error(error_msg)
    
    def detect_duplicate_vlans(self, vlans: List[VLANInfo]) -> List[VLANInfo]:
        """
        Detect and handle duplicate VLAN entries
        
        Args:
            vlans: List of VLAN information objects
            
        Returns:
            List of unique VLAN entries with duplicates resolved
        """
        seen_vlans = {}
        unique_vlans = []
        duplicates_found = []
        
        for vlan in vlans:
            vlan_key = (vlan.device_hostname, vlan.vlan_id)
            
            if vlan_key in seen_vlans:
                # Duplicate found
                existing_vlan = seen_vlans[vlan_key]
                duplicates_found.append((existing_vlan, vlan))
                
                # Keep the one with more complete information
                if (vlan.port_count + vlan.portchannel_count) > (existing_vlan.port_count + existing_vlan.portchannel_count):
                    # Replace with more complete entry
                    seen_vlans[vlan_key] = vlan
                    # Update in unique_vlans list
                    for i, unique_vlan in enumerate(unique_vlans):
                        if (unique_vlan.device_hostname == existing_vlan.device_hostname and 
                            unique_vlan.vlan_id == existing_vlan.vlan_id):
                            unique_vlans[i] = vlan
                            break
                
                self.logger.warning(f"Duplicate VLAN {vlan.vlan_id} found on device {vlan.device_hostname}")
            else:
                seen_vlans[vlan_key] = vlan
                unique_vlans.append(vlan)
        
        if duplicates_found:
            self.logger.info(f"Resolved {len(duplicates_found)} duplicate VLAN entries")
        
        return unique_vlans
    
    def validate_vlan_consistency(self, vlans: List[VLANInfo]) -> List[str]:
        """
        Validate VLAN data consistency and generate warnings
        
        Args:
            vlans: List of VLAN information objects
            
        Returns:
            List of warning messages for inconsistent data
        """
        warnings = []
        
        # Group VLANs by ID across devices
        vlan_groups = {}
        for vlan in vlans:
            if vlan.vlan_id not in vlan_groups:
                vlan_groups[vlan.vlan_id] = []
            vlan_groups[vlan.vlan_id].append(vlan)
        
        # Check for inconsistent VLAN names across devices
        for vlan_id, vlan_list in vlan_groups.items():
            if len(vlan_list) > 1:
                names = set(vlan.vlan_name for vlan in vlan_list)
                if len(names) > 1:
                    devices = [vlan.device_hostname for vlan in vlan_list]
                    warning = f"VLAN {vlan_id} has inconsistent names across devices {devices}: {list(names)}"
                    warnings.append(warning)
                    self.logger.warning(warning)
        
        # Check for unusual port counts (potential data issues)
        for vlan in vlans:
            total_ports = vlan.port_count + vlan.portchannel_count
            if total_ports > 100:  # Unusually high port count
                warning = f"VLAN {vlan.vlan_id} on {vlan.device_hostname} has unusually high port count: {total_ports}"
                warnings.append(warning)
                self.logger.warning(warning)
        
        return warnings
    
    def sanitize_vlan_name(self, vlan_name: str) -> str:
        """
        Sanitize VLAN name to handle special characters properly
        
        Args:
            vlan_name: Raw VLAN name from device output
            
        Returns:
            Sanitized VLAN name safe for Excel and reporting
        """
        if not vlan_name:
            return "UNNAMED"
        
        # Remove leading/trailing whitespace
        sanitized = vlan_name.strip()
        
        # Replace problematic characters for Excel
        problematic_chars = ['[', ']', '*', '?', ':', '\\', '/', '<', '>', '|']
        for char in problematic_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Limit length to reasonable size
        if len(sanitized) > 32:
            sanitized = sanitized[:29] + "..."
            self.logger.debug(f"Truncated long VLAN name: {vlan_name} -> {sanitized}")
        
        # Ensure it's not empty after sanitization
        if not sanitized or sanitized.isspace():
            sanitized = "UNNAMED"
        
        return sanitized
        
        # Log a sample of the problematic output for debugging
        sample_output = output[:200] + "..." if len(output) > 200 else output
        self.logger.debug(f"Problematic VLAN output sample: {sample_output}")
    
    def detect_duplicate_vlans(self, vlans: List[VLANInfo]) -> List[VLANInfo]:
        """
        Detect and log duplicate VLAN entries on the same device
        
        Args:
            vlans: List of VLAN information
            
        Returns:
            List of VLANs with duplicates logged but included
        """
        seen_vlans = {}
        duplicates = []
        
        for vlan in vlans:
            vlan_key = (vlan.device_hostname, vlan.vlan_id)
            
            if vlan_key in seen_vlans:
                duplicates.append(vlan)
                self.logger.warning(
                    f"Duplicate VLAN {vlan.vlan_id} found on device {vlan.device_hostname}: "
                    f"'{seen_vlans[vlan_key].vlan_name}' and '{vlan.vlan_name}'"
                )
            else:
                seen_vlans[vlan_key] = vlan
        
        if duplicates:
            self.logger.info(f"Found {len(duplicates)} duplicate VLAN entries, including all in results")
        
        return vlans  # Return all VLANs including duplicates for manual review