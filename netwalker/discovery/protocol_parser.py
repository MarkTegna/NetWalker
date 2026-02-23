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
        
        # CDP parsing patterns - enhanced for NEXUS
        self.cdp_device_pattern = re.compile(r'Device ID:\s*(.+)', re.IGNORECASE)
        self.cdp_ip_pattern = re.compile(r'(?:IP address|Entry address\(es\)):\s*(\d+\.\d+\.\d+\.\d+)', re.IGNORECASE)
        self.cdp_platform_pattern = re.compile(r'Platform:\s*(.+?)(?:,|\n)', re.IGNORECASE)
        self.cdp_capabilities_pattern = re.compile(r'Capabilities:\s*(.+)', re.IGNORECASE)
        self.cdp_interface_pattern = re.compile(r'Interface:\s*(.+?),\s*Port ID \(outgoing port\):\s*(.+)', re.IGNORECASE)
        
        # Enhanced patterns for NEXUS CDP output - fixed for actual format
        self.nexus_cdp_interface_pattern = re.compile(r'Local Intrfce:\s*(.+?)\s+Holdtme:\s*\d+\s+Capability:\s*.+?\s+Port ID:\s*(.+)', re.IGNORECASE | re.DOTALL)
        self.nexus_cdp_mgmt_pattern = re.compile(r'Management address\(es\):\s*IP address:\s*(\d+\.\d+\.\d+\.\d+)', re.IGNORECASE)
        
        # Additional patterns for IPv4 Address format found in actual CDP output
        self.cdp_ipv4_pattern = re.compile(r'IPv4 Address:\s*(\d+\.\d+\.\d+\.\d+)', re.IGNORECASE)
        self.cdp_interface_address_pattern = re.compile(r'Interface address\(es\):\s*\d+\s*IPv4 Address:\s*(\d+\.\d+\.\d+\.\d+)', re.IGNORECASE | re.DOTALL)
        
        # Version pattern for extracting version information (used for Nutanix detection)
        self.cdp_version_pattern = re.compile(r'Version\s*:\s*(.+?)(?:\n|$)', re.IGNORECASE)
        
        # LLDP parsing patterns - enhanced for NEXUS
        self.lldp_system_name_pattern = re.compile(r'System Name:\s*(.+)', re.IGNORECASE)
        self.lldp_system_desc_pattern = re.compile(r'System Description:\s*(.+)', re.IGNORECASE)
        self.lldp_port_id_pattern = re.compile(r'Port id:\s*(.+)', re.IGNORECASE)
        self.lldp_local_port_pattern = re.compile(r'Local Intf:\s*(.+)', re.IGNORECASE)
        self.lldp_capabilities_pattern = re.compile(r'System Capabilities:\s*(.+)', re.IGNORECASE)
        
        # Enhanced NEXUS LLDP patterns
        self.nexus_lldp_chassis_pattern = re.compile(r'Chassis id:\s*(.+)', re.IGNORECASE)
        self.nexus_lldp_mgmt_pattern = re.compile(r'Management Addresses:\s*(.+)', re.IGNORECASE)
        
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
        Parse a single CDP neighbor entry with enhanced NEXUS support
        
        Args:
            entry: Single CDP neighbor entry text
            
        Returns:
            NeighborInfo object or None if parsing failed
        """
        try:
            self.logger.debug(f"Parsing CDP entry: {entry[:200]}...")
            
            # Extract device ID (hostname)
            device_match = self.cdp_device_pattern.search(entry)
            if not device_match:
                self.logger.debug("No Device ID found in CDP entry")
                return None
            device_id = device_match.group(1).strip()
            
            # Clean up device ID - remove FQDN if present
            if '.' in device_id:
                device_id = device_id.split('.')[0]
            
            self.logger.debug(f"Found CDP device ID: {device_id}")
            
            # Extract IP address - try multiple patterns for different CDP formats
            ip_address = None
            
            # Try IPv4 Address pattern first (most common in actual output)
            ipv4_match = self.cdp_ipv4_pattern.search(entry)
            if ipv4_match:
                ip_address = ipv4_match.group(1)
                self.logger.debug(f"Found IP using IPv4 Address pattern: {ip_address}")
            
            # Try Interface address pattern (with context)
            if not ip_address:
                interface_addr_match = self.cdp_interface_address_pattern.search(entry)
                if interface_addr_match:
                    ip_address = interface_addr_match.group(1)
                    self.logger.debug(f"Found IP using Interface address pattern: {ip_address}")
            
            # Standard CDP IP pattern (fallback)
            if not ip_address:
                ip_match = self.cdp_ip_pattern.search(entry)
                if ip_match:
                    ip_address = ip_match.group(1)
                    self.logger.debug(f"Found IP using standard pattern: {ip_address}")
            
            # NEXUS management address pattern (fallback)
            if not ip_address:
                mgmt_match = self.nexus_cdp_mgmt_pattern.search(entry)
                if mgmt_match:
                    ip_address = mgmt_match.group(1)
                    self.logger.debug(f"Found IP using NEXUS mgmt pattern: {ip_address}")
            
            if not ip_address:
                self.logger.debug(f"No IP address found in CDP entry for device {device_id}")
            
            # Extract platform
            platform_match = self.cdp_platform_pattern.search(entry)
            platform = platform_match.group(1).strip() if platform_match else "Unknown"
            
            # Clean up platform string
            if ',' in platform:
                platform = platform.split(',')[0].strip()
            
            # Extract version information
            version_match = self.cdp_version_pattern.search(entry)
            version = version_match.group(1).strip() if version_match else None
            
            # Nutanix detection: If platform contains "Linux" and version contains "Nutanix"
            # Use the version information as the platform
            if version and 'Linux' in platform and 'Nutanix' in version:
                platform = version
                self.logger.info(f"Detected Nutanix device: {device_id}, Platform set to: {platform}")
            
            # Aruba AP detection: If platform contains "Aruba AP" or "AOS-"
            # Keep the platform as-is (it already has good information from LLDP)
            if 'Aruba AP' in platform or 'AOS-' in platform:
                self.logger.info(f"Detected Aruba AP device: {device_id}, Platform: {platform}")
            
            # Cisco ATA detection: If platform contains "Cisco ATA" or "ATA" followed by numbers
            # These are Analog Telephone Adapters (VoIP devices)
            if 'Cisco ATA' in platform or ('ATA' in platform and any(char.isdigit() for char in platform)):
                self.logger.info(f"Detected Cisco ATA device: {device_id}, Platform: {platform}")
            
            # Axis camera detection: If platform is "AXIS" or device_id starts with "axis-"
            # Store full version string which contains model information
            if platform.upper() == 'AXIS' or device_id.lower().startswith('axis-'):
                if version:
                    # Version string often contains model info like "P3265-LV Dome Camera"
                    platform = f"AXIS|{version}"  # Use delimiter to parse later
                else:
                    platform = "AXIS"
                self.logger.info(f"Detected Axis camera device: {device_id}, Platform: {platform}")
            
            # Cisco Paging Group detection: If device_id contains "paginggroup"
            # These are Cisco Unified Communications Manager paging group devices
            if 'paginggroup' in device_id.lower():
                # These devices typically show as "Unknown" platform in CDP
                # Mark them with a recognizable platform string
                if platform == 'Unknown' or not platform:
                    platform = 'Cisco Paging Group'
                self.logger.info(f"Detected Cisco Paging Group device: {device_id}, Platform: {platform}")
                # Add VoIP capability
                if 'VoIP' not in capabilities and 'voip' not in [c.lower() for c in capabilities]:
                    capabilities.append('VoIP')
            
            # Cisco SG300 detection: Parse platform string to extract model and PID
            # Platform format: "Cisco SG300-20 (PID:SRW2016-K9)-VSD"
            if 'SG300' in platform or 'SG200' in platform or 'SG500' in platform:
                # Extract model (e.g., "SG300-20", "SG300-10P")
                model_match = re.search(r'(SG\d+-\d+[A-Z]*)', platform, re.IGNORECASE)
                if model_match:
                    model = model_match.group(1)
                    
                    # Extract PID (Product ID) if present
                    pid_match = re.search(r'PID:([A-Z0-9-]+)', platform, re.IGNORECASE)
                    pid = pid_match.group(1) if pid_match else None
                    
                    # Store as "model|PID" for later parsing
                    if pid:
                        platform = f"{model}|{pid}"
                    else:
                        platform = model
                    
                    self.logger.info(f"Detected Cisco SG300 device: {device_id}, Model: {model}, PID: {pid}")
                else:
                    # Fallback: just use "SG300" if we can't parse the model
                    platform = "SG300"
                    self.logger.info(f"Detected Cisco SG300 device: {device_id} (generic)")
            
            self.logger.debug(f"Found CDP platform: {platform}")
            
            # Extract capabilities
            cap_match = self.cdp_capabilities_pattern.search(entry)
            capabilities_str = cap_match.group(1).strip() if cap_match else ""
            capabilities = [cap.strip() for cap in capabilities_str.split() if cap.strip()]
            
            self.logger.debug(f"Found CDP capabilities: {capabilities}")
            
            # Extract interface information - try multiple patterns
            local_interface = "Unknown"
            remote_interface = "Unknown"
            
            # Standard CDP interface pattern
            interface_match = self.cdp_interface_pattern.search(entry)
            if interface_match:
                local_interface = interface_match.group(1).strip()
                remote_interface = interface_match.group(2).strip()
                self.logger.debug(f"Found interfaces using standard pattern: {local_interface} -> {remote_interface}")
            else:
                # Try NEXUS-specific pattern
                nexus_match = self.nexus_cdp_interface_pattern.search(entry)
                if nexus_match:
                    local_interface = nexus_match.group(1).strip()
                    remote_interface = nexus_match.group(2).strip()
                    self.logger.debug(f"Found interfaces using NEXUS pattern: {local_interface} -> {remote_interface}")
            
            # Normalize interface names
            local_interface = self._normalize_interface_name(local_interface)
            remote_interface = self._normalize_interface_name(remote_interface)
            
            neighbor = NeighborInfo(
                device_id=device_id,
                local_interface=local_interface,
                remote_interface=remote_interface,
                platform=platform,
                capabilities=capabilities,
                ip_address=ip_address,
                protocol="CDP"
            )
            
            self.logger.info(f"Successfully parsed CDP neighbor: {device_id} ({ip_address}) via {local_interface}")
            return neighbor
            
        except Exception as e:
            self.logger.error(f"Error parsing CDP entry: {str(e)}")
            self.logger.debug(f"Failed CDP entry content: {entry}")
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
            
            # BACH_MINUET detection: Extract firmware version from system description
            # System Description format: "BACH_MINUET Board model. Fw version: v.2.3.2-b103-UN-ENCRYPTED"
            if 'BACH_MINUET' in device_id or 'BACH_MINUET' in platform:
                # Extract firmware version from system description
                fw_version_match = re.search(r'Fw version:\s*([^\s]+)', platform, re.IGNORECASE)
                if fw_version_match:
                    fw_version = fw_version_match.group(1)
                    # Store as "BACH_MINUET|version" for later parsing
                    platform = f"BACH_MINUET|{fw_version}"
                    self.logger.info(f"Detected BACH_MINUET device: {device_id}, Firmware: {fw_version}")
                else:
                    platform = "BACH_MINUET"
                    self.logger.info(f"Detected BACH_MINUET device: {device_id} (no firmware version found)")
            
            # Extract capabilities
            cap_match = self.lldp_capabilities_pattern.search(entry)
            capabilities_str = cap_match.group(1).strip() if cap_match else ""
            capabilities = [cap.strip() for cap in capabilities_str.split(',') if cap.strip()]
            
            # Extract management address (IP address) from LLDP
            ip_address = None
            mgmt_match = self.nexus_lldp_mgmt_pattern.search(entry)
            if mgmt_match:
                mgmt_addresses = mgmt_match.group(1).strip()
                # Extract first IPv4 address from management addresses
                ipv4_pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+)')
                ipv4_match = ipv4_pattern.search(mgmt_addresses)
                if ipv4_match:
                    ip_address = ipv4_match.group(1)
                    self.logger.debug(f"Extracted management IP {ip_address} from LLDP for {device_id}")
            
            return NeighborInfo(
                device_id=device_id,
                local_interface=local_interface,
                remote_interface=remote_interface,
                platform=platform,
                capabilities=capabilities,
                ip_address=ip_address,  # Now includes management address from LLDP if available
                protocol="LLDP"
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing LLDP entry: {str(e)}")
            return None
    
    def _normalize_interface_name(self, interface_name: str, platform: str = None) -> str:
        """
        Normalize interface names for consistency across platforms
        
        Args:
            interface_name: Raw interface name from device output
            platform: Device platform (IOS, NX-OS, etc.) - optional
            
        Returns:
            Normalized interface name
            
        Examples:
            "Gi1/0/1" → "GigabitEthernet1/0/1"
            "Eth1/1" → "Ethernet1/1" (NX-OS preserved)
            "Po1" → "Port-channel1"
            "mgmt0" → "Management0"
        """
        if not interface_name or interface_name == "Unknown":
            return interface_name
        
        # Remove common prefixes and normalize
        interface_name = interface_name.strip()
        
        # Detect platform from interface name if not provided
        if not platform:
            if re.match(r'^Ethernet\d+/\d+', interface_name):
                platform = 'NX-OS'
            else:
                platform = 'IOS'
        
        # Handle NX-OS interface formats - preserve as-is
        if platform and 'NX-OS' in platform.upper():
            # NX-OS uses full names already: Ethernet1/1, port-channel1, mgmt0
            # Standardize port-channel to Port-channel
            interface_name = re.sub(r'^port-channel(\d+)', r'Port-channel\1', interface_name, flags=re.IGNORECASE)
            # Standardize management to Management
            interface_name = re.sub(r'^mgmt(\d+)', r'Management\1', interface_name, flags=re.IGNORECASE)
            return interface_name
        
        # IOS abbreviation expansion
        # GigabitEthernet
        interface_name = re.sub(r'^Gi(?:gabitEthernet)?(\d+(?:/\d+)*)', r'GigabitEthernet\1', interface_name, flags=re.IGNORECASE)
        # TenGigabitEthernet
        interface_name = re.sub(r'^Te(?:nGigabitEthernet)?(\d+(?:/\d+)*)', r'TenGigabitEthernet\1', interface_name, flags=re.IGNORECASE)
        # FastEthernet
        interface_name = re.sub(r'^Fa(?:stEthernet)?(\d+(?:/\d+)*)', r'FastEthernet\1', interface_name, flags=re.IGNORECASE)
        # FortyGigabitEthernet
        interface_name = re.sub(r'^Fo(?:rtyGigabitEthernet)?(\d+(?:/\d+)*)', r'FortyGigabitEthernet\1', interface_name, flags=re.IGNORECASE)
        
        # Port-channel standardization
        interface_name = re.sub(r'^Po(?:rt-channel)?(\d+)', r'Port-channel\1', interface_name, flags=re.IGNORECASE)
        interface_name = re.sub(r'^PortChannel(\d+)', r'Port-channel\1', interface_name, flags=re.IGNORECASE)
        
        # Management interface standardization
        interface_name = re.sub(r'^mgmt(\d+)', r'Management\1', interface_name, flags=re.IGNORECASE)
        interface_name = re.sub(r'^Mgmt(\d+)', r'Management\1', interface_name)
        
        # Vlan interfaces - keep as is
        # Loopback interfaces - keep as is
        
        return interface_name
    
    def normalize_interface_name(self, interface_name: str, platform: str = None) -> str:
        """
        Public method for normalizing interface names
        
        Args:
            interface_name: Raw interface name from device output
            platform: Device platform (IOS, NX-OS, etc.) - optional
            
        Returns:
            Normalized interface name
        """
        return self._normalize_interface_name(interface_name, platform)
    
    def get_neighbor_summary(self, neighbors: List[NeighborInfo]) -> Dict[str, Any]:
        """
        Generate summary statistics for discovered neighbors
        
        Args:
            neighbors: List of NeighborInfo objects
            
        Returns:
            Dictionary with neighbor statistics
        """
        if not neighbors:
            return {
                'total_neighbors': 0,
                'cdp_neighbors': 0,
                'lldp_neighbors': 0,
                'neighbors_with_ip': 0,
                'unique_platforms': [],
                'interface_types': []
            }
        
        cdp_count = sum(1 for n in neighbors if n.protocol == "CDP")
        lldp_count = sum(1 for n in neighbors if n.protocol == "LLDP")
        ip_count = sum(1 for n in neighbors if n.ip_address)
        
        platforms = list(set(n.platform for n in neighbors if n.platform != "Unknown"))
        interfaces = list(set(n.local_interface for n in neighbors if n.local_interface != "Unknown"))
        
        return {
            'total_neighbors': len(neighbors),
            'cdp_neighbors': cdp_count,
            'lldp_neighbors': lldp_count,
            'neighbors_with_ip': ip_count,
            'unique_platforms': platforms,
            'interface_types': interfaces
        }
    
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
        
        # Remove serial numbers in parentheses first (e.g., "DEVICE(FOX123)" -> "DEVICE")
        hostname = re.sub(r'\([^)]*\)', '', hostname)
        
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

    def parse_aruba_platform_string(self, platform_str: str) -> Dict[str, str]:
        """
        Parse Aruba AP platform string to extract platform, model, and serial

        Args:
            platform_str: Raw platform string like "AOS-10 (MODEL: 655), Aruba AP, Version:10.7.2.1_93286 SSR, serial:PHSHKZ25TY"

        Returns:
            Dictionary with 'platform', 'model', and 'serial' keys
        """
        result = {
            'platform': platform_str,  # Default to full string
            'model': None,
            'serial': None
        }

        try:
            # Extract model number: "MODEL: 655" or "(MODEL: 655)"
            model_match = re.search(r'MODEL:\s*(\d+)', platform_str, re.IGNORECASE)
            if model_match:
                result['model'] = f"Aruba {model_match.group(1)}"

            # Extract serial number: "serial:PHSHKZ25TY" or "serial: PHSHKZ25TY"
            serial_match = re.search(r'serial:\s*([A-Z0-9]+)', platform_str, re.IGNORECASE)
            if serial_match:
                result['serial'] = serial_match.group(1)

            # Extract platform: "AOS-10" or "Aruba AP"
            if 'AOS-' in platform_str:
                aos_match = re.search(r'(AOS-\d+)', platform_str, re.IGNORECASE)
                if aos_match:
                    result['platform'] = aos_match.group(1)
            elif 'Aruba AP' in platform_str:
                result['platform'] = 'Aruba AP'

            self.logger.debug(f"Parsed Aruba platform: {result}")

        except Exception as e:
            self.logger.error(f"Error parsing Aruba platform string: {e}")

        return result


    def parse_aruba_platform_string(self, platform_str: str) -> Dict[str, str]:
        """
        Parse Aruba AP platform string to extract platform, model, and serial
        
        Args:
            platform_str: Raw platform string like "AOS-10 (MODEL: 655), Aruba AP, Version:10.7.2.1_93286 SSR, serial:PHSHKZ25TY"
            
        Returns:
            Dictionary with 'platform', 'model', and 'serial' keys
        """
        result = {
            'platform': platform_str,  # Default to full string
            'model': None,
            'serial': None
        }
        
        try:
            # Extract model number: "MODEL: 655" or "(MODEL: 655)"
            model_match = re.search(r'MODEL:\s*(\d+)', platform_str, re.IGNORECASE)
            if model_match:
                result['model'] = f"Aruba {model_match.group(1)}"
            
            # Extract serial number: "serial:PHSHKZ25TY" or "serial: PHSHKZ25TY"
            serial_match = re.search(r'serial:\s*([A-Z0-9]+)', platform_str, re.IGNORECASE)
            if serial_match:
                result['serial'] = serial_match.group(1)
            
            # Extract platform: "AOS-10" or "Aruba AP"
            if 'AOS-' in platform_str:
                aos_match = re.search(r'(AOS-\d+)', platform_str, re.IGNORECASE)
                if aos_match:
                    result['platform'] = aos_match.group(1)
            elif 'Aruba AP' in platform_str:
                result['platform'] = 'Aruba AP'
            
            self.logger.debug(f"Parsed Aruba platform: {result}")
            
        except Exception as e:
            self.logger.error(f"Error parsing Aruba platform string: {e}")
        
        return result

    def parse_axis_platform_string(self, platform_str: str) -> Dict[str, str]:
        """
        Parse Axis camera platform string to extract platform, model, and version
        
        Args:
            platform_str: Raw platform string like "AXIS|P3265-LV Dome Camera 10.12.130"
            
        Returns:
            Dictionary with 'platform', 'model', and 'version' keys
        """
        result = {
            'platform': 'AXIS',
            'model': None,
            'version': None
        }
        
        try:
            # Check if this is our delimited format
            if '|' in platform_str:
                parts = platform_str.split('|', 1)
                result['platform'] = parts[0]
                version_str = parts[1] if len(parts) > 1 else ''
            else:
                version_str = platform_str
            
            # Extract model: Look for pattern like "P3265-LV Dome Camera" or "M3046-V"
            # Axis models typically start with a letter followed by numbers
            model_match = re.search(r'([A-Z]\d+[A-Z0-9-]*(?:\s+[A-Za-z\s]+Camera)?)', version_str, re.IGNORECASE)
            if model_match:
                result['model'] = f"Axis {model_match.group(1).strip()}"
            
            # Extract version: Look for version number pattern like "10.12.130"
            version_match = re.search(r'(\d+\.\d+\.\d+)', version_str)
            if version_match:
                result['version'] = version_match.group(1)
            
            self.logger.debug(f"Parsed Axis camera: {result}")
            
        except Exception as e:
            self.logger.error(f"Error parsing Axis platform string: {e}")
        
        return result

    def parse_bach_minuet_platform_string(self, platform_str: str) -> Dict[str, str]:
        """
        Parse BACH_MINUET platform string to extract platform, model, and firmware version
        
        Args:
            platform_str: Raw platform string like "BACH_MINUET|v.2.3.2-b103-UN-ENCRYPTED"
            
        Returns:
            Dictionary with 'platform', 'model', and 'version' keys
        """
        result = {
            'platform': 'BACH_MINUET',
            'model': 'BACH_MINUET Board',
            'version': None
        }
        
        try:
            # Check if this is our delimited format
            if '|' in platform_str:
                parts = platform_str.split('|', 1)
                result['platform'] = parts[0]
                version_str = parts[1] if len(parts) > 1 else ''
            else:
                version_str = platform_str
            
            # Extract firmware version: Look for pattern like "v.2.3.2-b103-UN-ENCRYPTED"
            # Version format: v.X.X.X-bXXX-ENCRYPTED/UN-ENCRYPTED
            version_match = re.search(r'(v\.\d+\.\d+\.\d+-b\d+(?:-(?:UN-)?ENCRYPTED)?)', version_str, re.IGNORECASE)
            if version_match:
                result['version'] = version_match.group(1)
            
            self.logger.debug(f"Parsed BACH_MINUET device: {result}")
            
        except Exception as e:
            self.logger.error(f"Error parsing BACH_MINUET platform string: {e}")
        
        return result

    def parse_sg300_platform_string(self, platform_str: str) -> Dict[str, str]:
        """
        Parse Cisco SG300 platform string to extract platform, model, and PID
        
        Args:
            platform_str: Raw platform string like "SG300-20|SRW2016-K9"
            
        Returns:
            Dictionary with 'platform', 'model', and 'pid' keys
        """
        result = {
            'platform': 'SG300',
            'model': None,
            'pid': None
        }
        
        try:
            # Check if this is our delimited format
            if '|' in platform_str:
                parts = platform_str.split('|', 1)
                model = parts[0]
                pid = parts[1] if len(parts) > 1 else None
            else:
                model = platform_str
                pid = None
            
            # Set platform based on model series
            if 'SG200' in model:
                result['platform'] = 'SG200'
            elif 'SG300' in model:
                result['platform'] = 'SG300'
            elif 'SG500' in model:
                result['platform'] = 'SG500'
            
            # Set model (e.g., "SG300-20 SRW2016-K9")
            if pid:
                result['model'] = f"{model} {pid}"
            else:
                result['model'] = model
            
            result['pid'] = pid
            
            self.logger.debug(f"Parsed SG300 device: {result}")
            
        except Exception as e:
            self.logger.error(f"Error parsing SG300 platform string: {e}")
        
        return result
