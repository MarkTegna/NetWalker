"""
Custom exceptions for Command Executor

This module defines custom exception classes for better error handling
and reporting in the Command Executor feature.

Author: Mark Oldham
"""


class CommandExecutorError(Exception):
    """Base exception for CommandExecutor errors"""
    pass


class ConfigurationError(CommandExecutorError):
    """Raised when configuration loading or validation fails"""
    pass


class CredentialError(CommandExecutorError):
    """Raised when credential loading fails"""
    pass


class DatabaseConnectionError(CommandExecutorError):
    """Raised when database connection fails"""
    pass
