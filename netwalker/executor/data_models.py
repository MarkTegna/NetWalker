"""
Data Models for Command Executor

This module defines the data structures used throughout the command executor
feature for representing device information, command results, and execution
summaries.

Author: Mark Oldham
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DeviceInfo:
    """
    Represents basic device information for command execution.
    
    Attributes:
        device_name: The hostname or name of the device
        ip_address: The primary IP address to connect to the device
    """
    device_name: str
    ip_address: str


@dataclass
class CommandResult:
    """
    Represents the result of executing a command on a single device.
    
    Attributes:
        device_name: The hostname or name of the device
        ip_address: The IP address used to connect to the device
        status: The execution status ("Success", "Failed", "Timeout", "Auth Failed")
        output: The command output or error message
        execution_time: Time taken to execute the command in seconds
    """
    device_name: str
    ip_address: str
    status: str
    output: str
    execution_time: float


@dataclass
class ExecutionSummary:
    """
    Represents a summary of command execution across multiple devices.
    
    Attributes:
        total_devices: Total number of devices processed
        successful: Number of devices where command executed successfully
        failed: Number of devices where command execution failed
        total_time: Total time taken for all executions in seconds
        output_file: Path to the Excel file containing results
    """
    total_devices: int
    successful: int
    failed: int
    total_time: float
    output_file: Optional[str] = None
