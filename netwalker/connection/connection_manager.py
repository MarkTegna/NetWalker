"""
Connection Manager for NetWalker using scrapli library
"""

import logging
import time
from typing import Optional, Tuple, Dict, Any

# Force import of transport plugins to ensure they're available
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

try:
    import ssh2
    SSH2_AVAILABLE = True
except ImportError:
    SSH2_AVAILABLE = False

try:
    import asyncssh
    ASYNCSSH_AVAILABLE = True
except ImportError:
    ASYNCSSH_AVAILABLE = False

# Try to manually register transport plugins with scrapli
try:
    from scrapli.transport.plugins.paramiko.transport import ParamikoTransport
    from scrapli.transport.plugins.ssh2.transport import Ssh2Transport
    from scrapli.transport.plugins.system.transport import SystemTransport
    TRANSPORT_PLUGINS_LOADED = True
except ImportError as e:
    TRANSPORT_PLUGINS_LOADED = False
    print(f"Warning: Could not import transport plugins: {e}")

from scrapli import Scrapli
from scrapli.exceptions import ScrapliException

from netwalker.config import Credentials
from .data_models import ConnectionResult, ConnectionMethod, ConnectionStatus


class ConnectionManager:
    """Manages network device connections with SSH/Telnet fallback"""
    
    def __init__(self, ssh_port: int = 22, telnet_port: int = 23, timeout: int = 30):
        self.ssh_port = ssh_port
        self.telnet_port = telnet_port
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self._active_connections: Dict[str, Scrapli] = {}
        
        # Determine available transports
        self.available_transports = []
        if PARAMIKO_AVAILABLE:
            self.available_transports.append("paramiko")
        if SSH2_AVAILABLE:
            self.available_transports.append("ssh2")
        self.available_transports.append("system")  # Always available as fallback
        
        self.logger.info(f"Available transports: {self.available_transports}")
        
    def connect_device(self, host: str, credentials: Credentials) -> Tuple[Optional[Scrapli], ConnectionResult]:
        """
        Establish connection to device with SSH/Telnet fallback
        
        Args:
            host: Device hostname or IP address
            credentials: Authentication credentials
            
        Returns:
            Tuple of (connection object, connection result)
        """
        start_time = time.time()
        
        # Try SSH first
        connection, result = self._try_ssh_connection(host, credentials, start_time)
        if result.status == ConnectionStatus.SUCCESS:
            self._active_connections[host] = connection
            return connection, result
            
        # Fallback to Telnet
        self.logger.info(f"SSH failed for {host}, trying Telnet fallback")
        connection, result = self._try_telnet_connection(host, credentials, start_time)
        if result.status == ConnectionStatus.SUCCESS:
            self._active_connections[host] = connection
            
        return connection, result
    
    def _try_ssh_connection(self, host: str, credentials: Credentials, start_time: float) -> Tuple[Optional[Scrapli], ConnectionResult]:
        """
        Attempt SSH connection to device with transport fallback
        
        Args:
            host: Device hostname or IP address
            credentials: Authentication credentials
            start_time: Connection attempt start time
            
        Returns:
            Tuple of (connection object, connection result)
        """
        # Try each available transport
        for transport in self.available_transports:
            try:
                self.logger.info(f"Attempting SSH connection to {host} using {transport} transport")
                
                connection_params = {
                    "host": host,
                    "auth_username": credentials.username,
                    "auth_password": credentials.password,
                    "platform": "cisco_iosxe",  # Default platform, will be detected later
                    "port": self.ssh_port,
                    "transport": transport,
                    "timeout_socket": self.timeout,
                    "timeout_transport": self.timeout,
                    "timeout_ops": self.timeout,
                }
                
                # Add transport-specific parameters
                if transport == "paramiko":
                    connection_params.update({
                        "ssh_config_file": False,  # Disable SSH config file
                        "auth_strict_key": False   # Disable strict host key checking
                    })
                elif transport == "system":
                    connection_params.update({
                        "ssh_config_file": False,
                        "auth_strict_key": False
                    })
                
                # Add enable password if available
                if credentials.enable_password:
                    connection_params["auth_secondary"] = credentials.enable_password
                
                connection = Scrapli(**connection_params)
                connection.open()
                connection_time = time.time() - start_time
                
                self.logger.info(f"SSH connection successful to {host} using {transport} in {connection_time:.2f}s")
                
                return connection, ConnectionResult(
                    host=host,
                    method=ConnectionMethod.SSH,
                    status=ConnectionStatus.SUCCESS,
                    connection_time=connection_time
                )
                
            except ScrapliException as e:
                self.logger.warning(f"SSH connection failed with {transport} transport for {host}: {str(e)}")
                continue
            except Exception as e:
                self.logger.warning(f"Unexpected error with {transport} transport for {host}: {str(e)}")
                continue
        
        # All transports failed
        connection_time = time.time() - start_time
        error_msg = f"SSH connection failed with all available transports: {self.available_transports}"
        self.logger.warning(f"{error_msg} for {host}")
        
        return None, ConnectionResult(
            host=host,
            method=ConnectionMethod.SSH,
            status=ConnectionStatus.FAILED,
            error_message=error_msg,
            connection_time=connection_time
        )
    
    def _try_telnet_connection(self, host: str, credentials: Credentials, start_time: float) -> Tuple[Optional[Scrapli], ConnectionResult]:
        """
        Attempt Telnet connection to device using Windows-compatible transport
        
        Args:
            host: Device hostname or IP address
            credentials: Authentication credentials
            start_time: Connection attempt start time
            
        Returns:
            Tuple of (connection object, connection result)
        """
        try:
            self.logger.info(f"Attempting Telnet connection to {host} using telnet transport")
            
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
            
            self.logger.info(f"Telnet connection successful to {host} using telnet transport in {connection_time:.2f}s")
            
            return connection, ConnectionResult(
                host=host,
                method=ConnectionMethod.TELNET,
                status=ConnectionStatus.SUCCESS,
                connection_time=connection_time
            )
            
        except ScrapliException as e:
            connection_time = time.time() - start_time
            error_msg = f"Telnet connection failed: {str(e)}"
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
            error_msg = f"Telnet connection failed with unexpected error: {str(e)}"
            self.logger.error(f"{error_msg} for {host}")
            
            return None, ConnectionResult(
                host=host,
                method=ConnectionMethod.TELNET,
                status=ConnectionStatus.FAILED,
                error_message=error_msg,
                connection_time=connection_time
            )
    
    def execute_command(self, connection: Scrapli, command: str) -> Optional[str]:
        """
        Execute command on device connection
        
        Args:
            connection: Active scrapli connection
            command: Command to execute
            
        Returns:
            Command output or None if failed
        """
        try:
            self.logger.debug(f"Executing command: {command}")
            response = connection.send_command(command)
            return response.result
            
        except ScrapliException as e:
            self.logger.error(f"Command execution failed: {str(e)}")
            return None
    
    def detect_platform(self, connection: Scrapli) -> Optional[str]:
        """
        Detect device platform using 'show version' command
        
        Args:
            connection: Active scrapli connection
            
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
        Properly terminate device connection with exit commands
        
        Args:
            host: Device hostname or IP address
            
        Returns:
            True if connection closed successfully
        """
        if host not in self._active_connections:
            self.logger.warning(f"No active connection found for {host}")
            return False
            
        try:
            connection = self._active_connections[host]
            
            # Send exit commands to properly terminate session
            self.logger.debug(f"Sending exit commands to {host}")
            try:
                connection.send_command("exit", expect_string="")
            except:
                pass  # Exit command may cause connection to close immediately
                
            # Close the connection
            connection.close()
            
            # Remove from active connections
            del self._active_connections[host]
            
            self.logger.info(f"Connection to {host} closed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error closing connection to {host}: {str(e)}")
            return False
    
    def close_all_connections(self):
        """Close all active connections"""
        hosts = list(self._active_connections.keys())
        for host in hosts:
            self.close_connection(host)
    
    def get_active_connections(self) -> Dict[str, str]:
        """
        Get list of active connections
        
        Returns:
            Dictionary of host -> connection status
        """
        return {host: "active" for host in self._active_connections.keys()}