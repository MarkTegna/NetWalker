"""
Unit tests for Platform Handler component
"""

import pytest
from netwalker.vlan.platform_handler import PlatformHandler


class TestPlatformHandlerUnitTests:
    """Unit tests for Platform Handler functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.platform_handler = PlatformHandler()
    
    def test_ios_command_selection(self):
        """
        Test "show vlan brief" command selection for IOS platforms
        Requirements: 2.1
        """
        # Test IOS platform
        ios_commands = self.platform_handler.get_vlan_commands('IOS')
        assert 'show vlan brief' in ios_commands
        assert len(ios_commands) == 1
        
        # Test case insensitive
        ios_commands_lower = self.platform_handler.get_vlan_commands('ios')
        assert 'show vlan brief' in ios_commands_lower
    
    def test_ios_xe_command_selection(self):
        """
        Test "show vlan brief" command selection for IOS-XE platforms
        Requirements: 2.1
        """
        # Test IOS-XE platform
        ios_xe_commands = self.platform_handler.get_vlan_commands('IOS-XE')
        assert 'show vlan brief' in ios_xe_commands
        assert len(ios_xe_commands) == 1
        
        # Test case insensitive
        ios_xe_commands_lower = self.platform_handler.get_vlan_commands('ios-xe')
        assert 'show vlan brief' in ios_xe_commands_lower
    
    def test_nxos_command_selection(self):
        """
        Test "show vlan" command selection for NX-OS platform
        Requirements: 2.2
        """
        # Test NX-OS platform
        nxos_commands = self.platform_handler.get_vlan_commands('NX-OS')
        assert 'show vlan' in nxos_commands
        assert len(nxos_commands) == 1
        
        # Test case insensitive
        nxos_commands_lower = self.platform_handler.get_vlan_commands('nx-os')
        assert 'show vlan' in nxos_commands_lower
    
    def test_unknown_platform_fallback(self):
        """
        Test that unknown platforms get both command variants
        """
        # Test unknown platform
        unknown_commands = self.platform_handler.get_vlan_commands('Unknown')
        assert 'show vlan brief' in unknown_commands
        assert 'show vlan' in unknown_commands
        assert len(unknown_commands) == 2
        
        # Test completely unknown platform
        weird_commands = self.platform_handler.get_vlan_commands('WeirdOS')
        assert 'show vlan brief' in weird_commands
        assert 'show vlan' in weird_commands
    
    def test_empty_platform_handling(self):
        """
        Test handling of empty or None platform
        """
        # Test None platform
        none_commands = self.platform_handler.get_vlan_commands(None)
        assert 'show vlan brief' in none_commands
        assert 'show vlan' in none_commands
        
        # Test empty string platform
        empty_commands = self.platform_handler.get_vlan_commands('')
        assert 'show vlan brief' in empty_commands
        assert 'show vlan' in empty_commands
    
    def test_platform_support_validation(self):
        """
        Test platform support validation
        """
        # Test supported platforms
        assert self.platform_handler.validate_platform_support('IOS') == True
        assert self.platform_handler.validate_platform_support('IOS-XE') == True
        assert self.platform_handler.validate_platform_support('NX-OS') == True
        
        # Test unknown platform (should be supported for fallback)
        assert self.platform_handler.validate_platform_support('Unknown') == True
        assert self.platform_handler.validate_platform_support('WeirdOS') == False
        
        # Test empty platform
        assert self.platform_handler.validate_platform_support(None) == True
        assert self.platform_handler.validate_platform_support('') == True
    
    def test_command_adaptation(self):
        """
        Test command adaptation for different platforms
        """
        # Test IOS adaptation
        ios_adapted = self.platform_handler.adapt_commands_for_platform('IOS')
        assert ios_adapted['vlan_brief'] == 'show vlan brief'
        assert ios_adapted['vlan_detail'] == 'show vlan'
        
        # Test NX-OS adaptation
        nxos_adapted = self.platform_handler.adapt_commands_for_platform('NX-OS')
        assert nxos_adapted['vlan_brief'] == 'show vlan'
        assert nxos_adapted['vlan_detail'] == 'show vlan detail'
    
    def test_fallback_commands(self):
        """
        Test fallback command generation
        """
        # Test IOS fallback
        ios_fallback = self.platform_handler.get_fallback_commands('IOS')
        assert 'show vlan' in ios_fallback
        
        # Test NX-OS fallback
        nxos_fallback = self.platform_handler.get_fallback_commands('NX-OS')
        assert 'show vlan brief' in nxos_fallback
        
        # Test unknown platform fallback
        unknown_fallback = self.platform_handler.get_fallback_commands('Unknown')
        assert 'show vlan brief' in unknown_fallback
        assert 'show vlan' in unknown_fallback
    
    def test_command_support_check(self):
        """
        Test VLAN command support checking
        """
        # Test supported commands
        assert self.platform_handler.is_vlan_command_supported('IOS', 'show vlan brief') == True
        assert self.platform_handler.is_vlan_command_supported('NX-OS', 'show vlan') == True
        
        # Test unsupported commands
        assert self.platform_handler.is_vlan_command_supported('IOS', 'show vlan') == False
        assert self.platform_handler.is_vlan_command_supported('NX-OS', 'show vlan brief') == False
        
        # Test invalid inputs
        assert self.platform_handler.is_vlan_command_supported(None, 'show vlan') == False
        assert self.platform_handler.is_vlan_command_supported('IOS', None) == False
        assert self.platform_handler.is_vlan_command_supported('', '') == False