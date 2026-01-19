"""
Platform Handler for VLAN command selection

Determines appropriate VLAN commands for different Cisco platforms
and handles platform-specific variations.
"""

import logging
from typing import List, Dict


class PlatformHandler:
    """Handles platform-specific VLAN command selection and validation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Platform-specific VLAN command mapping
        self.platform_commands = {
            'IOS': ['show vlan brief'],
            'IOS-XE': ['show vlan brief'],
            'NX-OS': ['show vlan'],
            'Unknown': ['show vlan brief', 'show vlan']  # Try both for unknown platforms
        }
        
        # Platform-specific interface status command mapping
        self.interface_status_commands = {
            'IOS': ['show interfaces status'],
            'IOS-XE': ['show interfaces status'],
            'NX-OS': ['show interface status'],
            'Unknown': ['show interfaces status', 'show interface status']
        }
        
        # Supported platforms for VLAN collection
        self.supported_platforms = ['IOS', 'IOS-XE', 'NX-OS']
        
        self.logger.debug("PlatformHandler initialized with command mappings")
    
    def get_vlan_commands(self, platform: str) -> List[str]:
        """
        Get VLAN commands for the specified platform
        
        Args:
            platform: Device platform (IOS, IOS-XE, NX-OS, etc.)
            
        Returns:
            List of VLAN commands to try for the platform
        """
        if not platform:
            platform = 'Unknown'
            
        # Normalize platform string
        platform = platform.upper()
        
        # Get commands for platform, fallback to Unknown if not found
        commands = self.platform_commands.get(platform, self.platform_commands['Unknown'])
        
        self.logger.debug(f"Selected VLAN commands for platform {platform}: {commands}")
        return commands.copy()  # Return a copy to prevent modification
    
    def validate_platform_support(self, platform: str) -> bool:
        """
        Check if the platform supports VLAN collection
        
        Args:
            platform: Device platform to check
            
        Returns:
            True if platform supports VLAN collection, False otherwise
        """
        if not platform:
            return True  # Unknown platforms are supported (we'll try both commands)
            
        platform = platform.upper()
        
        # Supported platforms or Unknown (which we'll attempt)
        is_supported = platform in self.supported_platforms or platform == 'UNKNOWN'
        
        self.logger.debug(f"Platform {platform} VLAN support: {is_supported}")
        return is_supported
    
    def adapt_commands_for_platform(self, platform: str) -> Dict[str, str]:
        """
        Adapt VLAN commands for platform-specific variations
        
        Args:
            platform: Device platform
            
        Returns:
            Dictionary of adapted commands
        """
        if not platform:
            platform = 'Unknown'
            
        platform = platform.upper()
        
        # Get the primary VLAN command for the platform
        vlan_commands = self.get_vlan_commands(platform)
        primary_command = vlan_commands[0] if vlan_commands else 'show vlan brief'
        
        # Build command dictionary
        commands = {
            'vlan_brief': primary_command,
            'vlan_detail': primary_command  # For now, use same command for both
        }
        
        # Platform-specific adaptations
        if platform == 'NX-OS':
            commands['vlan_detail'] = 'show vlan detail'
        elif platform in ['IOS', 'IOS-XE']:
            commands['vlan_detail'] = 'show vlan'
        
        self.logger.debug(f"Adapted commands for platform {platform}: {commands}")
        return commands
    
    def get_fallback_commands(self, platform: str) -> List[str]:
        """
        Get fallback commands to try if primary commands fail
        
        Args:
            platform: Device platform
            
        Returns:
            List of fallback VLAN commands
        """
        if not platform:
            return ['show vlan brief', 'show vlan']
            
        platform = platform.upper()
        
        # For known platforms, try the alternative command
        if platform in ['IOS', 'IOS-XE']:
            fallback_commands = ['show vlan']
        elif platform == 'NX-OS':
            fallback_commands = ['show vlan brief']
        else:
            # For unknown platforms, try both
            fallback_commands = ['show vlan brief', 'show vlan']
        
        self.logger.debug(f"Fallback commands for platform {platform}: {fallback_commands}")
        return fallback_commands
    
    def is_vlan_command_supported(self, platform: str, command: str) -> bool:
        """
        Check if a specific VLAN command is supported on the platform
        
        Args:
            platform: Device platform
            command: VLAN command to check
            
        Returns:
            True if command is likely supported, False otherwise
        """
        if not platform or not command:
            return False
            
        platform = platform.upper()
        command = command.lower().strip()
        
        # Check if command is in the platform's command list
        platform_commands = [cmd.lower() for cmd in self.get_vlan_commands(platform)]
        is_supported = command in platform_commands
        
        self.logger.debug(f"Command '{command}' support on {platform}: {is_supported}")
        return is_supported

    
    def get_interface_status_commands(self, platform: str) -> List[str]:
        """
        Get interface status commands for the specified platform
        
        Args:
            platform: Device platform (IOS, IOS-XE, NX-OS, etc.)
            
        Returns:
            List of interface status commands to try for the platform
        """
        if not platform:
            platform = 'Unknown'
            
        # Normalize platform string
        platform = platform.upper()
        
        # Get commands for platform, fallback to Unknown if not found
        commands = self.interface_status_commands.get(platform, self.interface_status_commands['Unknown'])
        
        self.logger.debug(f"Selected interface status commands for platform {platform}: {commands}")
        return commands.copy()  # Return a copy to prevent modification
