"""
Discovery Engine for NetWalker

Implements breadth-first network topology discovery with depth limits and error isolation.
"""

import logging
from typing import Dict, List, Set, Optional, Tuple, Any
from collections import deque
from dataclasses import dataclass, field
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
    """
    
    def __init__(self, connection_manager: ConnectionManager, 
                 filter_manager: FilterManager, config: Dict[str, Any], credentials):
        """
        Initialize DiscoveryEngine.
        
        Args:
            connection_manager: Connection manager for device access
            filter_manager: Filter manager for boundary enforcement
            config: Configuration dictionary
            credentials: Device authentication credentials
        """
        self.logger = logging.getLogger(__name__)
        self.connection_manager = connection_manager
        self.filter_manager = filter_manager
        self.config = config
        self.credentials = credentials
        
        # Discovery configuration
        self.max_depth = config.get('max_discovery_depth', 5)
        self.discovery_timeout = config.get('discovery_timeout_seconds', 300)
        
        # Initialize components
        self.protocol_parser = ProtocolParser()
        self.device_collector = DeviceCollector()
        self.inventory = DeviceInventory()
        
        # Discovery state
        self.discovery_queue: deque[DiscoveryNode] = deque()
        self.discovered_devices: Set[str] = set()
        self.failed_devices: Set[str] = set()
        
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
        logger.info(f"Added seed device: {seed_node.device_key}")
    
    def discover_topology(self) -> Dict[str, Any]:
        """
        Execute breadth-first topology discovery.
        
        Returns:
            Discovery results summary
        """
        start_time = time.time()
        logger.info("Starting network topology discovery")
        
        try:
            while self.discovery_queue and (time.time() - start_time) < self.discovery_timeout:
                current_node = self.discovery_queue.popleft()
                
                # Skip if already discovered
                if current_node.device_key in self.discovered_devices:
                    continue
                
                # Check depth limit
                if current_node.depth > self.max_depth:
                    logger.debug(f"Skipping {current_node.device_key} - depth limit exceeded")
                    continue
                
                # Discover device
                self._discover_device(current_node)
            
            # Handle timeout
            if (time.time() - start_time) >= self.discovery_timeout:
                logger.warning(f"Discovery timeout reached after {self.discovery_timeout}s")
            
        except Exception as e:
            logger.error(f"Discovery engine error: {e}")
            raise
        
        discovery_time = time.time() - start_time
        results = self._generate_discovery_summary(discovery_time)
        
        logger.info(f"Discovery completed in {discovery_time:.2f}s - "
                   f"Found {results['total_devices']} devices")
        
        return results
    
    def _discover_device(self, node: DiscoveryNode):
        """
        Discover a single device and add neighbors to queue.
        
        Args:
            node: Discovery node to process
        """
        device_key = node.device_key
        logger.debug(f"Discovering device {device_key} at depth {node.depth}")
        
        try:
            # Mark as discovered to prevent loops
            self.discovered_devices.add(device_key)
            
            # Check if device should be filtered
            if self.filter_manager.should_filter_device(node.hostname, node.ip_address):
                logger.info(f"Device {device_key} filtered - marking as boundary")
                self.filter_manager.mark_as_boundary(node.hostname, node.ip_address, "Filtered device")
                
                # Add to inventory as filtered
                device_info = self._create_basic_device_info(node, "filtered")
                self.inventory.add_device(device_key, device_info, "filtered")
                return
            
            # Attempt connection and discovery
            discovery_result = self._connect_and_discover(node)
            
            if discovery_result.success:
                # Add device to inventory
                self.inventory.add_device(
                    device_key, 
                    discovery_result.device_info, 
                    "connected"
                )
                
                # Process neighbors for further discovery
                self._process_neighbors(discovery_result.neighbors, node)
                
            else:
                # Record failed device
                self.failed_devices.add(device_key)
                device_info = self._create_basic_device_info(node, "failed")
                device_info['error_message'] = discovery_result.error_message
                
                self.inventory.add_device(
                    device_key, 
                    device_info, 
                    "failed", 
                    discovery_result.error_message
                )
                
                logger.warning(f"Failed to discover {device_key}: {discovery_result.error_message}")
        
        except Exception as e:
            logger.error(f"Error discovering device {device_key}: {e}")
            self.failed_devices.add(device_key)
            
            # Add error device to inventory
            device_info = self._create_basic_device_info(node, "error")
            device_info['error_message'] = str(e)
            self.inventory.add_device(device_key, device_info, "failed", str(e))
    
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
            connection, connection_result = self.connection_manager.connect_device(node.ip_address, self.credentials)
            
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
                connection, node.hostname, connection_result.method.value, 
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
                'neighbors': device_info.neighbors  # Store the NeighborInfo objects directly
            }
            
            # Get neighbors from DeviceInfo object
            neighbors = device_info.neighbors
            
            # Close connection
            self.connection_manager.close_connection(node.hostname)
            
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
                
                # Skip if no IP address available
                if not neighbor_ip:
                    logger.debug(f"Skipping neighbor {neighbor_hostname} - no IP address available")
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
            if self.filter_manager.should_filter_device(
                neighbor_hostname, neighbor_ip, neighbor_platform, neighbor_capabilities
            ):
                logger.info(f"Neighbor {neighbor_hostname}:{neighbor_ip} filtered by platform/capabilities - "
                           f"platform: {neighbor_platform}, capabilities: {neighbor_capabilities}")
                self.filter_manager.mark_as_boundary(
                    neighbor_hostname, neighbor_ip, 
                    f"Filtered by platform ({neighbor_platform}) or capabilities ({neighbor_capabilities})"
                )
                
                # Add to inventory as filtered
                device_info = self._create_basic_device_info_for_neighbor(
                    neighbor_hostname, neighbor_ip, parent_node.depth + 1, 
                    protocol, parent_node.device_key, "filtered", 
                    neighbor_platform, neighbor_capabilities
                )
                self.inventory.add_device(f"{neighbor_hostname}:{neighbor_ip}", device_info, "filtered")
                continue
            
            # Create neighbor node
            neighbor_node = DiscoveryNode(
                hostname=neighbor_hostname,
                ip_address=neighbor_ip,
                depth=parent_node.depth + 1,
                parent_device=parent_node.device_key,
                discovery_method=protocol
            )
            
            # Skip if already discovered or queued
            if (neighbor_node.device_key in self.discovered_devices or 
                any(n.device_key == neighbor_node.device_key for n in self.discovery_queue)):
                continue
            
            # Add to discovery queue
            self.discovery_queue.append(neighbor_node)
            logger.debug(f"Added neighbor {neighbor_node.device_key} to discovery queue "
                        f"(depth {neighbor_node.depth})")
    
    def _create_basic_device_info(self, node: DiscoveryNode, status: str) -> Dict[str, Any]:
        """Create basic device info for failed/filtered devices"""
        return {
            'hostname': node.hostname,
            'ip_address': node.ip_address,
            'discovery_depth': node.depth,
            'discovery_method': node.discovery_method,
            'parent_device': node.parent_device,
            'discovery_timestamp': datetime.now().isoformat(),
            'status': status,
            'platform': 'unknown',
            'software_version': 'unknown',
            'serial_number': 'unknown',
            'hardware_model': 'unknown',
            'uptime': 'unknown',
            'connection_method': 'none'
        }
    
    def _create_basic_device_info_for_neighbor(self, hostname: str, ip_address: str, depth: int, 
                                             discovery_method: str, parent_device: str, status: str,
                                             platform: Optional[str] = None, 
                                             capabilities: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create basic device info for filtered neighbor devices"""
        return {
            'hostname': hostname,
            'ip_address': ip_address,
            'discovery_depth': depth,
            'discovery_method': discovery_method,
            'parent_device': parent_device,
            'discovery_timestamp': datetime.now().isoformat(),
            'status': status,
            'platform': platform or 'unknown',
            'capabilities': capabilities or [],
            'software_version': 'unknown',
            'serial_number': 'unknown',
            'hardware_model': 'unknown',
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
            'successful_connections': stats['successful_connections'],
            'failed_connections': stats['failed_connections'],
            'filtered_devices': stats['filtered_devices'],
            'boundary_devices': stats['boundary_devices'],
            'max_depth_reached': max_depth,
            'devices_in_queue': len(self.discovery_queue),
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