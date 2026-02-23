"""
Discovery Engine for NetWalker

Implements breadth-first network topology discovery with depth limits and error isolation.
"""

import logging
from typing import Dict, List, Set, Optional, Tuple, Any
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime
import time

from ..connection.connection_manager import ConnectionManager
from ..connection.data_models import ConnectionStatus
from ..filtering.filter_manager import FilterManager
from .protocol_parser import ProtocolParser
from .device_collector import DeviceCollector

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryNode:
    """Represents a device in the discovery queue"""
    hostname: str
    ip_address: str
    depth: int
    parent_device: Optional[str] = None
    discovery_method: str = "seed"  # seed, cdp, lldp
    is_seed: bool = False
    platform: Optional[str] = None  # Platform from CDP/LLDP discovery (e.g., "Palo Alto Networks PA-5200")
    
    def __post_init__(self):
        """Ensure hostname is limited to 36 characters"""
        if len(self.hostname) > 36:
            self.hostname = self.hostname[:36]
    
    @property
    def device_key(self) -> str:
        """Unique device identifier"""
        return f"{self.hostname}:{self.ip_address}"


@dataclass
class DiscoveryResult:
    """Results from device discovery operation"""
    hostname: str
    ip_address: str
    device_info: Dict[str, Any]
    neighbors: List[Dict[str, Any]]
    success: bool
    error_message: Optional[str] = None
    connection_method: Optional[str] = None
    discovery_timestamp: datetime = field(default_factory=datetime.now)


class DeviceInventory:
    """
    Thread-safe storage for discovered device information and status.
    """
    
    def __init__(self):
        """Initialize empty inventory"""
        self._devices: Dict[str, Dict[str, Any]] = {}
        self._device_status: Dict[str, str] = {}
        self._device_errors: Dict[str, str] = {}
        self._discovery_stats = {
            'total_discovered': 0,
            'successful_connections': 0,
            'failed_connections': 0,
            'filtered_devices': 0,
            'boundary_devices': 0
        }
        
        # Thread safety would be added here with threading.Lock() if needed
        # For now, assuming single-threaded operation
    
    def add_device(self, device_key: str, device_info: Dict[str, Any], 
                   status: str = "discovered", error: Optional[str] = None):
        """
        Add or update device information in inventory.
        
        Args:
            device_key: Unique device identifier (hostname:ip)
            device_info: Complete device information dictionary
            status: Device status (discovered, connected, failed, filtered, boundary)
            error: Error message if status is failed
        """
        logger.info(f"[INVENTORY ADD] Adding device {device_key} with status '{status}' to inventory")
        logger.info(f"  Current inventory size: {len(self._devices)} devices")
        
        self._devices[device_key] = device_info
        self._device_status[device_key] = status
        
        if error:
            self._device_errors[device_key] = error
        
        # Update statistics
        if status == "connected":
            self._discovery_stats['successful_connections'] += 1
        elif status == "failed":
            self._discovery_stats['failed_connections'] += 1
        elif status == "filtered":
            self._discovery_stats['filtered_devices'] += 1
        elif status == "boundary":
            self._discovery_stats['boundary_devices'] += 1
        
        self._discovery_stats['total_discovered'] = len(self._devices)
        
        logger.info(f"[INVENTORY UPDATED] Device {device_key} added successfully. New inventory size: {len(self._devices)}")
        logger.debug(f"Added device {device_key} with status {status}")
    
    def get_device(self, device_key: str) -> Optional[Dict[str, Any]]:
        """Get device information by key"""
        return self._devices.get(device_key)
    
    def get_device_status(self, device_key: str) -> Optional[str]:
        """Get device status by key"""
        return self._device_status.get(device_key)
    
    def get_device_error(self, device_key: str) -> Optional[str]:
        """Get device error by key"""
        return self._device_errors.get(device_key)
    
    def has_device(self, device_key: str) -> bool:
        """Check if device exists in inventory"""
        return device_key in self._devices
    
    def get_all_devices(self) -> Dict[str, Dict[str, Any]]:
        """Get all devices in inventory"""
        return self._devices.copy()
    
    def get_devices_by_status(self, status: str) -> Dict[str, Dict[str, Any]]:
        """Get all devices with specific status"""
        return {
            key: device for key, device in self._devices.items()
            if self._device_status.get(key) == status
        }
    
    def get_discovery_stats(self) -> Dict[str, int]:
        """Get discovery statistics"""
        return self._discovery_stats.copy()


class DiscoveryEngine:
    """
    Core discovery engine implementing breadth-first network topology discovery.
    
    Features:
    - Breadth-first traversal with configurable depth limits
    - Error isolation and continuation
    - Device filtering and boundary management
    - Comprehensive status tracking and reporting
    - Dynamic timeout reset for large network discovery
    """
    
    def __init__(self, connection_manager: ConnectionManager, 
                 filter_manager: FilterManager, config: Dict[str, Any], credentials,
                 db_manager=None):
        """
        Initialize DiscoveryEngine.
        
        Args:
            connection_manager: Connection manager for device access
            filter_manager: Filter manager for boundary enforcement
            config: Configuration dictionary
            credentials: Device authentication credentials
            db_manager: Optional database manager for inventory persistence
        """
        self.logger = logging.getLogger(__name__)
        self.connection_manager = connection_manager
        self.filter_manager = filter_manager
        self.config = config
        self.credentials = credentials
        self.db_manager = db_manager
        
        # Discovery configuration
        self.max_depth = config.get('max_discovery_depth', 1)
        self.discovery_timeout = config.get('discovery_timeout_seconds', 300)
        self.initial_discovery_timeout = self.discovery_timeout  # Store original timeout
        
        # Initialize components
        self.protocol_parser = ProtocolParser()
        self.device_collector = DeviceCollector(config)
        self.inventory = DeviceInventory()
        
        # Site collection integration
        # Get site boundary pattern - handle multiple config formats for compatibility
        self.site_boundary_pattern = None
        
        # First, try to get from nested output config (new format from config manager)
        if 'output' in config and isinstance(config['output'], dict):
            self.site_boundary_pattern = config['output'].get('site_boundary_pattern')
        # Then try flat config format (backward compatibility)
        elif 'site_boundary_pattern' in config:
            self.site_boundary_pattern = config.get('site_boundary_pattern')
        
        # Apply default pattern if no pattern was found (backward compatibility)
        # The configuration manager handles blank detection and returns None for blank patterns
        if self.site_boundary_pattern is None:
            # Check if pattern was explicitly provided as None (disabled) vs missing
            if ('output' in config and 'site_boundary_pattern' in config['output']) or 'site_boundary_pattern' in config:
                # Pattern was explicitly provided as None - keep as None (disabled)
                logger.info("Site boundary pattern explicitly disabled (None value)")
            else:
                # Pattern was missing - apply default for backward compatibility
                self.site_boundary_pattern = '*-CORE-*'
                logger.info("Site boundary pattern missing from configuration, applying default: *-CORE-*")
        elif isinstance(self.site_boundary_pattern, str):
            # Process string patterns through ConfigurationBlankHandler for blank detection with Unicode support
            from ..config.blank_detection import ConfigurationBlankHandler
            processed_pattern = ConfigurationBlankHandler.process_site_boundary_pattern_with_unicode(
                self.site_boundary_pattern,
                default_pattern="*-CORE-*",
                logger=logger
            )
            self.site_boundary_pattern = processed_pattern
        
        # Determine if site collection should be enabled
        # Site collection is enabled only if:
        # 1. enable_site_collection is True (default is False - must be explicitly enabled)
        # 2. site_boundary_pattern is not None (not disabled by blank pattern)
        base_site_collection_enabled = config.get('enable_site_collection', False)
        pattern_allows_site_collection = self.site_boundary_pattern is not None
        
        self.site_collection_enabled = base_site_collection_enabled and pattern_allows_site_collection
        
        if self.site_collection_enabled:
            from .site_specific_collection_manager import SiteSpecificCollectionManager
            self.site_collection_manager = SiteSpecificCollectionManager(
                connection_manager, self.device_collector, config, credentials, self.site_boundary_pattern
            )
            logger.info(f"Site collection enabled with pattern: {self.site_boundary_pattern}")
        else:
            self.site_collection_manager = None
            if not pattern_allows_site_collection:
                logger.info("Site collection disabled due to blank site boundary pattern - using global collection mode")
            else:
                logger.info("Site collection disabled by configuration - using global collection mode")
        
        # Site collection state
        self.site_boundaries: Dict[str, List[str]] = {}
        self.site_collection_results: Dict[str, Dict[str, Any]] = {}
        
        # Discovery state
        self.discovery_queue: deque[DiscoveryNode] = deque()
        self.discovered_devices: Set[str] = set()
        self.failed_devices: Set[str] = set()
        
        # Progress tracking
        self.total_devices_discovered = 0
        self.devices_processed = 0
        self.new_devices_discovered = 0  # Track newly discovered devices
        self.progress_enabled = config.get('enable_progress_tracking', True)
        
        # Queue progress tracking
        self.total_queued = 0  # Total devices added to queue (after dedupe)
        self.total_completed = 0  # Total devices completed (removed from queue)
        
        # Timeout management for large networks
        self.discovery_start_time: Optional[float] = None
        self.timeout_resets: int = 0
        self.devices_added_since_reset: int = 0
        
        logger.info(f"DiscoveryEngine initialized with max_depth={self.max_depth}, "
                   f"timeout={self.discovery_timeout}s")
    
    def add_seed_device(self, hostname: str, ip_address: str):
        """
        Add a seed device to start discovery.
        
        Args:
            hostname: Device hostname
            ip_address: Device IP address
        """
        seed_node = DiscoveryNode(
            hostname=hostname,
            ip_address=ip_address,
            depth=0,
            discovery_method="seed",
            is_seed=True
        )
        
        self.discovery_queue.append(seed_node)
        self.total_devices_discovered += 1
        self.total_queued += 1  # Increment total queued
        logger.info(f"Added seed device: {seed_node.device_key}")
        self._update_progress_display()
    
    def discover_topology(self) -> Dict[str, Any]:
        """
        Execute breadth-first topology discovery.
        
        Returns:
            Discovery results summary
        """
        self.discovery_start_time = time.time()
        logger.info("Starting network topology discovery")
        
        try:
            logger.info(f"[DISCOVERY LOOP] Starting discovery with {len(self.discovery_queue)} devices in queue")
            
            while self.discovery_queue:
                current_time = time.time()
                elapsed_time = current_time - self.discovery_start_time
                
                # Check if we've exceeded the discovery timeout
                if elapsed_time >= self.discovery_timeout:
                    logger.warning(f"Discovery timeout reached after {elapsed_time:.2f}s (limit: {self.discovery_timeout}s)")
                    logger.info(f"Timeout resets performed: {self.timeout_resets}")
                    break
                
                current_node = self.discovery_queue.popleft()
                
                logger.info(f"[QUEUE] Processing device {current_node.device_key} from queue (depth {current_node.depth})")
                logger.info(f"  Queue remaining: {len(self.discovery_queue)} devices")
                logger.info(f"  Elapsed time: {elapsed_time:.2f}s / {self.discovery_timeout}s")
                
                # Skip if already discovered
                if current_node.device_key in self.discovered_devices:
                    logger.info(f"  [SKIPPED] {current_node.device_key} already discovered")
                    continue
                
                # Check depth limit
                if current_node.depth > self.max_depth:
                    logger.info(f"  [DEPTH LIMIT] Skipping {current_node.device_key} - depth {current_node.depth} exceeds max_depth {self.max_depth}")
                    continue
                
                # Discover device
                self._discover_device(current_node)
                
                # Update completed count after device is processed
                self.total_completed += 1
                
                # Monitor connection status periodically
                if self.devices_processed % 10 == 0:  # Every 10 devices
                    active_connections = self.connection_manager.get_active_connection_count()
                    if active_connections > 0:
                        logger.warning(f"[CONNECTION LEAK] {active_connections} connections still active after device processing")
                        self.connection_manager.log_connection_status()
                        
                        # If we have too many leaked connections, try to clean them up
                        if active_connections > 5:
                            logger.error(f"[CONNECTION LEAK CRITICAL] {active_connections} leaked connections detected - attempting cleanup")
                            try:
                                self.connection_manager.close_all_connections()
                                remaining = self.connection_manager.get_active_connection_count()
                                if remaining > 0:
                                    logger.error(f"[CONNECTION LEAK CLEANUP] {remaining} connections still remain after cleanup attempt")
                                else:
                                    logger.info("[CONNECTION LEAK CLEANUP] All leaked connections successfully cleaned up")
                            except Exception as cleanup_error:
                                logger.error(f"[CONNECTION LEAK CLEANUP] Cleanup failed: {cleanup_error}")
                
                # Update progress after processing device
                self.devices_processed += 1
                self._update_progress_display()
            
            # Handle completion
            if not self.discovery_queue:
                logger.info(f"[DISCOVERY COMPLETE] Queue empty - all devices processed")
            
            # After main discovery, perform site-specific collection if enabled
            if self.site_collection_enabled and self.site_collection_manager and self.site_boundary_pattern is not None:
                logger.info("[SITE COLLECTION] Starting site-specific device collection")
                self._perform_site_collection()
            else:
                if self.site_boundary_pattern is None:
                    logger.info("[SITE COLLECTION] Skipping site collection - disabled due to blank site boundary pattern")
                elif not self.site_collection_enabled:
                    logger.info("[SITE COLLECTION] Skipping site collection - disabled by configuration")
                else:
                    logger.info("[SITE COLLECTION] Skipping site collection - site collection manager not initialized")
            
        except Exception as e:
            logger.error(f"Discovery engine error: {e}")
            raise
        
        discovery_time = time.time() - self.discovery_start_time
        
        # Final connection status check and cleanup
        active_connections = self.connection_manager.get_active_connection_count()
        if active_connections > 0:
            logger.error(f"[CONNECTION LEAK] {active_connections} connections still active after discovery completion!")
            self.connection_manager.log_connection_status()
            
            # Force cleanup any remaining connections
            logger.warning("[CONNECTION CLEANUP] Forcing cleanup of remaining connections")
            try:
                self.connection_manager.close_all_connections()
                final_count = self.connection_manager.get_active_connection_count()
                if final_count > 0:
                    logger.error(f"[CONNECTION CLEANUP FAILED] {final_count} connections still remain after force cleanup")
                    # Last resort - force cleanup
                    self.connection_manager.force_cleanup_connections()
                else:
                    logger.info("[CONNECTION CLEANUP] All remaining connections successfully cleaned up")
            except Exception as cleanup_error:
                logger.error(f"[CONNECTION CLEANUP ERROR] Force cleanup failed: {cleanup_error}")
        else:
            logger.info("[CONNECTION STATUS] All connections properly closed during discovery")
        
        results = self._generate_discovery_summary(discovery_time)
        
        logger.info(f"Discovery completed in {discovery_time:.2f}s - "
                   f"Found {results['total_devices']} devices "
                   f"({results['new_devices']} new), "
                   f"Timeout resets: {self.timeout_resets}")
        
        return results
    
    def _discover_device(self, node: DiscoveryNode):
        """
        Discover a single device and add neighbors to queue.
        
        Args:
            node: Discovery node to process
        """
        device_key = node.device_key
        logger.info(f"[DISCOVERY DECISION] Processing device {device_key} at depth {node.depth}")
        logger.info(f"  Device details: hostname='{node.hostname}', ip='{node.ip_address}', parent='{node.parent_device}'")
        logger.info(f"  Discovery state: discovered_devices={len(self.discovered_devices)}, queue_size={len(self.discovery_queue)}")
        
        # Special debugging for LUMT-CORE-A and similar NEXUS devices
        if 'LUMT' in node.hostname.upper() or 'CORE' in node.hostname.upper():
            self._debug_nexus_device_processing(node)
        
        try:
            # Check if already in discovered set (this should not happen if queue logic is correct)
            if device_key in self.discovered_devices:
                logger.warning(f"  [ALREADY DISCOVERED] Device {device_key} is already in discovered_devices set - this should not happen!")
                logger.warning(f"    Discovered devices: {list(self.discovered_devices)}")
                return
            
            # Mark as discovered to prevent loops
            self.discovered_devices.add(device_key)
            logger.info(f"  [MARKED DISCOVERED] Added {device_key} to discovered_devices set")
            
            # Check if device should be filtered
            logger.info(f"  [CHECKING] if device {device_key} should be filtered...")
            # For initial device discovery, we only have hostname and IP
            # Platform and capabilities will be checked during neighbor processing
            if self.filter_manager.should_filter_device(node.hostname, node.ip_address):
                logger.info(f"  [FILTERED] Device {device_key} will be marked as boundary (not discovered)")
                self.filter_manager.mark_as_boundary(node.hostname, node.ip_address, "Filtered device")
                
                # Add to inventory as filtered with skip reason
                device_info = self._create_basic_device_info(node, "filtered")
                device_info['skip_reason'] = "Filtered by hostname or IP address pattern"
                self.inventory.add_device(device_key, device_info, "filtered")
                logger.info(f"  [INVENTORY] Added {device_key} to inventory as FILTERED")
                return
            
            logger.info(f"  [NOT FILTERED] Device {device_key} passed initial filtering - proceeding with connection")
            
            # Check connection failure threshold if database is enabled
            connection_config = self.config.get('connection', {})
            skip_after_failures = getattr(connection_config, 'skip_after_failures', 3) if hasattr(connection_config, 'skip_after_failures') else connection_config.get('skip_after_failures', 3)
            
            if self.db_manager and self.db_manager.enabled and skip_after_failures > 0:
                failure_count = self.db_manager.get_connection_failures(node.hostname)
                if failure_count >= skip_after_failures:
                    logger.warning(f"  [SKIPPED] Device {device_key} has {failure_count} connection failures (threshold: {skip_after_failures})")
                    
                    # Add to inventory as skipped with failure reason
                    device_info = self._create_basic_device_info(node, "skipped")
                    device_info['skip_reason'] = f"Exceeded connection failure threshold ({failure_count} failures, limit: {skip_after_failures})"
                    self.inventory.add_device(device_key, device_info, "skipped")
                    logger.info(f"  [INVENTORY] Added {device_key} to inventory as SKIPPED (too many failures)")
                    return
            
            # Attempt connection and discovery
            logger.info(f"  [CONNECTING] Attempting connection to {device_key}")
            discovery_result = self._connect_and_discover(node)
            
            if discovery_result.success:
                logger.info(f"  [SUCCESS] Connected to {device_key} - adding to inventory and processing neighbors")
                
                # Now we have platform and capabilities, do a full filter check
                device_platform = discovery_result.device_info.get('platform')
                device_capabilities = discovery_result.device_info.get('capabilities', [])
                
                logger.info(f"  [FULL FILTER CHECK] Re-evaluating {device_key} with complete device info")
                logger.info(f"    Platform: {device_platform}, Capabilities: {device_capabilities}")
                
                if self.filter_manager.should_filter_device(
                    node.hostname, node.ip_address, device_platform, device_capabilities
                ):
                    logger.info(f"  [FILTERED AFTER CONNECTION] Device {device_key} filtered based on platform/capabilities")
                    self.filter_manager.mark_as_boundary(
                        node.hostname, node.ip_address, 
                        f"Filtered after connection - platform: {device_platform}, capabilities: {device_capabilities}"
                    )
                    
                    # Add to inventory as filtered with skip reason
                    device_info = self._create_basic_device_info(node, "filtered")
                    device_info.update({
                        'platform': device_platform,
                        'capabilities': device_capabilities,
                        'filter_reason': 'Filtered after connection based on platform/capabilities',
                        'skip_reason': f"Filtered by platform ({device_platform}) or capabilities ({', '.join(device_capabilities) if device_capabilities else 'none'})"
                    })
                    self.inventory.add_device(device_key, device_info, "filtered")
                    logger.info(f"  [INVENTORY] Added {device_key} to inventory as FILTERED (post-connection)")
                    return
                
                logger.info(f"  [PASSED FULL FILTER] Device {device_key} passed complete filtering - adding to inventory")
                
                # Reset connection failures on successful connection
                if self.db_manager and self.db_manager.enabled:
                    self.db_manager.reset_connection_failures(node.hostname)
                    logger.debug(f"  [CONNECTION SUCCESS] Reset failure count for {device_key}")
                
                # Add device to inventory
                self.inventory.add_device(
                    device_key, 
                    discovery_result.device_info, 
                    "connected"
                )
                logger.info(f"  [INVENTORY] Added {device_key} to inventory as CONNECTED")
                
                # Process device discovery in database if enabled
                if self.db_manager and self.db_manager.enabled:
                    logger.info(f"  [DATABASE] Processing device {device_key} for database storage")
                    try:
                        success, is_new_device = self.db_manager.process_device_discovery(discovery_result.device_info)
                        if success:
                            logger.info(f"  [DATABASE] Successfully stored {device_key} in database")
                            if is_new_device:
                                self.new_devices_discovered += 1
                                logger.info(f"  [DATABASE] New device discovered: {device_key}")
                        else:
                            logger.warning(f"  [DATABASE] Failed to store {device_key} in database")
                    except Exception as db_error:
                        logger.error(f"  [DATABASE] Error storing {device_key}: {db_error}")
                
                # Process neighbors for further discovery
                logger.info(f"  [PROCESSING NEIGHBORS] Evaluating neighbors of {device_key}")
                
                # Special debugging for NEXUS devices
                if 'LUMT' in node.hostname.upper() or 'CORE' in node.hostname.upper():
                    self._debug_nexus_neighbor_processing(node, discovery_result.neighbors)
                
                self._process_neighbors(discovery_result.neighbors, node)
                
            else:
                # Record failed device
                logger.info(f"  [CONNECTION FAILED] Could not connect to {device_key} - {discovery_result.error_message}")
                self.failed_devices.add(device_key)
                
                # Increment connection failures in database
                if self.db_manager and self.db_manager.enabled:
                    self.db_manager.increment_connection_failures(node.hostname)
                    new_count = self.db_manager.get_connection_failures(node.hostname)
                    logger.warning(f"  [CONNECTION FAILURE] Incremented failure count for {device_key} to {new_count}")
                
                # Add to inventory as failed
                device_info = self._create_basic_device_info(node, "failed")
                device_info['error_message'] = discovery_result.error_message
                self.inventory.add_device(device_key, device_info, "failed", discovery_result.error_message)
                logger.info(f"  [INVENTORY] Added {device_key} to inventory as FAILED")
                
                logger.warning(f"Failed to discover {device_key}: {discovery_result.error_message}")
        
        except Exception as e:
            logger.error(f"Error discovering device {device_key}: {e}")
            self.failed_devices.add(device_key)
            
            # Add error device to inventory
            device_info = self._create_basic_device_info(node, "error")
            device_info['error_message'] = str(e)
            self.inventory.add_device(device_key, device_info, "failed", str(e))
    
    def _debug_nexus_device_processing(self, node: DiscoveryNode):
        """
        Special debugging for NEXUS devices like LUMT-CORE-A
        
        Args:
            node: Discovery node for NEXUS device
        """
        logger.info(f"[NEXUS DEBUG] Processing NEXUS device: {node.device_key}")
        logger.info(f"  [NEXUS DEBUG] Hostname: '{node.hostname}'")
        logger.info(f"  [NEXUS DEBUG] IP Address: '{node.ip_address}'")
        logger.info(f"  [NEXUS DEBUG] Depth: {node.depth}")
        logger.info(f"  [NEXUS DEBUG] Parent: '{node.parent_device}'")
        logger.info(f"  [NEXUS DEBUG] Discovery method: '{node.discovery_method}'")
        
        # Check current filter configuration
        filter_criteria = self.filter_manager.criteria
        logger.info(f"  [NEXUS DEBUG] Current filter criteria:")
        logger.info(f"    Hostname excludes: {filter_criteria.hostname_excludes}")
        logger.info(f"    IP excludes: {filter_criteria.ip_excludes}")
        logger.info(f"    Platform excludes: {filter_criteria.platform_excludes}")
        logger.info(f"    Capability excludes: {filter_criteria.capability_excludes}")
    
    def _debug_nexus_neighbor_processing(self, node: DiscoveryNode, neighbors: List[Any]):
        """
        Special debugging for NEXUS neighbor processing
        
        Args:
            node: Parent NEXUS device node
            neighbors: List of discovered neighbors
        """
        logger.info(f"[NEXUS NEIGHBOR DEBUG] Processing {len(neighbors)} neighbors for {node.device_key}")
        
        for i, neighbor in enumerate(neighbors):
            if hasattr(neighbor, 'device_id'):
                neighbor_id = getattr(neighbor, 'device_id', 'Unknown')
                neighbor_ip = getattr(neighbor, 'ip_address', 'Unknown')
                neighbor_platform = getattr(neighbor, 'platform', 'Unknown')
                neighbor_capabilities = getattr(neighbor, 'capabilities', [])
                protocol = getattr(neighbor, 'protocol', 'Unknown')
            else:
                neighbor_id = neighbor.get('hostname', 'Unknown')
                neighbor_ip = neighbor.get('ip_address', 'Unknown')
                neighbor_platform = neighbor.get('platform', 'Unknown')
                neighbor_capabilities = neighbor.get('capabilities', [])
                protocol = neighbor.get('protocol', 'Unknown')
            
            logger.info(f"  [NEXUS NEIGHBOR DEBUG] Neighbor {i+1}: {neighbor_id}")
            logger.info(f"    IP: {neighbor_ip}")
            logger.info(f"    Platform: {neighbor_platform}")
            logger.info(f"    Capabilities: {neighbor_capabilities}")
            logger.info(f"    Protocol: {protocol}")
            
            # Check if this neighbor would be filtered
            would_filter = self.filter_manager.should_filter_device(
                neighbor_id, neighbor_ip, neighbor_platform, neighbor_capabilities
            )
            logger.info(f"    Would be filtered: {would_filter}")
            
            if would_filter:
                logger.warning(f"    [NEXUS NEIGHBOR DEBUG] Neighbor {neighbor_id} will be filtered!")
            else:
                logger.info(f"    [NEXUS NEIGHBOR DEBUG] Neighbor {neighbor_id} will be queued for discovery")
    
    def _connect_and_discover(self, node: DiscoveryNode) -> DiscoveryResult:
        """
        Connect to device and collect information.
        
        Args:
            node: Discovery node
            
        Returns:
            Discovery result
        """
        try:
            # Establish connection
            # Use IP address for connection (DNS may not resolve hostnames)
            # Pass platform from CDP/LLDP for reliable PAN-OS detection
            # Use IP address if available, otherwise fall back to hostname
            connection_target = node.ip_address if node.ip_address else node.hostname
            connection, connection_result = self.connection_manager.connect_device(
                connection_target, self.credentials, self.db_manager, node.platform
            )
            
            if connection_result.status != ConnectionStatus.SUCCESS:
                return DiscoveryResult(
                    hostname=node.hostname,
                    ip_address=node.ip_address,
                    device_info={},
                    neighbors=[],
                    success=False,
                    error_message=f"Connection failed: {connection_result.error_message or 'Unknown error'}"
                )
            
            # Collect device information
            device_info = self.device_collector.collect_device_information(
                connection, node.ip_address, connection_result.method.value, 
                node.depth, node.is_seed
            )
            
            if not device_info:
                self.logger.error(f"Failed to collect device information for {node.hostname}")
                return DiscoveryResult(
                    hostname=node.hostname,
                    ip_address=node.ip_address,
                    device_info={},
                    neighbors=[],
                    success=False,
                    error_message="Failed to collect device information"
                )
            
            # Convert DeviceInfo object to dictionary for compatibility
            device_info_dict = {
                'hostname': device_info.hostname,
                'primary_ip': device_info.primary_ip,
                'platform': device_info.platform,
                'capabilities': device_info.capabilities,
                'software_version': device_info.software_version,
                'vtp_version': device_info.vtp_version,
                'serial_number': device_info.serial_number,
                'hardware_model': device_info.hardware_model,
                'uptime': device_info.uptime,
                'discovery_depth': device_info.discovery_depth,
                'discovery_method': node.discovery_method,
                'parent_device': node.parent_device,
                'discovery_timestamp': device_info.discovery_timestamp.isoformat(),
                'connection_method': device_info.connection_method,
                'connection_status': device_info.connection_status,
                'error_details': device_info.error_details,
                'neighbors': device_info.neighbors,  # Store the NeighborInfo objects directly
                'vlans': device_info.vlans,  # Store the VLANInfo objects directly
                'vlan_collection_status': device_info.vlan_collection_status,
                'vlan_collection_error': device_info.vlan_collection_error,
                'stack_members': device_info.stack_members,  # Store the StackMemberInfo objects
                'is_stack': device_info.is_stack,  # Stack flag
                'is_physical_device': device_info.is_physical_device,  # Physical device flag (from cloud-mode)
                'ha_role': device_info.ha_role  # HA role for PAN-OS (Active/Passive/None)
            }
            
            # Get neighbors from DeviceInfo object
            neighbors = device_info.neighbors
            
            # Close connection using the same key that was used to create it
            # CRITICAL: Always close connection immediately after use to prevent leaks
            # IMPORTANT: Use the same connection_target that was used to open the connection
            try:
                connection_closed = self.connection_manager.close_connection(connection_target)
                if not connection_closed:
                    self.logger.warning(f"Failed to close connection to {node.hostname} ({connection_target}) - may cause connection leak")
                else:
                    self.logger.debug(f"Connection to {node.hostname} ({connection_target}) closed successfully")
            except Exception as close_error:
                self.logger.error(f"Error closing connection to {node.hostname} ({connection_target}): {close_error}")
            
            return DiscoveryResult(
                hostname=node.hostname,
                ip_address=node.ip_address,
                device_info=device_info_dict,
                neighbors=neighbors,
                success=True,
                error_message=None
            )
            
        except Exception as e:
            self.logger.error(f"Discovery failed for {node.hostname}: {str(e)}")
            return DiscoveryResult(
                hostname=node.hostname,
                ip_address=node.ip_address,
                device_info={},
                neighbors=[],
                success=False,
                error_message=str(e)
            )
    
    def _process_neighbors(self, neighbors: List[Any], parent_node: DiscoveryNode):
        """
        Process discovered neighbors and add to discovery queue.
        
        Args:
            neighbors: List of neighbor information (NeighborInfo objects or dictionaries)
            parent_node: Parent device node
        """
        new_devices_added = 0
        
        for neighbor in neighbors:
            # Handle both NeighborInfo objects and dictionaries
            if hasattr(neighbor, 'device_id'):
                # NeighborInfo object
                neighbor_hostname = getattr(neighbor, 'device_id', '').strip()
                neighbor_ip = getattr(neighbor, 'ip_address', None)
                protocol = getattr(neighbor, 'protocol', 'unknown').lower()
                neighbor_platform = getattr(neighbor, 'platform', None)
                neighbor_capabilities = getattr(neighbor, 'capabilities', [])
                
                # Clean up hostname (remove FQDN domain part)
                if '.' in neighbor_hostname:
                    neighbor_hostname = neighbor_hostname.split('.')[0]
                
                # If no IP address available, try DNS resolution
                if not neighbor_ip:
                    logger.info(f"    [DNS RESOLUTION] Neighbor {neighbor_hostname} has no IP address, attempting DNS lookup")
                    try:
                        import socket
                        resolved_ip = socket.gethostbyname(neighbor_hostname)
                        neighbor_ip = resolved_ip
                        logger.info(f"    [DNS SUCCESS] Resolved {neighbor_hostname} to {resolved_ip}")
                    except (socket.gaierror, socket.herror, OSError) as e:
                        logger.warning(f"    [DNS FAILED] Could not resolve {neighbor_hostname}: {e}")
                        logger.debug(f"Skipping neighbor {neighbor_hostname} - no IP address available and DNS resolution failed")
                        continue
                    
                neighbor_ip = neighbor_ip.strip()
            else:
                # Dictionary format (fallback)
                neighbor_hostname = neighbor.get('hostname', '').strip()
                neighbor_ip = neighbor.get('ip_address', '').strip()
                protocol = neighbor.get('protocol', 'unknown').lower()
                neighbor_platform = neighbor.get('platform', None)
                neighbor_capabilities = neighbor.get('capabilities', [])
            
            if not neighbor_hostname or not neighbor_ip:
                logger.debug(f"Skipping neighbor with missing hostname or IP: {neighbor}")
                continue
            
            # Check if neighbor should be filtered based on platform/capabilities
            logger.info(f"    [NEIGHBOR DECISION] Evaluating neighbor {neighbor_hostname}:{neighbor_ip}")
            logger.info(f"      Neighbor details: platform='{neighbor_platform}', capabilities={neighbor_capabilities}")
            
            if self.filter_manager.should_filter_device(
                neighbor_hostname, neighbor_ip, neighbor_platform, neighbor_capabilities
            ):
                logger.info(f"    [NEIGHBOR FILTERED] {neighbor_hostname}:{neighbor_ip} will not be added to discovery queue")
                logger.info(f"      Reason: platform='{neighbor_platform}', capabilities={neighbor_capabilities}")
                self.filter_manager.mark_as_boundary(
                    neighbor_hostname, neighbor_ip, 
                    f"Filtered by platform ({neighbor_platform}) or capabilities ({neighbor_capabilities})"
                )
                
                # Add to inventory as filtered with skip reason
                device_info = self._create_basic_device_info_for_neighbor(
                    neighbor_hostname, neighbor_ip, parent_node.depth + 1, 
                    protocol, parent_node.device_key, "filtered", 
                    neighbor_platform, neighbor_capabilities
                )
                device_info['skip_reason'] = f"Filtered by platform ({neighbor_platform}) or capabilities ({', '.join(neighbor_capabilities) if neighbor_capabilities else 'none'})"
                self.inventory.add_device(f"{neighbor_hostname}:{neighbor_ip}", device_info, "filtered")
                continue
            
            logger.info(f"    [NEIGHBOR PASSED] {neighbor_hostname}:{neighbor_ip} passed filtering checks")
            
            # Create neighbor node with platform from CDP/LLDP
            neighbor_node = DiscoveryNode(
                hostname=neighbor_hostname,
                ip_address=neighbor_ip,
                depth=parent_node.depth + 1,
                parent_device=parent_node.device_key,
                discovery_method=protocol,
                platform=neighbor_platform  # Pass platform from CDP/LLDP for PAN-OS detection
            )
            
            logger.info(f"    [NEIGHBOR CHECK] Checking if {neighbor_node.device_key} should be queued")
            logger.debug(f"      Current discovered_devices: {list(self.discovered_devices)}")
            logger.debug(f"      Current queue devices: {[n.device_key for n in self.discovery_queue]}")
            
            # Skip if already discovered or queued
            if neighbor_node.device_key in self.discovered_devices:
                logger.info(f"    [NEIGHBOR SKIPPED] {neighbor_node.device_key} already in discovered_devices set")
                continue
            
            if any(n.device_key == neighbor_node.device_key for n in self.discovery_queue):
                logger.info(f"    [NEIGHBOR SKIPPED] {neighbor_node.device_key} already in discovery queue")
                continue
            
            # Check depth limit
            if neighbor_node.depth > self.max_depth:
                logger.info(f"    [NEIGHBOR DEPTH LIMIT] {neighbor_node.device_key} at depth {neighbor_node.depth} exceeds max_depth {self.max_depth}")
                # Add to inventory with skip reason
                device_info = self._create_basic_device_info_for_neighbor(
                    neighbor_hostname, neighbor_ip, parent_node.depth + 1, 
                    protocol, parent_node.device_key, "skipped", 
                    neighbor_platform, neighbor_capabilities
                )
                device_info['skip_reason'] = f"Depth limit exceeded (depth {neighbor_node.depth} > max {self.max_depth})"
                self.inventory.add_device(f"{neighbor_hostname}:{neighbor_ip}", device_info, "skipped")
                continue
            
            # Add to discovery queue
            self.discovery_queue.append(neighbor_node)
            new_devices_added += 1
            self.total_devices_discovered += 1
            self.total_queued += 1  # Increment total queued after dedupe
            logger.info(f"    [NEIGHBOR QUEUED] Added {neighbor_node.device_key} to discovery queue (depth {neighbor_node.depth})")
            logger.info(f"      Queue size after addition: {len(self.discovery_queue)}")
            logger.debug(f"Added neighbor {neighbor_node.device_key} to discovery queue "
                        f"(depth {neighbor_node.depth})")
        
        # Reset discovery timeout if new devices were added (for large networks)
        if new_devices_added > 0:
            self._reset_discovery_timeout_if_needed(new_devices_added)
            self._update_progress_display()
    
    def _reset_discovery_timeout_if_needed(self, new_devices_count: int):
        """
        Reset discovery timeout when new devices are added to handle large networks.
        
        Args:
            new_devices_count: Number of new devices added to queue
        """
        if self.discovery_start_time is None:
            return
        
        current_time = time.time()
        elapsed_time = current_time - self.discovery_start_time
        remaining_time = self.discovery_timeout - elapsed_time
        
        # Reset timeout if we're getting close to the limit and have new devices to process
        # This prevents large networks from being cut off prematurely
        if remaining_time < (self.initial_discovery_timeout * 0.2):  # Less than 20% time remaining
            self.timeout_resets += 1
            self.devices_added_since_reset += new_devices_count
            
            # Reset the start time to give us more time for the new devices
            # But don't reset indefinitely - limit to reasonable number of resets
            if self.timeout_resets <= 10:  # Maximum 10 resets to prevent infinite discovery
                self.discovery_start_time = current_time
                logger.info(f"[TIMEOUT RESET] Discovery timeout reset #{self.timeout_resets}")
                logger.info(f"  Reason: {new_devices_count} new devices added, {remaining_time:.1f}s remaining")
                logger.info(f"  Total devices added since last reset: {self.devices_added_since_reset}")
                logger.info(f"  New timeout window: {self.discovery_timeout}s from now")
                
                # Reset the counter for next cycle
                self.devices_added_since_reset = 0
            else:
                logger.warning(f"[TIMEOUT RESET LIMIT] Maximum timeout resets ({10}) reached - no more resets allowed")
                logger.warning(f"  This prevents infinite discovery loops in very large networks")
        else:
            logger.debug(f"[TIMEOUT CHECK] No reset needed - {remaining_time:.1f}s remaining, {new_devices_count} devices added")
    
    def _update_progress_display(self):
        """
        Update and display discovery progress information.
        Shows queue progress: (completed / total) = percent complete
        """
        if not self.progress_enabled:
            return
        
        # Calculate queue progress
        if self.total_queued > 0:
            remaining = self.total_queued - self.total_completed
            percent_complete = (self.total_completed / self.total_queued) * 100
            
            # Create unified queue status message with visual markers
            # Shows: completed of total (percent complete) with remaining in queue
            queue_status = f"****** ({self.total_completed} of {self.total_queued}) {percent_complete:.1f}% complete - {remaining} remaining ******"
            
            # Log to file and console
            logger.info(queue_status)
        else:
            # Initial state - just show queue size
            queue_size = len(self.discovery_queue)
            if queue_size > 0:
                initial_msg = f"****** Discovery starting - {queue_size} devices to process ******"
                logger.info(initial_msg)
    
    def _create_basic_device_info(self, node: DiscoveryNode, status: str) -> Dict[str, Any]:
        """Create basic device info for failed/filtered devices"""
        # Try to get device info from database first (may have been discovered as neighbor)
        db_info = None
        if self.db_manager:
            db_info = self.db_manager.get_device_info_by_host(node.hostname)
            if not db_info and node.ip_address:
                db_info = self.db_manager.get_device_info_by_host(node.ip_address)
        
        # Use database info if available, otherwise use 'unknown' as fallback
        return {
            'hostname': node.hostname,
            'ip_address': node.ip_address,
            'discovery_depth': node.depth,
            'discovery_method': node.discovery_method,
            'parent_device': node.parent_device,
            'discovery_timestamp': datetime.now().isoformat(),
            'status': status,
            'platform': db_info['platform'] if db_info else 'unknown',
            'software_version': db_info['software_version'] if db_info else 'unknown',
            'serial_number': db_info['serial_number'] if db_info else 'unknown',
            'hardware_model': db_info['hardware_model'] if db_info else 'unknown',
            'uptime': 'unknown',
            'connection_method': 'none'
        }
    
    def _create_basic_device_info_for_neighbor(self, hostname: str, ip_address: str, depth: int, 
                                             discovery_method: str, parent_device: str, status: str,
                                             platform: Optional[str] = None, 
                                             capabilities: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create basic device info for filtered neighbor devices"""
        # Try to get device info from database first (may have been discovered as neighbor)
        db_info = None
        if self.db_manager:
            db_info = self.db_manager.get_device_info_by_host(hostname)
            if not db_info and ip_address:
                db_info = self.db_manager.get_device_info_by_host(ip_address)
        
        # Use database info if available, otherwise use provided/fallback values
        return {
            'hostname': hostname,
            'ip_address': ip_address,
            'discovery_depth': depth,
            'discovery_method': discovery_method,
            'parent_device': parent_device,
            'discovery_timestamp': datetime.now().isoformat(),
            'status': status,
            'platform': db_info['platform'] if db_info else (platform or 'unknown'),
            'capabilities': db_info['capabilities'] if db_info else (capabilities or []),
            'software_version': db_info['software_version'] if db_info else 'unknown',
            'serial_number': db_info['serial_number'] if db_info else 'unknown',
            'hardware_model': db_info['hardware_model'] if db_info else 'unknown',
            'uptime': 'unknown',
            'connection_method': 'none'
        }
    
    def _generate_discovery_summary(self, discovery_time: float) -> Dict[str, Any]:
        """Generate discovery results summary"""
        stats = self.inventory.get_discovery_stats()
        
        # Calculate max depth from inventory devices
        max_depth = 0
        for device_info in self.inventory.get_all_devices().values():
            depth = device_info.get('discovery_depth', 0)
            if isinstance(depth, int):
                max_depth = max(max_depth, depth)
        
        return {
            'discovery_time_seconds': discovery_time,
            'total_devices': stats['total_discovered'],
            'new_devices': self.new_devices_discovered,
            'successful_connections': stats['successful_connections'],
            'failed_connections': stats['failed_connections'],
            'filtered_devices': stats['filtered_devices'],
            'boundary_devices': stats['boundary_devices'],
            'max_depth_reached': max_depth,
            'devices_in_queue': len(self.discovery_queue),
            'timeout_resets': self.timeout_resets,
            'initial_timeout_seconds': self.initial_discovery_timeout,
            'filter_stats': self.filter_manager.get_filter_stats()
        }
    
    def get_inventory(self) -> DeviceInventory:
        """Get the device inventory"""
        return self.inventory
    
    def get_discovered_devices(self) -> Set[str]:
        """Get set of discovered device keys"""
        return self.discovered_devices.copy()
    
    def get_failed_devices(self) -> Set[str]:
        """Get set of failed device keys"""
        return self.failed_devices.copy()
    
    def _perform_site_collection(self):
        """
        Perform site-specific device collection after main discovery.
        
        This method identifies site boundaries from discovered devices and
        performs additional collection within each site to ensure complete
        topology mapping.
        
        Note: This method is only called when site collection is enabled.
        If site boundary pattern is None/blank, site collection is disabled
        and this method will not be called.
        """
        # Double-check that site collection is enabled and we have a valid pattern
        if not self.site_collection_enabled or self.site_boundary_pattern is None:
            logger.info("[SITE COLLECTION] Site collection is disabled - skipping site-specific collection")
            return
        
        logger.info("[SITE COLLECTION] Identifying site boundaries from discovered devices")
        
        # Identify site boundaries from discovered devices
        self.site_boundaries = self._identify_site_boundaries_from_inventory()
        
        if not self.site_boundaries:
            logger.info("[SITE COLLECTION] No site boundaries detected, skipping site collection")
            return
        
        logger.info(f"[SITE COLLECTION] Found {len(self.site_boundaries)} site boundaries: {list(self.site_boundaries.keys())}")
        
        # Initialize site queues with discovered devices
        site_queues = self.site_collection_manager.initialize_site_queues(self.site_boundaries)
        
        # Collect devices for each site
        for site_name in self.site_boundaries.keys():
            logger.info(f"[SITE COLLECTION] Starting collection for site '{site_name}'")
            
            try:
                # Update site queue with actual IP addresses from inventory
                self._update_site_queue_with_inventory(site_name)
                
                # Perform site collection
                collection_result = self.site_collection_manager.collect_site_devices(site_name)
                self.site_collection_results[site_name] = collection_result
                
                # Merge site inventory into main inventory
                self._merge_site_inventory_to_main(site_name, collection_result)
                
                logger.info(f"[SITE COLLECTION] Completed collection for site '{site_name}': {collection_result['statistics']}")
                
            except Exception as e:
                logger.error(f"[SITE COLLECTION] Error during collection for site '{site_name}': {e}")
                self.site_collection_results[site_name] = {
                    'site_name': site_name,
                    'success': False,
                    'error_message': str(e)
                }
        
        logger.info("[SITE COLLECTION] Site-specific collection completed")
    
    def _identify_site_boundaries_from_inventory(self) -> Dict[str, List[str]]:
        """
        Identify site boundaries from the current device inventory.
        
        Returns:
            Dictionary mapping site names to lists of device hostnames
        """
        site_boundaries = {}
        
        # Get all devices from inventory
        all_devices = self.inventory.get_all_devices()
        
        for device_key, device_info in all_devices.items():
            hostname = device_info.get('hostname', '')
            if not hostname:
                continue
            
            # Check if device matches site boundary pattern
            if self._matches_site_boundary_pattern(hostname):
                site_name = self._extract_site_name_from_hostname(hostname)
                
                if site_name not in site_boundaries:
                    site_boundaries[site_name] = []
                
                site_boundaries[site_name].append(hostname)
                logger.debug(f"[SITE BOUNDARIES] Device {hostname} assigned to site '{site_name}'")
        
        return site_boundaries
    
    def _matches_site_boundary_pattern(self, hostname: str) -> bool:
        """
        Check if hostname matches the site boundary pattern.
        
        Args:
            hostname: Device hostname to check
            
        Returns:
            True if hostname matches pattern, False otherwise
            
        Note: If site_boundary_pattern is None (disabled), this always returns False
        """
        # If site boundary pattern is None (disabled), no hostnames match
        if self.site_boundary_pattern is None:
            return False
        
        import fnmatch
        
        # Clean hostname for pattern matching
        clean_hostname = self._clean_hostname_for_pattern(hostname)
        
        # Convert wildcard pattern to fnmatch format
        pattern = self.site_boundary_pattern.replace('*', '*')
        
        return fnmatch.fnmatch(clean_hostname, pattern)
    
    def _extract_site_name_from_hostname(self, hostname: str) -> str:
        """
        Extract site name from hostname based on site boundary pattern.
        
        Args:
            hostname: Device hostname
            
        Returns:
            Site name extracted from hostname
        """
        # Clean hostname
        clean_hostname = self._clean_hostname_for_pattern(hostname)
        
        # For pattern like '*-CORE-*', extract the part before '-CORE-'
        if '-CORE-' in clean_hostname:
            return clean_hostname.split('-CORE-')[0]
        elif '-RTR-' in clean_hostname:
            return clean_hostname.split('-RTR-')[0]
        elif '-SW-' in clean_hostname:
            return clean_hostname.split('-SW-')[0]
        elif '-MDF-' in clean_hostname:
            return clean_hostname.split('-MDF-')[0]
        else:
            # Fallback: use first part of hostname
            parts = clean_hostname.split('-')
            return parts[0] if parts else clean_hostname
    
    def _clean_hostname_for_pattern(self, hostname: str) -> str:
        """
        Clean hostname for pattern matching.
        
        Args:
            hostname: Raw hostname
            
        Returns:
            Cleaned hostname suitable for pattern matching
        """
        if not hostname:
            return ""
        
        # Remove domain suffix if present
        if '.' in hostname:
            hostname = hostname.split('.')[0]
        
        # Convert to uppercase for consistent matching
        return hostname.upper()
    
    def _update_site_queue_with_inventory(self, site_name: str):
        """
        Update site queue devices with actual IP addresses from inventory.
        
        Args:
            site_name: Name of the site to update
        """
        if site_name not in self.site_boundaries:
            return
        
        # Get site queue manager
        site_queue_manager = self.site_collection_manager.site_queue_manager
        
        # Clear existing queue and rebuild with proper IP addresses
        site_queue_manager._site_queues[site_name].clear()
        site_queue_manager._site_device_sets[site_name].clear()
        
        # Add devices with correct IP addresses from inventory
        for hostname in self.site_boundaries[site_name]:
            # Find device in inventory by hostname
            device_info = None
            device_key = None
            
            for key, info in self.inventory.get_all_devices().items():
                if info.get('hostname', '').upper() == hostname.upper():
                    device_info = info
                    device_key = key
                    break
            
            if device_info and device_key:
                # Extract IP address
                ip_address = device_info.get('ip_address') or device_info.get('primary_ip', '0.0.0.0')
                
                # Create discovery node with correct IP
                device_node = DiscoveryNode(
                    hostname=hostname,
                    ip_address=ip_address,
                    depth=0,
                    discovery_method="site_boundary",
                    is_seed=True
                )
                
                # Add to site queue
                site_queue_manager.add_device_to_site(site_name, device_node)
                logger.debug(f"[SITE QUEUE UPDATE] Added {hostname}:{ip_address} to site '{site_name}' queue")
    
    def _merge_site_inventory_to_main(self, site_name: str, collection_result: Dict[str, Any]):
        """
        Merge site collection results into main inventory.
        
        Args:
            site_name: Name of the site
            collection_result: Site collection results
        """
        if not collection_result.get('success', False):
            logger.warning(f"[SITE MERGE] Skipping merge for failed site collection: {site_name}")
            return
        
        site_inventory = collection_result.get('inventory', {})
        
        for device_key, device_info in site_inventory.items():
            # Check if device already exists in main inventory
            if self.inventory.has_device(device_key):
                # Update existing device with additional information from site collection
                existing_info = self.inventory.get_device(device_key)
                
                # Merge neighbor information if site collection found more neighbors
                site_neighbors = device_info.get('neighbors', [])
                existing_neighbors = existing_info.get('neighbors', [])
                
                if len(site_neighbors) > len(existing_neighbors):
                    logger.info(f"[SITE MERGE] Updating {device_key} with {len(site_neighbors)} neighbors from site collection")
                    existing_info['neighbors'] = site_neighbors
                    existing_info['site_collection_enhanced'] = True
                    
                    # Update device in inventory
                    self.inventory.add_device(device_key, existing_info, "connected")
            else:
                # Add new device discovered during site collection
                logger.info(f"[SITE MERGE] Adding new device {device_key} discovered during site collection")
                device_info['discovered_by_site_collection'] = True
                self.inventory.add_device(device_key, device_info, "connected")
    
    def get_site_collection_results(self) -> Dict[str, Dict[str, Any]]:
        """
        Get site collection results.
        
        Returns:
            Dictionary mapping site names to their collection results
        """
        return self.site_collection_results.copy()
    
    def get_site_boundaries(self) -> Dict[str, List[str]]:
        """
        Get identified site boundaries.
        
        Returns:
            Dictionary mapping site names to lists of device hostnames
        """
        return self.site_boundaries.copy()