"""
Property-based tests for configuration management
Feature: network-topology-discovery, Property 20: Configuration Loading and Override
"""

import os
import tempfile
from hypothesis import given, strategies as st
import pytest
from netwalker.config import ConfigurationManager


@given(
    ini_max_depth=st.integers(min_value=1, max_value=50),
    cli_max_depth=st.integers(min_value=1, max_value=50),
    ini_timeout=st.integers(min_value=10, max_value=300),
    cli_timeout=st.integers(min_value=10, max_value=300)
)
def test_cli_overrides_ini_settings(ini_max_depth, cli_max_depth, ini_timeout, cli_timeout):
    """
    Feature: network-topology-discovery, Property 20: Configuration Loading and Override
    For any combination of INI file settings and CLI options, CLI options should take precedence
    **Validates: Requirements 7.2**
    """
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write(f"""[discovery]
max_depth = {ini_max_depth}
connection_timeout = {ini_timeout}
concurrent_connections = 5
discovery_protocols = CDP,LLDP
""")
        temp_config = f.name
    
    try:
        # Test CLI overrides
        config_manager = ConfigurationManager(temp_config)
        cli_args = {
            'max_depth': cli_max_depth,
            'timeout': cli_timeout
        }
        
        config = config_manager.load_configuration(cli_args)
        
        # CLI values should override INI values
        assert config['discovery'].max_depth == cli_max_depth, f"CLI max_depth {cli_max_depth} should override INI {ini_max_depth}"
        assert config['discovery'].connection_timeout == cli_timeout, f"CLI timeout {cli_timeout} should override INI {ini_timeout}"
        
        # Non-overridden values should come from INI
        assert config['discovery'].concurrent_connections == 5, "Non-overridden values should come from INI"
        
    finally:
        os.unlink(temp_config)


def test_default_configuration_completeness():
    """
    Feature: network-topology-discovery, Property 21: Default Configuration Completeness
    For any default configuration creation, all available options with descriptions should be included
    **Validates: Requirements 7.4**
    """
    with tempfile.NamedTemporaryFile(suffix='.ini', delete=False) as f:
        temp_config = f.name
    
    try:
        os.unlink(temp_config)  # Remove the file so it gets created as default
        
        config_manager = ConfigurationManager(temp_config)
        config = config_manager.load_configuration()
        
        # Verify all required sections exist
        assert 'discovery' in config, "Default config should include discovery section"
        assert 'filtering' in config, "Default config should include filtering section"
        assert 'exclusions' in config, "Default config should include exclusions section"
        assert 'output' in config, "Default config should include output section"
        assert 'connection' in config, "Default config should include connection section"
        
        # Verify discovery config has all required fields
        discovery = config['discovery']
        assert hasattr(discovery, 'max_depth'), "Discovery config should have max_depth"
        assert hasattr(discovery, 'concurrent_connections'), "Discovery config should have concurrent_connections"
        assert hasattr(discovery, 'connection_timeout'), "Discovery config should have connection_timeout"
        assert hasattr(discovery, 'protocols'), "Discovery config should have protocols"
        
        # Verify output config has all required fields
        output = config['output']
        assert hasattr(output, 'reports_directory'), "Output config should have reports_directory"
        assert hasattr(output, 'logs_directory'), "Output config should have logs_directory"
        assert hasattr(output, 'excel_format'), "Output config should have excel_format"
        
        # Verify exclusions config has default exclusions
        exclusions = config['exclusions']
        assert len(exclusions.exclude_hostnames) > 0, "Default exclusions should include hostname patterns"
        assert len(exclusions.exclude_platforms) > 0, "Default exclusions should include platform exclusions"
        
    finally:
        if os.path.exists(temp_config):
            os.unlink(temp_config)


@given(st.text(min_size=1, max_size=50))
def test_configuration_file_handling(config_filename):
    """
    Property test: For any valid configuration filename, the system should handle it gracefully
    """
    # Filter out invalid filename characters for Windows
    safe_filename = "".join(c for c in config_filename if c.isalnum() or c in "._-") + ".ini"
    
    if not safe_filename or safe_filename == ".ini":
        safe_filename = "test_config.ini"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, safe_filename)
        
        config_manager = ConfigurationManager(config_path)
        config = config_manager.load_configuration()
        
        # Should create default config and load successfully
        assert os.path.exists(config_path), f"Configuration file {config_path} should be created"
        assert 'discovery' in config, "Configuration should be loaded successfully"