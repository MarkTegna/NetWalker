"""
Unit tests for ProgressReporter module

Tests the progress reporting functionality for command execution.

Author: Mark Oldham
"""

from io import StringIO
from unittest.mock import patch
from netwalker.executor.progress_reporter import ProgressReporter
from netwalker.executor.data_models import ExecutionSummary


class TestProgressReporter:
    """Test progress reporting functionality"""

    def test_initialization(self):
        """Test ProgressReporter initialization"""
        reporter = ProgressReporter(total_devices=10, command='show version')

        assert reporter.total_devices == 10
        assert reporter.current_device == 0
        assert reporter.command == 'show version'

    @patch('sys.stdout', new_callable=StringIO)
    def test_display_header(self, mock_stdout):
        """Test display of command execution header"""
        reporter = ProgressReporter(total_devices=15, command='show ip eigrp neigh')

        reporter.display_header()

        output = mock_stdout.getvalue()

        # Verify header contains command
        assert 'Command Execution: show ip eigrp neigh' in output

        # Verify header contains device count
        assert 'Found 15 devices matching filter' in output

        # Verify header contains separator
        assert '=' * 80 in output

        # Verify header contains connection message
        assert 'Connecting to devices...' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_report_start(self, mock_stdout):
        """Test reporting start of device connection"""
        reporter = ProgressReporter(total_devices=5, command='show version')

        reporter.report_start('BORO-SW-UW01', '10.1.1.1')

        output = mock_stdout.getvalue()

        # Verify output contains device counter
        assert '[1/5]' in output

        # Verify output contains device name
        assert 'BORO-SW-UW01' in output

        # Verify output contains IP address
        assert '10.1.1.1' in output

        # Verify output contains connection message
        assert 'Connecting to' in output

        # Verify current device counter incremented
        assert reporter.current_device == 1

    @patch('sys.stdout', new_callable=StringIO)
    def test_report_start_multiple_devices(self, mock_stdout):
        """Test reporting start for multiple devices increments counter"""
        reporter = ProgressReporter(total_devices=3, command='show version')

        reporter.report_start('device1', '10.1.1.1')
        reporter.report_start('device2', '10.1.1.2')
        reporter.report_start('device3', '10.1.1.3')

        output = mock_stdout.getvalue()

        # Verify counters increment correctly
        assert '[1/3]' in output
        assert '[2/3]' in output
        assert '[3/3]' in output

        # Verify final counter value
        assert reporter.current_device == 3

    @patch('sys.stdout', new_callable=StringIO)
    def test_report_success(self, mock_stdout):
        """Test reporting successful command execution"""
        reporter = ProgressReporter(total_devices=5, command='show version')

        reporter.report_success('BORO-SW-UW01')

        output = mock_stdout.getvalue()

        # Verify output contains success indicator (ASCII)
        assert '[OK]' in output

        # Verify output contains device name
        assert 'BORO-SW-UW01' in output

        # Verify output contains success message
        assert 'Command executed successfully' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_report_failure(self, mock_stdout):
        """Test reporting failed command execution"""
        reporter = ProgressReporter(total_devices=5, command='show version')

        reporter.report_failure('BORO-SW-UW02', 'Connection timeout')

        output = mock_stdout.getvalue()

        # Verify output contains failure indicator (ASCII)
        assert '[FAIL]' in output

        # Verify output contains device name
        assert 'BORO-SW-UW02' in output

        # Verify output contains error type
        assert 'Connection timeout' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_report_failure_auth_error(self, mock_stdout):
        """Test reporting authentication failure"""
        reporter = ProgressReporter(total_devices=5, command='show version')

        reporter.report_failure('BORO-SW-UW03', 'Auth Failed')

        output = mock_stdout.getvalue()

        # Verify output contains failure indicator
        assert '[FAIL]' in output

        # Verify output contains device name
        assert 'BORO-SW-UW03' in output

        # Verify output contains auth error
        assert 'Auth Failed' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_report_summary_with_output_file(self, mock_stdout):
        """Test reporting execution summary with output file"""
        reporter = ProgressReporter(total_devices=15, command='show version')

        summary = ExecutionSummary(
            total_devices=15,
            successful=13,
            failed=2,
            total_time=45.3,
            output_file='Command_Results_20260209-19-15.xlsx'
        )

        reporter.report_summary(summary)

        output = mock_stdout.getvalue()

        # Verify summary contains separator
        assert '=' * 80 in output

        # Verify summary contains title
        assert 'Execution Summary:' in output

        # Verify summary contains total devices
        assert 'Total devices: 15' in output

        # Verify summary contains successful count
        assert 'Successful: 13' in output

        # Verify summary contains failed count
        assert 'Failed: 2' in output

        # Verify summary contains total time
        assert 'Total time: 45.3 seconds' in output

        # Verify summary contains output file path
        assert 'Results exported to: Command_Results_20260209-19-15.xlsx' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_report_summary_without_output_file(self, mock_stdout):
        """Test reporting execution summary without output file"""
        reporter = ProgressReporter(total_devices=5, command='show version')

        summary = ExecutionSummary(
            total_devices=5,
            successful=5,
            failed=0,
            total_time=12.5,
            output_file=None
        )

        reporter.report_summary(summary)

        output = mock_stdout.getvalue()

        # Verify summary contains statistics
        assert 'Total devices: 5' in output
        assert 'Successful: 5' in output
        assert 'Failed: 0' in output
        assert 'Total time: 12.5 seconds' in output

        # Verify no output file message when file is None
        assert 'Results exported to:' not in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_report_summary_all_failed(self, mock_stdout):
        """Test reporting execution summary with all failures"""
        reporter = ProgressReporter(total_devices=3, command='show version')

        summary = ExecutionSummary(
            total_devices=3,
            successful=0,
            failed=3,
            total_time=5.2,
            output_file='Command_Results_20260209-20-00.xlsx'
        )

        reporter.report_summary(summary)

        output = mock_stdout.getvalue()

        # Verify summary shows all failures
        assert 'Total devices: 3' in output
        assert 'Successful: 0' in output
        assert 'Failed: 3' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_ascii_characters_used(self, mock_stdout):
        """Test that ASCII characters are used instead of Unicode"""
        reporter = ProgressReporter(total_devices=2, command='show version')

        reporter.report_success('device1')
        reporter.report_failure('device2', 'Error')

        output = mock_stdout.getvalue()

        # Verify ASCII characters are used
        assert '[OK]' in output
        assert '[FAIL]' in output

        # Verify Unicode characters are NOT used
        assert '\u2713' not in output  # ✓
        assert '\u2717' not in output  # ✗
        assert '\u2502' not in output  # │
        assert '\u2550' not in output  # ═

    @patch('sys.stdout', new_callable=StringIO)
    def test_complete_workflow(self, mock_stdout):
        """Test complete progress reporting workflow"""
        reporter = ProgressReporter(total_devices=3, command='show ip route')

        # Display header
        reporter.display_header()

        # Report device connections and results
        reporter.report_start('device1', '10.1.1.1')
        reporter.report_success('device1')

        reporter.report_start('device2', '10.1.1.2')
        reporter.report_failure('device2', 'Connection timeout')

        reporter.report_start('device3', '10.1.1.3')
        reporter.report_success('device3')

        # Report summary
        summary = ExecutionSummary(
            total_devices=3,
            successful=2,
            failed=1,
            total_time=15.7,
            output_file='Command_Results_20260209-20-30.xlsx'
        )
        reporter.report_summary(summary)

        output = mock_stdout.getvalue()

        # Verify complete workflow output
        assert 'Command Execution: show ip route' in output
        assert '[1/3]' in output
        assert '[2/3]' in output
        assert '[3/3]' in output
        assert '[OK] device1' in output
        assert '[FAIL] device2' in output
        assert '[OK] device3' in output
        assert 'Execution Summary:' in output
        assert 'Total devices: 3' in output
        assert 'Successful: 2' in output
        assert 'Failed: 1' in output
