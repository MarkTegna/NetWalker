"""
Site Statistics Calculator for NetWalker

Calculates accurate statistics for site-specific reporting to ensure
site workbooks contain correct device counts and connection statistics.
"""

import logging
from typing import Dict, List, Set, Any, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SiteStatistics:
    """Comprehensive statistics for a site"""
    site_name: str
    total_devices: int = 0
    connected_devices: int = 0
    failed_devices: int = 0
    filtered_devices: int = 0
    boundary_devices: int = 0
    
    # Connection statistics
    total_connections: int = 0
    intra_site_connections: int = 0
    external_connections: int = 0
    
    # Discovery statistics
    discovery_success_rate: float = 0.0
    average_discovery_depth: float = 0.0
    total_neighbors_discovered: int = 0
    
    # Collection statistics
    devices_processed: int = 0
    collection_duration_seconds: float = 0.0
    
    # Platform breakdown
    platform_counts: Dict[str, int] = None
    
    def __post_init__(self):
        if self.platform_counts is None:
            self.platform_counts = {}


class SiteStatisticsCalculator:
    """
    Calculates accurate statistics for site-specific reporting.
    
    This calculator ensures that site workbooks contain correct device counts,
    connection statistics, and discovery metrics specific to each site boundary.
    """
    
    def __init__(self):
        """Initialize SiteStatisticsCalculator"""
        self.logger = logging.getLogger(__name__)
        
        # Cache for calculated statistics
        self._statistics_cache: Dict[str, SiteStatistics] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        logger.info("SiteStatisticsCalculator initialized")
    
    def calculate_site_device_counts(self, site_inventory: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate device counts specific to a site.
        
        Args:
            site_inventory: Site-specific device inventory
            
        Returns:
            Dictionary with device count statistics
        """
        logger.info(f"Calculating device counts for site inventory with {len(site_inventory)} devices")
        
        counts = {
            'total_devices': 0,
            'connected_devices': 0,
            'failed_devices': 0,
            'filtered_devices': 0,
            'boundary_devices': 0,
            'seed_devices': 0
        }
        
        for device_key, device_info in site_inventory.items():
            counts['total_devices'] += 1
            
            # Count by connection status
            status = device_info.get('status', 'unknown')
            connection_status = device_info.get('connection_status', 'unknown')
            
            if status == 'connected' or connection_status == 'connected':
                counts['connected_devices'] += 1
            elif status == 'failed' or connection_status == 'failed':
                counts['failed_devices'] += 1
            elif status == 'filtered':
                counts['filtered_devices'] += 1
            elif status == 'boundary':
                counts['boundary_devices'] += 1
            
            # Count seed devices
            if device_info.get('is_seed', False) or device_info.get('discovery_method') == 'seed':
                counts['seed_devices'] += 1
        
        logger.info(f"Device counts calculated: {counts}")
        return counts
    
    def calculate_site_connection_counts(self, site_inventory: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate connection counts specific to a site.
        
        Args:
            site_inventory: Site-specific device inventory
            
        Returns:
            Dictionary with connection count statistics
        """
        logger.info(f"Calculating connection counts for site inventory with {len(site_inventory)} devices")
        
        connection_counts = {
            'total_connections': 0,
            'intra_site_connections': 0,
            'external_connections': 0,
            'unique_neighbors': 0
        }
        
        # Track unique connections to avoid double counting
        unique_connections = set()
        all_neighbors = set()
        site_device_hostnames = set()
        
        # Build set of site device hostnames for intra-site detection
        for device_key, device_info in site_inventory.items():
            hostname = device_info.get('hostname', '')
            if hostname:
                site_device_hostnames.add(hostname.upper())
        
        # Count connections from each device
        for device_key, device_info in site_inventory.items():
            device_hostname = device_info.get('hostname', '').upper()
            neighbors = device_info.get('neighbors', [])
            
            for neighbor in neighbors:
                # Extract neighbor information
                neighbor_hostname = ''
                neighbor_ip = ''
                
                if hasattr(neighbor, 'hostname'):
                    neighbor_hostname = getattr(neighbor, 'hostname', '').upper()
                    neighbor_ip = getattr(neighbor, 'ip_address', '')
                elif isinstance(neighbor, dict):
                    neighbor_hostname = neighbor.get('hostname', '').upper()
                    neighbor_ip = neighbor.get('ip_address', '')
                
                if not neighbor_hostname and not neighbor_ip:
                    continue
                
                # Clean neighbor hostname
                if '.' in neighbor_hostname:
                    neighbor_hostname = neighbor_hostname.split('.')[0]
                
                # Create connection identifier (bidirectional)
                connection_id = tuple(sorted([device_hostname, neighbor_hostname]))
                
                if connection_id not in unique_connections:
                    unique_connections.add(connection_id)
                    connection_counts['total_connections'] += 1
                    
                    # Determine if connection is intra-site or external
                    if neighbor_hostname in site_device_hostnames:
                        connection_counts['intra_site_connections'] += 1
                    else:
                        connection_counts['external_connections'] += 1
                
                # Track unique neighbors
                if neighbor_hostname:
                    all_neighbors.add(neighbor_hostname)
        
        connection_counts['unique_neighbors'] = len(all_neighbors)
        
        logger.info(f"Connection counts calculated: {connection_counts}")
        return connection_counts
    
    def calculate_site_discovery_stats(self, site_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate discovery statistics for a site.
        
        Args:
            site_collection_results: Results from site collection process
            
        Returns:
            Dictionary with discovery statistics
        """
        logger.info("Calculating site discovery statistics")
        
        stats = site_collection_results.get('statistics', {})
        inventory = site_collection_results.get('inventory', {})
        
        discovery_stats = {
            'devices_processed': stats.get('devices_processed', 0),
            'devices_successful': stats.get('devices_successful', 0),
            'devices_failed': stats.get('devices_failed', 0),
            'neighbors_discovered': stats.get('neighbors_discovered', 0),
            'success_rate': stats.get('success_rate', 0.0),
            'collection_duration_seconds': stats.get('collection_duration_seconds', 0.0),
            'average_discovery_depth': 0.0,
            'max_discovery_depth': 0,
            'platform_distribution': {},
            'discovery_method_distribution': {}
        }
        
        # Calculate depth statistics
        depths = []
        platforms = Counter()
        discovery_methods = Counter()
        
        for device_key, device_info in inventory.items():
            # Discovery depth
            depth = device_info.get('discovery_depth', 0)
            if isinstance(depth, (int, float)):
                depths.append(depth)
                discovery_stats['max_discovery_depth'] = max(discovery_stats['max_discovery_depth'], depth)
            
            # Platform distribution
            platform = device_info.get('platform', 'unknown')
            platforms[platform] += 1
            
            # Discovery method distribution
            method = device_info.get('discovery_method', 'unknown')
            discovery_methods[method] += 1
        
        # Calculate average depth
        if depths:
            discovery_stats['average_discovery_depth'] = sum(depths) / len(depths)
        
        # Convert counters to dictionaries
        discovery_stats['platform_distribution'] = dict(platforms)
        discovery_stats['discovery_method_distribution'] = dict(discovery_methods)
        
        logger.info(f"Discovery statistics calculated: success_rate={discovery_stats['success_rate']:.1f}%, "
                   f"avg_depth={discovery_stats['average_discovery_depth']:.2f}")
        
        return discovery_stats
    
    def generate_site_summary(self, site_name: str, site_inventory: Dict[str, Dict[str, Any]], 
                            site_collection_results: Optional[Dict[str, Any]] = None) -> SiteStatistics:
        """
        Generate comprehensive site summary statistics.
        
        Args:
            site_name: Name of the site
            site_inventory: Site-specific device inventory
            site_collection_results: Optional site collection results
            
        Returns:
            SiteStatistics object with comprehensive site information
        """
        logger.info(f"Generating comprehensive summary for site '{site_name}'")
        
        # Check cache first
        cache_key = f"{site_name}_{len(site_inventory)}"
        if cache_key in self._statistics_cache:
            cached_time = self._cache_timestamps.get(cache_key)
            if cached_time and (datetime.now() - cached_time).seconds < 300:  # 5 minute cache
                logger.debug(f"Returning cached statistics for site '{site_name}'")
                return self._statistics_cache[cache_key]
        
        # Calculate device counts
        device_counts = self.calculate_site_device_counts(site_inventory)
        
        # Calculate connection counts
        connection_counts = self.calculate_site_connection_counts(site_inventory)
        
        # Calculate discovery statistics
        discovery_stats = {}
        if site_collection_results:
            discovery_stats = self.calculate_site_discovery_stats(site_collection_results)
        
        # Calculate platform distribution
        platform_counts = Counter()
        total_neighbors = 0
        
        for device_key, device_info in site_inventory.items():
            platform = device_info.get('platform', 'unknown')
            platform_counts[platform] += 1
            
            neighbors = device_info.get('neighbors', [])
            total_neighbors += len(neighbors)
        
        # Create comprehensive statistics
        site_stats = SiteStatistics(
            site_name=site_name,
            total_devices=device_counts['total_devices'],
            connected_devices=device_counts['connected_devices'],
            failed_devices=device_counts['failed_devices'],
            filtered_devices=device_counts['filtered_devices'],
            boundary_devices=device_counts['boundary_devices'],
            
            total_connections=connection_counts['total_connections'],
            intra_site_connections=connection_counts['intra_site_connections'],
            external_connections=connection_counts['external_connections'],
            
            discovery_success_rate=discovery_stats.get('success_rate', 0.0),
            average_discovery_depth=discovery_stats.get('average_discovery_depth', 0.0),
            total_neighbors_discovered=total_neighbors,
            
            devices_processed=discovery_stats.get('devices_processed', device_counts['total_devices']),
            collection_duration_seconds=discovery_stats.get('collection_duration_seconds', 0.0),
            
            platform_counts=dict(platform_counts)
        )
        
        # Cache the results
        self._statistics_cache[cache_key] = site_stats
        self._cache_timestamps[cache_key] = datetime.now()
        
        logger.info(f"Site summary generated for '{site_name}': {site_stats.total_devices} devices, "
                   f"{site_stats.total_connections} connections, {site_stats.discovery_success_rate:.1f}% success rate")
        
        return site_stats
    
    def compare_site_statistics(self, site_stats_list: List[SiteStatistics]) -> Dict[str, Any]:
        """
        Compare statistics across multiple sites.
        
        Args:
            site_stats_list: List of SiteStatistics objects
            
        Returns:
            Dictionary with comparative analysis
        """
        if not site_stats_list:
            return {}
        
        logger.info(f"Comparing statistics across {len(site_stats_list)} sites")
        
        comparison = {
            'total_sites': len(site_stats_list),
            'total_devices_all_sites': sum(s.total_devices for s in site_stats_list),
            'total_connections_all_sites': sum(s.total_connections for s in site_stats_list),
            'average_success_rate': sum(s.discovery_success_rate for s in site_stats_list) / len(site_stats_list),
            'site_rankings': {
                'largest_by_devices': sorted(site_stats_list, key=lambda s: s.total_devices, reverse=True),
                'highest_success_rate': sorted(site_stats_list, key=lambda s: s.discovery_success_rate, reverse=True),
                'most_connections': sorted(site_stats_list, key=lambda s: s.total_connections, reverse=True)
            },
            'platform_distribution_global': Counter(),
            'site_summary': []
        }
        
        # Aggregate platform distribution
        for site_stats in site_stats_list:
            for platform, count in site_stats.platform_counts.items():
                comparison['platform_distribution_global'][platform] += count
        
        # Create site summaries
        for site_stats in site_stats_list:
            comparison['site_summary'].append({
                'site_name': site_stats.site_name,
                'devices': site_stats.total_devices,
                'connections': site_stats.total_connections,
                'success_rate': site_stats.discovery_success_rate
            })
        
        logger.info(f"Site comparison completed: {comparison['total_devices_all_sites']} total devices across {comparison['total_sites']} sites")
        
        return comparison
    
    def validate_site_statistics_consistency(self, site_stats: SiteStatistics) -> List[str]:
        """
        Validate site statistics for consistency and logical correctness.
        
        Args:
            site_stats: SiteStatistics object to validate
            
        Returns:
            List of validation warnings/errors
        """
        warnings = []
        
        # Check device count consistency
        calculated_total = (site_stats.connected_devices + site_stats.failed_devices + 
                          site_stats.filtered_devices + site_stats.boundary_devices)
        
        if calculated_total != site_stats.total_devices:
            warnings.append(f"Device count mismatch: total={site_stats.total_devices}, "
                          f"sum of categories={calculated_total}")
        
        # Check connection consistency
        if site_stats.intra_site_connections + site_stats.external_connections > site_stats.total_connections:
            warnings.append(f"Connection count inconsistency: intra+external > total")
        
        # Check success rate bounds
        if not (0.0 <= site_stats.discovery_success_rate <= 100.0):
            warnings.append(f"Invalid success rate: {site_stats.discovery_success_rate}")
        
        # Check for negative values
        for field_name in ['total_devices', 'connected_devices', 'failed_devices', 
                          'total_connections', 'devices_processed']:
            value = getattr(site_stats, field_name)
            if value < 0:
                warnings.append(f"Negative value for {field_name}: {value}")
        
        if warnings:
            logger.warning(f"Site statistics validation found {len(warnings)} issues for site '{site_stats.site_name}'")
        
        return warnings
    
    def clear_cache(self):
        """Clear the statistics cache"""
        self._statistics_cache.clear()
        self._cache_timestamps.clear()
        logger.info("Statistics cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the statistics cache"""
        return {
            'cached_sites': len(self._statistics_cache),
            'cache_keys': list(self._statistics_cache.keys()),
            'oldest_cache_entry': min(self._cache_timestamps.values()) if self._cache_timestamps else None,
            'newest_cache_entry': max(self._cache_timestamps.values()) if self._cache_timestamps else None
        }
    
    def generate_site_summary_data(self, site_stats: SiteStatistics) -> Dict[str, Any]:
        """
        Generate site summary data structure for reporting.
        
        Args:
            site_stats: SiteStatistics object
            
        Returns:
            Dictionary with structured site summary data
        """
        logger.info(f"Generating site summary data for '{site_stats.site_name}'")
        
        summary_data = {
            'site_info': {
                'name': site_stats.site_name,
                'total_devices': site_stats.total_devices,
                'collection_duration': site_stats.collection_duration_seconds,
                'success_rate': site_stats.discovery_success_rate
            },
            'device_breakdown': {
                'connected': site_stats.connected_devices,
                'failed': site_stats.failed_devices,
                'filtered': site_stats.filtered_devices,
                'boundary': site_stats.boundary_devices,
                'total': site_stats.total_devices
            },
            'connection_breakdown': {
                'total_connections': site_stats.total_connections,
                'intra_site': site_stats.intra_site_connections,
                'external': site_stats.external_connections,
                'connection_ratio': (site_stats.total_connections / site_stats.total_devices) if site_stats.total_devices > 0 else 0.0
            },
            'discovery_metrics': {
                'devices_processed': site_stats.devices_processed,
                'neighbors_discovered': site_stats.total_neighbors_discovered,
                'average_depth': site_stats.average_discovery_depth,
                'success_rate': site_stats.discovery_success_rate
            },
            'platform_distribution': site_stats.platform_counts.copy(),
            'summary_flags': {
                'has_devices': site_stats.total_devices > 0,
                'has_connections': site_stats.total_connections > 0,
                'collection_successful': site_stats.discovery_success_rate > 0.0,
                'has_external_connections': site_stats.external_connections > 0,
                'is_isolated_site': site_stats.external_connections == 0 and site_stats.total_devices > 0
            }
        }
        
        logger.info(f"Site summary data generated for '{site_stats.site_name}': "
                   f"{summary_data['device_breakdown']['total']} devices, "
                   f"{summary_data['connection_breakdown']['total_connections']} connections")
        
        return summary_data
    
    def separate_site_vs_global_statistics(self, site_stats_list: List[SiteStatistics], 
                                         global_inventory: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Separate site-specific statistics from global statistics for accurate reporting.
        
        Args:
            site_stats_list: List of site statistics
            global_inventory: Global device inventory
            
        Returns:
            Dictionary with separated site and global statistics
        """
        logger.info(f"Separating site vs global statistics for {len(site_stats_list)} sites")
        
        # Calculate global statistics
        global_device_counts = self.calculate_site_device_counts(global_inventory)
        global_connection_counts = self.calculate_site_connection_counts(global_inventory)
        
        # Aggregate site statistics
        site_totals = {
            'total_devices': sum(s.total_devices for s in site_stats_list),
            'connected_devices': sum(s.connected_devices for s in site_stats_list),
            'failed_devices': sum(s.failed_devices for s in site_stats_list),
            'total_connections': sum(s.total_connections for s in site_stats_list),
            'intra_site_connections': sum(s.intra_site_connections for s in site_stats_list),
            'external_connections': sum(s.external_connections for s in site_stats_list)
        }
        
        # Calculate non-site devices (devices not assigned to any site)
        non_site_devices = global_device_counts['total_devices'] - site_totals['total_devices']
        non_site_connections = global_connection_counts['total_connections'] - site_totals['total_connections']
        
        separation_data = {
            'global_statistics': {
                'total_devices': global_device_counts['total_devices'],
                'connected_devices': global_device_counts['connected_devices'],
                'failed_devices': global_device_counts['failed_devices'],
                'total_connections': global_connection_counts['total_connections'],
                'unique_neighbors': global_connection_counts['unique_neighbors']
            },
            'site_aggregated_statistics': site_totals,
            'non_site_statistics': {
                'devices': max(0, non_site_devices),
                'connections': max(0, non_site_connections),
                'percentage_of_total': (non_site_devices / global_device_counts['total_devices'] * 100) if global_device_counts['total_devices'] > 0 else 0.0
            },
            'coverage_analysis': {
                'sites_count': len(site_stats_list),
                'site_coverage_percentage': (site_totals['total_devices'] / global_device_counts['total_devices'] * 100) if global_device_counts['total_devices'] > 0 else 0.0,
                'connection_coverage_percentage': (site_totals['total_connections'] / global_connection_counts['total_connections'] * 100) if global_connection_counts['total_connections'] > 0 else 0.0,
                'average_devices_per_site': site_totals['total_devices'] / len(site_stats_list) if site_stats_list else 0.0
            },
            'consistency_checks': {
                'device_count_matches': abs(global_device_counts['total_devices'] - (site_totals['total_devices'] + non_site_devices)) <= 1,
                'connection_count_reasonable': abs(global_connection_counts['total_connections'] - (site_totals['total_connections'] + non_site_connections)) <= len(site_stats_list),
                'no_negative_non_site': non_site_devices >= 0 and non_site_connections >= 0
            }
        }
        
        logger.info(f"Site vs global separation completed: {separation_data['coverage_analysis']['site_coverage_percentage']:.1f}% device coverage across {len(site_stats_list)} sites")
        
        return separation_data
    
    def prepare_site_reporting_data(self, site_stats: SiteStatistics, 
                                  site_inventory: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prepare comprehensive site-specific reporting data.
        
        Args:
            site_stats: Site statistics object
            site_inventory: Site-specific device inventory
            
        Returns:
            Dictionary with all data needed for site-specific reporting
        """
        logger.info(f"Preparing comprehensive reporting data for site '{site_stats.site_name}'")
        
        # Generate basic summary data
        summary_data = self.generate_site_summary_data(site_stats)
        
        # Prepare device lists by category
        device_categories = {
            'connected_devices': [],
            'failed_devices': [],
            'filtered_devices': [],
            'boundary_devices': [],
            'seed_devices': []
        }
        
        # Prepare connection details
        connection_details = {
            'intra_site_connections': [],
            'external_connections': [],
            'device_neighbor_counts': {}
        }
        
        # Process inventory for detailed reporting data
        for device_key, device_info in site_inventory.items():
            device_hostname = device_info.get('hostname', '')
            device_summary = {
                'hostname': device_hostname,
                'ip_address': device_info.get('ip_address', ''),
                'platform': device_info.get('platform', 'unknown'),
                'status': device_info.get('status', 'unknown'),
                'neighbor_count': len(device_info.get('neighbors', []))
            }
            
            # Categorize devices
            status = device_info.get('status', 'unknown')
            connection_status = device_info.get('connection_status', 'unknown')
            
            if status == 'connected' or connection_status == 'connected':
                device_categories['connected_devices'].append(device_summary)
            elif status == 'failed' or connection_status == 'failed':
                device_categories['failed_devices'].append(device_summary)
            elif status == 'filtered':
                device_categories['filtered_devices'].append(device_summary)
            elif status == 'boundary':
                device_categories['boundary_devices'].append(device_summary)
            
            if device_info.get('is_seed', False) or device_info.get('discovery_method') == 'seed':
                device_categories['seed_devices'].append(device_summary)
            
            # Process connections
            neighbors = device_info.get('neighbors', [])
            connection_details['device_neighbor_counts'][device_hostname] = len(neighbors)
            
            for neighbor in neighbors:
                neighbor_hostname = neighbor.get('hostname', '') if isinstance(neighbor, dict) else str(neighbor)
                
                if neighbor_hostname:
                    connection_info = {
                        'local_device': device_hostname,
                        'remote_device': neighbor_hostname,
                        'local_interface': neighbor.get('interface', '') if isinstance(neighbor, dict) else '',
                        'remote_interface': neighbor.get('remote_interface', '') if isinstance(neighbor, dict) else ''
                    }
                    
                    # Determine if connection is intra-site or external
                    # (This is a simplified check - in practice, would use site boundary logic)
                    if any(neighbor_hostname.upper() == inv_device.get('hostname', '').upper() 
                          for inv_device in site_inventory.values()):
                        connection_details['intra_site_connections'].append(connection_info)
                    else:
                        connection_details['external_connections'].append(connection_info)
        
        # Compile comprehensive reporting data
        reporting_data = {
            'site_summary': summary_data,
            'device_categories': device_categories,
            'connection_details': connection_details,
            'reporting_metadata': {
                'generated_timestamp': datetime.now().isoformat(),
                'site_name': site_stats.site_name,
                'total_inventory_items': len(site_inventory),
                'data_completeness': {
                    'has_device_details': len(device_categories['connected_devices']) > 0,
                    'has_connection_details': len(connection_details['intra_site_connections']) + len(connection_details['external_connections']) > 0,
                    'has_platform_info': len(site_stats.platform_counts) > 0
                }
            }
        }
        
        logger.info(f"Comprehensive reporting data prepared for '{site_stats.site_name}': "
                   f"{len(device_categories['connected_devices'])} connected devices, "
                   f"{len(connection_details['intra_site_connections'])} intra-site connections")
        
        return reporting_data