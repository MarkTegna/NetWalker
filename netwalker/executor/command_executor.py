"""
Command Executor Core Module for NetWalker

This module provides the core functionality for executing arbitrary commands
on filtered sets of network devices. It orchestrates device filtering, connection
management, command execution, and result collection.

Author: Mark Oldham
"""

import configparser
import logging
import os
import time
from typing import Dict, Any, Optional, List
from netwalker.config.credentials import CredentialManager, Credentials
from netwalker.connection.connection_manager import ConnectionManager
from netwalker.database.database_manager import DatabaseManager
from netwalker.executor.data_models import DeviceInfo, CommandResult, ExecutionSummary
from netwalker.executor.device_filter import DeviceFilter
from netwalker.executor.exceptions import (
    CommandExecutorError,
    ConfigurationError,
    CredentialError,
    DatabaseConnectionError
)


class CommandExecutor:
    """
    Executes commands on filtered network devices and collects results.
    
    This class orchestrates the complete command execution workflow:
    1. Load configuration from INI file
    2. Get credentials from CredentialManager
    3. Filter devices from database
    4. Execute commands sequentially on each device
    5. Collect and export results
    
    Attributes:
        config_file: Path to configuration file (default: netwalker.ini)
        device_filter: SQL wildcard pattern for device name matching
        command: Command string to execute on devices
        output_dir: Directory for Excel output file
    """
    
    def __init__(self, config_file: str, device_filter: str, command: str, output_dir: str):
        """
        Initialize the command executor.
        
        Args:
            config_file: Path to configuration file (e.g., netwalker.ini)
            device_filter: SQL wildcard pattern for device filtering
            command: Command to execute on devices
            output_dir: Output directory for results
        """
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file
        self.device_filter_pattern = device_filter
        self.command = command
        self.output_dir = output_dir
        
        # Configuration and credentials (loaded during execute)
        self.config: Optional[Dict[str, Any]] = None
        self.credentials: Optional[Credentials] = None
        
        # Database and filtering components
        self.db_manager: Optional[DatabaseManager] = None
        self.device_filter: Optional[DeviceFilter] = None

        # Connection manager (initialized during execute)
        self.connection_manager: Optional[ConnectionManager] = None

        self.logger.info(f"CommandExecutor initialized: filter='{device_filter}', command='{command}'")
    
    def execute(self) -> ExecutionSummary:
        """
        Execute the complete command execution workflow.

        This method orchestrates the entire process:
        1. Load configuration
        2. Get credentials
        3. Connect to database
        4. Filter devices
        5. Execute commands on each device
        6. Export results to Excel
        7. Display summary

        Returns:
            ExecutionSummary with execution statistics and output file path

        Raises:
            ConfigurationError: If configuration file is missing or invalid
            CredentialError: If credentials cannot be obtained
            DatabaseConnectionError: If database connection fails
        """
        self.logger.info("Starting command execution workflow")

        start_time = time.time()

        # Step 1: Load configuration with error handling
        try:
            self.config = self._load_configuration()
        except FileNotFoundError as e:
            error_msg = f"Configuration file not found: {self.config_file}"
            self.logger.error(error_msg)
            raise ConfigurationError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to load configuration: {str(e)}"
            self.logger.error(error_msg)
            raise ConfigurationError(error_msg) from e

        # Step 2: Get credentials with error handling
        try:
            self.credentials = self._get_credentials()
            if not self.credentials:
                error_msg = "Failed to obtain device credentials"
                self.logger.error(error_msg)
                raise CredentialError(error_msg)
        except Exception as e:
            error_msg = f"Error loading credentials: {str(e)}"
            self.logger.error(error_msg)
            raise CredentialError(error_msg) from e

        # Step 3: Initialize database connection with error handling
        try:
            if not self._initialize_database():
                error_msg = (
                    f"Failed to connect to database server: "
                    f"{self.config['database'].get('server', 'unknown')}. "
                    f"Please verify database configuration and network connectivity."
                )
                self.logger.error(error_msg)
                raise DatabaseConnectionError(error_msg)
        except DatabaseConnectionError:
            raise
        except Exception as e:
            error_msg = f"Database connection error: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseConnectionError(error_msg) from e

        # Step 4: Filter devices
        devices = self._filter_devices()
        if not devices:
            self.logger.warning(
                "No devices found matching filter: %s",
                self.device_filter_pattern
            )
            return ExecutionSummary(
                total_devices=0,
                successful=0,
                failed=0,
                total_time=0.0,
                output_file=None
            )

        self.logger.info("Found %d devices matching filter", len(devices))

        # Step 5: Initialize progress reporter and display header
        from netwalker.executor.progress_reporter import ProgressReporter
        progress_reporter = ProgressReporter(len(devices), self.command)
        progress_reporter.display_header()

        # Step 6: Execute commands on each device sequentially
        results = []
        successful_count = 0
        failed_count = 0

        for device in devices:
            # Report start of execution for this device
            progress_reporter.report_start(device.device_name, device.ip_address)

            # Execute command on device
            result = self._execute_on_device(device)
            results.append(result)

            # Report success or failure
            if result.status == "Success":
                successful_count += 1
                progress_reporter.report_success(device.device_name)
            else:
                failed_count += 1
                progress_reporter.report_failure(device.device_name, result.status)

        # Step 7: Export results to Excel with error handling
        from netwalker.executor.excel_exporter import CommandResultExporter
        exporter = CommandResultExporter(self.output_dir)

        try:
            output_file = exporter.export(results, self.command)
            self.logger.info("Results exported to: %s", output_file)
        except PermissionError as e:
            error_msg = (
                f"Permission denied writing Excel file to '{self.output_dir}'. "
                f"Please check directory permissions or choose a different output directory."
            )
            self.logger.error(error_msg)
            print(f"\n[FAIL] {error_msg}")
            output_file = None
        except OSError as e:
            error_msg = (
                f"Failed to write Excel file: {str(e)}. "
                f"Please verify disk space and directory access."
            )
            self.logger.error(error_msg)
            print(f"\n[FAIL] {error_msg}")
            output_file = None
        except Exception as e:
            error_msg = f"Failed to export results to Excel: {str(e)}"
            self.logger.error(error_msg)
            print(f"\n[FAIL] {error_msg}")
            output_file = None

        # Calculate total execution time
        total_time = time.time() - start_time

        # Step 8: Create execution summary
        summary = ExecutionSummary(
            total_devices=len(devices),
            successful=successful_count,
            failed=failed_count,
            total_time=total_time,
            output_file=output_file
        )

        # Step 9: Display summary
        progress_reporter.report_summary(summary)

        self.logger.info(
            "Command execution completed: total=%d, successful=%d, failed=%d, time=%.1fs",
            summary.total_devices,
            summary.successful,
            summary.failed,
            summary.total_time
        )

        return summary
    
    def _load_configuration(self) -> Dict[str, Any]:
        """
        Load configuration from INI file.

        This method loads the NetWalker configuration file and extracts
        settings needed for command execution including database connection,
        connection timeouts, and SSH parameters.

        Returns:
            Dictionary containing configuration sections:
            - database: Database connection settings
            - connection: SSH/Telnet connection settings
            - command_executor: Command executor specific settings

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ConfigurationError: If configuration is invalid or missing required sections
        """
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")

        self.logger.info("Loading configuration from: %s", self.config_file)

        config = configparser.ConfigParser(interpolation=None)
        try:
            config.read(self.config_file)
        except Exception as e:
            raise ConfigurationError(f"Failed to parse configuration file: {str(e)}") from e

        # Validate required sections exist
        if not config.has_section('database'):
            raise ConfigurationError(
                "Configuration file missing required [database] section. "
                "Please ensure netwalker.ini contains database configuration."
            )

        # Build configuration dictionary
        config_dict = {
            'database': self._load_database_config(config),
            'connection': self._load_connection_config(config),
            'command_executor': self._load_command_executor_config(config)
        }

        # Validate database configuration
        self._validate_database_config(config_dict['database'])

        self.logger.info("Configuration loaded successfully")
        return config_dict

    
    def _load_database_config(self, config: configparser.ConfigParser) -> Dict[str, Any]:
        """
        Load database configuration section.
        
        Args:
            config: ConfigParser object with loaded configuration
            
        Returns:
            Dictionary with database settings
        """
        db_config = {
            'enabled': True,  # Required for command executor
            'server': config.get('database', 'server', fallback='localhost'),
            'port': config.getint('database', 'port', fallback=1433),
            'database': config.get('database', 'database', fallback='NetWalker'),
            'username': config.get('database', 'username', fallback=''),
            'password': config.get('database', 'password', fallback=''),
            'trust_server_certificate': config.getboolean('database', 'trust_server_certificate', fallback=True),
            'connection_timeout': config.getint('database', 'connection_timeout', fallback=30),
            'command_timeout': config.getint('database', 'command_timeout', fallback=60)
        }
        
        # Handle encrypted passwords (ENC: prefix)
        if db_config['password'].startswith('ENC:'):
            db_config['password'] = self._decrypt_password(db_config['password'])
        
        return db_config
    
    def _load_connection_config(self, config: configparser.ConfigParser) -> Dict[str, Any]:
        """
        Load connection configuration section.
        
        Args:
            config: ConfigParser object with loaded configuration
            
        Returns:
            Dictionary with connection settings
        """
        conn_config = {
            'ssh_port': config.getint('connection', 'ssh_port', fallback=22),
            'telnet_port': config.getint('connection', 'telnet_port', fallback=23),
            'preferred_method': config.get('connection', 'preferred_method', fallback='ssh'),
            'ssl_verify': config.getboolean('connection', 'ssl_verify', fallback=False),
            'ssl_cert_file': config.get('connection', 'ssl_cert_file', fallback=''),
            'ssl_key_file': config.get('connection', 'ssl_key_file', fallback=''),
            'ssl_ca_bundle': config.get('connection', 'ssl_ca_bundle', fallback='')
        }
        
        # Convert empty strings to None for optional SSL file paths
        for key in ['ssl_cert_file', 'ssl_key_file', 'ssl_ca_bundle']:
            if conn_config[key] == '':
                conn_config[key] = None
        
        return conn_config
    
    def _load_command_executor_config(self, config: configparser.ConfigParser) -> Dict[str, Any]:
        """
        Load command executor specific configuration section.
        
        Args:
            config: ConfigParser object with loaded configuration
            
        Returns:
            Dictionary with command executor settings
        """
        # Check if command_executor section exists, otherwise use defaults
        if not config.has_section('command_executor'):
            self.logger.debug("No [command_executor] section found, using defaults")
            return {
                'connection_timeout': 30,
                'ssh_strict_key': False,
                'output_directory': self.output_dir
            }
        
        executor_config = {
            'connection_timeout': config.getint('command_executor', 'connection_timeout', fallback=30),
            'ssh_strict_key': config.getboolean('command_executor', 'ssh_strict_key', fallback=False),
            'output_directory': config.get('command_executor', 'output_directory', fallback=self.output_dir)
        }
        
        return executor_config
    
    def _validate_database_config(self, db_config: Dict[str, Any]) -> None:
        """
        Validate database configuration has required fields.

        Args:
            db_config: Database configuration dictionary

        Raises:
            ConfigurationError: If required configuration is missing or invalid
        """
        required_fields = ['server', 'database']

        for field in required_fields:
            if not db_config.get(field):
                raise ConfigurationError(
                    f"Database configuration missing required field: '{field}'. "
                    f"Please check [database] section in configuration file."
                )

        # Validate port is reasonable
        port = db_config.get('port', 1433)
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ConfigurationError(
                f"Invalid database port: {port}. Port must be between 1 and 65535."
            )

        self.logger.debug("Database configuration validated successfully")
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """
        Decrypt password from base64 encoding.
        
        Args:
            encrypted_password: Base64 encoded password with ENC: prefix
            
        Returns:
            Decrypted password string
        """
        import base64
        try:
            if encrypted_password.startswith('ENC:'):
                encoded = encrypted_password[4:]  # Remove 'ENC:' prefix
                decoded = base64.b64decode(encoded).decode('utf-8')
                return decoded
            return encrypted_password
        except Exception as e:
            self.logger.error(f"Failed to decrypt password: {e}")
            return encrypted_password
    
    def _get_credentials(self) -> Optional[Credentials]:
        """
        Get device credentials using CredentialManager.
        
        This method uses the existing CredentialManager to load credentials
        from the configuration file or prompt the user interactively.
        
        Returns:
            Credentials object or None if credentials cannot be obtained
        """
        self.logger.info("Loading device credentials")
        
        # Use secret_creds.ini for credentials (NetWalker convention)
        cred_manager = CredentialManager(credentials_file='secret_creds.ini')
        credentials = cred_manager.get_credentials()
        
        if credentials:
            self.logger.info(f"Credentials loaded for user: {credentials.username}")
        else:
            self.logger.error("Failed to load credentials")
        
        return credentials
    
    def _initialize_database(self) -> bool:
        """
        Initialize database connection.
        
        Returns:
            True if database connection successful, False otherwise
        """
        if not self.config:
            self.logger.error("Configuration not loaded")
            return False
        
        self.logger.info("Initializing database connection")
        
        # Create DatabaseManager with configuration
        self.db_manager = DatabaseManager(self.config['database'])
        
        # Attempt to connect
        if not self.db_manager.connect():
            self.logger.error("Failed to connect to database")
            return False
        
        self.logger.info("Database connection established")
        return True
    
    def _filter_devices(self) -> List[DeviceInfo]:
        """
        Filter devices from database using the device filter pattern.

        Returns:
            List of DeviceInfo objects matching the filter pattern
        """
        if not self.db_manager:
            self.logger.error("Database manager not initialized")
            return []

        self.logger.info(f"Filtering devices with pattern: {self.device_filter_pattern}")

        # Create DeviceFilter and query database
        self.device_filter = DeviceFilter(self.db_manager)
        devices = self.device_filter.filter_devices(self.device_filter_pattern)

        self.logger.info(f"Found {len(devices)} devices matching filter")
        return devices

    def _execute_on_device(self, device: DeviceInfo) -> CommandResult:
        """
        Execute command on a single device.

        This method:
        1. Establishes connection using ConnectionManager
        2. Executes the command and captures output
        3. Handles connection failures gracefully
        4. Closes connection after execution
        5. Returns CommandResult with status and output

        Args:
            device: DeviceInfo object containing device name and IP address

        Returns:
            CommandResult with execution status, output, and timing information
        """
        start_time = time.time()

        self.logger.info(f"Executing command on {device.device_name} ({device.ip_address})")

        # Initialize connection manager if not already done
        if not self.connection_manager:
            timeout = self.config['command_executor']['connection_timeout']
            self.connection_manager = ConnectionManager(
                ssh_port=self.config['connection']['ssh_port'],
                telnet_port=self.config['connection']['telnet_port'],
                timeout=timeout,
                ssl_verify=self.config['connection']['ssl_verify'],
                ssl_cert_file=self.config['connection']['ssl_cert_file'],
                ssl_key_file=self.config['connection']['ssl_key_file'],
                ssl_ca_bundle=self.config['connection']['ssl_ca_bundle']
            )

        try:
            # Attempt to connect to the device
            connection, conn_result = self.connection_manager.connect_device(
                device.ip_address,
                self.credentials
            )

            # Check if connection was successful
            if not connection or conn_result.status.value != "success":
                execution_time = time.time() - start_time
                error_msg = conn_result.error_message or "Connection failed"

                # Determine failure type from error message
                if "timeout" in error_msg.lower():
                    status = "Timeout"
                elif "auth" in error_msg.lower():
                    status = "Auth Failed"
                else:
                    status = "Failed"

                self.logger.warning(
                    f"Connection failed for {device.device_name}: {error_msg}"
                )

                return CommandResult(
                    device_name=device.device_name,
                    ip_address=device.ip_address,
                    status=status,
                    output=error_msg,
                    execution_time=execution_time
                )

            # Connection successful, execute command
            self.logger.debug(f"Executing command on {device.device_name}: {self.command}")

            output = self.connection_manager.execute_command(connection, self.command)

            execution_time = time.time() - start_time

            # Check if command execution was successful
            if output is None:
                self.logger.warning(f"Command execution failed on {device.device_name}")
                return CommandResult(
                    device_name=device.device_name,
                    ip_address=device.ip_address,
                    status="Success",  # Connection succeeded, but command had issues
                    output="Command execution failed - no output received",
                    execution_time=execution_time
                )

            # Command executed successfully
            self.logger.info(
                f"Command executed successfully on {device.device_name} "
                f"in {execution_time:.2f}s"
            )

            return CommandResult(
                device_name=device.device_name,
                ip_address=device.ip_address,
                status="Success",
                output=output,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(
                f"Error executing command on {device.device_name}: {error_msg}"
            )

            return CommandResult(
                device_name=device.device_name,
                ip_address=device.ip_address,
                status="Failed",
                output=error_msg,
                execution_time=execution_time
            )

        finally:
            # Always close the connection after execution or failure
            try:
                if self.connection_manager:
                    self.connection_manager.close_connection(device.ip_address)
                    self.logger.debug(f"Connection closed for {device.device_name}")
            except Exception as close_error:
                self.logger.warning(
                    f"Error closing connection for {device.device_name}: {close_error}"
                )
