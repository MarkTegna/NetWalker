"""
VLAN Collector for orchestrating VLAN information collection

Orchestrates VLAN information collection from network devices using 
platform-appropriate commands and handles errors gracefully.
"""

import logging
import asyncio
import concurrent.futures
import threading
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from netwalker.connection.data_models import VLANInfo, VLANCollectionResult, VLANCollectionConfig, DeviceInfo
from .platform_handler import PlatformHandler
from .vlan_parser import VLANParser


class VLANCollector:
    """Orchestrates VLAN information collection from network devices"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Initialize VLAN collection configuration
        vlan_config = config.get('vlan_collection', {})
        
        # Handle both dictionary and VLANCollectionConfig object
        if hasattr(vlan_config, 'enabled'):
            # Already a VLANCollectionConfig object
            self.vlan_config = vlan_config
        else:
            # Dictionary format - create VLANCollectionConfig
            self.vlan_config = VLANCollectionConfig(
                enabled=vlan_config.get('enabled', True),
                command_timeout=vlan_config.get('command_timeout', 30),
                max_retries=vlan_config.get('max_retries', 2),
                include_inactive_vlans=vlan_config.get('include_inactive_vlans', True),
                platforms_to_skip=vlan_config.get('platforms_to_skip', [])
            )
        
        # Initialize components
        self.platform_handler = PlatformHandler()
        self.vlan_parser = VLANParser()
        
        # Statistics tracking
        self.collection_stats = {
            'total_attempts': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'skipped_collections': 0,
            'total_vlans_collected': 0
        }
        
        # Concurrency and resource management
        self.max_concurrent_collections = config.get('max_concurrent_vlan_collections', 5)
        self.resource_semaphore = threading.Semaphore(self.max_concurrent_collections)
        self.active_collections = {}  # Track active collections for cleanup
        self.collection_lock = threading.Lock()
        
        # Performance tracking
        self.performance_stats = {
            'total_collection_time': 0.0,
            'average_collection_time': 0.0,
            'fastest_collection': float('inf'),
            'slowest_collection': 0.0
        }
        
        self.logger.info(f"VLANCollector initialized with config: enabled={self.vlan_config.enabled}, max_concurrent={self.max_concurrent_collections}")
    
    def collect_vlan_information(self, connection: Any, device_info: DeviceInfo) -> List[VLANInfo]:
        """
        Collect VLAN information from a device with resource management
        
        Args:
            connection: Active device connection
            device_info: Device information object
            
        Returns:
            List of VLANInfo objects collected from the device
        """
        if not self._is_vlan_collection_enabled():
            self.logger.debug(f"VLAN collection disabled, skipping device {device_info.hostname}")
            self.collection_stats['skipped_collections'] += 1
            return []
        
        if not self._should_collect_vlans_for_device(device_info):
            self.logger.info(f"Skipping VLAN collection for device {device_info.hostname} (platform: {device_info.platform})")
            self.collection_stats['skipped_collections'] += 1
            return []
        
        # Acquire resource semaphore for concurrent collection management
        collection_id = f"{device_info.hostname}_{int(time.time())}"
        
        try:
            # Use timeout for semaphore acquisition to prevent indefinite blocking
            if not self.resource_semaphore.acquire(timeout=60):
                self.logger.warning(f"Resource semaphore timeout for device {device_info.hostname}")
                self.collection_stats['failed_collections'] += 1
                return []
            
            # Track active collection
            with self.collection_lock:
                self.active_collections[collection_id] = {
                    'device': device_info.hostname,
                    'start_time': time.time(),
                    'thread_id': threading.current_thread().ident
                }
            
            return self._collect_vlan_information_with_timeout(connection, device_info, collection_id)
            
        finally:
            # Always release semaphore and clean up tracking
            try:
                self.resource_semaphore.release()
            except ValueError:
                # Semaphore was not acquired, ignore
                pass
            
            # Clean up active collection tracking
            with self.collection_lock:
                self.active_collections.pop(collection_id, None)
    
    def _collect_vlan_information_with_timeout(self, connection: Any, device_info: DeviceInfo, collection_id: str) -> List[VLANInfo]:
        """
        Internal method to collect VLAN information with timeout enforcement
        
        Args:
            connection: Active device connection
            device_info: Device information object
            collection_id: Unique collection identifier
            
        Returns:
            List of VLANInfo objects collected from the device
        """
        start_time = time.time()
        
        try:
            self.collection_stats['total_attempts'] += 1
            
            self.logger.info(f"Starting VLAN collection for device {device_info.hostname} (platform: {device_info.platform})")
            
            # Get platform-specific commands
            commands = self.platform_handler.get_vlan_commands(device_info.platform)
            
            # Execute VLAN commands with timeout
            vlan_output = self._execute_vlan_commands_with_timeout(connection, commands, device_info, collection_id)
            
            if not vlan_output:
                self._handle_collection_error(device_info, "No VLAN output received from device")
                return []
            
            # Parse VLAN information
            vlans = self.vlan_parser.parse_vlan_output(
                vlan_output, 
                device_info.platform, 
                device_info.hostname, 
                device_info.primary_ip
            )
            
            # Validate and process VLANs
            valid_vlans = self._validate_and_process_vlans(vlans, device_info)
            
            # Update statistics
            collection_time = time.time() - start_time
            self._update_performance_stats(collection_time)
            
            self.collection_stats['successful_collections'] += 1
            self.collection_stats['total_vlans_collected'] += len(valid_vlans)
            
            self.logger.info(f"Successfully collected {len(valid_vlans)} VLANs from device {device_info.hostname} in {collection_time:.2f}s")
            return valid_vlans
            
        except Exception as e:
            collection_time = time.time() - start_time
            self.logger.error(f"VLAN collection failed for {device_info.hostname} after {collection_time:.2f}s: {e}")
            self._handle_collection_error(device_info, str(e))
            return []
    
    def _execute_vlan_commands_with_timeout(self, connection: Any, commands: List[str], device_info: DeviceInfo, collection_id: str) -> Optional[str]:
        """
        Execute VLAN commands with strict timeout enforcement and resource cleanup
        
        Args:
            connection: Active device connection
            commands: List of VLAN commands to try
            device_info: Device information
            collection_id: Unique collection identifier
            
        Returns:
            VLAN command output or None if all commands failed
        """
        # Calculate total timeout including retries
        total_timeout = self.vlan_config.command_timeout * (self.vlan_config.max_retries + 1) * len(commands)
        
        for attempt in range(self.vlan_config.max_retries + 1):
            for command in commands:
                try:
                    # Check if collection should be cancelled (for resource cleanup)
                    if not self._is_collection_active(collection_id):
                        self.logger.warning(f"Collection {collection_id} was cancelled, aborting command execution")
                        return None
                    
                    self.logger.debug(f"Executing VLAN command '{command}' on {device_info.hostname} (attempt {attempt + 1})")
                    
                    # Execute command with strict timeout
                    output = self._execute_single_command_with_timeout(connection, command, collection_id)
                    
                    if output and output.strip():
                        self.logger.debug(f"Successfully executed '{command}' on {device_info.hostname}")
                        return output
                    else:
                        self.logger.warning(f"Empty output from command '{command}' on {device_info.hostname}")
                        
                except Exception as e:
                    error_msg = str(e).lower()
                    
                    # Check for specific error conditions
                    if 'invalid' in error_msg or 'unrecognized' in error_msg:
                        self.logger.warning(f"Command '{command}' not supported on {device_info.hostname}: {e}")
                        continue  # Try next command
                    elif 'permission' in error_msg or 'privilege' in error_msg or 'authorization' in error_msg:
                        self.logger.warning(f"Insufficient privileges for '{command}' on {device_info.hostname}")
                        break  # Don't retry on auth issues
                    elif 'timeout' in error_msg:
                        self.logger.warning(f"Timeout executing '{command}' on {device_info.hostname}: {e}")
                        if attempt < self.vlan_config.max_retries:
                            continue  # Retry on timeout
                        else:
                            break  # Max retries reached
                    else:
                        self.logger.warning(f"Command '{command}' failed on {device_info.hostname}: {e}")
                        
                        if attempt < self.vlan_config.max_retries:
                            continue  # Retry
        
        self.logger.error(f"All VLAN commands failed for device {device_info.hostname}")
        return None
    
    def _execute_single_command_with_timeout(self, connection: Any, command: str, collection_id: str) -> Optional[str]:
        """
        Execute a single command with timeout handling and resource monitoring
        
        Args:
            connection: Active device connection
            command: Command to execute
            collection_id: Unique collection identifier
            
        Returns:
            Command output or None if failed
        """
        try:
            # Use concurrent.futures for timeout enforcement
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._execute_command_raw, connection, command)
                
                try:
                    # Wait for command completion with timeout
                    result = future.result(timeout=self.vlan_config.command_timeout)
                    return result
                    
                except concurrent.futures.TimeoutError:
                    self.logger.error(f"Command '{command}' timed out after {self.vlan_config.command_timeout}s for collection {collection_id}")
                    
                    # Cancel the future to clean up resources
                    future.cancel()
                    
                    # Update collection tracking
                    with self.collection_lock:
                        if collection_id in self.active_collections:
                            self.active_collections[collection_id]['timeout'] = True
                    
                    raise Exception(f"Command timeout after {self.vlan_config.command_timeout}s")
                    
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            raise
    
    def _execute_command_raw(self, connection: Any, command: str) -> Optional[str]:
        """
        Raw command execution method (extracted for timeout handling)
        
        Args:
            connection: Active device connection
            command: Command to execute
            
        Returns:
            Command output or None if failed
        """
        try:
            # Determine connection type and execute accordingly
            if hasattr(connection, 'send_command') and hasattr(connection, 'device_type'):
                # Netmiko connection
                response = connection.send_command(command, read_timeout=self.vlan_config.command_timeout)
                return response
            elif hasattr(connection, 'send_command') and hasattr(connection, 'transport'):
                # Scrapli connection
                response = connection.send_command(command)
                return response.result if hasattr(response, 'result') else str(response)
            elif hasattr(connection, 'send_command'):
                # Generic connection (for testing)
                try:
                    response = connection.send_command(command)
                    if hasattr(response, 'result'):
                        return response.result
                    else:
                        return str(response)
                except TypeError:
                    # Fallback for netmiko-style
                    response = connection.send_command(command, read_timeout=self.vlan_config.command_timeout)
                    return response
            else:
                self.logger.error(f"Unknown connection type: {type(connection)}")
                return None
                
        except Exception as e:
            self.logger.error(f"Raw command execution failed: {e}")
            raise
    
    def _is_collection_active(self, collection_id: str) -> bool:
        """
        Check if a collection is still active (for resource cleanup)
        
        Args:
            collection_id: Unique collection identifier
            
        Returns:
            True if collection is active, False otherwise
        """
        with self.collection_lock:
            return collection_id in self.active_collections
    
    def _update_performance_stats(self, collection_time: float) -> None:
        """
        Update performance statistics for collection operations
        
        Args:
            collection_time: Time taken for collection in seconds
        """
        self.performance_stats['total_collection_time'] += collection_time
        
        if self.collection_stats['successful_collections'] > 0:
            self.performance_stats['average_collection_time'] = (
                self.performance_stats['total_collection_time'] / self.collection_stats['successful_collections']
            )
        
        if collection_time < self.performance_stats['fastest_collection']:
            self.performance_stats['fastest_collection'] = collection_time
        
        if collection_time > self.performance_stats['slowest_collection']:
            self.performance_stats['slowest_collection'] = collection_time
    
    def get_active_collections(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about currently active collections
        
        Returns:
            Dictionary of active collections with their details
        """
        with self.collection_lock:
            current_time = time.time()
            active_info = {}
            
            for collection_id, info in self.active_collections.items():
                active_info[collection_id] = {
                    'device': info['device'],
                    'duration': current_time - info['start_time'],
                    'thread_id': info['thread_id'],
                    'timeout': info.get('timeout', False)
                }
            
            return active_info
    
    def cleanup_resources(self) -> None:
        """
        Clean up resources and cancel any hanging collections
        """
        self.logger.info("Cleaning up VLAN collection resources...")
        
        # Get list of active collections
        active_collections = self.get_active_collections()
        
        if active_collections:
            self.logger.warning(f"Found {len(active_collections)} active collections during cleanup")
            
            for collection_id, info in active_collections.items():
                if info['duration'] > self.vlan_config.command_timeout * 2:
                    self.logger.warning(f"Collection {collection_id} for device {info['device']} has been running for {info['duration']:.1f}s")
        
        # Clear active collections tracking
        with self.collection_lock:
            self.active_collections.clear()
        
        # Log performance summary
        self._log_performance_summary()
        
        self.logger.info("VLAN collection resource cleanup completed")
    
    def _log_performance_summary(self) -> None:
        """Log performance statistics summary"""
        if self.collection_stats['successful_collections'] > 0:
            self.logger.info("VLAN Collection Performance Summary:")
            self.logger.info(f"  Total Collection Time: {self.performance_stats['total_collection_time']:.2f}s")
            self.logger.info(f"  Average Collection Time: {self.performance_stats['average_collection_time']:.2f}s")
            self.logger.info(f"  Fastest Collection: {self.performance_stats['fastest_collection']:.2f}s")
            self.logger.info(f"  Slowest Collection: {self.performance_stats['slowest_collection']:.2f}s")
            self.logger.info(f"  Concurrent Collections Limit: {self.max_concurrent_collections}")
    
    def collect_vlans_concurrently(self, device_connections: List[tuple]) -> List[VLANCollectionResult]:
        """
        Collect VLANs from multiple devices concurrently
        
        Args:
            device_connections: List of (connection, device_info) tuples
            
        Returns:
            List of VLANCollectionResult objects
        """
        if not device_connections:
            return []
        
        self.logger.info(f"Starting concurrent VLAN collection for {len(device_connections)} devices")
        
        results = []
        
        # Use ThreadPoolExecutor for concurrent collection
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_collections) as executor:
            # Submit all collection tasks
            future_to_device = {}
            
            for connection, device_info in device_connections:
                future = executor.submit(self._collect_single_device_safe, connection, device_info)
                future_to_device[future] = device_info
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_device, timeout=300):  # 5 minute total timeout
                device_info = future_to_device[future]
                
                try:
                    vlans = future.result()
                    
                    result = VLANCollectionResult(
                        device_hostname=device_info.hostname,
                        device_ip=device_info.primary_ip,
                        vlans=vlans,
                        collection_success=len(vlans) > 0 or device_info.vlan_collection_status == "no_vlans_found",
                        collection_timestamp=datetime.now(),
                        error_details=device_info.vlan_collection_error
                    )
                    
                    results.append(result)
                    
                except Exception as e:
                    self.logger.error(f"Concurrent collection failed for device {device_info.hostname}: {e}")
                    
                    result = VLANCollectionResult(
                        device_hostname=device_info.hostname,
                        device_ip=device_info.primary_ip,
                        vlans=[],
                        collection_success=False,
                        collection_timestamp=datetime.now(),
                        error_details=str(e)
                    )
                    
                    results.append(result)
        
        self.logger.info(f"Concurrent VLAN collection completed for {len(results)} devices")
        return results
    
    def _collect_single_device_safe(self, connection: Any, device_info: DeviceInfo) -> List[VLANInfo]:
        """
        Safe wrapper for single device collection (for concurrent execution)
        
        Args:
            connection: Active device connection
            device_info: Device information
            
        Returns:
            List of VLANInfo objects
        """
        try:
            return self.collect_vlan_information(connection, device_info)
        except Exception as e:
            self.logger.error(f"Safe collection wrapper caught exception for {device_info.hostname}: {e}")
            self._handle_collection_error(device_info, str(e))
            return []
    
    def _is_vlan_collection_enabled(self) -> bool:
        """Check if VLAN collection is enabled in configuration"""
        return self.vlan_config.enabled
    
    def _should_collect_vlans_for_device(self, device_info: DeviceInfo) -> bool:
        """
        Determine if VLAN collection should be performed for a device
        
        Args:
            device_info: Device information
            
        Returns:
            True if VLAN collection should be performed, False otherwise
        """
        # Check if platform is in skip list
        if device_info.platform in self.vlan_config.platforms_to_skip:
            self._log_unsupported_device(device_info, f"Platform {device_info.platform} is in skip list")
            return False
        
        # Check if platform supports VLAN collection
        if not self.platform_handler.validate_platform_support(device_info.platform):
            self._log_unsupported_device(device_info, f"Platform {device_info.platform} is not supported for VLAN collection")
            return False
        
        # Check device capabilities (skip if it's clearly not a switch/router)
        if device_info.capabilities:
            unsupported_capabilities = ['phone', 'camera', 'printer', 'server', 'host']
            device_caps_lower = [cap.lower() for cap in device_info.capabilities]
            
            for unsupported in unsupported_capabilities:
                if unsupported in device_caps_lower:
                    self._log_unsupported_device(device_info, f"Device has unsupported capability: {unsupported}")
                    return False
        
        return True
    
    def _validate_and_process_vlans(self, vlans: List[VLANInfo], device_info: DeviceInfo) -> List[VLANInfo]:
        """
        Validate and process collected VLANs
        
        Args:
            vlans: Raw VLAN list from parser
            device_info: Device information
            
        Returns:
            List of validated VLANs
        """
        if not vlans:
            return []
        
        valid_vlans = []
        
        for vlan in vlans:
            # Sanitize VLAN name
            vlan.vlan_name = self.vlan_parser.sanitize_vlan_name(vlan.vlan_name)
            
            # Validate VLAN data
            if self.vlan_parser.validate_vlan_data(vlan):
                valid_vlans.append(vlan)
            else:
                self.logger.warning(f"Invalid VLAN data for VLAN {vlan.vlan_id} on device {device_info.hostname}")
        
        # Check for duplicates and resolve them
        valid_vlans = self.vlan_parser.detect_duplicate_vlans(valid_vlans)
        
        # Validate consistency and log warnings
        consistency_warnings = self.vlan_parser.validate_vlan_consistency(valid_vlans)
        for warning in consistency_warnings:
            self.logger.warning(warning)
        
        # Check for device-specific inconsistencies
        self._check_vlan_consistency(valid_vlans, device_info)
        
        return valid_vlans
    
    def _check_vlan_consistency(self, vlans: List[VLANInfo], device_info: DeviceInfo) -> None:
        """
        Check for VLAN data inconsistencies and log warnings
        
        Args:
            vlans: List of VLANs to check
            device_info: Device information
        """
        if not vlans:
            return
        
        # Check for unusual VLAN configurations
        high_vlan_count = len(vlans) > 100
        if high_vlan_count:
            self.logger.warning(f"Device {device_info.hostname} has unusually high VLAN count: {len(vlans)}")
        
        # Check for VLANs with very high port counts (might indicate parsing issues)
        for vlan in vlans:
            if vlan.port_count > 50:
                self.logger.warning(
                    f"VLAN {vlan.vlan_id} on device {device_info.hostname} has unusually high port count: {vlan.port_count}"
                )
            
            if vlan.portchannel_count > 20:
                self.logger.warning(
                    f"VLAN {vlan.vlan_id} on device {device_info.hostname} has unusually high PortChannel count: {vlan.portchannel_count}"
                )
    
    def _handle_collection_error(self, device_info: DeviceInfo, error_message: str) -> None:
        """
        Handle VLAN collection errors with appropriate logging
        
        Args:
            device_info: Device information
            error_message: Error message to log
        """
        self.collection_stats['failed_collections'] += 1
        
        # Check for authentication errors and log securely
        error_lower = error_message.lower()
        if any(auth_term in error_lower for auth_term in ['permission', 'privilege', 'authorization', 'authentication', 'login']):
            self._log_authentication_error_securely(device_info, error_message)
        else:
            # Log detailed command failure information
            self._log_command_failure_details(device_info, error_message)
        
        # Log error without exposing sensitive information
        safe_error = self._sanitize_error_message(error_message)
        
        self.logger.error(f"VLAN collection failed for device {device_info.hostname} ({device_info.primary_ip}): {safe_error}")
        
        # Update device info with error details
        device_info.vlan_collection_status = "failed"
        device_info.vlan_collection_error = safe_error
    
    def _sanitize_error_message(self, error_message: str) -> str:
        """
        Sanitize error message to remove potential credential exposure
        
        Args:
            error_message: Raw error message
            
        Returns:
            Sanitized error message
        """
        # Remove potential password/credential information
        sanitized = error_message
        
        # Common patterns to sanitize
        patterns_to_remove = [
            r'password[=:]\s*\S+',
            r'passwd[=:]\s*\S+',
            r'secret[=:]\s*\S+',
            r'key[=:]\s*\S+',
            r'token[=:]\s*\S+'
        ]
        
        import re
        for pattern in patterns_to_remove:
            sanitized = re.sub(pattern, 'password=***', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def get_collection_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for VLAN collection operations
        
        Returns:
            Dictionary containing collection statistics
        """
        summary = {
            'collection_enabled': self.vlan_config.enabled,
            'total_attempts': self.collection_stats['total_attempts'],
            'successful_collections': self.collection_stats['successful_collections'],
            'failed_collections': self.collection_stats['failed_collections'],
            'skipped_collections': self.collection_stats['skipped_collections'],
            'total_vlans_collected': self.collection_stats['total_vlans_collected'],
            'success_rate': 0.0
        }
        
        if summary['total_attempts'] > 0:
            summary['success_rate'] = summary['successful_collections'] / summary['total_attempts'] * 100
        
        return summary
    
    def _log_command_failure_details(self, device_info: DeviceInfo, error_message: str) -> None:
        """
        Log detailed command failure information for troubleshooting
        
        Args:
            device_info: Device information
            error_message: Error message from command execution
        """
        # Log command failure with device context
        self.logger.error(f"VLAN command failure details for {device_info.hostname}:")
        self.logger.error(f"  Device IP: {device_info.primary_ip}")
        self.logger.error(f"  Platform: {device_info.platform}")
        self.logger.error(f"  Connection Method: {device_info.connection_method}")
        self.logger.error(f"  Error: {self._sanitize_error_message(error_message)}")
        
        # Log platform-specific command information
        try:
            commands = self.platform_handler.get_vlan_commands(device_info.platform)
            self.logger.error(f"  Commands attempted: {commands}")
        except Exception as e:
            self.logger.error(f"  Could not determine commands for platform {device_info.platform}: {e}")
        
        # Log configuration context
        self.logger.error(f"  Command timeout: {self.vlan_config.command_timeout}s")
        self.logger.error(f"  Max retries: {self.vlan_config.max_retries}")
        
        # Check for common error patterns and provide guidance
        error_lower = error_message.lower()
        if 'timeout' in error_lower:
            self.logger.warning(f"  Suggestion: Consider increasing command_timeout (current: {self.vlan_config.command_timeout}s)")
        elif 'permission' in error_lower or 'privilege' in error_lower:
            self.logger.warning("  Suggestion: Check device credentials and privilege levels")
        elif 'invalid' in error_lower or 'unrecognized' in error_lower:
            self.logger.warning(f"  Suggestion: Platform {device_info.platform} may not support VLAN commands or needs different commands")
        elif 'connection' in error_lower:
            self.logger.warning("  Suggestion: Check network connectivity and device availability")
    
    def _log_authentication_error_securely(self, device_info: DeviceInfo, error_message: str) -> None:
        """
        Log authentication errors without exposing credentials
        
        Args:
            device_info: Device information
            error_message: Authentication error message
        """
        # Sanitize error message to remove any credential information
        safe_error = self._sanitize_error_message(error_message)
        
        self.logger.error(f"Authentication failed for device {device_info.hostname} ({device_info.primary_ip})")
        self.logger.error(f"  Connection method: {device_info.connection_method}")
        self.logger.error(f"  Platform: {device_info.platform}")
        self.logger.error(f"  Error details: {safe_error}")
        
        # Log guidance without exposing sensitive information
        self.logger.warning("  Suggestion: Verify device credentials and authentication method")
        self.logger.warning("  Note: Check if device requires enable password or different privilege level")
    
    def _log_unsupported_device(self, device_info: DeviceInfo, reason: str) -> None:
        """
        Log when a device is skipped due to being unsupported
        
        Args:
            device_info: Device information
            reason: Reason why device is unsupported
        """
        self.logger.info(f"Skipping VLAN collection for unsupported device {device_info.hostname}")
        self.logger.info(f"  Device IP: {device_info.primary_ip}")
        self.logger.info(f"  Platform: {device_info.platform}")
        self.logger.info(f"  Capabilities: {device_info.capabilities}")
        self.logger.info(f"  Reason: {reason}")
        
        # Update statistics
        self.collection_stats['skipped_collections'] += 1
    
    def log_collection_summary(self) -> None:
        """Log summary statistics for VLAN collection operations"""
        summary = self.get_collection_summary()
        
        self.logger.info("VLAN Collection Summary:")
        self.logger.info(f"  Collection Enabled: {summary['collection_enabled']}")
        self.logger.info(f"  Total Attempts: {summary['total_attempts']}")
        self.logger.info(f"  Successful Collections: {summary['successful_collections']}")
        self.logger.info(f"  Failed Collections: {summary['failed_collections']}")
        self.logger.info(f"  Skipped Collections: {summary['skipped_collections']}")
        self.logger.info(f"  Total VLANs Collected: {summary['total_vlans_collected']}")
        self.logger.info(f"  Success Rate: {summary['success_rate']:.1f}%")
        
        # Log additional insights
        if summary['total_attempts'] > 0:
            avg_vlans_per_device = summary['total_vlans_collected'] / summary['successful_collections'] if summary['successful_collections'] > 0 else 0
            self.logger.info(f"  Average VLANs per successful device: {avg_vlans_per_device:.1f}")
        
        # Log warnings for poor performance
        if summary['success_rate'] < 50 and summary['total_attempts'] > 5:
            self.logger.warning("  Low VLAN collection success rate detected - check device connectivity and credentials")
        
        if summary['skipped_collections'] > summary['successful_collections'] and summary['total_attempts'] > 5:
            self.logger.warning("  High number of skipped collections - check platform support and configuration")