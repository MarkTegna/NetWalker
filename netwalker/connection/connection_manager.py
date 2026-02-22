"""
Connection Manager for NetWalker using scrapli and netmiko libraries
"""

import logging
import time
import threading
from typing import Optional, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor, Future

from scrapli import Scrapli
from scrapli.exceptions import ScrapliException

# Import netmiko with proper async support
try:
    from netmiko import ConnectHandler
    from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
    NETMIKO_AVAILABLE = True
except ImportError:
    NETMIKO_AVAILABLE = False

from netwalker.config import Credentials
from .data_models import ConnectionResult, ConnectionMethod, ConnectionStatus


class ConnectionManager:
    """Manages network device connections with SSH/Telnet fallback using scrapli and netmiko"""

    def __init__(self, ssh_port: int = 22, telnet_port: int = 23, timeout: int = 30,
                 ssl_verify: bool = False, ssl_cert_file: str = None, ssl_key_file: str = None, ssl_ca_bundle: str = None):
        self.ssh_port = ssh_port
        self.telnet_port = telnet_port
        self.timeout = timeout
        self.ssl_verify = ssl_verify
        self.ssl_cert_file = ssl_cert_file
        self.ssl_key_file = ssl_key_file
        self.ssl_ca_bundle = ssl_ca_bundle
        self.logger = logging.getLogger(__name__)
        self._active_connections: Dict[str, Any] = {}
        self._connection_locks: Dict[str, threading.Lock] = {}
        self._executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="netwalker-conn")

        # Log SSL configuration
        if not self.ssl_verify:
            self.logger.info("SSL certificate verification disabled")
        else:
            self.logger.info("SSL certificate verification enabled")
            if self.ssl_cert_file:
                self.logger.info(f"SSL certificate file: {self.ssl_cert_file}")
            if self.ssl_ca_bundle:
                self.logger.info(f"SSL CA bundle: {self.ssl_ca_bundle}")

        # Determine available connection methods
        self.available_methods = ["netmiko", "scrapli_telnet"]
        if NETMIKO_AVAILABLE:
            self.logger.info("Netmiko available for SSH connections with async support")
        else:
            self.logger.warning("Netmiko not available, using scrapli telnet only")
            self.available_methods = ["scrapli_telnet"]

        self.logger.info(f"Available connection methods: {self.available_methods}")

    def _detect_panos_from_context(self, host: str, db_manager=None, neighbor_platform: str = None) -> bool:
        """
        Detect if device is PAN-OS based on neighbor platform, hostname, or database information

        Args:
            host: Device hostname or IP address
            db_manager: Optional database manager for platform lookup
            neighbor_platform: Optional platform string from CDP/LLDP neighbor discovery

        Returns:
            True if device is likely PAN-OS, False otherwise
        """
        # Check neighbor platform from CDP/LLDP first (most reliable)
        if neighbor_platform:
            platform_lower = neighbor_platform.lower()
            if any(pattern in platform_lower for pattern in ["palo alto", "pa-", "panos", "pan-os"]):
                self.logger.info(f"PAN-OS detected for {host}: neighbor platform='{neighbor_platform}'")
                return True
        
        # Check hostname pattern (case-insensitive)
        if "-fw" in host.lower():
            self.logger.info(f"PAN-OS detected for {host}: hostname contains '-fw'")
            return True

        # Check database if available
        if db_manager:
            try:
                platform = db_manager.get_device_platform(host)
                if platform:
                    platform_lower = platform.lower()
                    if any(pattern in platform_lower for pattern in ["palo alto", "pa-", "panos", "pan-os"]):
                        self.logger.info(f"PAN-OS detected for {host}: database platform='{platform}'")
                        return True
            except Exception as e:
                self.logger.debug(f"Error checking database for PAN-OS detection: {e}")

        return False

    def connect_device(self, host: str, credentials: Credentials, db_manager=None, neighbor_platform: str = None) -> Tuple[Optional[Any], ConnectionResult]:
        """
        Establish connection to device with SSH/Telnet fallback using async operations

        Args:
            host: Device hostname or IP address
            credentials: Authentication credentials
            db_manager: Optional database manager for platform lookup
            neighbor_platform: Optional platform string from CDP/LLDP neighbor discovery

        Returns:
            Tuple of (connection object, connection result)
        """
        start_time = time.time()

        # Validate credentials
        if not credentials:
            error_msg = "No credentials provided for connection"
            self.logger.error(f"{error_msg} for {host}")
            return None, ConnectionResult(
                host=host,
                method=ConnectionMethod.SSH,
                status=ConnectionStatus.FAILED,
                error_message=error_msg,
                connection_time=0.0
            )

        if not credentials.username or not credentials.password:
            error_msg = "Invalid credentials: username or password is empty"
            self.logger.error(f"{error_msg} for {host}")
            return None, ConnectionResult(
                host=host,
                method=ConnectionMethod.SSH,
                status=ConnectionStatus.FAILED,
                error_message=error_msg,
                connection_time=0.0
            )

        # Ensure thread-safe connection management
        if host not in self._connection_locks:
            self._connection_locks[host] = threading.Lock()

        with self._connection_locks[host]:
            # Try netmiko SSH first (async) with neighbor platform for PAN-OS detection
            if NETMIKO_AVAILABLE:
                connection, result = self._try_netmiko_ssh_connection(host, credentials, start_time, db_manager, neighbor_platform)
                if result.status == ConnectionStatus.SUCCESS:
                    self._active_connections[host] = connection
                    return connection, result

            # Fallback to scrapli Telnet
            self.logger.info(f"SSH failed for {host}, trying Telnet fallback")
            connection, result = self._try_scrapli_telnet_connection(host, credentials, start_time)
            if result.status == ConnectionStatus.SUCCESS:
                self._active_connections[host] = connection

            return connection, result

    def _try_netmiko_ssh_connection(self, host: str, credentials: Credentials, start_time: float, db_manager=None, neighbor_platform: str = None) -> Tuple[Optional[Any], ConnectionResult]:
        """
        Attempt SSH connection using netmiko with async support and proper cleanup

        Args:
            host: Device hostname or IP address
            credentials: Authentication credentials
            start_time: Connection attempt start time
            db_manager: Optional database manager for platform lookup
            neighbor_platform: Optional platform string from CDP/LLDP neighbor discovery

        Returns:
            Tuple of (connection object, connection result)
        """
        try:
            self.logger.info(f"Attempting SSH connection to {host} using netmiko (async)")

            # Detect if this is a PAN-OS device (check neighbor platform first, then hostname, then database)
            is_panos = self._detect_panos_from_context(host, db_manager, neighbor_platform)

            # Select appropriate device_type
            device_type = 'paloalto_panos' if is_panos else 'cisco_ios'

            self.logger.info(f"Using device_type='{device_type}' for {host}")

            # Netmiko device parameters
            device_params = {
                'device_type': device_type,  # Platform-specific
                'host': host,
                'username': credentials.username,
                'password': credentials.password,
                'port': self.ssh_port,
                'timeout': self.timeout,
                'conn_timeout': self.timeout,
                'auth_timeout': self.timeout,
                'banner_timeout': self.timeout,
                'blocking_timeout': self.timeout,
                'keepalive': 30,  # Keep connection alive
                'global_delay_factor': 1,
                'fast_cli': True,  # Optimize for speed
                'session_log': None,  # Disable session logging for performance
                'allow_agent': False,  # Disable SSH agent
                'use_keys': False,  # Disable SSH key authentication
            }

            # Add certificate files if provided
            if self.ssl_cert_file:
                device_params['key_file'] = self.ssl_cert_file
                self.logger.debug(f"Using SSL certificate file: {self.ssl_cert_file}")

            if self.ssl_key_file:
                device_params['key_file'] = self.ssl_key_file
                self.logger.debug(f"Using SSL key file: {self.ssl_key_file}")

            # Add enable password if available
            if credentials.enable_password:
                device_params['secret'] = credentials.enable_password

            # Execute connection in thread pool for async operation
            future: Future = self._executor.submit(self._establish_netmiko_connection, device_params)
            connection = future.result(timeout=self.timeout + 10)  # Allow extra time for connection setup

            if connection:
                connection_time = time.time() - start_time
                self.logger.info(f"SSH connection successful to {host} using netmiko in {connection_time:.2f}s")

                return connection, ConnectionResult(
                    host=host,
                    method=ConnectionMethod.SSH,
                    status=ConnectionStatus.SUCCESS,
                    connection_time=connection_time
                )
            else:
                raise Exception("Connection establishment failed")

        except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
            connection_time = time.time() - start_time
            # Extract just the first line of the error message
            error_msg = f"Netmiko SSH connection failed: {str(e).split(chr(10))[0]}"
            self.logger.warning(f"{error_msg} for {host}")

            return None, ConnectionResult(
                host=host,
                method=ConnectionMethod.SSH,
                status=ConnectionStatus.FAILED,
                error_message=error_msg,
                connection_time=connection_time
            )
        except Exception as e:
            connection_time = time.time() - start_time
            # Extract just the first line of the error message
            error_msg = f"Netmiko SSH connection failed with unexpected error: {str(e).split(chr(10))[0]}"
            self.logger.warning(f"{error_msg} for {host}")

            return None, ConnectionResult(
                host=host,
                method=ConnectionMethod.SSH,
                status=ConnectionStatus.FAILED,
                error_message=error_msg,
                connection_time=connection_time
            )

    def _establish_netmiko_connection(self, device_params: Dict[str, Any]) -> Optional[Any]:
        """
        Establish netmiko connection in a separate thread for async operation

        Args:
            device_params: Device connection parameters

        Returns:
            Connected netmiko device or None if failed
        """
        try:
            connection = ConnectHandler(**device_params)

            # Test the connection with a simple command
            output = connection.send_command("show version", read_timeout=10)
            if output:
                self.logger.debug(f"Connection test successful for {device_params['host']}")
                return connection
            else:
                self.logger.warning(f"Connection test failed for {device_params['host']}")
                connection.disconnect()
                return None

        except Exception as e:
            # Extract just the first line of the error message to avoid garbage text
            error_msg = str(e).split('\n')[0]
            self.logger.error(f"Failed to establish netmiko connection: {error_msg}")
            return None

    def _try_scrapli_telnet_connection(self, host: str, credentials: Credentials, start_time: float) -> Tuple[Optional[Scrapli], ConnectionResult]:
        """
        Attempt Telnet connection using scrapli

        Args:
            host: Device hostname or IP address
            credentials: Authentication credentials
            start_time: Connection attempt start time

        Returns:
            Tuple of (connection object, connection result)
        """
        try:
            self.logger.info(f"Attempting Telnet connection to {host} using scrapli telnet transport")

            connection_params = {
                "host": host,
                "auth_username": credentials.username,
                "auth_password": credentials.password,
                "platform": "cisco_iosxe",  # Default platform, will be detected later
                "port": self.telnet_port,
                "transport": "telnet",  # Use dedicated telnet transport
                "timeout_socket": self.timeout,
                "timeout_transport": self.timeout,
                "timeout_ops": self.timeout,
                "default_desired_privilege_level": "exec"  # Don't try to escalate to enable mode automatically
            }

            # Add enable password if available
            if credentials.enable_password:
                connection_params["auth_secondary"] = credentials.enable_password

            connection = Scrapli(**connection_params)
            connection.open()
            connection_time = time.time() - start_time

            self.logger.info(f"Telnet connection successful to {host} using scrapli in {connection_time:.2f}s")

            return connection, ConnectionResult(
                host=host,
                method=ConnectionMethod.TELNET,
                status=ConnectionStatus.SUCCESS,
                connection_time=connection_time
            )

        except ScrapliException as e:
            connection_time = time.time() - start_time
            error_msg = f"Scrapli Telnet connection failed: {str(e)}"
            self.logger.error(f"{error_msg} for {host}")

            return None, ConnectionResult(
                host=host,
                method=ConnectionMethod.TELNET,
                status=ConnectionStatus.FAILED,
                error_message=error_msg,
                connection_time=connection_time
            )
        except Exception as e:
            connection_time = time.time() - start_time
            error_msg = f"Scrapli Telnet connection failed with unexpected error: {str(e)}"
            self.logger.error(f"{error_msg} for {host}")

            return None, ConnectionResult(
                host=host,
                method=ConnectionMethod.TELNET,
                status=ConnectionStatus.FAILED,
                error_message=error_msg,
                connection_time=connection_time
            )

    def execute_command(self, connection: Any, command: str) -> Optional[str]:
        """
        Execute command on device connection (supports both netmiko and scrapli)

        Args:
            connection: Active connection object (netmiko or scrapli)
            command: Command to execute

        Returns:
            Command output or None if failed
        """
        try:
            self.logger.debug(f"Executing command: {command}")

            # Determine connection type and execute accordingly
            if hasattr(connection, 'send_command') and hasattr(connection, 'device_type'):
                # Netmiko connection
                response = connection.send_command(command, read_timeout=30)
                return response
            elif hasattr(connection, 'send_command') and hasattr(connection, 'transport'):
                # Scrapli connection
                response = connection.send_command(command)
                return response.result
            else:
                self.logger.error(f"Unknown connection type: {type(connection)}")
                return None

        except Exception as e:
            self.logger.error(f"Command execution failed: {str(e)}")
            return None

    def detect_platform(self, connection: Any) -> Optional[str]:
        """
        Detect device platform using 'show version' command (supports both netmiko and scrapli)

        Args:
            connection: Active connection object (netmiko or scrapli)

        Returns:
            Detected platform string or None if detection failed
        """
        try:
            self.logger.debug("Detecting device platform")
            version_output = self.execute_command(connection, "show version")

            if not version_output:
                return None

            # Simple platform detection based on version output
            version_lower = version_output.lower()

            if "nx-os" in version_lower or "nexus" in version_lower:
                return "NX-OS"
            elif "ios-xe" in version_lower:
                return "IOS-XE"
            elif "ios" in version_lower:
                return "IOS"
            else:
                return "Unknown"

        except Exception as e:
            self.logger.error(f"Platform detection failed: {str(e)}")
            return None

    def close_connection(self, host: str) -> bool:
        """
        Properly terminate device connection with exit commands and thread cleanup

        Args:
            host: Device hostname or IP address

        Returns:
            True if connection closed successfully
        """
        if host not in self._active_connections:
            self.logger.debug(f"No active connection found for {host} (may already be closed)")
            return False

        try:
            connection = self._active_connections[host]
            self.logger.debug(f"Closing connection to {host}...")

            # Send exit commands to properly terminate session (causes host to disconnect)
            try:
                # Determine connection type and send appropriate exit commands
                if hasattr(connection, 'send_command') and hasattr(connection, 'device_type'):
                    # Netmiko connection - send proper exit sequence
                    self.logger.debug(f"Closing netmiko connection to {host}")
                    try:
                        # Send multiple exit commands to ensure proper session termination
                        connection.send_command("exit", expect_string="", read_timeout=2)
                        connection.send_command("exit", expect_string="", read_timeout=2)
                        # Send logout as additional cleanup
                        connection.send_command("logout", expect_string="", read_timeout=2)
                    except Exception as exit_error:
                        self.logger.debug(f"Exit commands failed for {host}: {exit_error}")
                        # Exit commands may cause connection to close immediately

                    # Always call disconnect to ensure cleanup
                    try:
                        connection.disconnect()
                        self.logger.debug(f"Netmiko disconnect successful for {host}")
                    except Exception as disconnect_error:
                        self.logger.debug(f"Netmiko disconnect failed for {host}: {disconnect_error}")

                elif hasattr(connection, 'send_command') and hasattr(connection, 'transport'):
                    # Scrapli connection
                    self.logger.debug(f"Closing scrapli connection to {host}")
                    try:
                        # Send exit commands to properly terminate session
                        connection.send_command("exit", expect_string="")
                        connection.send_command("logout", expect_string="")
                    except Exception as exit_error:
                        self.logger.debug(f"Exit commands failed for {host}: {exit_error}")
                        # Exit commands may cause connection to close immediately

                    # Always call close to ensure cleanup
                    try:
                        connection.close()
                        self.logger.debug(f"Scrapli close successful for {host}")
                    except Exception as close_error:
                        self.logger.debug(f"Scrapli close failed for {host}: {close_error}")

                else:
                    self.logger.warning(f"Unknown connection type for {host}: {type(connection)}")
                    # Try generic close methods
                    if hasattr(connection, 'close'):
                        try:
                            connection.close()
                        except Exception as generic_close_error:
                            self.logger.debug(f"Generic close failed for {host}: {generic_close_error}")
                    elif hasattr(connection, 'disconnect'):
                        try:
                            connection.disconnect()
                        except Exception as generic_disconnect_error:
                            self.logger.debug(f"Generic disconnect failed for {host}: {generic_disconnect_error}")

            except Exception as e:
                self.logger.debug(f"Error during graceful close for {host}: {str(e)}")
                # Force disconnect anyway
                try:
                    if hasattr(connection, 'disconnect'):
                        connection.disconnect()
                    elif hasattr(connection, 'close'):
                        connection.close()
                except Exception as force_error:
                    self.logger.debug(f"Force close also failed for {host}: {force_error}")

            # Remove from active connections and locks
            del self._active_connections[host]
            if host in self._connection_locks:
                del self._connection_locks[host]

            self.logger.debug(f"Connection to {host} closed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error closing connection to {host}: {str(e)}")
            # Ensure cleanup even if there was an error
            if host in self._active_connections:
                del self._active_connections[host]
            if host in self._connection_locks:
                del self._connection_locks[host]
            return False

    def close_all_connections(self):
        """Close all active connections with proper thread cleanup and timeout handling"""
        hosts = list(self._active_connections.keys())
        closed_count = 0
        failed_count = 0

        self.logger.info(f"Closing {len(hosts)} active connections...")

        for host in hosts:
            try:
                if self.close_connection(host):
                    closed_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                self.logger.error(f"Error closing connection to {host}: {e}")
                failed_count += 1

        # Shutdown the thread pool executor with proper timeout handling
        self.logger.info("Shutting down connection thread pool...")
        try:
            # First, try graceful shutdown with timeout
            self._executor.shutdown(wait=False)  # Don't wait initially

            # Give threads a reasonable time to complete (30 seconds)
            import concurrent.futures
            import time

            shutdown_start = time.time()
            timeout_seconds = 30

            while time.time() - shutdown_start < timeout_seconds:
                # Check if all threads are done
                if not any(thread.is_alive() for thread in self._executor._threads):
                    break
                time.sleep(0.1)  # Small delay to avoid busy waiting

            # If threads are still running after timeout, log warning
            remaining_threads = [t for t in self._executor._threads if t.is_alive()]
            if remaining_threads:
                self.logger.warning(f"Thread pool shutdown timeout - {len(remaining_threads)} threads still running")
                self.logger.warning("This may indicate connection cleanup issues")

                # Force shutdown without waiting
                try:
                    # Try to interrupt remaining threads
                    for thread in remaining_threads:
                        if hasattr(thread, '_stop'):
                            thread._stop()
                except Exception as thread_error:
                    self.logger.debug(f"Error stopping threads: {thread_error}")
            else:
                self.logger.info("All connection threads terminated successfully")

        except Exception as e:
            self.logger.warning(f"Error during connection thread pool shutdown: {e}")
            # Force shutdown if there's an issue
            try:
                self._executor.shutdown(wait=False)
                self.logger.info("Forced connection thread pool shutdown")
            except Exception as force_error:
                self.logger.error(f"Force shutdown also failed: {force_error}")

        # Final cleanup verification
        remaining_connections = len(self._active_connections)
        if remaining_connections > 0:
            self.logger.error(f"Connection cleanup incomplete - {remaining_connections} connections still tracked")
            # Force clear the tracking dictionaries
            self._active_connections.clear()
            self._connection_locks.clear()

        self.logger.info(f"Connection cleanup complete - closed: {closed_count}, failed: {failed_count}")

        # Force garbage collection to help with cleanup
        import gc
        gc.collect()

    def get_active_connections(self) -> Dict[str, str]:
        """
        Get list of active connections

        Returns:
            Dictionary of host -> connection status
        """
        return {host: "active" for host in self._active_connections.keys()}

    def get_active_connection_count(self) -> int:
        """
        Get count of active connections

        Returns:
            Number of active connections
        """
        return len(self._active_connections)

    def log_connection_status(self):
        """Log current connection status for debugging"""
        active_count = len(self._active_connections)
        if active_count > 0:
            self.logger.info(f"Active connections: {active_count}")
            for host in list(self._active_connections.keys())[:5]:  # Log first 5
                self.logger.debug(f"  - Active connection: {host}")
            if active_count > 5:
                self.logger.debug(f"  - ... and {active_count - 5} more")
        else:
            self.logger.debug("No active connections")

    def force_cleanup_connections(self):
        """
        Force cleanup of all connections without graceful termination.
        Use only when normal cleanup fails.
        """
        self.logger.warning("Force cleanup of connections initiated")

        # Force close all tracked connections
        connection_count = len(self._active_connections)
        if connection_count > 0:
            self.logger.warning(f"Force closing {connection_count} tracked connections")

            for host, connection in list(self._active_connections.items()):
                try:
                    # Try multiple cleanup methods without waiting
                    if hasattr(connection, 'disconnect'):
                        connection.disconnect()
                    elif hasattr(connection, 'close'):
                        connection.close()
                except Exception as e:
                    self.logger.debug(f"Force close failed for {host}: {e}")

            # Clear tracking dictionaries
            self._active_connections.clear()
            self._connection_locks.clear()

        # Force shutdown thread pool
        try:
            self._executor.shutdown(wait=False)
            self.logger.warning("Thread pool force shutdown completed")
        except Exception as e:
            self.logger.error(f"Thread pool force shutdown failed: {e}")

        # Force garbage collection
        import gc
        gc.collect()

        self.logger.warning("Force cleanup completed")
