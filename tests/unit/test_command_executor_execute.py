"""
Unit tests for CommandExecutor.execute() method

Tests the complete orchestration workflow of the CommandExecutor.

Author: Mark Oldham
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from netwalker.executor.command_executor import CommandExecutor
from netwalker.executor.data_models import DeviceInfo, CommandResult, ExecutionSummary
from netwalker.config.credentials import Credentials


class TestExecuteMethod:
    """Test the complete execute() orchestration method"""

    @patch('netwalker.executor.excel_exporter.CommandResultExporter')
    @patch('netwalker.executor.progress_reporter.ProgressReporter')
    @patch('netwalker.executor.command_executor.DeviceFilter')
    @patch('netwalker.executor.command_executor.DatabaseManager')
    @patch('netwalker.executor.command_executor.CredentialManager')
    @patch('os.path.exists')
    def test_execute_complete_workflow(
        self,
        mock_exists,
        mock_cred_manager_class,
        mock_db_manager_class,
        mock_device_filter_class,
        mock_progress_reporter_class,
        mock_exporter_class
    ):
        """Test complete execution workflow with multiple devices"""
        # Setup mocks
        mock_exists.return_value = True

        # Mock credentials
        mock_cred_manager = Mock()
        mock_credentials = Credentials(
            username='testuser',
            password='testpass',
            enable_password='enablepass'
        )
        mock_cred_manager.get_credentials.return_value = mock_credentials
        mock_cred_manager_class.return_value = mock_cred_manager

        # Mock database
        mock_db_manager = Mock()
        mock_db_manager.connect.return_value = True
        mock_db_manager_class.return_value = mock_db_manager

        # Mock device filter
        mock_device_filter = Mock()
        test_devices = [
            DeviceInfo(device_name='device1', ip_address='10.1.1.1'),
            DeviceInfo(device_name='device2', ip_address='10.1.1.2'),
            DeviceInfo(device_name='device3', ip_address='10.1.1.3')
        ]
        mock_device_filter.filter_devices.return_value = test_devices
        mock_device_filter_class.return_value = mock_device_filter

        # Mock progress reporter
        mock_progress_reporter = Mock()
        mock_progress_reporter_class.return_value = mock_progress_reporter

        # Mock Excel exporter
        mock_exporter = Mock()
        mock_exporter.export.return_value = 'Command_Results_20260209-19-15.xlsx'
        mock_exporter_class.return_value = mock_exporter

        # Create executor
        executor = CommandExecutor(
            config_file='netwalker.ini',
            device_filter='*',
            command='show version',
            output_dir='.'
        )

        # Mock _execute_on_device to return results
        test_results = [
            CommandResult('device1', '10.1.1.1', 'Success', 'Output 1', 1.0),
            CommandResult('device2', '10.1.1.2', 'Success', 'Output 2', 1.5),
            CommandResult('device3', '10.1.1.3', 'Failed', 'Connection timeout', 2.0)
        ]

        def mock_execute_on_device(device):
            for result in test_results:
                if result.device_name == device.device_name:
                    return result
            return test_results[0]

        executor._execute_on_device = Mock(side_effect=mock_execute_on_device)

        # Execute
        summary = executor.execute()

        # Verify summary
        assert summary.total_devices == 3
        assert summary.successful == 2
        assert summary.failed == 1
        assert summary.total_time > 0
        assert summary.output_file == 'Command_Results_20260209-19-15.xlsx'

        # Verify progress reporter was used
        assert mock_progress_reporter.display_header.called
        assert mock_progress_reporter.report_start.call_count == 3
        assert mock_progress_reporter.report_success.call_count == 2
        assert mock_progress_reporter.report_failure.call_count == 1
        assert mock_progress_reporter.report_summary.called

        # Verify Excel export was called
        assert mock_exporter.export.called
        export_args = mock_exporter.export.call_args
        assert len(export_args[0][0]) == 3  # 3 results

    @patch('netwalker.executor.command_executor.CredentialManager')
    @patch('os.path.exists')
    def test_execute_no_devices_found(self, mock_exists, mock_cred_manager_class):
        """Test execution when no devices match the filter"""
        # Setup mocks
        mock_exists.return_value = True

        mock_cred_manager = Mock()
        mock_credentials = Credentials('testuser', 'testpass', 'enablepass')
        mock_cred_manager.get_credentials.return_value = mock_credentials
        mock_cred_manager_class.return_value = mock_cred_manager

        # Create executor
        executor = CommandExecutor(
            config_file='netwalker.ini',
            device_filter='nonexistent*',
            command='show version',
            output_dir='.'
        )

        # Mock methods to return empty device list
        executor._load_configuration = Mock(return_value={
            'database': {},
            'connection': {},
            'command_executor': {}
        })
        executor._initialize_database = Mock(return_value=True)
        executor._filter_devices = Mock(return_value=[])

        # Execute
        summary = executor.execute()

        # Verify summary shows no devices
        assert summary.total_devices == 0
        assert summary.successful == 0
        assert summary.failed == 0
        assert summary.output_file is None
