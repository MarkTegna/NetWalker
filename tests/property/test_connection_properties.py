"""
Property-based tests for connection management
Feature: network-topology-discovery, Property 5: SSH Priority and Telnet Fallback
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st
from scrapli.exceptions import ScrapliException

from netwalker.connection import ConnectionManager
from netwalker.connection.data_models import ConnectionMethod, ConnectionStatus
from netwalker.config import Credentials


@given(
    host=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyz0123456789.-'),
    username=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
    password=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
)
def test_ssh_priority_and_telnet_fallback(host, username, password):
    """
    Feature: network-topology-discovery, Property 5: SSH Priority and Telnet Fallback
    For any device connection attempt, SSH should always be attempted first, and if SSH fails, Telnet should be attempted as fallback
    **Validates: Requirements 2.1, 2.2**
    """
    credentials = Credentials(username=username, password=password)
    connection_manager = ConnectionManager()
    
    with patch('netwalker.connection.connection_manager.Scrapli') as mock_scrapli:
        # Configure SSH to fail and Telnet to succeed
        ssh_instance = Mock()
        ssh_instance.open.side_effect = ScrapliException("SSH connection failed")
        
        telnet_instance = Mock()
        telnet_instance.open.return_value = None  # Success
        
        # Mock Scrapli constructor to return different instances based on port and transport
        def scrapli_side_effect(*args, **kwargs):
            port = kwargs.get('port', 22)
            transport = kwargs.get('transport', 'paramiko')
            
            # SSH attempts (port 22) - should fail
            if port == 22:
                return ssh_instance
            # TELNET attempts (port 23) - should succeed
            elif port == 23:
                return telnet_instance
            
            return Mock()
        
        mock_scrapli.side_effect = scrapli_side_effect
        
        # Attempt connection
        connection, result = connection_manager.connect_device(host, credentials)
        
        # Verify SSH was attempted first (port 22 calls)
        ssh_calls = [call for call in mock_scrapli.call_args_list if call[1].get('port') == 22]
        assert len(ssh_calls) >= 1, "SSH should be attempted first"
        
        # Verify Telnet was attempted as fallback (port 23 calls)
        telnet_calls = [call for call in mock_scrapli.call_args_list if call[1].get('port') == 23]
        assert len(telnet_calls) >= 1, "Telnet should be attempted as fallback when SSH fails"
        
        # Verify final result shows Telnet success
        assert result.method == ConnectionMethod.TELNET, "Final connection should use Telnet method"
        assert result.status == ConnectionStatus.SUCCESS, "Connection should succeed via Telnet fallback"


def test_connection_method_recording():
    """
    Feature: network-topology-discovery, Property 6: Connection Method Recording
    For any successful device connection, the connection method (SSH or Telnet) should be accurately recorded
    **Validates: Requirements 2.3**
    """
    credentials = Credentials(username="testuser", password="testpass")
    connection_manager = ConnectionManager()
    
    with patch('netwalker.connection.connection_manager.Scrapli') as mock_scrapli:
        # Test SSH success
        ssh_instance = Mock()
        ssh_instance.open.return_value = None
        mock_scrapli.return_value = ssh_instance
        
        connection, result = connection_manager.connect_device("test-host", credentials)
        
        assert result.method == ConnectionMethod.SSH, "SSH connection should be recorded as SSH method"
        assert result.status == ConnectionStatus.SUCCESS, "SSH connection should be recorded as successful"
        assert result.host == "test-host", "Host should be recorded correctly"


def test_connection_termination():
    """
    Feature: network-topology-discovery, Property 7: Proper Connection Termination
    For any established device connection, when terminating the session, exit commands should be sent to ensure clean disconnection
    **Validates: Requirements 2.4**
    """
    credentials = Credentials(username="testuser", password="testpass")
    connection_manager = ConnectionManager()
    
    with patch('netwalker.connection.connection_manager.Scrapli') as mock_scrapli:
        # Setup successful connection
        connection_instance = Mock()
        connection_instance.open.return_value = None
        connection_instance.send_command.return_value = Mock()
        connection_instance.close.return_value = None
        mock_scrapli.return_value = connection_instance
        
        # Establish connection
        connection, result = connection_manager.connect_device("test-host", credentials)
        assert result.status == ConnectionStatus.SUCCESS
        
        # Close connection
        success = connection_manager.close_connection("test-host")
        
        # Verify exit command was sent
        connection_instance.send_command.assert_called_with("exit", expect_string="")
        
        # Verify connection was closed
        connection_instance.close.assert_called_once()
        
        # Verify method returned success
        assert success is True, "Connection termination should return success"


def test_platform_detection_command_execution():
    """
    Feature: network-topology-discovery, Property 29: Platform Detection Command Execution
    For any device connection, the "show version" command should be executed for platform detection
    **Validates: Requirements 11.1**
    """
    connection_manager = ConnectionManager()
    
    with patch('netwalker.connection.connection_manager.Scrapli') as mock_scrapli:
        # Setup mock connection
        connection_instance = Mock()
        connection_instance.send_command.return_value = Mock(result="Cisco IOS-XE Software")
        
        # Test platform detection
        platform = connection_manager.detect_platform(connection_instance)
        
        # Verify "show version" command was executed
        connection_instance.send_command.assert_called_with("show version")
        
        # Verify platform was detected
        assert platform == "IOS-XE", "Platform should be detected from show version output"


def test_windows_telnet_transport_compatibility():
    """
    Feature: network-topology-discovery, Property 8: Windows TELNET Transport Compatibility
    For any TELNET connection attempt on Windows platform, the connection should use a Windows-compatible transport mechanism
    **Validates: Requirements 2.6**
    """
    credentials = Credentials(username="testuser", password="testpass")
    connection_manager = ConnectionManager()
    
    with patch('netwalker.connection.connection_manager.Scrapli') as mock_scrapli:
        # Configure SSH to fail to force TELNET fallback
        ssh_instance = Mock()
        ssh_instance.open.side_effect = ScrapliException("SSH connection failed")
        
        # Configure TELNET to succeed with paramiko transport
        telnet_instance = Mock()
        telnet_instance.open.return_value = None  # Success
        
        # Mock Scrapli constructor to return different instances based on transport
        def scrapli_side_effect(*args, **kwargs):
            transport = kwargs.get('transport')
            port = kwargs.get('port', 22)
            
            # SSH attempts (should fail)
            if port == 22:  # SSH port
                return ssh_instance
            # TELNET attempts (should succeed with paramiko)
            elif port == 23 and transport == 'paramiko':  # TELNET port with paramiko
                return telnet_instance
            # TELNET with system transport (should be avoided on Windows)
            elif port == 23 and transport == 'system':
                system_instance = Mock()
                system_instance.open.side_effect = ScrapliException("system transport is not supported on windows devices")
                return system_instance
            
            return Mock()
        
        mock_scrapli.side_effect = scrapli_side_effect
        
        # Attempt connection (should fallback to TELNET)
        connection, result = connection_manager.connect_device("test-host", credentials)
        
        # Verify TELNET connection succeeded
        assert result.method == ConnectionMethod.TELNET, "Connection should use TELNET method"
        assert result.status == ConnectionStatus.SUCCESS, "TELNET connection should succeed"
        
        # Verify paramiko transport was used for TELNET (Windows-compatible)
        telnet_calls = [call for call in mock_scrapli.call_args_list 
                       if call[1].get('port') == 23 and call[1].get('transport') == 'paramiko']
        assert len(telnet_calls) >= 1, "TELNET should use paramiko transport for Windows compatibility"
        
        # Verify system transport was not used successfully (should fail on Windows)
        system_calls = [call for call in mock_scrapli.call_args_list 
                       if call[1].get('port') == 23 and call[1].get('transport') == 'system']
        # System transport may be attempted but should not be the successful connection
        if system_calls:
            # If system transport was attempted, it should have failed
            assert result.method == ConnectionMethod.TELNET and result.status == ConnectionStatus.SUCCESS
            # The successful connection should be via paramiko, not system transport


@given(
    version_output=st.sampled_from([
        "Cisco IOS Software",
        "Cisco IOS-XE Software", 
        "Cisco Nexus Operating System (NX-OS) Software",
        "Unknown system software"
    ])
)
def test_platform_detection_accuracy(version_output):
    """
    Property test: For any version output, platform detection should correctly identify the platform type
    """
    connection_manager = ConnectionManager()
    
    with patch.object(connection_manager, 'execute_command') as mock_execute:
        mock_execute.return_value = version_output
        
        connection_mock = Mock()
        platform = connection_manager.detect_platform(connection_mock)
        
        # Verify correct platform detection
        if "NX-OS" in version_output or "Nexus" in version_output:
            assert platform == "NX-OS"
        elif "IOS-XE" in version_output:
            assert platform == "IOS-XE"
        elif "IOS" in version_output:
            assert platform == "IOS"
        else:
            assert platform == "Unknown"


def test_concurrent_connection_management():
    """
    Test that connection manager can handle multiple simultaneous connections
    """
    credentials = Credentials(username="testuser", password="testpass")
    connection_manager = ConnectionManager()
    
    with patch('netwalker.connection.connection_manager.Scrapli') as mock_scrapli:
        # Setup successful connections
        connection_instance = Mock()
        connection_instance.open.return_value = None
        mock_scrapli.return_value = connection_instance
        
        # Establish multiple connections
        hosts = ["host1", "host2", "host3"]
        connections = {}
        
        for host in hosts:
            connection, result = connection_manager.connect_device(host, credentials)
            assert result.status == ConnectionStatus.SUCCESS
            connections[host] = connection
        
        # Verify all connections are tracked
        active_connections = connection_manager.get_active_connections()
        assert len(active_connections) == 3, "All connections should be tracked"
        
        for host in hosts:
            assert host in active_connections, f"Host {host} should be in active connections"
        
        # Close all connections
        connection_manager.close_all_connections()
        
        # Verify all connections are closed
        active_connections = connection_manager.get_active_connections()
        assert len(active_connections) == 0, "All connections should be closed"