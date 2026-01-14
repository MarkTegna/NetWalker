"""
Unit tests for Configuration Manager VLAN integration
Feature: vlan-inventory-collection
"""

import pytest
import tempfile
import os
from unittest.mock import patch

from netwalker.config.config_manager import ConfigurationManager
from netwalker.config.data_models import VLANCollectionConfig


class TestConfigVLANIntegration:
    """Unit tests for Configuration Manager VLAN integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create temporary config file for testing
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        self.temp_config.close()  # Close the file handle so we can use it
        self.config_manager = ConfigurationManager(self.temp_config.name)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        # Remove temporary config file
        if os.path.exists(self.temp_config.name):
            os.unlink(self.temp_config.name)
    
    def test_default_vlan_configuration_creation(self):
        """
        Test that VLAN options are included in default config
        
        Validates: Requirements 7.4
        """
        # Create default configuration
        self.config_manager.create_default_config()
        
        # Read the created config file
        with open(self.temp_config.name, 'r') as f:
            config_content = f.read()
        
        # Verify VLAN collection section is present
        assert '[vlan_collection]' in config_content, "VLAN collection section should be in default config"
        
        # Verify VLAN collection options are present
        expected_options = [
            'enabled = true',
            'command_timeout = 30',
            'max_retries = 2',
            'include_inactive_vlans = true',
            '# platforms_to_skip ='
        ]
        
        for option in expected_options:
            assert option in config_content, f"VLAN option '{option}' should be in default config"
    
    def test_vlan_configuration_loading(self):
        """
        Test loading VLAN configuration from INI file
        """
        # Write test configuration
        test_config = """
[vlan_collection]
enabled = false
command_timeout = 45
max_retries = 3
include_inactive_vlans = false
platforms_to_skip = linux,windows
"""
        with open(self.temp_config.name, 'w') as f:
            f.write(test_config)
        
        # Load configuration
        config = self.config_manager.load_configuration()
        
        # Verify VLAN configuration is loaded correctly
        vlan_config = config['vlan_collection']
        assert isinstance(vlan_config, VLANCollectionConfig), "Should return VLANCollectionConfig object"
        assert vlan_config.enabled == False, "Should load enabled setting from INI"
        assert vlan_config.command_timeout == 45, "Should load command_timeout from INI"
        assert vlan_config.max_retries == 3, "Should load max_retries from INI"
        assert vlan_config.include_inactive_vlans == False, "Should load include_inactive_vlans from INI"
        assert vlan_config.platforms_to_skip == ['linux', 'windows'], "Should load platforms_to_skip from INI"
    
    def test_vlan_configuration_defaults(self):
        """
        Test VLAN configuration defaults when section is missing
        """
        # Write minimal configuration without VLAN section
        test_config = """
[discovery]
max_depth = 1
"""
        with open(self.temp_config.name, 'w') as f:
            f.write(test_config)
        
        # Load configuration
        config = self.config_manager.load_configuration()
        
        # Verify VLAN configuration uses defaults
        vlan_config = config['vlan_collection']
        assert isinstance(vlan_config, VLANCollectionConfig), "Should return VLANCollectionConfig object"
        assert vlan_config.enabled == True, "Should use default enabled setting"
        assert vlan_config.command_timeout == 30, "Should use default command_timeout"
        assert vlan_config.max_retries == 2, "Should use default max_retries"
        assert vlan_config.include_inactive_vlans == True, "Should use default include_inactive_vlans"
        assert vlan_config.platforms_to_skip == [], "Should use default empty platforms_to_skip"
    
    def test_cli_override_functionality(self):
        """
        Test CLI override functionality for VLAN configuration
        
        Validates: Requirements 7.5 (Property 26: CLI Override Functionality)
        """
        # Write base configuration
        test_config = """
[vlan_collection]
enabled = true
command_timeout = 30
max_retries = 2
include_inactive_vlans = true
"""
        with open(self.temp_config.name, 'w') as f:
            f.write(test_config)
        
        # Test CLI overrides
        cli_args = {
            'vlan_enabled': False,
            'vlan_timeout': 60,
            'vlan_retries': 5,
            'vlan_include_inactive': False
        }
        
        # Load configuration with CLI overrides
        config = self.config_manager.load_configuration(cli_args)
        
        # Verify CLI overrides are applied
        vlan_config = config['vlan_collection']
        assert vlan_config.enabled == False, "CLI override should set enabled to False"
        assert vlan_config.command_timeout == 60, "CLI override should set command_timeout to 60"
        assert vlan_config.max_retries == 5, "CLI override should set max_retries to 5"
        assert vlan_config.include_inactive_vlans == False, "CLI override should set include_inactive_vlans to False"
    
    def test_empty_platforms_to_skip_handling(self):
        """
        Test handling of empty platforms_to_skip configuration
        """
        # Write configuration with empty platforms_to_skip
        test_config = """
[vlan_collection]
enabled = true
platforms_to_skip = 
"""
        with open(self.temp_config.name, 'w') as f:
            f.write(test_config)
        
        # Load configuration
        config = self.config_manager.load_configuration()
        
        # Verify empty platforms_to_skip is handled correctly
        vlan_config = config['vlan_collection']
        assert vlan_config.platforms_to_skip == [], "Empty platforms_to_skip should result in empty list"
    
    def test_platforms_to_skip_parsing(self):
        """
        Test parsing of comma-separated platforms_to_skip values
        """
        # Write configuration with multiple platforms
        test_config = """
[vlan_collection]
enabled = true
platforms_to_skip = linux, windows , unix,  freebsd
"""
        with open(self.temp_config.name, 'w') as f:
            f.write(test_config)
        
        # Load configuration
        config = self.config_manager.load_configuration()
        
        # Verify platforms are parsed correctly (with whitespace trimmed)
        vlan_config = config['vlan_collection']
        expected_platforms = ['linux', 'windows', 'unix', 'freebsd']
        assert vlan_config.platforms_to_skip == expected_platforms, "Should parse and trim platform names correctly"
    
    def test_vlan_config_in_full_configuration(self):
        """
        Test that VLAN configuration is included in full configuration load
        """
        # Create default configuration
        self.config_manager.create_default_config()
        
        # Load full configuration
        config = self.config_manager.load_configuration()
        
        # Verify VLAN configuration is included
        assert 'vlan_collection' in config, "VLAN collection should be in loaded configuration"
        assert isinstance(config['vlan_collection'], VLANCollectionConfig), "Should be VLANCollectionConfig instance"
        
        # Verify other sections are still present
        expected_sections = ['discovery', 'filtering', 'exclusions', 'output', 'connection', 'vlan_collection']
        for section in expected_sections:
            assert section in config, f"Configuration section '{section}' should be present"
    
    def test_boolean_configuration_parsing(self):
        """
        Test proper parsing of boolean values in VLAN configuration
        """
        # Test various boolean representations
        test_configs = [
            ("enabled = true", True),
            ("enabled = false", False),
            ("enabled = True", True),
            ("enabled = False", False),
            ("enabled = yes", True),
            ("enabled = no", False),
            ("enabled = 1", True),
            ("enabled = 0", False)
        ]
        
        for config_line, expected_value in test_configs:
            # Write test configuration
            test_config = f"""
[vlan_collection]
{config_line}
"""
            with open(self.temp_config.name, 'w') as f:
                f.write(test_config)
            
            # Load configuration
            config = self.config_manager.load_configuration()
            
            # Verify boolean parsing
            vlan_config = config['vlan_collection']
            assert vlan_config.enabled == expected_value, f"Boolean parsing failed for '{config_line}'"
    
    def test_integer_configuration_parsing(self):
        """
        Test proper parsing of integer values in VLAN configuration
        """
        # Write configuration with integer values
        test_config = """
[vlan_collection]
command_timeout = 45
max_retries = 5
"""
        with open(self.temp_config.name, 'w') as f:
            f.write(test_config)
        
        # Load configuration
        config = self.config_manager.load_configuration()
        
        # Verify integer parsing
        vlan_config = config['vlan_collection']
        assert isinstance(vlan_config.command_timeout, int), "command_timeout should be parsed as integer"
        assert isinstance(vlan_config.max_retries, int), "max_retries should be parsed as integer"
        assert vlan_config.command_timeout == 45, "Should parse command_timeout correctly"
        assert vlan_config.max_retries == 5, "Should parse max_retries correctly"