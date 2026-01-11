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
        
    def collect_device_information(self, connection: Scrapli, host: str, 
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
    
    def _execute_command(self, connection: Scrapli, command: str) -> Optional[str]:
        """Execute command and return output"""
        try:
            response = connection.send_command(command)
            return response.result
        except Exception as e:
            self.logger.error(f"Command execution failed for '{command}': {str(e)}")
            return None
    
    def _extract_hostname(self, version_output: str, fallback_host: str) -> str:
        """Extract hostname from version output"""
        # Try to find hostname in version output
        hostname_match = self.hostname_pattern.search(version_output)
        if hostname_match:
            hostname = hostname_match.group(1)
        else:
            # Use the connection host as fallback
            hostname = fallback_host
            
        # Ensure hostname is not longer than 36 characters
        if len(hostname) > 36:
            hostname = hostname[:36]
            
        return hostname
    
    def _extract_primary_ip(self, connection: Scrapli, host: str) -> str:
        """Extract primary IP address"""
        # For now, use the connection host
        # In a more advanced implementation, we could parse interface information
        return host
    
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
        model_match = self.model_pattern.search(version_output)
        if model_match:
            return model_match.group(1).strip()
        return "Unknown"
    
    def _extract_uptime(self, version_output: str) -> str:
        """Extract uptime from version output"""
        uptime_match = self.uptime_pattern.search(version_output)
        return uptime_match.group(1).strip() if uptime_match else "Unknown"
    
    def _get_vtp_version(self, connection: Scrapli) -> Optional[str]:
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
    
    def _collect_neighbors(self, connection: Scrapli, platform: str) -> List[NeighborInfo]:
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