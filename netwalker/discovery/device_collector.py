"""
Device Collector for gathering comprehensive device information
"""

import re
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from scrapli import Scrapli

from netwalker.connection.data_models import DeviceInfo, NeighborInfo
from .protocol_parser import ProtocolParser


class DeviceCollector:
    """Collects comprehensive device information during discovery"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.protocol_parser = ProtocolParser()
        
        # Regex patterns for parsing device information
        self.hostname_pattern = re.compile(r'^(\S+)\s+uptime is', re.MULTILINE | re.IGNORECASE)
        self.version_pattern = re.compile(r'Version\s+([^\s,]+)', re.IGNORECASE)
        self.serial_pattern = re.compile(r'Processor board ID\s+(\S+)', re.IGNORECASE)
        # Updated model pattern to prioritize Model Number field over platform line
        self.model_pattern = re.compile(r'Model [Nn]umber\s*:\s*([\w-]+)', re.IGNORECASE)
        self.uptime_pattern = re.compile(r'uptime is\s+(.+)', re.IGNORECASE)
        
    def collect_device_information(self, connection: Any, host: str, 
                                 connection_method: str, discovery_depth: int = 0, 
                                 is_seed: bool = False) -> Optional[DeviceInfo]:
        """
        Collect comprehensive device information
        
        Args:
            connection: Active scrapli connection
            host: Device hostname or IP
            connection_method: SSH or Telnet
            discovery_depth: Current discovery depth level
            is_seed: Whether this is a seed device
            
        Returns:
            DeviceInfo object or None if collection failed
        """
        try:
            self.logger.info(f"Collecting device information from {host}")
            
            # Get show version output
            version_output = self._execute_command(connection, "show version")
            if not version_output:
                return self._create_failed_device_info(host, connection_method, 
                                                     discovery_depth, is_seed, 
                                                     "Failed to get version information")
            
            # Extract basic device information
            hostname = self._extract_hostname(version_output, host)
            primary_ip = self._extract_primary_ip(connection, host)
            platform = self._detect_platform(version_output)
            software_version = self._extract_software_version(version_output)
            serial_number = self._extract_serial_number(version_output)
            hardware_model = self._extract_hardware_model(version_output)
            uptime = self._extract_uptime(version_output)
            
            # Get VTP information
            vtp_version = self._get_vtp_version(connection)
            
            # Determine capabilities
            capabilities = self._determine_capabilities(version_output, platform)
            
            # Collect neighbor information
            neighbors = self._collect_neighbors(connection, platform)
            
            device_info = DeviceInfo(
                hostname=hostname,
                primary_ip=primary_ip,
                platform=platform,
                capabilities=capabilities,
                software_version=software_version,
                vtp_version=vtp_version,
                serial_number=serial_number,
                hardware_model=hardware_model,
                uptime=uptime,
                discovery_timestamp=datetime.now(),
                discovery_depth=discovery_depth,
                is_seed=is_seed,
                connection_method=connection_method,
                connection_status="success",
                error_details=None,
                neighbors=neighbors
            )
            
            self.logger.info(f"Successfully collected information for {hostname}")
            return device_info
            
        except Exception as e:
            error_msg = f"Error collecting device information: {str(e)}"
            self.logger.error(error_msg)
            return self._create_failed_device_info(host, connection_method, 
                                                 discovery_depth, is_seed, error_msg)
    
    def _execute_command(self, connection: Any, command: str) -> Optional[str]:
        """Execute command and return output (supports both netmiko and scrapli)"""
        try:
            # Determine connection type and execute accordingly
            if hasattr(connection, 'send_command') and hasattr(connection, 'device_type'):
                # Netmiko connection - returns string directly
                response = connection.send_command(command, read_timeout=30)
                return response
            elif hasattr(connection, 'send_command') and hasattr(connection, 'transport'):
                # Scrapli connection - returns response object with .result attribute
                response = connection.send_command(command)
                return response.result
            elif hasattr(connection, 'send_command'):
                # Generic connection (for testing) - try scrapli format first
                try:
                    response = connection.send_command(command)
                    if hasattr(response, 'result'):
                        return response.result
                    else:
                        return str(response)
                except TypeError:
                    # If scrapli format fails, try netmiko format
                    response = connection.send_command(command, read_timeout=30)
                    return response
            else:
                self.logger.error(f"Unknown connection type: {type(connection)}")
                return None
        except Exception as e:
            self.logger.error(f"Command execution failed for '{command}': {str(e)}")
            return None
    
    def _extract_hostname(self, version_output: str, fallback_host: str) -> str:
        """Extract hostname from version output with enhanced NEXUS support"""
        # Try multiple patterns for different platforms
        hostname = None
        
        # Pattern 1: Look for device name in NX-OS format (Device name: hostname)
        nxos_hostname_match = re.search(r'Device name:\s*(\S+)', version_output, re.IGNORECASE)
        if nxos_hostname_match:
            hostname = nxos_hostname_match.group(1)
            self.logger.debug(f"Found hostname using NX-OS Device name pattern: {hostname}")
        
        # Pattern 2: Look for NEXUS hostname in system information
        if not hostname:
            nexus_system_match = re.search(r'cisco\s+Nexus\s+\d+.*?(\S+)\s+uptime', version_output, re.IGNORECASE | re.DOTALL)
            if nexus_system_match:
                potential_hostname = nexus_system_match.group(1)
                # Make sure it's not a model number or system word
                if not re.match(r'^(N\d+K?|Nexus|cisco|system|kernel)$', potential_hostname, re.IGNORECASE):
                    hostname = potential_hostname
                    self.logger.debug(f"Found hostname using NEXUS system pattern: {hostname}")
        
        # Pattern 3: Look for hostname in prompt format (hostname# or hostname>)
        if not hostname:
            prompt_match = re.search(r'^(\S+)[#>]\s*$', version_output, re.MULTILINE)
            if prompt_match:
                potential_hostname = prompt_match.group(1)
                # Exclude common prompt prefixes that aren't hostnames
                if potential_hostname.lower() not in ['switch', 'router', 'nexus', 'cisco']:
                    hostname = potential_hostname
                    self.logger.debug(f"Found hostname using prompt pattern: {hostname}")
        
        # Pattern 4: Enhanced uptime pattern but exclude system words
        if not hostname:
            hostname_match = self.hostname_pattern.search(version_output)
            if hostname_match:
                potential_hostname = hostname_match.group(1)
                # Exclude system words that are not actual hostnames
                excluded_words = ['kernel', 'system', 'device', 'switch', 'router', 'nexus', 'cisco']
                if potential_hostname.lower() not in excluded_words:
                    hostname = potential_hostname
                    self.logger.debug(f"Found hostname using uptime pattern: {hostname}")
                else:
                    self.logger.debug(f"Rejected system word as hostname: {potential_hostname}")
        
        # Pattern 5: Look for hostname in IOS format (hostname uptime is...)
        if not hostname:
            ios_hostname_match = re.search(r'^([A-Za-z][A-Za-z0-9_-]*)\s+uptime is', version_output, re.MULTILINE | re.IGNORECASE)
            if ios_hostname_match:
                potential_hostname = ios_hostname_match.group(1)
                # Additional validation for IOS hostnames
                if len(potential_hostname) > 2 and not potential_hostname.lower().startswith('cisco'):
                    hostname = potential_hostname
                    self.logger.debug(f"Found hostname using IOS pattern: {hostname}")
        
        # Pattern 6: Look for NEXUS-specific hostname in version string
        if not hostname:
            nexus_version_match = re.search(r'(\S+)\s+\(.*?\)\s+processor.*?uptime', version_output, re.IGNORECASE | re.DOTALL)
            if nexus_version_match:
                potential_hostname = nexus_version_match.group(1)
                # Validate it looks like a hostname
                if re.match(r'^[A-Za-z][A-Za-z0-9_-]*$', potential_hostname) and len(potential_hostname) > 2:
                    hostname = potential_hostname
                    self.logger.debug(f"Found hostname using NEXUS version pattern: {hostname}")
        
        # If no hostname found, use fallback
        if not hostname:
            hostname = fallback_host
            self.logger.debug(f"Using fallback hostname: {hostname}")
        
        # Clean up the hostname
        # Remove serial numbers in parentheses (e.g., "DEVICE(FOX123)" -> "DEVICE")
        hostname = re.sub(r'\([^)]*\)', '', hostname)
        
        # Remove any trailing whitespace or special characters
        hostname = re.sub(r'[^\w-]', '', hostname)
        
        # Ensure hostname is not longer than 36 characters
        if len(hostname) > 36:
            hostname = hostname[:36]
            
        self.logger.info(f"Final extracted hostname: '{hostname}' from fallback: '{fallback_host}'")
        return hostname
    
    def _extract_primary_ip(self, connection: Any, host: str) -> str:
        """
        Extract primary IP address using multiple methods:
        1. If host is already an IP, use it
        2. Try to get management IP from device interfaces
        3. Try forward DNS lookup of hostname
        4. Fall back to connection host
        """
        import ipaddress
        import socket
        
        def is_valid_ip(ip_str: str) -> bool:
            """Check if string is a valid IP address"""
            try:
                ipaddress.ip_address(ip_str.strip())
                return True
            except (ipaddress.AddressValueError, ValueError):
                return False
        
        # Method 1: If host is already an IP address, use it
        if is_valid_ip(host):
            return host
        
        # Method 2: Try to get management IP from device interfaces
        try:
            interface_ip = self._get_management_ip_from_interfaces(connection)
            if interface_ip and is_valid_ip(interface_ip):
                self.logger.debug(f"Found management IP from interfaces: {interface_ip}")
                return interface_ip
        except Exception as e:
            self.logger.debug(f"Failed to get IP from interfaces: {e}")
        
        # Method 3: Try forward DNS lookup
        try:
            resolved_ip = socket.gethostbyname(host)
            if resolved_ip and is_valid_ip(resolved_ip):
                self.logger.debug(f"Resolved {host} to {resolved_ip} via DNS")
                return resolved_ip
        except Exception as e:
            self.logger.debug(f"DNS lookup failed for {host}: {e}")
        
        # Method 4: Fall back to connection host (might be hostname)
        if is_valid_ip(host):
            return host
        
        # If all methods fail, return empty string
        self.logger.warning(f"Could not determine IP address for {host}")
        return ""
    
    def _get_management_ip_from_interfaces(self, connection: Any) -> Optional[str]:
        """
        Try to extract management IP address from device interfaces.
        Looks for common management interface patterns.
        """
        try:
            # Try show ip interface brief first
            interface_output = self._execute_command(connection, "show ip interface brief")
            if interface_output:
                # Look for management interfaces (Vlan1, Management0, etc.)
                lines = interface_output.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line or 'Interface' in line or 'unassigned' in line.lower():
                        continue
                    
                    # Look for management interface patterns
                    if any(pattern in line.lower() for pattern in ['vlan1', 'management', 'mgmt', 'loopback0']):
                        # Extract IP address from the line
                        parts = line.split()
                        for part in parts:
                            if '.' in part and not part.startswith('255.'):  # Skip subnet masks
                                # Basic IP validation
                                try:
                                    import ipaddress
                                    ipaddress.ip_address(part)
                                    return part
                                except:
                                    continue
            
            # Try show ip route as fallback to find local interfaces
            route_output = self._execute_command(connection, "show ip route connected")
            if route_output:
                # Look for directly connected routes that might indicate local IPs
                lines = route_output.split('\n')
                for line in lines:
                    if 'directly connected' in line.lower():
                        # Extract network from route line
                        parts = line.split()
                        for part in parts:
                            if '/' in part and '.' in part:  # CIDR notation
                                try:
                                    network = part.split('/')[0]
                                    import ipaddress
                                    ipaddress.ip_address(network)
                                    # This is a network address, we'd need the interface IP
                                    # For now, skip this approach
                                    continue
                                except:
                                    continue
                                    
        except Exception as e:
            self.logger.debug(f"Error getting management IP from interfaces: {e}")
        
        return None
    
    def _detect_platform(self, version_output: str) -> str:
        """Detect device platform from version output"""
        version_lower = version_output.lower()
        
        if "nx-os" in version_lower or "nexus" in version_lower:
            return "NX-OS"
        elif "ios-xe" in version_lower:
            return "IOS-XE"
        elif "ios" in version_lower:
            return "IOS"
        else:
            return "Unknown"
    
    def _extract_software_version(self, version_output: str) -> str:
        """Extract software version from version output"""
        version_match = self.version_pattern.search(version_output)
        return version_match.group(1) if version_match else "Unknown"
    
    def _extract_serial_number(self, version_output: str) -> str:
        """Extract serial number from version output"""
        serial_match = self.serial_pattern.search(version_output)
        return serial_match.group(1) if serial_match else "Unknown"
    
    def _extract_hardware_model(self, version_output: str) -> str:
        """Extract hardware model from version output"""
        # Pattern 1: Model Number field (NX-OS and some IOS)
        model_match = self.model_pattern.search(version_output)
        if model_match:
            return model_match.group(1).strip()
        
        # Pattern 2: Cisco model in platform line (IOS)
        cisco_model_match = re.search(r'Cisco\s+(\d+[A-Z]*)\s+\(', version_output, re.IGNORECASE)
        if cisco_model_match:
            return cisco_model_match.group(1).strip()
        
        # Pattern 3: Model in hardware description line
        hardware_model_match = re.search(r'cisco\s+([\w-]+)\s+', version_output, re.IGNORECASE)
        if hardware_model_match:
            model = hardware_model_match.group(1).strip()
            # Filter out common non-model words
            if model.lower() not in ['systems', 'nexus', 'catalyst']:
                return model
        
        return "Unknown"
    
    def _extract_uptime(self, version_output: str) -> str:
        """Extract uptime from version output"""
        uptime_match = self.uptime_pattern.search(version_output)
        return uptime_match.group(1).strip() if uptime_match else "Unknown"
    
    def _get_vtp_version(self, connection: Any) -> Optional[str]:
        """Get VTP version information"""
        try:
            vtp_output = self._execute_command(connection, "show vtp status")
            if vtp_output:
                # Extract VTP version running - matches "VTP version running : 2"
                vtp_match = re.search(r'VTP version running\s*:\s*(\d+)', vtp_output, re.IGNORECASE)
                return vtp_match.group(1) if vtp_match else None
        except:
            pass
        return None
    
    def _determine_capabilities(self, version_output: str, platform: str) -> List[str]:
        """Determine device capabilities based on version output and platform"""
        capabilities = []
        
        version_lower = version_output.lower()
        
        # Basic capabilities based on platform
        if platform in ["IOS", "IOS-XE", "NX-OS"]:
            capabilities.append("Router")
            
        # Check for switching capabilities
        if "switch" in version_lower or "catalyst" in version_lower:
            capabilities.append("Switch")
            
        # Check for other capabilities
        if "bridge" in version_lower:
            capabilities.append("Bridge")
            
        if not capabilities:
            capabilities.append("Host")
            
        return capabilities
    
    def _collect_neighbors(self, connection: Any, platform: str) -> List[NeighborInfo]:
        """Collect neighbor information using CDP and LLDP"""
        neighbors = []
        
        try:
            # Get platform-specific commands
            commands = self.protocol_parser.adapt_commands_for_platform(platform)
            
            # Get CDP neighbors
            cdp_output = self._execute_command(connection, commands['cdp_neighbors'])
            
            # Get LLDP neighbors
            lldp_output = self._execute_command(connection, commands['lldp_neighbors'])
            
            # Parse both protocols
            if cdp_output or lldp_output:
                neighbors = self.protocol_parser.parse_multi_protocol_output(
                    cdp_output or "", lldp_output or ""
                )
                
        except Exception as e:
            self.logger.error(f"Error collecting neighbors: {str(e)}")
            
        return neighbors
    
    def _create_failed_device_info(self, host: str, connection_method: str, 
                                 discovery_depth: int, is_seed: bool, 
                                 error_message: str) -> DeviceInfo:
        """Create DeviceInfo object for failed discovery"""
        return DeviceInfo(
            hostname=host,
            primary_ip=host,
            platform="Unknown",
            capabilities=["Unknown"],
            software_version="Unknown",
            vtp_version=None,
            serial_number="Unknown",
            hardware_model="Unknown",
            uptime="Unknown",
            discovery_timestamp=datetime.now(),
            discovery_depth=discovery_depth,
            is_seed=is_seed,
            connection_method=connection_method,
            connection_status="failed",
            error_details=error_message,
            neighbors=[]
        )