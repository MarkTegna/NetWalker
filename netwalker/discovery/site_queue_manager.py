"""
Site Queue Manager for NetWalker

Manages separate device queues for each site boundary to ensure proper site-specific device collection.
"""

import logging
from typing import Dict, Optional, Set, List
from collections import deque

from .discovery_engine import DiscoveryNode

logger = logging.getLogger(__name__)


class SiteQueueManager:
    """
    Manages separate device queues for each site boundary.
    
    Features:
    - Separate queues for each identified site
    - Deduplication to prevent duplicate devices in site queues
    - Queue size tracking and empty queue detection
    - Thread-safe operations for concurrent access
    """
    
    def __init__(self):
        """Initialize empty site queue manager"""
        self._site_queues: Dict[str, deque[DiscoveryNode]] = {}
        self._site_device_sets: Dict[str, Set[str]] = {}  # For deduplication
        self._queue_stats: Dict[str, Dict[str, int]] = {}
        
        logger.info("SiteQueueManager initialized")
    
    def create_site_queue(self, site_name: str) -> deque[DiscoveryNode]:
        """
        Create a new queue for a site boundary.
        
        Args:
            site_name: Name of the site boundary
            
        Returns:
            The created queue for the site
        """
        if site_name in self._site_queues:
            logger.warning(f"Site queue for '{site_name}' already exists")
            return self._site_queues[site_name]
        
        self._site_queues[site_name] = deque()
        self._site_device_sets[site_name] = set()
        self._queue_stats[site_name] = {
            'devices_added': 0,
            'devices_processed': 0,
            'duplicates_rejected': 0
        }
        
        logger.info(f"Created site queue for '{site_name}'")
        return self._site_queues[site_name]
    
    def add_device_to_site(self, site_name: str, device_node: DiscoveryNode) -> bool:
        """
        Add a device to a site's queue with deduplication.
        
        Args:
            site_name: Name of the site boundary
            device_node: Device node to add to the queue
            
        Returns:
            True if device was added, False if it was a duplicate
        """
        # Create site queue if it doesn't exist
        if site_name not in self._site_queues:
            self.create_site_queue(site_name)
        
        device_key = device_node.device_key
        
        # Check for duplicates
        if device_key in self._site_device_sets[site_name]:
            logger.debug(f"Duplicate device {device_key} rejected for site '{site_name}'")
            self._queue_stats[site_name]['duplicates_rejected'] += 1
            return False
        
        # Add device to queue and tracking set
        self._site_queues[site_name].append(device_node)
        self._site_device_sets[site_name].add(device_key)
        self._queue_stats[site_name]['devices_added'] += 1
        
        logger.info(f"Added device {device_key} to site '{site_name}' queue (queue size: {len(self._site_queues[site_name])})")
        return True
    
    def get_next_device(self, site_name: str) -> Optional[DiscoveryNode]:
        """
        Get the next device from a site's queue (FIFO order).
        
        Args:
            site_name: Name of the site boundary
            
        Returns:
            Next device node or None if queue is empty
        """
        if site_name not in self._site_queues or not self._site_queues[site_name]:
            return None
        
        device_node = self._site_queues[site_name].popleft()
        self._queue_stats[site_name]['devices_processed'] += 1
        
        logger.debug(f"Retrieved device {device_node.device_key} from site '{site_name}' queue (remaining: {len(self._site_queues[site_name])})")
        return device_node
    
    def is_site_queue_empty(self, site_name: str) -> bool:
        """
        Check if a site's queue is empty.
        
        Args:
            site_name: Name of the site boundary
            
        Returns:
            True if queue is empty or doesn't exist
        """
        if site_name not in self._site_queues:
            return True
        
        return len(self._site_queues[site_name]) == 0
    
    def get_site_queue_size(self, site_name: str) -> int:
        """
        Get the current size of a site's queue.
        
        Args:
            site_name: Name of the site boundary
            
        Returns:
            Number of devices in the queue
        """
        if site_name not in self._site_queues:
            return 0
        
        return len(self._site_queues[site_name])
    
    def get_all_site_names(self) -> List[str]:
        """
        Get list of all site names with queues.
        
        Returns:
            List of site names
        """
        return list(self._site_queues.keys())
    
    def get_site_stats(self, site_name: str) -> Dict[str, int]:
        """
        Get statistics for a site's queue.
        
        Args:
            site_name: Name of the site boundary
            
        Returns:
            Dictionary with queue statistics
        """
        if site_name not in self._queue_stats:
            return {
                'devices_added': 0,
                'devices_processed': 0,
                'duplicates_rejected': 0,
                'current_queue_size': 0
            }
        
        stats = self._queue_stats[site_name].copy()
        stats['current_queue_size'] = self.get_site_queue_size(site_name)
        return stats
    
    def get_all_site_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get statistics for all site queues.
        
        Returns:
            Dictionary mapping site names to their statistics
        """
        all_stats = {}
        for site_name in self._site_queues.keys():
            all_stats[site_name] = self.get_site_stats(site_name)
        
        return all_stats
    
    def clear_site_queue(self, site_name: str) -> bool:
        """
        Clear all devices from a site's queue.
        
        Args:
            site_name: Name of the site boundary
            
        Returns:
            True if queue was cleared, False if site doesn't exist
        """
        if site_name not in self._site_queues:
            return False
        
        queue_size = len(self._site_queues[site_name])
        self._site_queues[site_name].clear()
        self._site_device_sets[site_name].clear()
        
        logger.info(f"Cleared {queue_size} devices from site '{site_name}' queue")
        return True
    
    def remove_site_queue(self, site_name: str) -> bool:
        """
        Remove a site's queue entirely.
        
        Args:
            site_name: Name of the site boundary
            
        Returns:
            True if queue was removed, False if site doesn't exist
        """
        if site_name not in self._site_queues:
            return False
        
        queue_size = len(self._site_queues[site_name])
        del self._site_queues[site_name]
        del self._site_device_sets[site_name]
        del self._queue_stats[site_name]
        
        logger.info(f"Removed site queue for '{site_name}' (had {queue_size} devices)")
        return True
    
    def has_any_devices(self) -> bool:
        """
        Check if any site queues have devices.
        
        Returns:
            True if any site has devices in queue
        """
        return any(len(queue) > 0 for queue in self._site_queues.values())
    
    def get_total_queued_devices(self) -> int:
        """
        Get total number of devices across all site queues.
        
        Returns:
            Total number of queued devices
        """
        return sum(len(queue) for queue in self._site_queues.values())
    
    def log_queue_status(self):
        """Log current status of all site queues"""
        if not self._site_queues:
            logger.info("No site queues created")
            return
        
        logger.info(f"Site queue status ({len(self._site_queues)} sites):")
        for site_name, queue in self._site_queues.items():
            stats = self.get_site_stats(site_name)
            logger.info(f"  {site_name}: {len(queue)} queued, {stats['devices_processed']} processed, {stats['duplicates_rejected']} duplicates rejected")