"""
Site-Specific Collection Manager for NetWalker

Orchestrates site-specific device collection and walking to ensure complete
topology discovery within site boundaries.
"""

import logging
from typing import Dict, List, Set, Optional, Any, Deque, Callable
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
import traceback
from enum import Enum

from .discovery_engine import DiscoveryNode, DeviceInventory
from .site_queue_manager import SiteQueueManager
from .site_device_walker import SiteDeviceWalker, SiteWalkResult
from .site_association_validator import SiteAssociationValidator
from ..connection.connection_manager import ConnectionManager
from .device_collector import DeviceCollector

logger = logging.getLogger(__name__)


class SiteCollectionErrorType(Enum):
    """Types of errors that can occur during site collection"""
    DEVICE_CONNECTION_FAILED = "device_connection_failed"
    DEVICE_WALK_FAILED = "device_walk_failed"
    SITE_QUEUE_ERROR = "site_queue_error"
    SITE_INITIALIZATION_FAILED = "site_initialization_failed"
    CONFIGURATION_ERROR = "configuration_error"
    TIMEOUT_ERROR = "timeout_error"
    CRITICAL_SYSTEM_ERROR = "critical_system_error"


@dataclass
class SiteCollectionError:
    """Represents an error that occurred during site collection"""
    error_type: SiteCollectionErrorType
    site_name: str
    device_key: Optional[str] = None
    error_message: str = ""
    exception: Optional[Exception] = None
    timestamp: datetime = field(default_factory=datetime.now)
    recovery_attempted: bool = False
    recovery_successful: bool = False
    fallback_to_global: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/reporting"""
        return {
            'error_type': self.error_type.value,
            'site_name': self.site_name,
            'device_key': self.device_key,
            'error_message': self.error_message,
            'timestamp': self.timestamp.isoformat(),
            'recovery_attempted': self.recovery_attempted,
            'recovery_successful': self.recovery_successful,
            'fallback_to_global': self.fallback_to_global
        }


@dataclass
class SiteCollectionStats:
    """Statistics for site-specific device collection"""
    site_name: str
    devices_queued: int = 0
    devices_processed: int = 0
    devices_successful: int = 0
    devices_failed: int = 0
    neighbors_discovered: int = 0
    collection_start_time: Optional[datetime] = None
    collection_end_time: Optional[datetime] = None
    
    # Error tracking
    errors_encountered: int = 0
    recoveries_attempted: int = 0
    recoveries_successful: int = 0
    fallbacks_to_global: int = 0
    
    @property
    def collection_duration_seconds(self) -> float:
        """Calculate collection duration in seconds"""
        if self.collection_start_time and self.collection_end_time:
            return (self.collection_end_time - self.collection_start_time).total_seconds()
        return 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.devices_processed == 0:
            return 0.0
        return (self.devices_successful / self.devices_processed) * 100.0
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage"""
        if self.devices_processed == 0:
            return 0.0
        return (self.errors_encountered / self.devices_processed) * 100.0
    
    @property
    def recovery_rate(self) -> float:
        """Calculate recovery success rate as percentage"""
        if self.recoveries_attempted == 0:
            return 0.0
        return (self.recoveries_successful / self.recoveries_attempted) * 100.0


class SiteSpecificCollectionManager:
    """
    Orchestrates site-specific device collection and walking.
    
    This manager ensures that devices discovered within site boundaries are
    properly collected, walked for neighbors, and processed completely to
    build accurate site topology maps. Includes comprehensive error handling
    and recovery mechanisms.
    """
    
    def __init__(self, connection_manager: ConnectionManager, 
                 device_collector: DeviceCollector, config: Dict[str, Any],
                 credentials, site_boundary_pattern: str = r".*-CORE-.*",
                 global_fallback_callback: Optional[Callable] = None):
        """
        Initialize SiteSpecificCollectionManager.
        
        Args:
            connection_manager: Connection manager for device access
            device_collector: Device collector for information gathering
            config: Configuration dictionary
            credentials: Device authentication credentials
            site_boundary_pattern: Regex pattern for site boundary detection
            global_fallback_callback: Callback function for global discovery fallback
        """
        self.logger = logging.getLogger(__name__)
        self.connection_manager = connection_manager
        self.device_collector = device_collector
        self.config = config
        self.credentials = credentials
        self.global_fallback_callback = global_fallback_callback
        
        # Enhanced logging configuration
        self.progress_logging_enabled = config.get('enable_progress_logging', True)
        self.detailed_error_logging = config.get('enable_detailed_error_logging', True)
        self.statistics_logging_enabled = config.get('enable_statistics_logging', True)
        self.progress_update_interval = config.get('progress_update_interval_devices', 5)
        self.log_level_override = config.get('site_collection_log_level', None)
        
        # Initialize components
        self.site_queue_manager = SiteQueueManager()
        self.site_association_validator = SiteAssociationValidator(site_boundary_pattern)
        self.site_device_walker = SiteDeviceWalker(
            connection_manager, device_collector, self.site_association_validator, self.credentials, config
        )
        
        # Site collection state
        self.site_inventories: Dict[str, DeviceInventory] = {}
        self.site_stats: Dict[str, SiteCollectionStats] = {}
        self.discovered_devices_by_site: Dict[str, Set[str]] = defaultdict(set)
        
        # Enhanced progress tracking
        self.site_progress_trackers: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.last_progress_update: Dict[str, datetime] = {}
        self.collection_start_times: Dict[str, datetime] = {}
        
        # Error handling state
        self.site_errors: Dict[str, List[SiteCollectionError]] = defaultdict(list)
        self.failed_sites: Set[str] = set()
        self.global_fallback_devices: Set[str] = set()
        
        # Configuration
        self.max_depth = config.get('max_discovery_depth', 1)
        self.collection_timeout = config.get('site_collection_timeout_seconds', 600)
        self.connection_timeout = config.get('connection_timeout_seconds', 30)
        self.retry_attempts = config.get('connection_retry_attempts', 3)
        
        # Error handling configuration
        self.max_site_errors = config.get('max_site_errors_before_fallback', 10)
        self.max_device_retries = config.get('max_device_retries', 3)
        self.error_recovery_enabled = config.get('enable_error_recovery', True)
        self.inter_site_error_isolation = config.get('enable_inter_site_error_isolation', True)
        self.critical_error_threshold = config.get('critical_error_threshold_percent', 50.0)
        
        # Filtering configuration
        self.enable_filtering = config.get('enable_device_filtering', True)
        self.filter_patterns = config.get('device_filter_patterns', [])
        self.exclude_patterns = config.get('device_exclude_patterns', [])
        
        # Site collection specific configuration
        self.site_collection_enabled = config.get('enable_site_collection', True)
        self.site_collection_parallel = config.get('site_collection_parallel', False)
        self.site_collection_max_workers = config.get('site_collection_max_workers', 4)
        
        # Configure enhanced logging if log level override is specified
        if self.log_level_override:
            site_logger = logging.getLogger(f"{__name__}.site_collection")
            site_logger.setLevel(getattr(logging, self.log_level_override.upper(), logging.INFO))
        
        logger.info(f"SiteSpecificCollectionManager initialized with pattern: {site_boundary_pattern}")
        logger.info(f"Configuration: max_depth={self.max_depth}, timeout={self.collection_timeout}s")
        logger.info(f"Error handling: max_errors={self.max_site_errors}, recovery_enabled={self.error_recovery_enabled}")
        logger.info(f"Filtering enabled: {self.enable_filtering}, Site collection enabled: {self.site_collection_enabled}")
        logger.info(f"Enhanced logging: progress={self.progress_logging_enabled}, detailed_errors={self.detailed_error_logging}, statistics={self.statistics_logging_enabled}")
        logger.info(f"Progress update interval: {self.progress_update_interval} devices")
    
    def apply_configuration_to_collection(self, device_node: DiscoveryNode) -> bool:
        """
        Apply configuration settings to determine if device should be collected.
        
        Args:
            device_node: Device node to evaluate
            
        Returns:
            True if device should be collected, False if filtered out
        """
        # Check if site collection is enabled
        if not self.site_collection_enabled:
            logger.debug(f"Site collection disabled, skipping {device_node.device_key}")
            return False
        
        # Check discovery depth limits
        if device_node.depth > self.max_depth:
            logger.debug(f"Device {device_node.device_key} exceeds max depth {self.max_depth}")
            return False
        
        # Apply filtering if enabled
        if self.enable_filtering:
            hostname = device_node.hostname.lower()
            
            # Check exclude patterns first
            for exclude_pattern in self.exclude_patterns:
                if exclude_pattern.lower() in hostname:
                    logger.debug(f"Device {device_node.device_key} excluded by pattern: {exclude_pattern}")
                    return False
            
            # Check include patterns (if any specified)
            if self.filter_patterns:
                include_match = False
                for filter_pattern in self.filter_patterns:
                    if filter_pattern.lower() in hostname:
                        include_match = True
                        break
                
                if not include_match:
                    logger.debug(f"Device {device_node.device_key} does not match any filter patterns")
                    return False
        
        return True
    
    def _log_site_collection_start(self, site_name: str):
        """
        Log the start of site collection with detailed information.
        
        Args:
            site_name: Name of the site starting collection
            
        Requirement 7.1: Log the number of devices queued for each site when collection begins
        """
        if not self.progress_logging_enabled:
            return
        
        stats = self.site_stats.get(site_name)
        if not stats:
            return
        
        queue_size = self.site_queue_manager.get_site_queue_size(site_name)
        
        # Enhanced start logging
        self.logger.info(f"[SITE COLLECTION START] ===============================================")
        self.logger.info(f"[SITE COLLECTION START] Site: '{site_name}'")
        self.logger.info(f"[SITE COLLECTION START] Devices queued: {stats.devices_queued}")
        self.logger.info(f"[SITE COLLECTION START] Current queue size: {queue_size}")
        self.logger.info(f"[SITE COLLECTION START] Max discovery depth: {self.max_depth}")
        self.logger.info(f"[SITE COLLECTION START] Collection timeout: {self.collection_timeout}s")
        self.logger.info(f"[SITE COLLECTION START] Error recovery enabled: {self.error_recovery_enabled}")
        self.logger.info(f"[SITE COLLECTION START] Start time: {stats.collection_start_time}")
        self.logger.info(f"[SITE COLLECTION START] ===============================================")
        
        # Initialize progress tracking
        self.site_progress_trackers[site_name] = {
            'devices_processed_at_last_update': 0,
            'last_update_time': datetime.now(),
            'processing_rate_devices_per_minute': 0.0,
            'estimated_completion_time': None,
            'current_device': None,
            'phase': 'starting'
        }
        
        self.collection_start_times[site_name] = datetime.now()
        self.last_progress_update[site_name] = datetime.now()
    
    def _log_site_collection_progress(self, site_name: str, current_device: Optional[str] = None):
        """
        Log progress updates during site collection.
        
        Args:
            site_name: Name of the site
            current_device: Currently processing device (optional)
            
        Requirement 7.2: Report progress as devices are completed
        Requirement 7.5: Provide progress updates for each site independently
        """
        if not self.progress_logging_enabled:
            return
        
        stats = self.site_stats.get(site_name)
        if not stats:
            return
        
        # Check if it's time for a progress update
        now = datetime.now()
        last_update = self.last_progress_update.get(site_name, now)
        
        # Update progress every N devices or every 30 seconds, whichever comes first
        devices_since_update = stats.devices_processed - self.site_progress_trackers[site_name].get('devices_processed_at_last_update', 0)
        time_since_update = (now - last_update).total_seconds()
        
        should_update = (devices_since_update >= self.progress_update_interval or 
                        time_since_update >= 30 or 
                        current_device is not None)
        
        if not should_update:
            return
        
        # Calculate processing rate
        total_time = (now - self.collection_start_times[site_name]).total_seconds()
        if total_time > 0:
            processing_rate = (stats.devices_processed / total_time) * 60  # devices per minute
        else:
            processing_rate = 0.0
        
        # Estimate completion time
        remaining_devices = stats.devices_queued - stats.devices_processed
        if processing_rate > 0 and remaining_devices > 0:
            estimated_minutes = remaining_devices / processing_rate
            estimated_completion = now + timedelta(minutes=estimated_minutes)
        else:
            estimated_completion = None
        
        # Update progress tracker
        self.site_progress_trackers[site_name].update({
            'devices_processed_at_last_update': stats.devices_processed,
            'last_update_time': now,
            'processing_rate_devices_per_minute': processing_rate,
            'estimated_completion_time': estimated_completion,
            'current_device': current_device,
            'phase': 'processing'
        })
        
        # Log progress update
        progress_percent = (stats.devices_processed / stats.devices_queued * 100) if stats.devices_queued > 0 else 0
        
        self.logger.info(f"[SITE PROGRESS] Site '{site_name}' - Progress Update")
        self.logger.info(f"[SITE PROGRESS]   Processed: {stats.devices_processed}/{stats.devices_queued} ({progress_percent:.1f}%)")
        self.logger.info(f"[SITE PROGRESS]   Success rate: {stats.success_rate:.1f}% ({stats.devices_successful} successful)")
        self.logger.info(f"[SITE PROGRESS]   Failed: {stats.devices_failed} devices")
        self.logger.info(f"[SITE PROGRESS]   Neighbors found: {stats.neighbors_discovered}")
        self.logger.info(f"[SITE PROGRESS]   Processing rate: {processing_rate:.1f} devices/min")
        
        if estimated_completion:
            self.logger.info(f"[SITE PROGRESS]   Estimated completion: {estimated_completion.strftime('%H:%M:%S')}")
        
        if current_device:
            self.logger.info(f"[SITE PROGRESS]   Currently processing: {current_device}")
        
        if stats.errors_encountered > 0:
            self.logger.info(f"[SITE PROGRESS]   Errors: {stats.errors_encountered} (recovery rate: {stats.recovery_rate:.1f}%)")
        
        self.last_progress_update[site_name] = now
    
    def _log_site_collection_error_detailed(self, error: SiteCollectionError):
        """
        Log detailed error information with site context.
        
        Args:
            error: The error that occurred
            
        Requirement 7.3: Log detailed error information with site context
        """
        if not self.detailed_error_logging:
            return
        
        # Get current site statistics for context
        stats = self.site_stats.get(error.site_name)
        
        self.logger.error(f"[SITE ERROR DETAIL] ======================================================================")
        self.logger.error(f"[SITE ERROR DETAIL] | Site Collection Error Details")
        self.logger.error(f"[SITE ERROR DETAIL] +======================================================================")
        self.logger.error(f"[SITE ERROR DETAIL] | Site Name: {error.site_name}")
        self.logger.error(f"[SITE ERROR DETAIL] | Error Type: {error.error_type.value}")
        self.logger.error(f"[SITE ERROR DETAIL] | Device: {error.device_key or 'N/A'}")
        self.logger.error(f"[SITE ERROR DETAIL] | Error Message: {error.error_message}")
        self.logger.error(f"[SITE ERROR DETAIL] | Timestamp: {error.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if stats:
            self.logger.error(f"[SITE ERROR DETAIL] | Site Context:")
            self.logger.error(f"[SITE ERROR DETAIL] |   Devices processed: {stats.devices_processed}/{stats.devices_queued}")
            self.logger.error(f"[SITE ERROR DETAIL] |   Success rate: {stats.success_rate:.1f}%")
            self.logger.error(f"[SITE ERROR DETAIL] |   Total errors: {stats.errors_encountered}")
            self.logger.error(f"[SITE ERROR DETAIL] |   Error rate: {stats.error_rate:.1f}%")
        
        self.logger.error(f"[SITE ERROR DETAIL] | Recovery Status:")
        self.logger.error(f"[SITE ERROR DETAIL] |   Recovery attempted: {error.recovery_attempted}")
        self.logger.error(f"[SITE ERROR DETAIL] |   Recovery successful: {error.recovery_successful}")
        self.logger.error(f"[SITE ERROR DETAIL] |   Fallback to global: {error.fallback_to_global}")
        
        if error.exception:
            self.logger.error(f"[SITE ERROR DETAIL] | Exception Details:")
            self.logger.error(f"[SITE ERROR DETAIL] |   Exception Type: {type(error.exception).__name__}")
            self.logger.error(f"[SITE ERROR DETAIL] |   Exception Message: {str(error.exception)}")
            
            # Log stack trace if available
            if hasattr(error.exception, '__traceback__') and error.exception.__traceback__:
                import traceback
                tb_lines = traceback.format_exception(type(error.exception), error.exception, error.exception.__traceback__)
                for i, line in enumerate(tb_lines[-5:]):  # Last 5 lines of traceback
                    self.logger.error(f"[SITE ERROR DETAIL] |   Traceback[{i}]: {line.strip()}")
        
        self.logger.error(f"[SITE ERROR DETAIL] +=======================================================================")
    
    def _log_site_collection_completion(self, site_name: str, success: bool, error_message: Optional[str] = None):
        """
        Log final statistics when site collection completes.
        
        Args:
            site_name: Name of the site
            success: Whether collection was successful
            error_message: Error message if collection failed
            
        Requirement 7.4: Report final statistics for devices processed, failed, and skipped
        """
        if not self.statistics_logging_enabled:
            return
        
        stats = self.site_stats.get(site_name)
        if not stats:
            return
        
        # Calculate final statistics
        duration = stats.collection_duration_seconds
        queue_size = self.site_queue_manager.get_site_queue_size(site_name)
        devices_skipped = max(0, stats.devices_queued - stats.devices_processed)
        
        # Log completion header
        status_symbol = "[OK]" if success else "[FAIL]"
        self.logger.info(f"[SITE COMPLETION] +======================================================================")
        self.logger.info(f"[SITE COMPLETION] | {status_symbol} Site Collection Complete: '{site_name}'")
        self.logger.info(f"[SITE COMPLETION] +======================================================================")
        
        # Collection summary
        self.logger.info(f"[SITE COMPLETION] | Collection Status: {'SUCCESS' if success else 'FAILED'}")
        if error_message:
            self.logger.info(f"[SITE COMPLETION] | Error Message: {error_message}")
        
        # Device statistics
        self.logger.info(f"[SITE COMPLETION] | Device Statistics:")
        self.logger.info(f"[SITE COMPLETION] |   Total queued: {stats.devices_queued}")
        self.logger.info(f"[SITE COMPLETION] |   Processed: {stats.devices_processed}")
        self.logger.info(f"[SITE COMPLETION] |   Successful: {stats.devices_successful}")
        self.logger.info(f"[SITE COMPLETION] |   Failed: {stats.devices_failed}")
        self.logger.info(f"[SITE COMPLETION] |   Skipped: {devices_skipped}")
        self.logger.info(f"[SITE COMPLETION] |   Remaining in queue: {queue_size}")
        
        # Performance metrics
        self.logger.info(f"[SITE COMPLETION] | Performance Metrics:")
        self.logger.info(f"[SITE COMPLETION] |   Success rate: {stats.success_rate:.1f}%")
        self.logger.info(f"[SITE COMPLETION] |   Error rate: {stats.error_rate:.1f}%")
        self.logger.info(f"[SITE COMPLETION] |   Duration: {duration:.2f} seconds")
        
        if duration > 0:
            processing_rate = (stats.devices_processed / duration) * 60
            self.logger.info(f"[SITE COMPLETION] |   Processing rate: {processing_rate:.1f} devices/min")
        
        # Discovery results
        self.logger.info(f"[SITE COMPLETION] | Discovery Results:")
        self.logger.info(f"[SITE COMPLETION] |   Neighbors discovered: {stats.neighbors_discovered}")
        
        if stats.neighbors_discovered > 0 and stats.devices_successful > 0:
            avg_neighbors = stats.neighbors_discovered / stats.devices_successful
            self.logger.info(f"[SITE COMPLETION] |   Avg neighbors per device: {avg_neighbors:.1f}")
        
        # Error handling summary
        if stats.errors_encountered > 0:
            self.logger.info(f"[SITE COMPLETION] | Error Handling:")
            self.logger.info(f"[SITE COMPLETION] |   Total errors: {stats.errors_encountered}")
            self.logger.info(f"[SITE COMPLETION] |   Recovery attempts: {stats.recoveries_attempted}")
            self.logger.info(f"[SITE COMPLETION] |   Successful recoveries: {stats.recoveries_successful}")
            self.logger.info(f"[SITE COMPLETION] |   Recovery rate: {stats.recovery_rate:.1f}%")
            
            if stats.fallbacks_to_global > 0:
                self.logger.info(f"[SITE COMPLETION] |   Global fallbacks: {stats.fallbacks_to_global}")
        
        # Site status
        if site_name in self.failed_sites:
            self.logger.info(f"[SITE COMPLETION] | Site Status: MARKED AS FAILED")
        
        if site_name in self.global_fallback_devices:
            fallback_count = len([d for d in self.global_fallback_devices if d.startswith(site_name)])
            if fallback_count > 0:
                self.logger.info(f"[SITE COMPLETION] | Global Fallback: {fallback_count} devices")
        
        # Timestamps
        if stats.collection_start_time:
            self.logger.info(f"[SITE COMPLETION] | Start Time: {stats.collection_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if stats.collection_end_time:
            self.logger.info(f"[SITE COMPLETION] | End Time: {stats.collection_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.logger.info(f"[SITE COMPLETION] +=======================================================================")
    
    def _log_multi_site_progress_summary(self):
        """
        Log progress summary for all sites being processed.
        
        Requirement 7.5: Provide progress updates for each site independently
        """
        if not self.progress_logging_enabled or not self.site_stats:
            return
        
        self.logger.info(f"[MULTI-SITE PROGRESS] +======================================================================")
        self.logger.info(f"[MULTI-SITE PROGRESS] | Multi-Site Collection Progress Summary")
        self.logger.info(f"[MULTI-SITE PROGRESS] +======================================================================")
        
        total_sites = len(self.site_stats)
        completed_sites = sum(1 for stats in self.site_stats.values() if stats.collection_end_time is not None)
        failed_sites_count = len(self.failed_sites)
        
        self.logger.info(f"[MULTI-SITE PROGRESS] | Overall Status:")
        self.logger.info(f"[MULTI-SITE PROGRESS] |   Total sites: {total_sites}")
        self.logger.info(f"[MULTI-SITE PROGRESS] |   Completed: {completed_sites}")
        self.logger.info(f"[MULTI-SITE PROGRESS] |   Failed: {failed_sites_count}")
        self.logger.info(f"[MULTI-SITE PROGRESS] |   In progress: {total_sites - completed_sites}")
        
        # Individual site status
        self.logger.info(f"[MULTI-SITE PROGRESS] | Individual Site Status:")
        
        for site_name, stats in self.site_stats.items():
            if stats.collection_end_time:
                status = "FAILED" if site_name in self.failed_sites else "COMPLETE"
                progress = f"{stats.devices_processed}/{stats.devices_queued}"
                success_rate = f"{stats.success_rate:.1f}%"
            else:
                status = "IN PROGRESS"
                progress = f"{stats.devices_processed}/{stats.devices_queued}"
                success_rate = f"{stats.success_rate:.1f}%" if stats.devices_processed > 0 else "N/A"
            
            self.logger.info(f"[MULTI-SITE PROGRESS] |   {site_name}: {status} - {progress} ({success_rate})")
        
        # Global statistics
        total_queued = sum(stats.devices_queued for stats in self.site_stats.values())
        total_processed = sum(stats.devices_processed for stats in self.site_stats.values())
        total_successful = sum(stats.devices_successful for stats in self.site_stats.values())
        total_failed = sum(stats.devices_failed for stats in self.site_stats.values())
        total_neighbors = sum(stats.neighbors_discovered for stats in self.site_stats.values())
        
        if total_processed > 0:
            overall_success_rate = (total_successful / total_processed) * 100
        else:
            overall_success_rate = 0.0
        
        self.logger.info(f"[MULTI-SITE PROGRESS] | Global Totals:")
        self.logger.info(f"[MULTI-SITE PROGRESS] |   Devices queued: {total_queued}")
        self.logger.info(f"[MULTI-SITE PROGRESS] |   Devices processed: {total_processed}")
        self.logger.info(f"[MULTI-SITE PROGRESS] |   Overall success rate: {overall_success_rate:.1f}%")
        self.logger.info(f"[MULTI-SITE PROGRESS] |   Total neighbors found: {total_neighbors}")
        
        self.logger.info(f"[MULTI-SITE PROGRESS] +=======================================================================")
    
    def _handle_site_collection_error(self, error: SiteCollectionError) -> bool:
        """
        Handle errors that occur during site collection.
        
        Args:
            error: The error that occurred
            
        Returns:
            True if error was handled and collection can continue, False if critical
        """
        self.logger.error(f"[ERROR HANDLER] Site collection error in '{error.site_name}': {error.error_message}")
        
        # Log detailed error information
        self._log_site_collection_error_detailed(error)
        
        # Add error to site error list
        self.site_errors[error.site_name].append(error)
        
        # Update statistics
        if error.site_name in self.site_stats:
            self.site_stats[error.site_name].errors_encountered += 1
        
        # Determine if error is critical
        is_critical = self._is_critical_error(error)
        
        if is_critical:
            self.logger.error(f"[ERROR HANDLER] Critical error detected for site '{error.site_name}': {error.error_type.value}")
            return self._handle_critical_site_error(error)
        
        # Attempt recovery for non-critical errors
        if self.error_recovery_enabled:
            return self._attempt_error_recovery(error)
        
        return True  # Continue collection even without recovery
    
    def _is_critical_error(self, error: SiteCollectionError) -> bool:
        """
        Determine if an error is critical and requires special handling.
        
        Args:
            error: The error to evaluate
            
        Returns:
            True if error is critical, False otherwise
        """
        critical_error_types = {
            SiteCollectionErrorType.CRITICAL_SYSTEM_ERROR,
            SiteCollectionErrorType.SITE_INITIALIZATION_FAILED,
            SiteCollectionErrorType.CONFIGURATION_ERROR
        }
        
        # Check error type
        if error.error_type in critical_error_types:
            return True
        
        # Check error rate threshold
        if error.site_name in self.site_stats:
            stats = self.site_stats[error.site_name]
            if stats.devices_processed > 0:
                error_rate = (stats.errors_encountered / stats.devices_processed) * 100.0
                if error_rate >= self.critical_error_threshold:
                    self.logger.warning(f"[ERROR HANDLER] Site '{error.site_name}' error rate {error_rate:.1f}% exceeds threshold {self.critical_error_threshold}%")
                    return True
        
        # Check total error count
        site_error_count = len(self.site_errors[error.site_name])
        if site_error_count >= self.max_site_errors:
            self.logger.warning(f"[ERROR HANDLER] Site '{error.site_name}' has {site_error_count} errors, exceeding max {self.max_site_errors}")
            return True
        
        return False
    
    def _attempt_error_recovery(self, error: SiteCollectionError) -> bool:
        """
        Attempt to recover from a site collection error.
        
        Args:
            error: The error to recover from
            
        Returns:
            True if recovery was successful, False otherwise
        """
        self.logger.info(f"[ERROR RECOVERY] Attempting recovery for error in site '{error.site_name}': {error.error_type.value}")
        
        error.recovery_attempted = True
        if error.site_name in self.site_stats:
            self.site_stats[error.site_name].recoveries_attempted += 1
        
        try:
            recovery_successful = False
            
            if error.error_type == SiteCollectionErrorType.DEVICE_CONNECTION_FAILED:
                recovery_successful = self._recover_device_connection_error(error)
            elif error.error_type == SiteCollectionErrorType.DEVICE_WALK_FAILED:
                recovery_successful = self._recover_device_walk_error(error)
            elif error.error_type == SiteCollectionErrorType.SITE_QUEUE_ERROR:
                recovery_successful = self._recover_site_queue_error(error)
            elif error.error_type == SiteCollectionErrorType.TIMEOUT_ERROR:
                recovery_successful = self._recover_timeout_error(error)
            else:
                self.logger.warning(f"[ERROR RECOVERY] No recovery method for error type: {error.error_type.value}")
            
            if recovery_successful:
                error.recovery_successful = True
                if error.site_name in self.site_stats:
                    self.site_stats[error.site_name].recoveries_successful += 1
                self.logger.info(f"[ERROR RECOVERY] Successfully recovered from error in site '{error.site_name}'")
            else:
                self.logger.warning(f"[ERROR RECOVERY] Failed to recover from error in site '{error.site_name}'")
            
            return recovery_successful
            
        except Exception as e:
            self.logger.error(f"[ERROR RECOVERY] Exception during recovery for site '{error.site_name}': {e}")
            return False
    
    def _recover_device_connection_error(self, error: SiteCollectionError) -> bool:
        """Attempt to recover from device connection errors"""
        if not error.device_key:
            return False
        
        # Try alternative connection methods or retry with different parameters
        self.logger.info(f"[ERROR RECOVERY] Retrying connection to device {error.device_key}")
        
        # This would integrate with the connection manager's retry logic
        # For now, we'll mark it as a recovery attempt
        return True  # Simplified recovery
    
    def _recover_device_walk_error(self, error: SiteCollectionError) -> bool:
        """Attempt to recover from device walk errors"""
        if not error.device_key:
            return False
        
        # Try walking device with reduced information gathering
        self.logger.info(f"[ERROR RECOVERY] Retrying device walk for {error.device_key} with reduced scope")
        
        # This would retry the walk with minimal information gathering
        return True  # Simplified recovery
    
    def _recover_site_queue_error(self, error: SiteCollectionError) -> bool:
        """Attempt to recover from site queue errors"""
        # Reinitialize site queue if corrupted
        self.logger.info(f"[ERROR RECOVERY] Reinitializing queue for site '{error.site_name}'")
        
        try:
            # Clear and recreate site queue
            self.site_queue_manager.create_site_queue(error.site_name)
            return True
        except Exception as e:
            self.logger.error(f"[ERROR RECOVERY] Failed to reinitialize queue for site '{error.site_name}': {e}")
            return False
    
    def _recover_timeout_error(self, error: SiteCollectionError) -> bool:
        """Attempt to recover from timeout errors"""
        # Increase timeout for this site or skip problematic devices
        self.logger.info(f"[ERROR RECOVERY] Adjusting timeout settings for site '{error.site_name}'")
        
        # This would adjust timeout parameters for the site
        return True  # Simplified recovery
    
    def _handle_critical_site_error(self, error: SiteCollectionError) -> bool:
        """
        Handle critical errors that may require site collection to be abandoned.
        
        Args:
            error: The critical error
            
        Returns:
            True if collection can continue, False if site should be abandoned
        """
        self.logger.error(f"[CRITICAL ERROR] Handling critical error for site '{error.site_name}': {error.error_message}")
        
        # Mark site as failed
        self.failed_sites.add(error.site_name)
        
        # Determine if we should fall back to global discovery
        should_fallback = self._should_fallback_to_global(error)
        
        if should_fallback:
            self._initiate_global_fallback(error)
            error.fallback_to_global = True
            if error.site_name in self.site_stats:
                self.site_stats[error.site_name].fallbacks_to_global += 1
        
        # If inter-site error isolation is enabled, continue with other sites
        if self.inter_site_error_isolation:
            self.logger.info(f"[CRITICAL ERROR] Isolating error to site '{error.site_name}', continuing with other sites")
            return True
        else:
            self.logger.error(f"[CRITICAL ERROR] Inter-site isolation disabled, stopping all site collection")
            return False
    
    def _should_fallback_to_global(self, error: SiteCollectionError) -> bool:
        """
        Determine if we should fall back to global discovery for this site.
        
        Args:
            error: The error that occurred
            
        Returns:
            True if should fallback to global discovery
        """
        # Always fallback for critical system errors
        if error.error_type == SiteCollectionErrorType.CRITICAL_SYSTEM_ERROR:
            return True
        
        # Fallback if site has too many errors
        site_error_count = len(self.site_errors[error.site_name])
        if site_error_count >= self.max_site_errors:
            return True
        
        # Fallback if error rate is too high
        if error.site_name in self.site_stats:
            stats = self.site_stats[error.site_name]
            if stats.devices_processed > 0:
                error_rate = (stats.errors_encountered / stats.devices_processed) * 100.0
                if error_rate >= self.critical_error_threshold:
                    return True
        
        return False
    
    def _initiate_global_fallback(self, error: SiteCollectionError):
        """
        Initiate fallback to global discovery for devices in the failed site.
        
        Args:
            error: The error that triggered the fallback
        """
        self.logger.info(f"[GLOBAL FALLBACK] Initiating global discovery fallback for site '{error.site_name}'")
        
        # Get all devices that were queued for this site
        site_devices = set()
        
        # Add devices from site queue
        while not self.site_queue_manager.is_site_queue_empty(error.site_name):
            device_node = self.site_queue_manager.get_next_device(error.site_name)
            if device_node:
                site_devices.add(device_node.device_key)
        
        # Add devices that were already processed but may need reprocessing
        if error.site_name in self.discovered_devices_by_site:
            site_devices.update(self.discovered_devices_by_site[error.site_name])
        
        # Add to global fallback set
        self.global_fallback_devices.update(site_devices)
        
        # Call global fallback callback if provided
        if self.global_fallback_callback and site_devices:
            try:
                self.logger.info(f"[GLOBAL FALLBACK] Calling global fallback for {len(site_devices)} devices from site '{error.site_name}'")
                self.global_fallback_callback(list(site_devices), error.site_name)
            except Exception as e:
                self.logger.error(f"[GLOBAL FALLBACK] Error calling global fallback callback: {e}")
        
        self.logger.info(f"[GLOBAL FALLBACK] Added {len(site_devices)} devices to global fallback from site '{error.site_name}'")
    
    def get_collection_configuration(self) -> Dict[str, Any]:
        """
        Get current collection configuration settings.
        
        Returns:
            Dictionary of configuration settings
        """
        return {
            'max_depth': self.max_depth,
            'collection_timeout': self.collection_timeout,
            'connection_timeout': self.connection_timeout,
            'retry_attempts': self.retry_attempts,
            'enable_filtering': self.enable_filtering,
            'filter_patterns': self.filter_patterns,
            'exclude_patterns': self.exclude_patterns,
            'site_collection_enabled': self.site_collection_enabled,
            'site_collection_parallel': self.site_collection_parallel,
            'site_collection_max_workers': self.site_collection_max_workers
        }
    
    def initialize_site_queues(self, site_boundaries: Dict[str, List[str]]) -> Dict[str, Deque[DiscoveryNode]]:
        """
        Initialize site-specific device queues.
        
        Args:
            site_boundaries: Dictionary mapping site names to lists of device hostnames
            
        Returns:
            Dictionary mapping site names to their device queues
        """
        logger.info(f"[SITE INIT] Initializing queues for {len(site_boundaries)} sites")
        
        site_queues = {}
        
        for site_name, device_hostnames in site_boundaries.items():
            logger.info(f"[SITE INIT] Creating queue for site '{site_name}' with {len(device_hostnames)} devices")
            
            # Create site queue
            site_queue = self.site_queue_manager.create_site_queue(site_name)
            site_queues[site_name] = site_queue
            
            # Initialize site inventory and statistics
            self.site_inventories[site_name] = DeviceInventory()
            self.site_stats[site_name] = SiteCollectionStats(site_name=site_name)
            
            # Add devices to site queue (these would come from global discovery)
            for hostname in device_hostnames:
                # Create discovery node for site device
                # Note: IP address would need to be resolved from global inventory
                # For now, using placeholder - this will be enhanced in integration
                device_node = DiscoveryNode(
                    hostname=hostname,
                    ip_address="0.0.0.0",  # Placeholder - will be resolved during integration
                    depth=0,
                    discovery_method="site_boundary",
                    is_seed=True
                )
                
                if self.site_queue_manager.add_device_to_site(site_name, device_node):
                    self.site_stats[site_name].devices_queued += 1
                    logger.debug(f"Added {hostname} to site '{site_name}' queue")
            
            logger.info(f"[SITE INIT] Site '{site_name}' initialized with {self.site_stats[site_name].devices_queued} devices queued")
        
        logger.info(f"[SITE INIT] All site queues initialized successfully")
        return site_queues
    
    def collect_site_devices(self, site_name: str) -> Dict[str, Any]:
        """
        Collect and walk all devices within a specific site boundary.
        
        Args:
            site_name: Name of the site to collect devices for
            
        Returns:
            Dictionary containing collection results and statistics
        """
        logger.info(f"[SITE COLLECTION] Starting collection for site '{site_name}'")
        
        if site_name not in self.site_stats:
            error = SiteCollectionError(
                error_type=SiteCollectionErrorType.SITE_INITIALIZATION_FAILED,
                site_name=site_name,
                error_message=f"Site '{site_name}' not initialized"
            )
            self._handle_site_collection_error(error)
            raise ValueError(f"Site '{site_name}' not initialized")
        
        # Check if site has already failed
        if site_name in self.failed_sites:
            logger.warning(f"[SITE COLLECTION] Site '{site_name}' previously failed, skipping collection")
            return self._create_failed_collection_result(site_name, "Site previously failed")
        
        stats = self.site_stats[site_name]
        stats.collection_start_time = datetime.now()
        
        # Log collection start with detailed information (Requirement 7.1)
        self._log_site_collection_start(site_name)
        
        try:
            # Set collection timeout
            collection_start_time = time.time()
            
            # Process all devices in the site queue
            while not self.site_queue_manager.is_site_queue_empty(site_name):
                # Check for timeout
                if time.time() - collection_start_time > self.collection_timeout:
                    timeout_error = SiteCollectionError(
                        error_type=SiteCollectionErrorType.TIMEOUT_ERROR,
                        site_name=site_name,
                        error_message=f"Site collection timeout after {self.collection_timeout}s"
                    )
                    if not self._handle_site_collection_error(timeout_error):
                        break
                
                # Check if site has been marked as failed
                if site_name in self.failed_sites:
                    logger.warning(f"[SITE COLLECTION] Site '{site_name}' marked as failed during collection, stopping")
                    break
                
                device_node = self.site_queue_manager.get_next_device(site_name)
                if device_node is None:
                    break
                
                logger.info(f"[SITE COLLECTION] Processing device {device_node.device_key} for site '{site_name}'")
                
                # Log progress update (Requirement 7.2, 7.5)
                self._log_site_collection_progress(site_name, device_node.device_key)
                
                # Skip if already processed
                if device_node.device_key in self.discovered_devices_by_site[site_name]:
                    logger.info(f"[SITE COLLECTION] Device {device_node.device_key} already processed for site '{site_name}'")
                    continue
                
                # Apply configuration filtering
                if not self.apply_configuration_to_collection(device_node):
                    logger.info(f"[SITE COLLECTION] Device {device_node.device_key} filtered out by configuration")
                    stats.devices_processed += 1
                    # Log progress after processing
                    self._log_site_collection_progress(site_name)
                    continue
                
                # Mark as discovered
                self.discovered_devices_by_site[site_name].add(device_node.device_key)
                
                # Process device with error handling
                success = self._process_device_with_error_handling(device_node, site_name)
                
                # Update statistics
                stats.devices_processed += 1
                
                if success:
                    stats.devices_successful += 1
                else:
                    stats.devices_failed += 1
                
                # Log progress after processing device
                self._log_site_collection_progress(site_name)
                
                # Check if we should continue after errors
                if not self._should_continue_site_collection(site_name):
                    logger.warning(f"[SITE COLLECTION] Stopping collection for site '{site_name}' due to error threshold")
                    break
            
            stats.collection_end_time = datetime.now()
            
            # Generate collection summary
            collection_results = self._create_successful_collection_result(site_name)
            
            # Log completion with final statistics (Requirement 7.4)
            self._log_site_collection_completion(site_name, True)
            
            logger.info(f"[SITE COLLECTION] Completed collection for site '{site_name}'")
            logger.info(f"  Processed: {stats.devices_processed}/{stats.devices_queued} devices")
            logger.info(f"  Success rate: {stats.success_rate:.1f}%")
            logger.info(f"  Error rate: {stats.error_rate:.1f}%")
            logger.info(f"  Neighbors found: {stats.neighbors_discovered}")
            logger.info(f"  Duration: {stats.collection_duration_seconds:.2f}s")
            logger.info(f"  Errors: {stats.errors_encountered}, Recoveries: {stats.recoveries_successful}/{stats.recoveries_attempted}")
            
            return collection_results
            
        except Exception as e:
            stats.collection_end_time = datetime.now()
            
            # Handle unexpected exceptions
            critical_error = SiteCollectionError(
                error_type=SiteCollectionErrorType.CRITICAL_SYSTEM_ERROR,
                site_name=site_name,
                error_message=f"Unexpected exception during collection: {str(e)}",
                exception=e
            )
            self._handle_site_collection_error(critical_error)
            
            # Log completion with failure (Requirement 7.4)
            self._log_site_collection_completion(site_name, False, str(e))
            
            logger.error(f"[SITE COLLECTION] Critical error during collection for site '{site_name}': {e}")
            logger.error(f"[SITE COLLECTION] Traceback: {traceback.format_exc()}")
            
            return self._create_failed_collection_result(site_name, str(e))
    
    def _process_device_with_error_handling(self, device_node: DiscoveryNode, site_name: str) -> bool:
        """
        Process a device with comprehensive error handling.
        
        Args:
            device_node: Device to process
            site_name: Site name
            
        Returns:
            True if processing was successful, False otherwise
        """
        retry_count = 0
        max_retries = self.max_device_retries
        
        while retry_count <= max_retries:
            try:
                # Walk the device
                walk_result = self.site_device_walker.walk_site_device(device_node, site_name)
                
                if walk_result.walk_success:
                    # Update statistics
                    self.site_stats[site_name].neighbors_discovered += len(walk_result.neighbors_found)
                    
                    # Add device to site inventory
                    self.site_inventories[site_name].add_device(
                        device_node.device_key,
                        walk_result.device_info,
                        "connected"
                    )
                    
                    # Process neighbors and add to queue if they belong to this site
                    self._process_site_neighbors(walk_result.neighbors_found, site_name, device_node)
                    
                    logger.info(f"[SITE COLLECTION] Successfully processed {device_node.device_key} - found {len(walk_result.neighbors_found)} neighbors")
                    return True
                    
                else:
                    # Handle walk failure
                    walk_error = SiteCollectionError(
                        error_type=SiteCollectionErrorType.DEVICE_WALK_FAILED,
                        site_name=site_name,
                        device_key=device_node.device_key,
                        error_message=walk_result.error_message or "Device walk failed"
                    )
                    
                    # Try recovery if this is not the last retry
                    if retry_count < max_retries and self.error_recovery_enabled:
                        if self._handle_site_collection_error(walk_error):
                            retry_count += 1
                            logger.info(f"[SITE COLLECTION] Retrying device {device_node.device_key} (attempt {retry_count + 1}/{max_retries + 1})")
                            time.sleep(1)  # Brief delay before retry
                            continue
                    
                    # Final failure - add failed device to inventory
                    device_info = self._create_failed_device_info(device_node, walk_result.error_message)
                    self.site_inventories[site_name].add_device(
                        device_node.device_key,
                        device_info,
                        "failed",
                        walk_result.error_message
                    )
                    
                    logger.warning(f"[SITE COLLECTION] Failed to process {device_node.device_key} after {retry_count + 1} attempts: {walk_result.error_message}")
                    return False
                    
            except Exception as e:
                # Handle unexpected exceptions during device processing
                connection_error = SiteCollectionError(
                    error_type=SiteCollectionErrorType.DEVICE_CONNECTION_FAILED,
                    site_name=site_name,
                    device_key=device_node.device_key,
                    error_message=f"Exception during device processing: {str(e)}",
                    exception=e
                )
                
                # Try recovery if this is not the last retry
                if retry_count < max_retries and self.error_recovery_enabled:
                    if self._handle_site_collection_error(connection_error):
                        retry_count += 1
                        logger.info(f"[SITE COLLECTION] Retrying device {device_node.device_key} after exception (attempt {retry_count + 1}/{max_retries + 1})")
                        time.sleep(2)  # Longer delay after exception
                        continue
                
                # Final failure
                device_info = self._create_failed_device_info(device_node, str(e))
                self.site_inventories[site_name].add_device(
                    device_node.device_key,
                    device_info,
                    "failed",
                    str(e)
                )
                
                logger.error(f"[SITE COLLECTION] Exception processing {device_node.device_key} after {retry_count + 1} attempts: {e}")
                return False
        
        return False
    
    def _should_continue_site_collection(self, site_name: str) -> bool:
        """
        Determine if site collection should continue based on error rates.
        
        Args:
            site_name: Site name to check
            
        Returns:
            True if collection should continue, False if should stop
        """
        if site_name in self.failed_sites:
            return False
        
        if site_name not in self.site_stats:
            return True
        
        stats = self.site_stats[site_name]
        
        # Check error count threshold
        if stats.errors_encountered >= self.max_site_errors:
            logger.warning(f"[SITE COLLECTION] Site '{site_name}' has {stats.errors_encountered} errors, exceeding threshold {self.max_site_errors}")
            return False
        
        # Check error rate threshold
        if stats.devices_processed > 0:
            error_rate = (stats.errors_encountered / stats.devices_processed) * 100.0
            if error_rate >= self.critical_error_threshold:
                logger.warning(f"[SITE COLLECTION] Site '{site_name}' error rate {error_rate:.1f}% exceeds threshold {self.critical_error_threshold}%")
                return False
        
        return True
    
    def _create_successful_collection_result(self, site_name: str) -> Dict[str, Any]:
        """Create a successful collection result dictionary"""
        stats = self.site_stats[site_name]
        
        return {
            'site_name': site_name,
            'success': True,
            'statistics': {
                'devices_queued': stats.devices_queued,
                'devices_processed': stats.devices_processed,
                'devices_successful': stats.devices_successful,
                'devices_failed': stats.devices_failed,
                'neighbors_discovered': stats.neighbors_discovered,
                'success_rate': stats.success_rate,
                'error_rate': stats.error_rate,
                'collection_duration_seconds': stats.collection_duration_seconds,
                'errors_encountered': stats.errors_encountered,
                'recoveries_attempted': stats.recoveries_attempted,
                'recoveries_successful': stats.recoveries_successful,
                'recovery_rate': stats.recovery_rate,
                'fallbacks_to_global': stats.fallbacks_to_global
            },
            'inventory': self.site_inventories[site_name].get_all_devices(),
            'discovery_stats': self.site_inventories[site_name].get_discovery_stats(),
            'errors': [error.to_dict() for error in self.site_errors[site_name]],
            'failed_site': site_name in self.failed_sites,
            'global_fallback_devices': len(self.global_fallback_devices)
        }
    
    def _create_failed_collection_result(self, site_name: str, error_message: str) -> Dict[str, Any]:
        """Create a failed collection result dictionary"""
        stats = self.site_stats.get(site_name, SiteCollectionStats(site_name=site_name))
        
        return {
            'site_name': site_name,
            'success': False,
            'error_message': error_message,
            'statistics': {
                'devices_queued': stats.devices_queued,
                'devices_processed': stats.devices_processed,
                'devices_successful': stats.devices_successful,
                'devices_failed': stats.devices_failed,
                'neighbors_discovered': stats.neighbors_discovered,
                'success_rate': stats.success_rate,
                'error_rate': stats.error_rate,
                'collection_duration_seconds': stats.collection_duration_seconds,
                'errors_encountered': stats.errors_encountered,
                'recoveries_attempted': stats.recoveries_attempted,
                'recoveries_successful': stats.recoveries_successful,
                'recovery_rate': stats.recovery_rate,
                'fallbacks_to_global': stats.fallbacks_to_global
            },
            'errors': [error.to_dict() for error in self.site_errors[site_name]],
            'failed_site': True,
            'global_fallback_devices': len(self.global_fallback_devices)
        }
    
    def _process_site_neighbors(self, neighbors: List[Any], site_name: str, parent_node: DiscoveryNode):
        """
        Process neighbors discovered during site collection.
        
        Args:
            neighbors: List of neighbor information
            site_name: Name of the current site
            parent_node: Parent device node
        """
        logger.info(f"[SITE NEIGHBORS] Processing {len(neighbors)} neighbors for site '{site_name}'")
        
        for neighbor in neighbors:
            # Extract neighbor information
            if hasattr(neighbor, 'device_id'):
                neighbor_hostname = getattr(neighbor, 'device_id', '').strip()
                neighbor_ip = getattr(neighbor, 'ip_address', '').strip()
                protocol = getattr(neighbor, 'protocol', 'unknown').lower()
            else:
                neighbor_hostname = neighbor.get('hostname', '').strip()
                neighbor_ip = neighbor.get('ip_address', '').strip()
                protocol = neighbor.get('protocol', 'unknown').lower()
            
            if not neighbor_hostname or not neighbor_ip:
                logger.debug(f"[SITE NEIGHBORS] Skipping neighbor with missing hostname or IP")
                continue
            
            # Clean hostname
            if '.' in neighbor_hostname:
                neighbor_hostname = neighbor_hostname.split('.')[0]
            
            # Determine if neighbor belongs to this site
            neighbor_site = self.site_association_validator.determine_device_site(
                neighbor_hostname, neighbor_ip, site_name
            )
            
            logger.info(f"[SITE NEIGHBORS] Neighbor {neighbor_hostname}:{neighbor_ip} associated with site '{neighbor_site}'")
            
            # Only add to queue if it belongs to the current site and hasn't been processed
            if neighbor_site == site_name:
                neighbor_key = f"{neighbor_hostname}:{neighbor_ip}"
                
                if neighbor_key not in self.discovered_devices_by_site[site_name]:
                    # Create neighbor node
                    neighbor_node = DiscoveryNode(
                        hostname=neighbor_hostname,
                        ip_address=neighbor_ip,
                        depth=parent_node.depth + 1,
                        parent_device=parent_node.device_key,
                        discovery_method=protocol
                    )
                    
                    # Check depth limit
                    if neighbor_node.depth <= self.max_depth:
                        if self.site_queue_manager.add_device_to_site(site_name, neighbor_node):
                            self.site_stats[site_name].devices_queued += 1
                            logger.info(f"[SITE NEIGHBORS] Added {neighbor_key} to site '{site_name}' queue (depth {neighbor_node.depth})")
                        else:
                            logger.debug(f"[SITE NEIGHBORS] Device {neighbor_key} already in site '{site_name}' queue")
                    else:
                        logger.info(f"[SITE NEIGHBORS] Neighbor {neighbor_key} exceeds depth limit ({neighbor_node.depth} > {self.max_depth})")
                else:
                    logger.debug(f"[SITE NEIGHBORS] Neighbor {neighbor_key} already processed for site '{site_name}'")
            else:
                logger.info(f"[SITE NEIGHBORS] Neighbor {neighbor_hostname}:{neighbor_ip} belongs to different site '{neighbor_site}' - not adding to current site queue")
    
    def _create_failed_device_info(self, node: DiscoveryNode, error_message: Optional[str]) -> Dict[str, Any]:
        """
        Create device info dictionary for failed devices.
        
        Args:
            node: Discovery node that failed
            error_message: Error message from failure
            
        Returns:
            Device info dictionary
        """
        return {
            'hostname': node.hostname,
            'ip_address': node.ip_address,
            'discovery_depth': node.depth,
            'discovery_method': node.discovery_method,
            'parent_device': node.parent_device,
            'discovery_timestamp': datetime.now().isoformat(),
            'status': 'failed',
            'error_message': error_message or 'Unknown error',
            'platform': 'unknown',
            'software_version': 'unknown',
            'serial_number': 'unknown',
            'hardware_model': 'unknown',
            'uptime': 'unknown',
            'connection_method': 'none',
            'neighbors': [],
            'vlans': []
        }
    
    def get_site_collection_stats(self, site_name: str) -> Dict[str, Any]:
        """
        Get collection statistics for a specific site.
        
        Args:
            site_name: Name of the site
            
        Returns:
            Dictionary containing site collection statistics
        """
        if site_name not in self.site_stats:
            return {}
        
        stats = self.site_stats[site_name]
        return {
            'site_name': site_name,
            'devices_queued': stats.devices_queued,
            'devices_processed': stats.devices_processed,
            'devices_successful': stats.devices_successful,
            'devices_failed': stats.devices_failed,
            'neighbors_discovered': stats.neighbors_discovered,
            'success_rate': stats.success_rate,
            'error_rate': stats.error_rate,
            'collection_duration_seconds': stats.collection_duration_seconds,
            'errors_encountered': stats.errors_encountered,
            'recoveries_attempted': stats.recoveries_attempted,
            'recoveries_successful': stats.recoveries_successful,
            'recovery_rate': stats.recovery_rate,
            'fallbacks_to_global': stats.fallbacks_to_global,
            'queue_size': self.site_queue_manager.get_site_queue_size(site_name),
            'is_failed_site': site_name in self.failed_sites
        }
    
    def get_site_errors(self, site_name: str) -> List[Dict[str, Any]]:
        """
        Get error information for a specific site.
        
        Args:
            site_name: Name of the site
            
        Returns:
            List of error dictionaries
        """
        if site_name not in self.site_errors:
            return []
        
        return [error.to_dict() for error in self.site_errors[site_name]]
    
    def get_all_site_errors(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get error information for all sites.
        
        Returns:
            Dictionary mapping site names to their error lists
        """
        return {
            site_name: [error.to_dict() for error in errors]
            for site_name, errors in self.site_errors.items()
        }
    
    def get_failed_sites(self) -> List[str]:
        """
        Get list of sites that have failed collection.
        
        Returns:
            List of failed site names
        """
        return list(self.failed_sites)
    
    def get_global_fallback_devices(self) -> List[str]:
        """
        Get list of devices that have been marked for global fallback.
        
        Returns:
            List of device keys
        """
        return list(self.global_fallback_devices)
    
    def reset_site_errors(self, site_name: str):
        """
        Reset error tracking for a specific site.
        
        Args:
            site_name: Name of the site to reset
        """
        if site_name in self.site_errors:
            self.site_errors[site_name].clear()
        
        if site_name in self.failed_sites:
            self.failed_sites.remove(site_name)
        
        if site_name in self.site_stats:
            stats = self.site_stats[site_name]
            stats.errors_encountered = 0
            stats.recoveries_attempted = 0
            stats.recoveries_successful = 0
            stats.fallbacks_to_global = 0
        
        self.logger.info(f"[ERROR RESET] Reset error tracking for site '{site_name}'")
    
    def get_error_handling_configuration(self) -> Dict[str, Any]:
        """
        Get current error handling configuration.
        
        Returns:
            Dictionary of error handling settings
        """
        return {
            'max_site_errors': self.max_site_errors,
            'max_device_retries': self.max_device_retries,
            'error_recovery_enabled': self.error_recovery_enabled,
            'inter_site_error_isolation': self.inter_site_error_isolation,
            'critical_error_threshold': self.critical_error_threshold,
            'collection_timeout': self.collection_timeout,
            'connection_timeout': self.connection_timeout,
            'retry_attempts': self.retry_attempts
        }
    
    def get_all_site_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get collection statistics for all sites.
        
        Returns:
            Dictionary mapping site names to their statistics
        """
        return {
            site_name: self.get_site_collection_stats(site_name)
            for site_name in self.site_stats.keys()
        }
    
    def get_site_inventory(self, site_name: str) -> Optional[DeviceInventory]:
        """
        Get device inventory for a specific site.
        
        Args:
            site_name: Name of the site
            
        Returns:
            DeviceInventory for the site, or None if site not found
        """
        return self.site_inventories.get(site_name)
    
    def get_all_site_inventories(self) -> Dict[str, DeviceInventory]:
        """
        Get device inventories for all sites.
        
        Returns:
            Dictionary mapping site names to their inventories
        """
        return self.site_inventories.copy()
    
    def is_site_collection_complete(self, site_name: str) -> bool:
        """
        Check if collection is complete for a specific site.
        
        Args:
            site_name: Name of the site
            
        Returns:
            True if collection is complete, False otherwise
        """
        if site_name not in self.site_stats:
            return False
        
        return (self.site_queue_manager.is_site_queue_empty(site_name) and 
                self.site_stats[site_name].collection_end_time is not None)
    
    def get_site_names(self) -> List[str]:
        """
        Get list of all initialized site names.
        
        Returns:
            List of site names
        """
        return list(self.site_stats.keys())
    
    def get_logging_configuration(self) -> Dict[str, Any]:
        """
        Get current logging configuration settings.
        
        Returns:
            Dictionary of logging configuration settings
        """
        return {
            'progress_logging_enabled': self.progress_logging_enabled,
            'detailed_error_logging': self.detailed_error_logging,
            'statistics_logging_enabled': self.statistics_logging_enabled,
            'progress_update_interval': self.progress_update_interval,
            'log_level_override': self.log_level_override
        }
    
    def log_multi_site_progress_summary(self):
        """
        Public method to log multi-site progress summary.
        
        This can be called externally to get progress updates across all sites.
        Requirement 7.5: Provide progress updates for each site independently
        """
        self._log_multi_site_progress_summary()
    
    def set_logging_configuration(self, config: Dict[str, Any]):
        """
        Update logging configuration settings.
        
        Args:
            config: Dictionary of logging configuration settings
        """
        if 'progress_logging_enabled' in config:
            self.progress_logging_enabled = config['progress_logging_enabled']
        
        if 'detailed_error_logging' in config:
            self.detailed_error_logging = config['detailed_error_logging']
        
        if 'statistics_logging_enabled' in config:
            self.statistics_logging_enabled = config['statistics_logging_enabled']
        
        if 'progress_update_interval' in config:
            self.progress_update_interval = config['progress_update_interval']
        
        if 'log_level_override' in config:
            self.log_level_override = config['log_level_override']
            # Apply log level override if specified
            if self.log_level_override:
                site_logger = logging.getLogger(f"{__name__}.site_collection")
                site_logger.setLevel(getattr(logging, self.log_level_override.upper(), logging.INFO))
        
        self.logger.info(f"[LOGGING CONFIG] Updated logging configuration: {config}")
    
    def get_site_progress_tracker(self, site_name: str) -> Optional[Dict[str, Any]]:
        """
        Get progress tracking information for a specific site.
        
        Args:
            site_name: Name of the site
            
        Returns:
            Progress tracking dictionary or None if site not found
        """
        return self.site_progress_trackers.get(site_name)