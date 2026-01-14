"""
Site Device Walker for NetWalker

Handles site-specific device walking with connection management and neighbor processing.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from ..connection.connection_manager import ConnectionManager
from ..connection.data_models import ConnectionStatus
from .device_collector import DeviceCollector
from .discovery_engine import DiscoveryNode
from .site_association_validator import SiteAssociationValidator

logger = logging.getLogger(__name__)


@dataclass
class SiteWalkResult:
    """Results from site-specific device walking operation"""
    device_key: str
    site_name: str
    walk_success: bool
    device_info: Optional[Dict[str, Any]] = None
    neighbors_found: List[Any] = field(default_factory=list)
    neighbors_added_to_queue: int = 0
    error_message: Optional[str] = None
    walk_timestamp: datetime = field(default_factory=datetime.now)
    connection_method: Optional[str] = None
    walk_duration: float = 0.0


class SiteDeviceWalker:
    """
    Walks devices within site boundaries to discover neighbors.
    
    Features:
    - Site device walking with connection management
    - Neighbor processing with site association
    - Error handling for failed device walks
    - Connection method tracking (SSH/Telnet)
    """
    
    def __init__(self, connection_manager: ConnectionManager, device_collector: DeviceCollector,
                 site_association_validator: SiteAssociationValidator, credentials=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize SiteDeviceWalker.
        
        Args:
            connection_manager: Connection manager for device connections
            device_collector: Device collector for extracting device information
            site_association_validator: Validator for determining device site associations
            credentials: Authentication credentials for device connections
            config: Configuration dictionary for walker settings
        """
        self.connection_manager = connection_manager
        self.device_collector = device_collector
        self.site_validator = site_association_validator
        self.credentials = credentials
        
        # Configuration settings
        self.config = config or {}
        self.connection_timeout = self.config.get('connection_timeout_seconds', 30)
        self.retry_attempts = self.config.get('connection_retry_attempts', 3)
        self.max_neighbors_per_device = self.config.get('max_neighbors_per_device', 50)
        self.enable_neighbor_filtering = self.config.get('enable_neighbor_filtering', True)
        
        # Statistics tracking
        self._walk_stats = {
            'total_walks': 0,
            'successful_walks': 0,
            'failed_walks': 0,
            'neighbors_discovered': 0,
            'neighbors_queued': 0,
            'neighbors_filtered': 0
        }
        
        logger.info("SiteDeviceWalker initialized")
        logger.info(f"Configuration: timeout={self.connection_timeout}s, retries={self.retry_attempts}, max_neighbors={self.max_neighbors_per_device}")
    
    def walk_site_device(self, device_node: DiscoveryNode, site_name: str) -> SiteWalkResult:
        """
        Walk a device within a site boundary to discover neighbors.
        
        Args:
            device_node: Device node to walk
            site_name: Site name the device belongs to
            
        Returns:
            SiteWalkResult with walk results and neighbor information
        """
        start_time = datetime.now()
        device_key = device_node.device_key
        
        logger.info(f"Walking site device: {device_key} in site '{site_name}'")
        
        self._walk_stats['total_walks'] += 1
        
        try:
            # Attempt to connect to the device
            connection, connection_result = self.connection_manager.connect_device(
                device_node.ip_address, 
                self.credentials  # Use the credentials passed to the walker
            )
            
            if connection_result.status != ConnectionStatus.SUCCESS:
                error_msg = f"Failed to connect to {device_key}: {connection_result.error_message}"
                logger.warning(error_msg)
                self._walk_stats['failed_walks'] += 1
                
                return SiteWalkResult(
                    device_key=device_key,
                    site_name=site_name,
                    walk_success=False,
                    error_message=error_msg,
                    walk_timestamp=start_time,
                    walk_duration=(datetime.now() - start_time).total_seconds()
                )
            
            # Collect device information
            device_info = self.device_collector.collect_device_info(
                connection,
                device_node.hostname,
                device_node.ip_address
            )
            
            if not device_info:
                error_msg = f"Failed to collect device information from {device_key}"
                logger.warning(error_msg)
                self._walk_stats['failed_walks'] += 1
                
                # Close connection
                self.connection_manager.close_connection(connection)
                
                return SiteWalkResult(
                    device_key=device_key,
                    site_name=site_name,
                    walk_success=False,
                    error_message=error_msg,
                    connection_method=connection_result.method.value,
                    walk_timestamp=start_time,
                    walk_duration=(datetime.now() - start_time).total_seconds()
                )
            
            # Extract neighbors from device
            neighbors = device_info.get('neighbors', [])
            logger.info(f"Device {device_key} has {len(neighbors)} neighbors")
            
            # Process neighbors for site association
            processed_neighbors = self.process_site_neighbors(neighbors, site_name)
            
            # Close connection
            self.connection_manager.close_connection(connection)
            
            # Update statistics
            self._walk_stats['successful_walks'] += 1
            self._walk_stats['neighbors_discovered'] += len(neighbors)
            self._walk_stats['neighbors_queued'] += len(processed_neighbors)
            
            walk_duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Successfully walked device {device_key}: {len(neighbors)} neighbors found, {len(processed_neighbors)} processed")
            
            return SiteWalkResult(
                device_key=device_key,
                site_name=site_name,
                walk_success=True,
                device_info=device_info,
                neighbors_found=neighbors,
                neighbors_added_to_queue=len(processed_neighbors),
                connection_method=connection_result.method.value,
                walk_timestamp=start_time,
                walk_duration=walk_duration
            )
            
        except Exception as e:
            error_msg = f"Exception during device walk for {device_key}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._walk_stats['failed_walks'] += 1
            
            return SiteWalkResult(
                device_key=device_key,
                site_name=site_name,
                walk_success=False,
                error_message=error_msg,
                walk_timestamp=start_time,
                walk_duration=(datetime.now() - start_time).total_seconds()
            )
    
    def process_site_neighbors(self, neighbors: List[Any], parent_site: str) -> List[DiscoveryNode]:
        """
        Process neighbors discovered from a site device and determine their site associations.
        
        Args:
            neighbors: List of neighbor objects from device discovery
            parent_site: Site name of the parent device
            
        Returns:
            List of DiscoveryNode objects for neighbors that should be queued
        """
        processed_neighbors = []
        
        logger.debug(f"Processing {len(neighbors)} neighbors for parent site '{parent_site}'")
        
        for neighbor in neighbors:
            try:
                # Extract neighbor information
                neighbor_hostname = ''
                neighbor_ip = ''
                
                # Handle different neighbor object types
                if hasattr(neighbor, 'hostname'):
                    neighbor_hostname = neighbor.hostname
                    neighbor_ip = getattr(neighbor, 'ip_address', '')
                elif isinstance(neighbor, dict):
                    neighbor_hostname = neighbor.get('hostname', '')
                    neighbor_ip = neighbor.get('ip_address', '')
                else:
                    logger.warning(f"Unknown neighbor object type: {type(neighbor)}")
                    continue
                
                if not neighbor_hostname and not neighbor_ip:
                    logger.debug("Skipping neighbor with no hostname or IP")
                    continue
                
                # Validate neighbor site association
                neighbor_site = self.validate_neighbor_site_association(
                    neighbor_hostname, neighbor_ip, parent_site
                )
                
                # Create DiscoveryNode for the neighbor
                discovery_node = DiscoveryNode(
                    hostname=neighbor_hostname,
                    ip_address=neighbor_ip,
                    depth=0,  # Will be set by the calling code
                    parent_device=f"{parent_site}",  # Track parent site
                    discovery_method="site_walk",
                    is_seed=False
                )
                
                processed_neighbors.append(discovery_node)
                
                logger.debug(f"Processed neighbor {neighbor_hostname} -> site: {neighbor_site}")
                
            except Exception as e:
                logger.warning(f"Error processing neighbor {neighbor}: {str(e)}")
                continue
        
        logger.info(f"Processed {len(processed_neighbors)} valid neighbors from {len(neighbors)} total")
        return processed_neighbors
    
    def validate_neighbor_site_association(self, neighbor_hostname: str, neighbor_ip: str, 
                                         parent_site: str) -> str:
        """
        Validate and determine the site association for a discovered neighbor.
        
        Args:
            neighbor_hostname: Hostname of the neighbor device
            neighbor_ip: IP address of the neighbor device
            parent_site: Site of the parent device that discovered this neighbor
            
        Returns:
            Site name for the neighbor device
        """
        # Use the site validator to determine the neighbor's site
        neighbor_site = self.site_validator.determine_device_site(
            neighbor_hostname, neighbor_ip, parent_site
        )
        
        logger.debug(f"Neighbor {neighbor_hostname} ({neighbor_ip}) associated with site: {neighbor_site}")
        
        return neighbor_site
    
    def get_walk_statistics(self) -> Dict[str, Any]:
        """
        Get walking statistics.
        
        Returns:
            Dictionary with walking statistics
        """
        stats = self._walk_stats.copy()
        
        # Calculate success rate
        if stats['total_walks'] > 0:
            stats['success_rate'] = stats['successful_walks'] / stats['total_walks']
        else:
            stats['success_rate'] = 0.0
        
        # Calculate average neighbors per device
        if stats['successful_walks'] > 0:
            stats['avg_neighbors_per_device'] = stats['neighbors_discovered'] / stats['successful_walks']
        else:
            stats['avg_neighbors_per_device'] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset walking statistics"""
        self._walk_stats = {
            'total_walks': 0,
            'successful_walks': 0,
            'failed_walks': 0,
            'neighbors_discovered': 0,
            'neighbors_queued': 0
        }
        logger.info("Site device walker statistics reset")
    
    def walk_multiple_devices(self, device_nodes: List[DiscoveryNode], 
                            site_name: str) -> List[SiteWalkResult]:
        """
        Walk multiple devices in a site.
        
        Args:
            device_nodes: List of device nodes to walk
            site_name: Site name for all devices
            
        Returns:
            List of SiteWalkResult objects
        """
        results = []
        
        logger.info(f"Walking {len(device_nodes)} devices in site '{site_name}'")
        
        for device_node in device_nodes:
            result = self.walk_site_device(device_node, site_name)
            results.append(result)
            
            # Log progress
            if len(results) % 10 == 0:
                logger.info(f"Walked {len(results)}/{len(device_nodes)} devices in site '{site_name}'")
        
        # Log final statistics
        successful = sum(1 for r in results if r.walk_success)
        failed = len(results) - successful
        total_neighbors = sum(len(r.neighbors_found) for r in results)
        
        logger.info(f"Site '{site_name}' walk complete: {successful} successful, {failed} failed, {total_neighbors} neighbors discovered")
        
        return results
    
    def get_site_neighbor_summary(self, walk_results: List[SiteWalkResult]) -> Dict[str, Any]:
        """
        Generate a summary of neighbors discovered during site walking.
        
        Args:
            walk_results: List of walk results from site devices
            
        Returns:
            Dictionary with neighbor discovery summary
        """
        summary = {
            'total_devices_walked': len(walk_results),
            'successful_walks': sum(1 for r in walk_results if r.walk_success),
            'failed_walks': sum(1 for r in walk_results if not r.walk_success),
            'total_neighbors_found': sum(len(r.neighbors_found) for r in walk_results),
            'unique_neighbors': set(),
            'connection_methods': {},
            'walk_errors': []
        }
        
        # Collect unique neighbors and connection methods
        for result in walk_results:
            if result.walk_success:
                # Track connection methods
                method = result.connection_method or 'unknown'
                summary['connection_methods'][method] = summary['connection_methods'].get(method, 0) + 1
                
                # Track unique neighbors
                for neighbor in result.neighbors_found:
                    if hasattr(neighbor, 'hostname') and neighbor.hostname:
                        summary['unique_neighbors'].add(neighbor.hostname)
                    elif isinstance(neighbor, dict) and neighbor.get('hostname'):
                        summary['unique_neighbors'].add(neighbor['hostname'])
            else:
                # Track errors
                if result.error_message:
                    summary['walk_errors'].append({
                        'device': result.device_key,
                        'error': result.error_message
                    })
        
        summary['unique_neighbor_count'] = len(summary['unique_neighbors'])
        summary['unique_neighbors'] = list(summary['unique_neighbors'])  # Convert set to list for JSON serialization
        
        return summary