"""
Unit tests for main.py execute command integration
"""

import pytest
import sys
from unittest.mock import patch, MagicMock


class TestMainExecuteIntegration:
    """Test the execute command integration in main.py"""

    @patch('main.handle_execute_command')
    @patch('main.parse_cli_args')
    def test_execute_command_routing(self, mock_parse_args, mock_handle_execute):
        """Test that execute command is routed to handle_execute_command"""
        # Setup mocks
        mock_args = MagicMock()
        mock_args.config = 'netwalker.ini'
        mock_args.filter = '*-uw*'
        mock_args.command = 'show version'
        mock_args.output = '.'
        mock_parse_args.return_value = mock_args
        mock_handle_execute.return_value = 0

        # Simulate command line: python main.py execute --filter "*-uw*" --command "show version"
        with patch.object(sys, 'argv', ['main.py', 'execute', '--filter', '*-uw*', '--command', 'show version']):
            from main import main
            result = main()

        # Verify handle_execute_command was called
        assert mock_handle_execute.called
        assert mock_handle_execute.call_count == 1
        assert result == 0

    @patch('main.handle_execute_command')
    @patch('main.parse_cli_args')
    def test_execute_command_with_custom_config(self, mock_parse_args, mock_handle_execute):
        """Test execute command with custom config file"""
        # Setup mocks
        mock_args = MagicMock()
        mock_args.config = 'custom.ini'
        mock_args.filter = 'BORO-*'
        mock_args.command = 'show ip route'
        mock_args.output = './reports'
        mock_parse_args.return_value = mock_args
        mock_handle_execute.return_value = 0

        # Simulate command line with custom config
        with patch.object(sys, 'argv', ['main.py', 'execute', '-c', 'custom.ini', '-f', 'BORO-*', '-cmd', 'show ip route', '-o', './reports']):
            from main import main
            result = main()

        # Verify handle_execute_command was called with correct args
        assert mock_handle_execute.called
        call_args = mock_handle_execute.call_args[0][0]
        assert call_args.config == 'custom.ini'
        assert call_args.filter == 'BORO-*'
        assert call_args.command == 'show ip route'
        assert call_args.output == './reports'
        assert result == 0

    @patch('main.handle_execute_command')
    @patch('main.parse_cli_args')
    def test_execute_command_keyboard_interrupt(self, mock_parse_args, mock_handle_execute):
        """Test that KeyboardInterrupt is handled gracefully"""
        # Setup mocks
        mock_parse_args.side_effect = KeyboardInterrupt()

        # Simulate command line
        with patch.object(sys, 'argv', ['main.py', 'execute', '--filter', '*', '--command', 'show version']):
            from main import main
            result = main()

        # Verify exit code is 130 (standard for SIGINT)
        assert result == 130

    @patch('main.handle_execute_command')
    @patch('main.parse_cli_args')
    def test_execute_command_exception_handling(self, mock_parse_args, mock_handle_execute):
        """Test that exceptions are handled gracefully"""
        # Setup mocks
        mock_parse_args.side_effect = Exception("Test error")

        # Simulate command line
        with patch.object(sys, 'argv', ['main.py', 'execute', '--filter', '*', '--command', 'show version']):
            from main import main
            result = main()

        # Verify exit code is 1 (error)
        assert result == 1

    @patch('main.parse_arguments')
    def test_non_execute_command_uses_old_parser(self, mock_parse_arguments):
        """Test that non-execute commands use the old argument parser"""
        # Setup mock
        mock_args = MagicMock()
        mock_args.visio = False
        mock_args.db_init = False
        mock_args.db_purge = False
        mock_args.db_purge_devices = False
        mock_args.db_status = False
        mock_args.rewalk_stale = None
        mock_args.walk_unwalked = False
        mock_parse_arguments.return_value = mock_args

        # Simulate command line without execute
        with patch.object(sys, 'argv', ['main.py', '--config', 'netwalker.ini']):
            # This will fail because we're not mocking the full discovery flow,
            # but we can verify parse_arguments was called
            try:
                from main import main
                main()
            except:
                pass  # Expected to fail, we just want to verify the parser was called

        # Verify old parser was called
        assert mock_parse_arguments.called


class TestHandleExecuteCommand:
    """Test the handle_execute_command function"""

    @patch('netwalker.executor.command_executor.CommandExecutor')
    def test_handle_execute_command_success(self, mock_executor_class):
        """Test successful command execution"""
        # Setup mocks
        mock_executor = MagicMock()
        mock_summary = MagicMock()
        mock_summary.total_devices = 5
        mock_executor.execute.return_value = mock_summary
        mock_executor_class.return_value = mock_executor

        # Create mock args
        mock_args = MagicMock()
        mock_args.config = 'netwalker.ini'
        mock_args.filter = '*-uw*'
        mock_args.command = 'show version'
        mock_args.output = '.'

        # Call function
        from main import handle_execute_command
        result = handle_execute_command(mock_args)

        # Verify
        assert result == 0
        assert mock_executor_class.called
        assert mock_executor.execute.called

    @patch('netwalker.executor.command_executor.CommandExecutor')
    def test_handle_execute_command_no_devices(self, mock_executor_class):
        """Test command execution with no matching devices"""
        # Setup mocks
        mock_executor = MagicMock()
        mock_summary = MagicMock()
        mock_summary.total_devices = 0
        mock_executor.execute.return_value = mock_summary
        mock_executor_class.return_value = mock_executor

        # Create mock args
        mock_args = MagicMock()
        mock_args.config = 'netwalker.ini'
        mock_args.filter = 'NONEXISTENT-*'
        mock_args.command = 'show version'
        mock_args.output = '.'

        # Call function
        from main import handle_execute_command
        result = handle_execute_command(mock_args)

        # Verify exit code is 1 (no devices found)
        assert result == 1

    @patch('netwalker.executor.command_executor.CommandExecutor')
    def test_handle_execute_command_file_not_found(self, mock_executor_class):
        """Test command execution with missing config file"""
        # Setup mocks
        mock_executor_class.side_effect = FileNotFoundError("Config file not found")

        # Create mock args
        mock_args = MagicMock()
        mock_args.config = 'nonexistent.ini'
        mock_args.filter = '*'
        mock_args.command = 'show version'
        mock_args.output = '.'

        # Call function
        from main import handle_execute_command
        result = handle_execute_command(mock_args)

        # Verify exit code is 1 (error)
        assert result == 1

    @patch('netwalker.executor.command_executor.CommandExecutor')
    def test_handle_execute_command_exception(self, mock_executor_class):
        """Test command execution with unexpected exception"""
        # Setup mocks
        mock_executor_class.side_effect = Exception("Unexpected error")

        # Create mock args
        mock_args = MagicMock()
        mock_args.config = 'netwalker.ini'
        mock_args.filter = '*'
        mock_args.command = 'show version'
        mock_args.output = '.'

        # Call function
        from main import handle_execute_command
        result = handle_execute_command(mock_args)

        # Verify exit code is 1 (error)
        assert result == 1
