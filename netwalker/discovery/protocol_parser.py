"""
Protocol Parser for CDP and LLDP neighbor discovery
"""

import re
import logging
from typing import List, Dict, Optional, Any
from netwalker.connection.data_models import NeighborInfo


class ProtocolParser:
    """Parses CDP and LLDP protocol outputs to extract neighbor information"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # CDP parsing patterns
        self.cdp_device_pattern = re.compile(r'Device ID:\s*(.+)', re.IGNORECASE)
        self.cdp_ip_pattern = re.compile(r'IP address:\s*(\d+\.\d+\.\d+\.\d+)', re.IGNORECASE)
        self.cdp_platform_pattern = re.compile(r'Platform:\s*(.+?),', re.IGNORECASE)
        self.cdp_capabilities_pattern = re.compile(r'Capabilities:\s*(.+)', re.IGNORECASE)
        self.cdp_interface_pattern = re.compile(r'Interface:\s*(.+?),\s*Port ID \(outgoing port\):\s*(.+)', re.IGNORECASE)
        
        # LLDP parsing patterns
        self.lldp_system_name_pattern = re.compile(r'System Name:\s*(.+)', re.IGNORECASE)
        self.lldp_system_desc_pattern = re.compile(r'System Description:\s*(.+)', re.IGNORECASE)
        self.lldp_port_id_pattern = re.compile(r'Port id:\s*(.+)', re.IGNORECASE)
        self.lldp_local_port_pattern = re.compile(r'Local Intf:\s*(.+)', re.IGNORECASE)
        self.lldp_capabilities_pattern = re.compile(r'System Capabilities:\s*(.+)', re.IGNORECASE)
        
    def parse_cdp_neighbors(self, cdp_output: str) -> List[NeighborInfo]:
        """
        Parse CDP neighbors detail output
        
        Args:
            cdp_output: Output from 'show cdp neighbors detail' command
            
        Returns:
            List of NeighborInfo objects
        """
        neighbors = []
        
        if not cdp_output:
            self.logger.warning("Empty CDP output provided")
            return neighbors
            
        try:
            # Split output into individual device entries
            # CDP entries are typically separated by "-------------------------"
            device_entries = re.split(r'-{20,}', cdp_output)
            
            for entry in device_entries:
                if not entry.strip():
                    continue
                    
                neighbor = self._parse_cdp_entry(entry)
                if neighbor:
                    neighbors.append(neighbor)
                    
            self.logger.info(f"Parsed {len(neighbors)} CDP neighbors")
            
        except Exception as e:
            self.logger.error(f"Error parsing CDP output: {str(e)}")
            
        return neighbors
    
    def _parse_cdp_entry(self, entry: str) -> Optional[NeighborInfo]:
        """
        Parse a single CDP neighbor entry
        
        Args:
            entry: Single CDP neighbor entry text
            
        Returns:
            NeighborInfo object or None if parsing failed
        """
        try:
            # Extract device ID (hostname)
            device_match = self.cdp_device_pattern.search(entry)
            if not device_match:
                return None
            device_id = device_match.group(1).strip()
            
            # Extract IP address
            ip_match = self.cdp_ip_pattern.search(entry)
            ip_address = ip_match.group(1) if ip_match else None
            
            # Extract platform
            platform_match = self.cdp_platform_pattern.search(entry)
            platform = platform_match.group(1).strip() if platform_match else "Unknown"
            
            # Extract capabilities
            cap_match = self.cdp_capabilities_pattern.search(entry)
            capabilities_str = cap_match.group(1).strip() if cap_match else ""
            capabilities = [cap.strip() for cap in capabilities_str.split() if cap.strip()]
            
            # Extract interface information
            interface_match = self.cdp_interface_pattern.search(entry)
            if interface_match:
                local_interface = interface_match.group(1).strip()
                remote_interface = interface_match.group(2).strip()
            else:
                local_interface = "Unknown"
                remote_interface = "Unknown"
            
            return NeighborInfo(
                device_id=device_id,
                local_interface=local_interface,
                remote_interface=remote_interface,
                platform=platform,
                capabilities=capabilities,
                ip_address=ip_address,
                protocol="CDP"
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing CDP entry: {str(e)}")
            return None
    
    def parse_lldp_neighbors(self, lldp_output: str) -> List[NeighborInfo]:
        """
        Parse LLDP neighbors detail output
        
        Args:
            lldp_output: Output from 'show lldp neighbors detail' command
            
        Returns:
            List of NeighborInfo objects
        """
        neighbors = []
        
        if not lldp_output:
            self.logger.warning("Empty LLDP output provided")
            return neighbors
            
        try:
            # Split output into individual device entries
            # LLDP entries are typically separated by "Local Intf:" or similar patterns
            device_entries = re.split(r'(?=Local Intf:)', lldp_output)
            
            for entry in device_entries:
                if not entry.strip():
                    continue
                    
                neighbor = self._parse_lldp_entry(entry)
                if neighbor:
                    neighbors.append(neighbor)
                    
            self.logger.info(f"Parsed {len(neighbors)} LLDP neighbors")
            
        except Exception as e:
            self.logger.error(f"Error parsing LLDP output: {str(e)}")
            
        return neighbors
    
    def _parse_lldp_entry(self, entry: str) -> Optional[NeighborInfo]:
        """
        Parse a single LLDP neighbor entry
        
        Args:
            entry: Single LLDP neighbor entry text
            
        Returns:
            NeighborInfo object or None if parsing failed
        """
        try:
            # Extract system name (hostname)
            name_match = self.lldp_system_name_pattern.search(entry)
            if not name_match:
                return None
            device_id = name_match.group(1).strip()
            
            # Extract local interface
            local_match = self.lldp_local_port_pattern.search(entry)
            local_interface = local_match.group(1).strip() if local_match else "Unknown"
            
            # Extract remote port ID
            port_match = self.lldp_port_id_pattern.search(entry)
            remote_interface = port_match.group(1).strip() if port_match else "Unknown"
            
            # Extract system description (contains platform info)
            desc_match = self.lldp_system_desc_pattern.search(entry)
            platform = desc_match.group(1).strip() if desc_match else "Unknown"
            
            # Extract capabilities
            cap_match = self.lldp_capabilities_pattern.search(entry)
            capabilities_str = cap_match.group(1).strip() if cap_match else ""
            capabilities = [cap.strip() for cap in capabilities_str.split(',') if cap.strip()]
            
            return NeighborInfo(
                device_id=device_id,
                local_interface=local_interface,
                remote_interface=remote_interface,
                platform=platform,
                capabilities=capabilities,
                ip_address=None,  # LLDP doesn't always provide IP
                protocol="LLDP"
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing LLDP entry: {str(e)}")
            return None
    
    def extract_hostname(self, neighbor_entry: NeighborInfo) -> str:
        """
        Extract clean hostname from neighbor device ID
        
        Args:
            neighbor_entry: NeighborInfo object
            
        Returns:
            Clean hostname string
        """
        device_id = neighbor_entry.device_id
        
        # Remove common suffixes and clean up hostname
        # Handle FQDN by taking only the hostname part
        if '.' in device_id:
            hostname = device_id.split('.')[0]
        else:
            hostname = device_id
            
        # Remove any trailing whitespace or special characters
        hostname = re.sub(r'[^\w-]', '', hostname)
        
        # Ensure hostname is not longer than 36 characters (requirement)
        if len(hostname) > 36:
            hostname = hostname[:36]
            self.logger.warning(f"Truncated hostname to 36 characters: {hostname}")
            
        return hostname
    
    def parse_multi_protocol_output(self, cdp_output: str, lldp_output: str) -> List[NeighborInfo]:
        """
        Parse both CDP and LLDP outputs and combine results
        
        Args:
            cdp_output: CDP neighbors detail output
            lldp_output: LLDP neighbors detail output
            
        Returns:
            Combined list of unique neighbors from both protocols
        """
        all_neighbors = []
        
        # Parse CDP neighbors
        cdp_neighbors = self.parse_cdp_neighbors(cdp_output)
        all_neighbors.extend(cdp_neighbors)
        
        # Parse LLDP neighbors
        lldp_neighbors = self.parse_lldp_neighbors(lldp_output)
        
        # Add LLDP neighbors, avoiding duplicates based on device_id
        existing_device_ids = {self.extract_hostname(n) for n in cdp_neighbors}
        
        for lldp_neighbor in lldp_neighbors:
            lldp_hostname = self.extract_hostname(lldp_neighbor)
            if lldp_hostname not in existing_device_ids:
                all_neighbors.append(lldp_neighbor)
            else:
                self.logger.debug(f"Skipping duplicate neighbor: {lldp_hostname}")
        
        self.logger.info(f"Combined parsing found {len(all_neighbors)} unique neighbors")
        return all_neighbors
    
    def adapt_commands_for_platform(self, platform: str) -> Dict[str, str]:
        """
        Adapt command syntax for different platforms
        
        Args:
            platform: Detected platform (IOS/IOS-XE/NX-OS)
            
        Returns:
            Dictionary of commands adapted for the platform
        """
        commands = {
            'cdp_neighbors': 'show cdp neighbors detail',
            'lldp_neighbors': 'show lldp neighbors detail',
            'version': 'show version'
        }
        
        # Platform-specific command adaptations
        if platform.upper() == 'NX-OS':
            # NX-OS uses slightly different syntax
            commands['cdp_neighbors'] = 'show cdp neighbors detail'
            commands['lldp_neighbors'] = 'show lldp neighbors detail'
        elif platform.upper() in ['IOS', 'IOS-XE']:
            # Standard IOS commands
            commands['cdp_neighbors'] = 'show cdp neighbors detail'
            commands['lldp_neighbors'] = 'show lldp neighbors detail'
        
        self.logger.debug(f"Adapted commands for platform {platform}: {commands}")
        return commands