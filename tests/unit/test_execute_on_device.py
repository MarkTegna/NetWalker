"""Unit tests for _execute_on_device method"""

import pytest
from unittest.mock import Mock, patch
from netwalker.executor.command_executor import CommandExecutor
from netwalker.executor.data_models import DeviceInfo
from netwalker.config.credentials import Credentials


class TestExecuteOnDevice:
    """Test single device command execution"""

    @patch('netwalker.executor.command_executor.ConnectionManager')
    def test_success(self, mock_conn_mgr_class):
        """Test successful command execution"""
        mock_mgr = Mock()
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.status.value = "success"
        mock_result.error_message = None
        
        mock_mgr.connect_device.return_value = (mock_conn, mock_result)
        mock_mgr.execute_command.return_value = "Output"
        mock_mgr.close_connection.return_value = True
        mock_conn_mgr_class.return_value = mock_mgr
        
        executor = CommandExecutor('netwalker.ini', '*', 'show version', '.')
        executor.config = {
            'command_executor': {'connection_timeout': 30},
            'connection': {
                'ssh_port': 22, 'telnet_port': 23, 'ssl_verify': False,
                'ssl_cert_file': None, 'ssl_key_file': None, 'ssl_ca_bundle': None
            }
        }
        executor.credentials = Credentials('user', 'pass', 'enable')
        
        device = DeviceInfo('test-device', '10.1.1.1')
        result = executor._execute_on_device(device)
        
        assert result.device_name == 'test-device'
        assert result.status == 'Success'
        assert result.output == 'Output'
        mock_mgr.close_connection.assert_called_once_with('10.1.1.1')

    @patch('netwalker.executor.command_executor.ConnectionManager')
    def test_timeout(self, mock_conn_mgr_class):
        """Test connection timeout"""
        mock_mgr = Mock()
        mock_result = Mock()
        mock_result.status.value = "failed"
        mock_result.error_message = "Connection timeout"
        
        mock_mgr.connect_device.return_value = (None, mock_result)
        mock_conn_mgr_class.return_value = mock_mgr
        
        executor = CommandExecutor('netwalker.ini', '*', 'show version', '.')
        executor.config = {
            'command_executor': {'connection_timeout': 30},
            'connection': {
                'ssh_port': 22, 'telnet_port': 23, 'ssl_verify': False,
                'ssl_cert_file': None, 'ssl_key_file': None, 'ssl_ca_bundle': None
            }
        }
        executor.credentials = Credentials('user', 'pass', 'enable')
        
        device = DeviceInfo('test-device', '10.1.1.1')
        result = executor._execute_on_device(device)
        
        assert result.status == 'Timeout'
        assert 'timeout' in result.output.lower()
