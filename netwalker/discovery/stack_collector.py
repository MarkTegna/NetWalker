"""
Stack Collector for detecting and collecting switch stack member information

Author: Mark Oldham
"""

import re
import logging
from typing import List, Optional, Any
from netwalker.connection.data_models import StackMemberInfo


class StackCollector:
    """Collects switch stack member information from Cisco devices"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def collect_stack_members(self, connection: Any, platform: str) -> List[StackMemberInfo]:
        """
        Collect stack member information from device.
        
        Args:
            connection: Active device connection
            platform: Device platform (IOS, IOS-XE, NX-OS)
            
        Returns:
            List of StackMemberInfo objects (empty if not a stack or collection fails)
        """
        try:
            # Get stack information based on platform
            if platform.upper() in ['IOS', 'IOS-XE']:
                return self._collect_ios_stack(connection)
            elif platform.upper() == 'NX-OS':
                return self._collect_nxos_stack(connection)
            else:
                self.logger.debug(f"Stack collection not supported for platform: {platform}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error collecting stack members: {str(e)}")
            return []
    
    def _execute_command(self, connection: Any, command: str) -> Optional[str]:
        """Execute command and return output (supports both netmiko and scrapli)"""
        try:
            if hasattr(connection, 'send_command') and hasattr(connection, 'device_type'):
                # Netmiko connection
                response = connection.send_command(command, read_timeout=30)
                return response
            elif hasattr(connection, 'send_command') and hasattr(connection, 'transport'):
                # Scrapli connection
                response = connection.send_command(command)
                return response.result
            elif hasattr(connection, 'send_command'):
                # Generic connection
                try:
                    response = connection.send_command(command)
                    if hasattr(response, 'result'):
                        return response.result
                    else:
                        return str(response)
                except TypeError:
                    response = connection.send_command(command, read_timeout=30)
                    return response
            else:
                self.logger.error(f"Unknown connection type: {type(connection)}")
                return None
        except Exception as e:
            self.logger.error(f"Command execution failed for '{command}': {str(e)}")
            return None
    
    def _collect_ios_stack(self, connection: Any) -> List[StackMemberInfo]:
        """
        Collect stack information from IOS/IOS-XE devices.
        
        Uses 'show switch' command to get stack member details.
        Falls back to 'show mod' for VSS detection if 'show switch' fails.
        """
        stack_members = []
        
        # Execute show switch command
        output = self._execute_command(connection, "show switch")
        
        if not output:
            self.logger.debug("No output from 'show switch' command")
            # Try VSS detection as fallback
            return self._collect_vss_stack(connection)
        
        # Check if this is actually a stack
        if 'invalid' in output.lower() or 'not supported' in output.lower():
            self.logger.debug("Device is not a stack (show switch not supported)")
            # Try VSS detection as fallback
            return self._collect_vss_stack(connection)
        
        # Parse the output
        stack_members = self._parse_ios_stack_output(output)
        
        if stack_members:
            self.logger.info(f"Found {len(stack_members)} stack members")
        else:
            # If no stack members found, try VSS detection
            self.logger.debug("No stack members found in 'show switch', trying VSS detection")
            stack_members = self._collect_vss_stack(connection)
        
        return stack_members
    
    def _parse_ios_stack_output(self, output: str) -> List[StackMemberInfo]:
        """
        Parse 'show switch' output from IOS/IOS-XE devices.
        
        Example output format:
        Switch/Stack Mac Address : 0123.4567.89ab - Local Mac Address
        Mac persistency wait time: Indefinite
                                                     H/W   Current
        Switch#   Role    Mac Address     Priority Version  State 
        ---------------------------------------------------------------------------
        *1       Master   0123.4567.89ab     15     V01     Ready               
         2       Member   0123.4567.89cd     1      V01     Ready               
         3       Member   0123.4567.89ef     1      V01     Ready
        """
        stack_members = []
        lines = output.split('\n')
        
        # Find the data section (after the header line with dashes)
        in_data_section = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                continue
            
            # Look for the separator line (dashes)
            if '---' in line_stripped:
                in_data_section = True
                continue
            
            # Skip header lines
            if 'Switch#' in line or 'Role' in line or 'Mac Address' in line:
                continue
            
            # Parse data lines
            if in_data_section:
                member = self._parse_ios_stack_line(line_stripped)
                if member:
                    stack_members.append(member)
        
        return stack_members
    
    def _parse_ios_stack_line(self, line: str) -> Optional[StackMemberInfo]:
        """
        Parse a single line from 'show switch' output.
        
        Format: *1       Master   0123.4567.89ab     15     V01     Ready
        """
        # Remove asterisk (indicates active master)
        line = line.lstrip('*').strip()
        
        # Split by whitespace
        parts = line.split()
        
        if len(parts) < 6:
            return None
        
        try:
            switch_number = int(parts[0])
            role = parts[1]
            mac_address = parts[2]
            priority = int(parts[3]) if parts[3].isdigit() else None
            hardware_version = parts[4]
            state = parts[5]
            
            # Get additional details if available (model, serial)
            # Note: Basic show switch doesn't include serial/model, need show switch detail
            
            return StackMemberInfo(
                switch_number=switch_number,
                role=role,
                priority=priority,
                hardware_model="Unknown",  # Will be populated by show inventory
                serial_number="Unknown",   # Will be populated by show inventory
                mac_address=mac_address,
                software_version=None,  # Will be set from parent device software version
                state=state
            )
            
        except (ValueError, IndexError) as e:
            self.logger.debug(f"Failed to parse stack line: {line} - {str(e)}")
            return None
    
    def _collect_nxos_stack(self, connection: Any) -> List[StackMemberInfo]:
        """
        Collect stack information from NX-OS devices.
        
        NOTE: NX-OS devices do not support traditional stacking like IOS devices.
        NX-OS uses modular chassis with supervisor modules and line cards, not stacks.
        VPC (Virtual Port Channel) is used for redundancy, but that's not the same as stacking.
        
        Returning empty list to avoid treating line cards as stack members.
        """
        # NX-OS doesn't have traditional stacking - return empty list
        self.logger.debug("NX-OS devices do not support traditional stacking - skipping stack collection")
        return []
    
    def _parse_nxos_module_output(self, output: str) -> List[StackMemberInfo]:
        """
        Parse 'show module' output from NX-OS devices.
        
        Example output format:
        Mod Ports             Module-Type                       Model           Status
        --- ----- ------------------------------------- --------------------- ----------
        1    48   48x10GE + 6x40G Supervisor            N9K-C9396PX           active *
        """
        stack_members = []
        lines = output.split('\n')
        
        # Find the data section
        in_data_section = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                continue
            
            # Look for the separator line (dashes)
            if '---' in line_stripped:
                in_data_section = True
                continue
            
            # Skip header lines
            if 'Mod' in line and 'Ports' in line:
                continue
            
            # Parse data lines
            if in_data_section:
                member = self._parse_nxos_module_line(line_stripped)
                if member:
                    stack_members.append(member)
        
        return stack_members
    
    def _parse_nxos_module_line(self, line: str) -> Optional[StackMemberInfo]:
        """
        Parse a single line from 'show module' output.
        
        Format: 1    48   48x10GE + 6x40G Supervisor            N9K-C9396PX           active *
        """
        # Split by whitespace (multiple spaces)
        parts = re.split(r'\s{2,}', line)
        
        if len(parts) < 4:
            return None
        
        try:
            module_number = int(parts[0].strip())
            model = parts[3].strip() if len(parts) > 3 else "Unknown"
            state = parts[4].strip() if len(parts) > 4 else "Unknown"
            
            # Remove asterisk from state
            state = state.rstrip('*').strip()
            
            # Determine role based on state (check if asterisk was present)
            role = "Active" if (len(parts) > 4 and '*' in parts[4]) else "Standby"
            
            return StackMemberInfo(
                switch_number=module_number,
                role=role,
                priority=None,
                hardware_model=model,
                serial_number="Unknown",  # Need show module detail for serial
                mac_address=None,
                software_version=None,
                state=state
            )
            
        except (ValueError, IndexError) as e:
            self.logger.debug(f"Failed to parse module line: {line} - {str(e)}")
            return None
    
    def enrich_stack_members_with_detail(self, connection: Any, platform: str, 
                                        stack_members: List[StackMemberInfo]) -> List[StackMemberInfo]:
        """
        Enrich stack member information with detailed data (serial numbers, models).
        
        Args:
            connection: Active device connection
            platform: Device platform
            stack_members: List of basic stack member info
            
        Returns:
            Enriched list of StackMemberInfo objects
        """
        if not stack_members:
            return stack_members
        
        try:
            if platform.upper() in ['IOS', 'IOS-XE']:
                return self._enrich_ios_stack_detail(connection, stack_members)
            elif platform.upper() == 'NX-OS':
                return self._enrich_nxos_module_detail(connection, stack_members)
            else:
                return stack_members
                
        except Exception as e:
            self.logger.error(f"Error enriching stack member details: {str(e)}")
            return stack_members
    
    def _enrich_ios_stack_detail(self, connection: Any, 
                                 stack_members: List[StackMemberInfo]) -> List[StackMemberInfo]:
        """
        Enrich IOS stack members with detailed information from 'show inventory'.
        
        Uses 'show inventory' which provides hardware model and serial number
        for each switch in the stack.
        """
        self.logger.info(f"Enriching {len(stack_members)} IOS stack members with inventory details")
        output = self._execute_command(connection, "show inventory")
        
        if not output:
            self.logger.warning("No output from 'show inventory' command - stack members will have incomplete data")
            return stack_members
        
        # Log raw output for debugging (first 1000 chars at DEBUG level)
        self.logger.debug(f"Raw 'show inventory' output (first 1000 chars): {output[:1000]}")
        
        # Parse inventory output and update stack members
        detail_map = self._parse_ios_inventory(output)
        self.logger.info(f"Parsed inventory data for {len(detail_map)} switches: {list(detail_map.keys())}")
        
        for member in stack_members:
            if member.switch_number in detail_map:
                details = detail_map[member.switch_number]
                old_serial = member.serial_number
                old_model = member.hardware_model
                member.serial_number = details.get('serial', member.serial_number)
                member.hardware_model = details.get('model', member.hardware_model)
                self.logger.info(f"  Switch {member.switch_number}: Model={old_model}->{member.hardware_model}, Serial={old_serial}->{member.serial_number}")
            else:
                self.logger.warning(f"  Switch {member.switch_number}: No inventory data found - keeping existing values (Model={member.hardware_model}, Serial={member.serial_number})")
        
        return stack_members
    
    def _parse_ios_stack_detail(self, output: str) -> dict:
        """
        Parse 'show switch detail' output to extract serial numbers and models.
        
        Returns dict mapping switch_number to details dict.
        
        NOTE: This method is deprecated in favor of _parse_ios_inventory
        as many devices don't provide detailed info in 'show switch detail'.
        """
        detail_map = {}
        current_switch = None
        
        lines = output.split('\n')
        
        for line in lines:
            line_stripped = line.strip()
            
            # Look for switch number header
            switch_match = re.match(r'Switch\s+(\d+)', line_stripped, re.IGNORECASE)
            if switch_match:
                current_switch = int(switch_match.group(1))
                detail_map[current_switch] = {}
                continue
            
            if current_switch is not None:
                # Extract serial number
                serial_match = re.search(r'Serial [Nn]umber\s*:\s*(\S+)', line_stripped)
                if serial_match:
                    detail_map[current_switch]['serial'] = serial_match.group(1)
                
                # Extract model
                model_match = re.search(r'Model [Nn]umber\s*:\s*([\w-]+)', line_stripped)
                if model_match:
                    detail_map[current_switch]['model'] = model_match.group(1)
                
                # Extract version
                version_match = re.search(r'Version\s*:\s*(\S+)', line_stripped)
                if version_match:
                    detail_map[current_switch]['version'] = version_match.group(1)
        
        return detail_map
    
    def _parse_ios_inventory(self, output: str) -> dict:
        """
        Parse 'show inventory' output to extract serial numbers and models for stack members.
        
        Example output:
        NAME: "Switch 1 Chassis", DESCR: "Cisco Catalyst 9500 Series Chassis"
        PID: C9500-48Y4C       , VID: V06  , SN: FDO281500VJ
        
        NAME: "Switch 1 Slot 1 Supervisor", DESCR: "Cisco Catalyst 9500 Series Router"
        PID: C9500-48Y4C       , VID: V06  , SN: FDO281500VJ
        
        Returns dict mapping switch_number to details dict.
        Priority: Chassis > Supervisor > other components
        """
        detail_map = {}
        lines = output.split('\n')
        
        self.logger.info(f"Parsing inventory output with {len(lines)} lines")
        self.logger.info(f"Looking for pattern: NAME: \"Switch X\" followed by PID/SN line")
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for "Switch X" in NAME field (may have additional text like "Chassis", "Slot 1 Supervisor", etc.)
            switch_match = re.search(r'NAME:\s*"Switch\s+(\d+)(?:\s+([^"]+))?"', line, re.IGNORECASE)
            if switch_match:
                switch_number = int(switch_match.group(1))
                component_type = switch_match.group(2).strip() if switch_match.group(2) else ""
                
                # Determine priority: Chassis (highest) > Supervisor > other components (lowest)
                priority = 0
                if 'chassis' in component_type.lower():
                    priority = 3
                elif 'supervisor' in component_type.lower():
                    priority = 2
                else:
                    priority = 1
                
                self.logger.debug(f"Found Switch {switch_number} component: '{component_type}' (priority={priority})")
                
                # Next line should have PID and SN
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    
                    # Extract PID (model)
                    pid_match = re.search(r'PID:\s*([\w-]+)', next_line)
                    if pid_match:
                        model = pid_match.group(1).strip()
                        
                        # Filter out network modules (models containing -NM-), power supplies, fans, disks
                        if '-NM-' in model or 'PWR' in model or 'FAN' in model or 'SSD' in model:
                            self.logger.debug(f"  Skipping component: {model}")
                        else:
                            # Only update if this is higher priority than existing entry
                            if switch_number not in detail_map:
                                detail_map[switch_number] = {'priority': priority}
                            
                            if priority >= detail_map[switch_number].get('priority', 0):
                                detail_map[switch_number]['model'] = model
                                detail_map[switch_number]['priority'] = priority
                                self.logger.debug(f"  Switch {switch_number} model: {model} (priority={priority})")
                    
                    # Extract SN (serial number) - always update if priority is higher
                    sn_match = re.search(r'SN:\s*(\S+)', next_line)
                    if sn_match:
                        serial = sn_match.group(1).strip()
                        if switch_number not in detail_map:
                            detail_map[switch_number] = {'priority': priority}
                        
                        if priority >= detail_map[switch_number].get('priority', 0):
                            detail_map[switch_number]['serial'] = serial
                            detail_map[switch_number]['priority'] = priority
                            self.logger.debug(f"  Switch {switch_number} serial: {serial} (priority={priority})")
            
            i += 1
        
        # Remove priority field from final results
        for switch_num in detail_map:
            if 'priority' in detail_map[switch_num]:
                del detail_map[switch_num]['priority']
        
        self.logger.info(f"Inventory parsing complete: found data for switches {list(detail_map.keys())}")
        return detail_map
    
    def _enrich_nxos_module_detail(self, connection: Any, 
                                   stack_members: List[StackMemberInfo]) -> List[StackMemberInfo]:
        """
        Enrich NX-OS modules with detailed information from 'show module detail'.
        """
        # For each module, get detailed info
        for member in stack_members:
            output = self._execute_command(connection, f"show module {member.switch_number}")
            
            if output:
                # Extract serial number
                serial_match = re.search(r'Serial [Nn]umber:\s*(\S+)', output)
                if serial_match:
                    member.serial_number = serial_match.group(1)
                
                # Extract model (if not already set)
                if member.hardware_model == "Unknown":
                    model_match = re.search(r'Model:\s*([\w-]+)', output)
                    if model_match:
                        member.hardware_model = model_match.group(1)
        
        return stack_members

    def _collect_vss_stack(self, connection: Any) -> List[StackMemberInfo]:
        """
        Collect VSS (Virtual Switching System) stack information from Catalyst 4500-X/6500 devices.
        
        Uses 'show mod' command to detect VSS configuration.
        """
        stack_members = []
        
        # Execute show mod command
        output = self._execute_command(connection, "show mod")
        
        if not output:
            self.logger.debug("No output from 'show mod' command")
            return stack_members
        
        # Check if command is supported
        if 'invalid' in output.lower() or 'not supported' in output.lower():
            self.logger.debug("'show mod' command not supported on this device")
            return stack_members
        
        # Parse the output for VSS members
        stack_members = self._parse_vss_output(output)
        
        if stack_members:
            self.logger.info(f"Found {len(stack_members)} VSS members")
        
        return stack_members

    def _parse_vss_output(self, output: str) -> List[StackMemberInfo]:
        """
        Parse 'show mod' output from VSS devices (Catalyst 4500-X, 6500).
        
        VSS devices show separate sections for each switch in the pair:
        Switch Number: 1 Role: Virtual Switch Active
        Mod Ports Card Type                              Model              Serial No.
        ---+-----+--------------------------------------+------------------+-----------
         1    32  4500X-32 10GE (SFP+)                   WS-C4500X-32       JAE240213DA
         2     8  10GE SFP+                              C4KX-NM-8          JAE242325EK
        
        Switch Number: 2 Role: Virtual Switch Standby
        Mod Ports Card Type                              Model              Serial No.
        ---+-----+--------------------------------------+------------------+-----------
         1    32  4500X-32 10GE (SFP+)                   WS-C4500X-32       JAE171504NJ
         2     8  10GE SFP+                              C4KX-NM-8          JAE17130DJ9
        """
        stack_members = []
        lines = output.split('\n')
        
        self.logger.debug(f"Parsing VSS output with {len(lines)} lines")
        
        # Track which VSS switch we're parsing (1 or 2)
        current_vss_switch = None
        in_data_section = False
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                continue
            
            # Look for "Switch Number: X Role:" to identify which VSS switch section we're in
            if 'switch number:' in line_stripped.lower() and 'role:' in line_stripped.lower():
                # Extract switch number (1 or 2)
                import re
                match = re.search(r'switch number:\s*([12])', line_stripped, re.IGNORECASE)
                if match:
                    current_vss_switch = int(match.group(1))
                    self.logger.debug(f"Line {line_num}: Entering VSS switch {current_vss_switch} section")
                    in_data_section = False
                continue
            
            # Look for module table header
            if 'mod' in line_stripped.lower() and 'ports' in line_stripped.lower() and 'card type' in line_stripped.lower():
                self.logger.debug(f"Line {line_num}: Found module table header for VSS switch {current_vss_switch}")
                continue
            
            # Look for separator line (dashes)
            if '---' in line_stripped or '------' in line_stripped:
                in_data_section = True
                self.logger.debug(f"Line {line_num}: Found separator, entering data section for VSS switch {current_vss_switch}")
                continue
            
            # Parse data lines
            if in_data_section and current_vss_switch:
                # Module lines start with module number (1 or 2) followed by spaces and port count
                if re.match(r'^\s*[12]\s+\d+\s+', line):
                    self.logger.debug(f"Line {line_num}: Attempting to parse module line for VSS switch {current_vss_switch}")
                    member = self._parse_vss_line(line_stripped)
                    if member:
                        # Override the switch number with the VSS switch number
                        member.switch_number = current_vss_switch
                        # Check if we already have this switch
                        existing = next((m for m in stack_members if m.switch_number == current_vss_switch), None)
                        if not existing:
                            stack_members.append(member)
                            self.logger.debug(f"Line {line_num}: Added VSS switch {current_vss_switch}: model={member.hardware_model}, serial={member.serial_number}")
                        else:
                            self.logger.debug(f"Line {line_num}: Already have VSS switch {current_vss_switch}, skipping")
                    else:
                        self.logger.debug(f"Line {line_num}: Failed to parse (likely filtered as module)")
                else:
                    # Non-module line, exit data section
                    if 'mac addresses' in line_stripped.lower() or 'redundancy' in line_stripped.lower():
                        in_data_section = False
                        self.logger.debug(f"Line {line_num}: Exiting data section (found MAC/redundancy section)")
        
        # Only return stack members if we found multiple switches (VSS requires 2)
        if len(stack_members) >= 2:
            self.logger.info(f"Found {len(stack_members)} VSS members")
            return stack_members
        else:
            self.logger.debug(f"Found {len(stack_members)} switch(es), not a VSS configuration (requires 2)")
            return []

    def _parse_vss_line(self, line: str, has_switch_column: bool = False) -> Optional[StackMemberInfo]:
        """
        Parse a single line from 'show mod' VSS output.
        
        Format examples:
        1   52  Sup 7-E, 48 GE (SFP+), 4 XGMII Fabric WS-C4500X-32       JAE240213DA
        1       52     WS-C4500X-32         JAE240213DA  xxxx.xxxx.xxxx  1.0           03.11.03.E
        """
        try:
            self.logger.debug(f"Parsing VSS line: '{line}'")
            
            # Extract switch number (first field)
            switch_match = re.match(r'^\s*([12])\s+', line)
            if not switch_match:
                self.logger.debug(f"No switch number match for line: '{line}'")
                return None
            
            switch_number = int(switch_match.group(1))
            self.logger.debug(f"Extracted switch number: {switch_number}")
            
            # Extract model - look for WS-C pattern or other Cisco model patterns
            # Matches: WS-C4500X-32, C4KX-NM-8, C9300-48P, N9K-C9504, etc.
            model_match = re.search(r'((?:WS-)?C[\w-]+|N\d+K-C[\w-]+)', line, re.IGNORECASE)
            model = model_match.group(1) if model_match else "Unknown"
            
            # Skip network modules - only capture chassis/supervisor modules
            # Network modules have "NM-" in the model name (e.g., C4KX-NM-8, C9300-NM-4G)
            if '-NM-' in model.upper():
                self.logger.debug(f"Skipping network module (not a chassis): model={model}, line='{line}'")
                return None
            
            self.logger.debug(f"Extracted model: '{model}' (match: {model_match.group(1) if model_match else 'None'})")
            
            # Extract serial number - Cisco serial format is typically:
            # 3 letters + 6 digits + 2 letters (e.g., JAE240213DA)
            # or 3 letters + 9 digits (e.g., FOC123456789)
            serial_match = re.search(r'\b([A-Z]{3}\d{6}[A-Z]{2})\b', line)
            if not serial_match:
                # Try alternate pattern: 3 letters + 9 digits
                serial_match = re.search(r'\b([A-Z]{3}\d{9})\b', line)
            
            serial = serial_match.group(1) if serial_match else "Unknown"
            self.logger.debug(f"Extracted serial: '{serial}' (match: {serial_match.group(1) if serial_match else 'None'})")
            
            # Determine role - for VSS, switch 1 is typically Active, switch 2 is Standby
            role = "Active" if switch_number == 1 else "Standby"
            
            # Check if there's a status indicator in the line
            if 'active' in line.lower():
                role = "Active"
            elif 'standby' in line.lower():
                role = "Standby"
            
            self.logger.debug(f"VSS member parsed: switch={switch_number}, role={role}, model={model}, serial={serial}")
            
            return StackMemberInfo(
                switch_number=switch_number,
                role=role,
                priority=None,  # VSS doesn't use priority like StackWise
                hardware_model=model,
                serial_number=serial,
                mac_address=None,
                software_version=None,
                state="Ok"  # Default state for VSS
            )
            
        except (ValueError, IndexError) as e:
            self.logger.debug(f"Failed to parse VSS line: {line} - {str(e)}")
            return None
