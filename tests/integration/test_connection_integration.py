"""
Integration tests for connection management
These tests verify the connection management system works end-to-end
"""

import pytest
from netwalker.connection import ConnectionManager
from netwalker.config import Credentials, CredentialManager, ConfigurationManager


def test_connection_manager_initialization():
    """Test that connection manager initializes properly with configuration"""
    # Test with default configuration
    config_manager = ConfigurationManager()
    config = config_manager.load_configuration()
    
    connection_config = config['connection']
    connection_manager = ConnectionManager(
        ssh_port=connection_config.ssh_port,
        telnet_port=connection_config.telnet_port,
        timeout=config['discovery'].connection_timeout
    )
    
    assert connection_manager.ssh_port == 22
    assert connection_manager.telnet_port == 23
    assert connection_manager.timeout == 30
    assert len(connection_manager.get_active_connections()) == 0


def test_credential_integration():
    """Test credential management integration"""
    # Create sample credentials
    cred_manager = CredentialManager("test_creds.ini")
    cred_manager.create_sample_credentials_file("testuser", "testpass")
    
    # Load credentials
    credentials = cred_manager.get_credentials()
    
    assert credentials is not None
    assert credentials.username == "testuser"
    # Password should be encrypted after loading
    
    # Clean up
    import os
    if os.path.exists("test_creds.ini"):
        os.unlink("test_creds.ini")


def test_configuration_integration():
    """Test full configuration loading and integration"""
    config_manager = ConfigurationManager("test_config.ini")
    
    # Test CLI overrides
    cli_args = {
        'max_depth': 15,
        'timeout': 45,
        'concurrent_connections': 8
    }
    
    config = config_manager.load_configuration(cli_args)
    
    # Verify CLI overrides worked
    assert config['discovery'].max_depth == 15
    assert config['discovery'].connection_timeout == 45
    assert config['discovery'].concurrent_connections == 8
    
    # Verify other defaults
    assert config['output'].reports_directory == "./reports"
    assert config['output'].logs_directory == "./logs"
    
    # Clean up
    import os
    if os.path.exists("test_config.ini"):
        os.unlink("test_config.ini")


def test_end_to_end_configuration_flow():
    """Test the complete configuration and connection setup flow"""
    # 1. Load configuration
    config_manager = ConfigurationManager("integration_test.ini")
    config = config_manager.load_configuration()
    
    # 2. Setup connection manager with config
    connection_manager = ConnectionManager(
        ssh_port=config['connection'].ssh_port,
        telnet_port=config['connection'].telnet_port,
        timeout=config['discovery'].connection_timeout
    )
    
    # 3. Load credentials
    cred_manager = CredentialManager("integration_creds.ini")
    cred_manager.create_sample_credentials_file()
    credentials = cred_manager.get_credentials()
    
    # 4. Verify everything is properly configured
    assert connection_manager is not None
    assert credentials is not None
    assert config['discovery'].max_depth == 10  # Default value
    assert config['exclusions'].exclude_hostnames == ['LUMT*', 'LUMV*']  # Default exclusions
    
    # Clean up
    import os
    for file in ["integration_test.ini", "integration_creds.ini"]:
        if os.path.exists(file):
            os.unlink(file)


if __name__ == "__main__":
    # Run basic integration tests
    test_connection_manager_initialization()
    test_credential_integration()
    test_configuration_integration()
    test_end_to_end_configuration_flow()
    print("All integration tests passed!")