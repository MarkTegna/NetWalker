"""
Collector Component for IPv4 Prefix Inventory Module

This module handles the collection of routing information from network devices,
including VRF discovery, routing table collection, and BGP prefix collection.

Author: Mark Oldham
"""

import logging
from typing import List, Optional


class VRFDiscovery:
    """
    Discovers VRFs on network devices.
    
    Executes 'show vrf' command on Cisco devices (IOS, IOS-XE, NX-OS) and
    parses the output to extract VRF names.
    """
    
    def __init__(self):
        """Initialize VRF discovery component."""
        self.logger = logging.getLogger(__name__)
    
    def discover_vrfs(self, connection, platform: str) -> List[str]:
        """
        Execute 'show vrf' and parse VRF names.
        
        This method executes the 'show vrf' command on the device and parses
        the output to extract VRF names. It handles all Cisco platforms
        (IOS, IOS-XE, NX-OS) which use the same command syntax.
        
        Args:
            connection: Active device connection (from NetWalker Connection Manager)
            platform: Device platform (ios, iosxe, nxos)
            
        Returns:
            List of VRF names discovered on the device. Returns empty list if:
            - No VRFs are configured
            - Command execution fails
            - Output cannot be parsed
            
        Requirements:
            - 1.1: Execute 'show vrf' on IOS/IOS-XE devices
            - 1.2: Execute 'show vrf' on NX-OS devices
            - 1.3: Return list of VRF names
            - 1.4: Log errors and continue on failure
            - 1.5: Return empty list when no VRFs configured
        """
        vrfs = []
        
        try:
            # Execute 'show vrf' command
            # All Cisco platforms (IOS, IOS-XE, NX-OS) use the same command
            self.logger.debug(f"Executing 'show vrf' on {platform} device")
            output = connection.send_command("show vrf")
            
            if not output or not output.strip():
                self.logger.warning("Empty output from 'show vrf' command")
                return vrfs
            
            # Parse VRF names from output
            vrfs = self._parse_vrf_output(output, platform)
            
            if vrfs:
                self.logger.info(f"Discovered {len(vrfs)} VRFs: {', '.join(vrfs)}")
            else:
                self.logger.info("No VRFs configured on device")
            
            return vrfs
            
        except Exception as e:
            # Requirement 1.4: Log error and continue with global table collection only
            self.logger.error(f"VRF discovery failed: {str(e)}")
            self.logger.info("Continuing with global table collection only")
            return vrfs
    
    def _parse_vrf_output(self, output: str, platform: str) -> List[str]:
        """
        Parse VRF names from 'show vrf' command output.
        
        The output format varies slightly between platforms but generally follows:
        
        IOS/IOS-XE:
          Name                             Default RD            Interfaces
          MGMT                             <not set>             
          WAN                              65000:100             Gi0/0/1
        
        NX-OS:
          VRF-Name                           VRF-ID State   Reason
          MGMT                                    2 Up      --
          WAN                                     3 Up      --
        
        Args:
            output: Raw command output from 'show vrf'
            platform: Device platform (ios, iosxe, nxos)
            
        Returns:
            List of VRF names extracted from output
        """
        vrfs = []
        lines = output.split('\n')
        
        # Skip header lines and parse VRF names
        # VRF names are typically in the first column
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip header lines (contain keywords like "Name", "VRF-Name", "Default", "State")
            if any(keyword in line for keyword in ['Name', 'VRF-Name', 'Default', 'State', 
                                                     'Interfaces', 'VRF-ID', 'Reason', '---']):
                continue
            
            # Extract VRF name (first token on the line)
            tokens = line.split()
            if tokens:
                vrf_name = tokens[0]
                
                # Validate VRF name (basic sanity check)
                # VRF names should not contain special characters that indicate it's not a VRF
                if vrf_name and not vrf_name.startswith('#'):
                    vrfs.append(vrf_name)
        
        return vrfs


class RoutingCollector:
    """Collects routing table information from network devices."""

    def __init__(self):
        """Initialize routing collector component."""
        self.logger = logging.getLogger(__name__)

    def collect_global_routes(self, connection) -> str:
        """
        Execute 'show ip route' for global routing table.

        Collects all routes from the global (default) routing table.

        Args:
            connection: Active device connection

        Returns:
            Command output as string

        Requirements:
            - 2.1: Execute 'show ip route' on the device
        """
        try:
            self.logger.debug("Executing 'show ip route' for global table")
            output = connection.send_command("show ip route")
            return output if output else ""
        except Exception as e:
            self.logger.error("Failed to collect global routes: %s", str(e))
            return ""

    def collect_global_connected(self, connection) -> str:
        """
        Execute 'show ip route connected' for global routing table.

        Collects only directly connected routes from the global routing table.

        Args:
            connection: Active device connection

        Returns:
            Command output as string

        Requirements:
            - 2.2: Execute 'show ip route connected' on the device
        """
        try:
            self.logger.debug("Executing 'show ip route connected' for global table")
            output = connection.send_command("show ip route connected")
            return output if output else ""
        except Exception as e:
            self.logger.error("Failed to collect global connected routes: %s", str(e))
            return ""

    def collect_vrf_routes(self, connection, vrf: str) -> str:
        """
        Execute 'show ip route vrf <VRF>' for specific VRF.

        Collects all routes from a specific VRF routing table. Handles VRF names
        with spaces and special characters by properly quoting them.

        Args:
            connection: Active device connection
            vrf: VRF name (may contain spaces or special characters)

        Returns:
            Command output as string

        Requirements:
            - 3.1: Execute 'show ip route vrf <VRF>' for each VRF
            - 17.1: Quote VRF names containing spaces
            - 17.2: Escape special characters in VRF names
            - 17.3: Validate VRF name format before execution
            - 17.5: Log sanitized VRF name used in commands
        """
        try:
            # Sanitize and validate VRF name
            sanitized_vrf = self._sanitize_vrf_name(vrf)
            if not sanitized_vrf:
                self.logger.error("Invalid VRF name: %s", vrf)
                return ""

            # Build command with properly quoted VRF name
            command = f"show ip route vrf {sanitized_vrf}"
            self.logger.debug("Executing '%s' (sanitized VRF: %s)", command, sanitized_vrf)

            output = connection.send_command(command)
            return output if output else ""
        except Exception as e:
            self.logger.error("Failed to collect routes for VRF '%s': %s", vrf, str(e))
            return ""

    def collect_vrf_connected(self, connection, vrf: str) -> str:
        """
        Execute 'show ip route vrf <VRF> connected' for specific VRF.

        Collects only directly connected routes from a specific VRF routing table.
        Handles VRF names with spaces and special characters by properly quoting them.

        Args:
            connection: Active device connection
            vrf: VRF name (may contain spaces or special characters)

        Returns:
            Command output as string

        Requirements:
            - 3.2: Execute 'show ip route vrf <VRF> connected' for each VRF
            - 17.1: Quote VRF names containing spaces
            - 17.2: Escape special characters in VRF names
            - 17.3: Validate VRF name format before execution
            - 17.5: Log sanitized VRF name used in commands
        """
        try:
            # Sanitize and validate VRF name
            sanitized_vrf = self._sanitize_vrf_name(vrf)
            if not sanitized_vrf:
                self.logger.error("Invalid VRF name: %s", vrf)
                return ""

            # Build command with properly quoted VRF name
            command = f"show ip route vrf {sanitized_vrf} connected"
            self.logger.debug("Executing '%s' (sanitized VRF: %s)", command, sanitized_vrf)

            output = connection.send_command(command)
            return output if output else ""
        except Exception as e:
            self.logger.error("Failed to collect connected routes for VRF '%s': %s", vrf, str(e))
            return ""

    def _sanitize_vrf_name(self, vrf: str) -> str:
        """
        Sanitize VRF name for use in commands.

        Handles VRF names with spaces and special characters by quoting them
        appropriately for Cisco IOS command syntax.

        Args:
            vrf: Raw VRF name

        Returns:
            Sanitized VRF name (quoted if necessary), or empty string if invalid

        Requirements:
            - 17.1: Quote VRF names containing spaces
            - 17.2: Escape special characters appropriately
            - 17.3: Validate VRF name format
            - 17.4: Skip invalid VRF names
        """
        if not vrf or not vrf.strip():
            return ""

        vrf = vrf.strip()

        # Check for obviously invalid characters that shouldn't be in VRF names
        # Cisco VRF names can contain alphanumeric, hyphen, underscore, period, colon, and space
        invalid_chars = ['|', '&', ';', '>', '<', '`', '$', '(', ')', '{', '}', '[', ']', '\\', '"', "'"]
        if any(char in vrf for char in invalid_chars):
            self.logger.warning("VRF name contains invalid characters: %s", vrf)
            return ""

        # If VRF name contains spaces, quote it
        # Cisco IOS accepts VRF names with spaces when quoted
        if ' ' in vrf:
            # Use double quotes for VRF names with spaces
            return f'"{vrf}"'

        # For VRF names without spaces, return as-is
        return vrf


class BGPCollector:
    """Collects BGP routing information from network devices."""
    
    def __init__(self):
        """Initialize BGP collector component."""
        self.logger = logging.getLogger(__name__)
    
    def collect_global_bgp(self, connection) -> Optional[str]:
        """
        Execute 'show ip bgp' for global routing table.
        
        Returns None if BGP is not configured on the device. This method
        implements graceful degradation - if BGP is not configured, it logs
        the error and returns None without failing the collection process.
        
        Args:
            connection: Active device connection
            
        Returns:
            Command output as string, or None if BGP not configured
            
        Requirements:
            - 2.3: Execute 'show ip bgp' to collect BGP prefixes
            - 2.4: Handle BGP not configured gracefully
        """
        try:
            self.logger.debug("Executing 'show ip bgp' for global table")
            output = connection.send_command("show ip bgp")
            
            # Check if output indicates BGP is not configured
            if self._is_bgp_not_configured(output):
                self.logger.info("BGP is not configured on device (global table)")
                return None
            
            return output if output else None
            
        except Exception as e:
            # Graceful degradation - log error and return None
            self.logger.info(f"BGP collection failed (global table): {str(e)}")
            self.logger.debug("Continuing with collection without BGP data")
            return None
    
    def collect_vrf_bgp(self, connection, vrf: str, platform: str) -> Optional[str]:
        """
        Execute platform-specific BGP VRF command.
        
        - IOS/IOS-XE: 'show ip bgp vpnv4 vrf <VRF>'
        - NX-OS: 'show ip bgp vrf <VRF>'
        
        Returns None if BGP is not configured for the VRF. This method
        implements graceful degradation and handles VRF names with spaces
        and special characters.
        
        Args:
            connection: Active device connection
            vrf: VRF name (may contain spaces or special characters)
            platform: Device platform (ios, iosxe, nxos)
            
        Returns:
            Command output as string, or None if BGP not configured
            
        Requirements:
            - 3.3: Execute 'show ip bgp vpnv4 vrf <VRF>' for IOS/IOS-XE
            - 3.4: Execute 'show ip bgp vrf <VRF>' for NX-OS
            - 17.1: Quote VRF names containing spaces
            - 17.2: Escape special characters in VRF names
        """
        try:
            # Sanitize VRF name (reuse logic from RoutingCollector)
            sanitized_vrf = self._sanitize_vrf_name(vrf)
            if not sanitized_vrf:
                self.logger.error(f"Invalid VRF name for BGP collection: {vrf}")
                return None
            
            # Build platform-specific command
            if platform.lower() in ['ios', 'iosxe', 'ios-xe']:
                command = f"show ip bgp vpnv4 vrf {sanitized_vrf}"
            elif platform.lower() in ['nxos', 'nx-os']:
                command = f"show ip bgp vrf {sanitized_vrf}"
            else:
                self.logger.warning(f"Unknown platform '{platform}' for BGP VRF collection, trying IOS command")
                command = f"show ip bgp vpnv4 vrf {sanitized_vrf}"
            
            self.logger.debug(f"Executing '{command}' (sanitized VRF: {sanitized_vrf})")
            output = connection.send_command(command)
            
            # Check if output indicates BGP is not configured
            if self._is_bgp_not_configured(output):
                self.logger.info(f"BGP is not configured for VRF '{vrf}'")
                return None
            
            return output if output else None
            
        except Exception as e:
            # Graceful degradation - log error and return None
            self.logger.info(f"BGP collection failed for VRF '{vrf}': {str(e)}")
            self.logger.debug("Continuing with collection without BGP data for this VRF")
            return None
    
    def _is_bgp_not_configured(self, output: str) -> bool:
        """
        Check if command output indicates BGP is not configured.
        
        Common indicators:
        - "% BGP not active"
        - "BGP not enabled"
        - "Invalid input detected"
        - Empty or very short output
        
        Args:
            output: Command output to check
            
        Returns:
            True if BGP appears to be not configured
        """
        if not output or len(output.strip()) < 10:
            return True
        
        # Check for common "not configured" messages
        not_configured_indicators = [
            '% BGP not active',
            'BGP not enabled',
            'Invalid input detected',
            '% BGP instance',
            'not found',
            'does not exist'
        ]
        
        output_lower = output.lower()
        for indicator in not_configured_indicators:
            if indicator.lower() in output_lower:
                return True
        
        return False
    
    def _sanitize_vrf_name(self, vrf: str) -> str:
        """
        Sanitize VRF name for use in commands.
        
        Reuses the same logic as RoutingCollector for consistency.
        
        Args:
            vrf: Raw VRF name
            
        Returns:
            Sanitized VRF name (quoted if necessary), or empty string if invalid
        """
        if not vrf or not vrf.strip():
            return ""
        
        vrf = vrf.strip()
        
        # Check for invalid characters
        invalid_chars = ['|', '&', ';', '>', '<', '`', '\n', '\r', '(', ')', '{', '}', '[', ']', '\\', '"', "'"]
        if any(char in vrf for char in invalid_chars):
            self.logger.warning(f"VRF name contains invalid characters: {vrf}")
            return ""
        
        # Quote VRF names with spaces
        if ' ' in vrf:
            return f'"{vrf}"'
        
        return vrf


class PrefixCollector:
    """
    Orchestrates collection workflow for a single device.
    
    Coordinates VRF discovery, routing table collection, and BGP collection
    for a single network device.
    """
    
    def __init__(self, config, connection_manager, credentials):
        """
        Initialize prefix collector.
        
        Args:
            config: IPv4PrefixConfig instance
            connection_manager: NetWalker ConnectionManager instance
            credentials: NetWalker Credentials instance
        """
        self.config = config
        self.connection_manager = connection_manager
        self.credentials = credentials
        self.vrf_discovery = VRFDiscovery()
        self.routing_collector = RoutingCollector()
        self.bgp_collector = BGPCollector()
        self.logger = logging.getLogger(__name__)
    
    def _disable_pagination(self, connection) -> bool:
        """
        Disable terminal pagination to ensure complete command outputs.
        
        Executes 'terminal length 0' on Cisco devices to disable pagination.
        This ensures that all command outputs are received in full without
        requiring manual intervention to page through results.
        
        Args:
            connection: Active device connection
            
        Returns:
            True if pagination was successfully disabled, False otherwise
            
        Requirements:
            - 4.1: Execute 'terminal length 0' before collection
            - 4.2: Receive complete command outputs without manual intervention
            - 4.3: Log errors and continue if pagination control fails
        """
        try:
            self.logger.debug("Disabling terminal pagination with 'terminal length 0'")
            connection.send_command("terminal length 0")
            self.logger.debug("Terminal pagination disabled successfully")
            return True
            
        except Exception as e:
            # Requirement 4.3: Log error and continue with collection anyway
            self.logger.warning(f"Failed to disable pagination: {str(e)}")
            self.logger.info("Continuing with collection - outputs may be truncated")
            return False
    
    def collect_device(self, device):
        """
        Collect all prefix data from a single device.
        
        Orchestrates the complete collection workflow:
        1. Connect to device
        2. Disable pagination
        3. Discover VRFs
        4. Collect global table (if enabled)
        5. Collect per-VRF tables (if enabled)
        6. Collect BGP (if enabled)
        7. Handle errors gracefully
        
        Args:
            device: DeviceInfo object with device details (hostname, platform, ip_address)
            
        Returns:
            DeviceCollectionResult with raw command outputs and metadata
            
        Requirements:
            - 2.1-2.5: Collect global table
            - 3.1-3.5: Collect per-VRF tables
            - 4.1-4.3: Disable pagination
            - 16.1-16.3: Handle failures gracefully
            - 21.1, 21.2, 21.4: Progress reporting
        """
        from netwalker.ipv4_prefix.data_models import DeviceCollectionResult
        
        device_name = device.hostname if hasattr(device, 'hostname') else str(device)
        platform = device.platform if hasattr(device, 'platform') else 'unknown'
        
        self.logger.info(f"Starting prefix collection for device: {device_name}")
        
        # Initialize result
        result = DeviceCollectionResult(
            device=device_name,
            platform=platform,
            success=False,
            vrfs=[],
            raw_outputs={},
            error=None
        )
        
        connection = None
        
        try:
            # Connect to device
            self.logger.debug(f"Connecting to {device_name}...")
            connection, conn_result = self.connection_manager.connect_device(device.ip_address, self.credentials)
            
            if not connection:
                result.error = "Failed to establish connection"
                self.logger.error(f"Connection failed for {device_name}")
                return result
            
            # Disable pagination
            self._disable_pagination(connection)
            
            # Discover VRFs
            self.logger.debug(f"Discovering VRFs on {device_name}...")
            vrfs = self.vrf_discovery.discover_vrfs(connection, platform)
            result.vrfs = vrfs
            
            # Collect global table (if enabled)
            if self.config.collect_global_table:
                self.logger.debug(f"Collecting global routing table from {device_name}...")
                
                # Collect global routes
                output = self.routing_collector.collect_global_routes(connection)
                if output:
                    result.raw_outputs['show ip route'] = output
                
                # Collect global connected routes
                output = self.routing_collector.collect_global_connected(connection)
                if output:
                    result.raw_outputs['show ip route connected'] = output
                
                # Collect global BGP (if enabled)
                if self.config.collect_bgp:
                    output = self.bgp_collector.collect_global_bgp(connection)
                    if output:
                        result.raw_outputs['show ip bgp'] = output
            
            # Collect per-VRF tables (if enabled)
            if self.config.collect_per_vrf and vrfs:
                self.logger.debug(f"Collecting per-VRF routing tables from {device_name} ({len(vrfs)} VRFs)...")
                
                for vrf in vrfs:
                    # Collect VRF routes
                    output = self.routing_collector.collect_vrf_routes(connection, vrf)
                    if output:
                        result.raw_outputs[f'show ip route vrf {vrf}'] = output
                    
                    # Collect VRF connected routes
                    output = self.routing_collector.collect_vrf_connected(connection, vrf)
                    if output:
                        result.raw_outputs[f'show ip route vrf {vrf} connected'] = output
                    
                    # Collect VRF BGP (if enabled)
                    if self.config.collect_bgp:
                        output = self.bgp_collector.collect_vrf_bgp(connection, vrf, platform)
                        if output:
                            if platform.lower() in ['ios', 'iosxe', 'ios-xe']:
                                result.raw_outputs[f'show ip bgp vpnv4 vrf {vrf}'] = output
                            else:
                                result.raw_outputs[f'show ip bgp vrf {vrf}'] = output
            
            # Collection successful
            result.success = True
            self.logger.info(f"Successfully collected prefix data from {device_name} ({len(result.raw_outputs)} commands)")
            
        except Exception as e:
            # Handle any unexpected errors
            result.error = str(e)
            result.success = False
            self.logger.error(f"Error collecting from {device_name}: {str(e)}")
            
        finally:
            # Disconnect from device
            if connection:
                try:
                    self.connection_manager.close_connection(device.ip_address)
                except Exception as e:
                    self.logger.warning(f"Error disconnecting from {device_name}: {str(e)}")
        
        return result
