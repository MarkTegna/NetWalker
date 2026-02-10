"""
Progress Reporter Module for Command Executor

This module provides real-time progress feedback during command execution
on network devices. It displays device connection status, success/failure
indicators, and execution summaries using ASCII characters for Windows
compatibility.

Author: Mark Oldham
"""

import logging
from netwalker.executor.data_models import ExecutionSummary


class ProgressReporter:
    """
    Provides real-time progress reporting for command execution.

    This class displays progress information as commands are executed on
    devices, including:
    - Total device count at start
    - Connection attempts with device name and IP
    - Success/failure indicators using ASCII characters
    - Final execution summary with statistics

    Uses ASCII characters ([OK], [FAIL]) instead of Unicode for Windows
    console compatibility.

    Attributes:
        total_devices: Total number of devices to process
        current_device: Current device number being processed (1-indexed)
        command: The command being executed (for display)
    """

    def __init__(self, total_devices: int, command: str):
        """
        Initialize the progress reporter.

        Args:
            total_devices: Total number of devices to process
            command: The command being executed on devices
        """
        self.logger = logging.getLogger(__name__)
        self.total_devices = total_devices
        self.current_device = 0
        self.command = command

        self.logger.debug(
            "ProgressReporter initialized: total_devices=%d, command='%s'",
            total_devices,
            command
        )

    def report_start(self, device_name: str, ip_address: str) -> None:
        """
        Report the start of command execution on a device.

        Displays a message indicating connection attempt to the device,
        including the device name and IP address.

        Args:
            device_name: The hostname or name of the device
            ip_address: The IP address being connected to

        Example output:
            [1/15] Connecting to BORO-SW-UW01 (10.1.1.1)...
        """
        self.current_device += 1

        print(
            f"  [{self.current_device}/{self.total_devices}] "
            f"Connecting to {device_name} ({ip_address})..."
        )

        self.logger.debug(
            "Progress: [%d/%d] Connecting to %s (%s)",
            self.current_device,
            self.total_devices,
            device_name,
            ip_address
        )

    def report_success(self, device_name: str) -> None:
        """
        Report successful command execution on a device.

        Displays a success indicator with the device name using ASCII
        characters for Windows compatibility.

        Args:
            device_name: The hostname or name of the device

        Example output:
            [OK] BORO-SW-UW01: Command executed successfully
        """
        print(f"    [OK] {device_name}: Command executed successfully")

        self.logger.info(
            "Command executed successfully on %s",
            device_name
        )

    def report_failure(self, device_name: str, error_type: str) -> None:
        """
        Report failed command execution on a device.

        Displays a failure indicator with the device name and error type
        using ASCII characters for Windows compatibility.

        Args:
            device_name: The hostname or name of the device
            error_type: Brief description of the error (e.g., "Connection timeout",
                       "Auth Failed", "Command error")

        Example output:
            [FAIL] BORO-SW-UW02: Connection timeout
        """
        print(f"    [FAIL] {device_name}: {error_type}")

        self.logger.warning(
            "Command execution failed on %s: %s",
            device_name,
            error_type
        )

    def report_summary(self, summary: ExecutionSummary) -> None:
        """
        Report the final execution summary.

        Displays a formatted summary of the command execution including:
        - Total devices processed
        - Number of successful executions
        - Number of failed executions
        - Total execution time
        - Output file path (if available)

        Args:
            summary: ExecutionSummary object with execution statistics

        Example output:
            ================================================================================
            Execution Summary:
              Total devices: 15
              Successful: 13
              Failed: 2
              Total time: 45.3 seconds

            Results exported to: Command_Results_20260209-19-15.xlsx
        """
        separator = "=" * 80

        print(f"\n{separator}")
        print("Execution Summary:")
        print(f"  Total devices: {summary.total_devices}")
        print(f"  Successful: {summary.successful}")
        print(f"  Failed: {summary.failed}")
        print(f"  Total time: {summary.total_time:.1f} seconds")

        if summary.output_file:
            print(f"\nResults exported to: {summary.output_file}")

        print(separator)

        self.logger.info(
            "Execution summary: total=%d, successful=%d, failed=%d, time=%.1fs",
            summary.total_devices,
            summary.successful,
            summary.failed,
            summary.total_time
        )

    def display_header(self) -> None:
        """
        Display the command execution header.

        Shows the command being executed and the total number of devices
        found matching the filter pattern.

        Example output:
            Command Execution: show ip eigrp vrf WAN neigh
            ================================================================================
            Found 15 devices matching filter

            Connecting to devices...
        """
        separator = "=" * 80

        print(f"\nCommand Execution: {self.command}")
        print(separator)
        print(f"Found {self.total_devices} devices matching filter\n")
        print("Connecting to devices...")

        self.logger.info(
            "Starting command execution: command='%s', devices=%d",
            self.command,
            self.total_devices
        )
