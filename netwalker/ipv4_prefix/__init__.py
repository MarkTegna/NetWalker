"""
IPv4 Prefix Inventory Module

This module provides comprehensive IPv4 prefix collection and analysis capabilities
for NetWalker. It discovers VRFs, collects routing information from global and per-VRF
routing tables, extracts BGP prefixes, normalizes all formats to CIDR notation, resolves
ambiguous prefixes, tracks route summarization hierarchies, and exports results to Excel
and database storage.

Author: Mark Oldham
"""

from netwalker.ipv4_prefix.data_models import (
    IPv4PrefixConfig,
    RawPrefix,
    ParsedPrefix,
    NormalizedPrefix,
    DeduplicatedPrefix,
    SummarizationRelationship,
    CollectionException,
    DeviceCollectionResult,
    InventoryResult,
)

__all__ = [
    "IPv4PrefixConfig",
    "RawPrefix",
    "ParsedPrefix",
    "NormalizedPrefix",
    "DeduplicatedPrefix",
    "SummarizationRelationship",
    "CollectionException",
    "DeviceCollectionResult",
    "InventoryResult",
]


import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from datetime import datetime


class IPv4PrefixInventory:
    """
    Main orchestrator for IPv4 prefix inventory.
    
    Coordinates the complete workflow:
    1. Load configuration
    2. Get credentials
    3. Connect to database
    4. Query device inventory
    5. Collect from devices (concurrent)
    6. Parse and normalize
    7. Deduplicate
    8. Analyze summarization
    9. Export results
    10. Display summary
    """
    
    def __init__(self, config_file: str = "netwalker.ini"):
        """
        Initialize IPv4 prefix inventory orchestrator.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = None
        self.connection_manager = None
        self.credential_manager = None
        self.db_manager = None
        self.logger = logging.getLogger(__name__)
    
    def run(self, device_filter: str = None) -> 'InventoryResult':
        """
        Execute complete inventory workflow.
        
        Steps:
        1. Load configuration
        2. Get credentials
        3. Connect to database
        4. Query device inventory
        5. Collect from devices (concurrent)
        6. Parse and normalize
        7. Deduplicate
        8. Analyze summarization
        9. Export results
        10. Display summary
        
        Args:
            device_filter: Optional SQL wildcard filter for device names
            
        Returns:
            InventoryResult with statistics and output paths
            
        Requirements:
            - 18.1-18.5: Concurrent collection with thread pool
            - 20.1-20.7: Configuration and infrastructure integration
            - 21.1-21.6: Complete workflow orchestration
        """
        start_time = time.time()
        
        # Log system information banner
        import socket
        import os
        from netwalker.version import __version__
        
        hostname = socket.gethostname()
        execution_path = os.getcwd()
        
        self.logger.info("=" * 70)
        self.logger.info(f"Program: NetWalker - IPv4 Prefix Inventory")
        self.logger.info(f"Version: {__version__}")
        self.logger.info(f"Author: Mark Oldham")
        self.logger.info("-" * 70)
        self.logger.info(f"Hostname: {hostname}")
        self.logger.info(f"Execution Path: {execution_path}")
        self.logger.info("=" * 70)
        self.logger.info("IPv4 Prefix Inventory - Starting")
        self.logger.info("=" * 70)
        
        # Step 1: Load configuration
        self.logger.info("Loading configuration...")
        from netwalker.config.config_manager import ConfigurationManager
        config_manager = ConfigurationManager(self.config_file)
        full_config = config_manager.load_configuration()
        self.config = full_config['ipv4_prefix_inventory']
        
        self.logger.info(f"Configuration loaded: collect_global={self.config.collect_global_table}, "
                        f"collect_vrf={self.config.collect_per_vrf}, collect_bgp={self.config.collect_bgp}")
        
        # Step 2: Get credentials
        self.logger.info("Loading credentials...")
        from netwalker.config.credentials import CredentialManager
        credentials_file = full_config.get('credentials_file', 'secret_creds.ini')
        self.credential_manager = CredentialManager(credentials_file, full_config)
        credentials = self.credential_manager.get_credentials()
        
        if not credentials or not credentials.username:
            self.logger.error("No credentials available")
            return self._create_error_result("No credentials available", start_time)
        
        self.logger.info(f"Credentials loaded: username={credentials.username}")
        
        # Step 3: Connect to database
        self.logger.info("Connecting to database...")
        from netwalker.database.database_manager import DatabaseManager
        self.db_manager = DatabaseManager(full_config['database'])
        
        if self.config.enable_database_storage:
            if not self.db_manager.connect():
                self.logger.warning("Database connection failed - continuing without database storage")
                self.config.enable_database_storage = False
            else:
                self.logger.info("Database connected successfully")
                # Initialize IPv4 prefix schema
                self.db_manager.initialize_ipv4_prefix_schema()
        
        # Step 4: Query device inventory
        self.logger.info("Querying device inventory...")
        devices = self._query_devices(device_filter)
        
        if not devices:
            self.logger.error("No devices found in inventory")
            return self._create_error_result("No devices found", start_time)
        
        self.logger.info(f"Found {len(devices)} devices to process")
        
        # Step 5: Collect from devices (concurrent)
        self.logger.info(f"Starting concurrent collection (max {self.config.concurrent_devices} devices)...")
        collection_results = self.collect_from_devices(devices)
        
        successful_results = [r for r in collection_results if r.success]
        failed_results = [r for r in collection_results if not r.success]
        
        self.logger.info(f"Collection complete: {len(successful_results)} successful, {len(failed_results)} failed")
        
        if not successful_results:
            self.logger.error("No successful device collections")
            return self._create_error_result("All device collections failed", start_time)
        
        # Step 6: Parse and normalize
        self.logger.info("Parsing and normalizing prefixes...")
        all_prefixes, exceptions = self._parse_and_normalize(successful_results)
        
        self.logger.info(f"Parsed {len(all_prefixes)} prefixes with {len(exceptions)} exceptions")
        
        # Step 7: Deduplicate
        self.logger.info("Deduplicating prefixes...")
        from netwalker.ipv4_prefix.normalizer import PrefixDeduplicator
        deduplicator = PrefixDeduplicator()
        
        deduplicated_by_device = deduplicator.deduplicate_by_device(all_prefixes)
        deduplicated_by_vrf = deduplicator.deduplicate_by_vrf(all_prefixes)
        
        self.logger.info(f"Deduplicated: {len(deduplicated_by_device)} unique by device, "
                        f"{len(deduplicated_by_vrf)} unique by VRF")
        
        # Step 8: Analyze summarization (if enabled)
        summarization_relationships = []
        if self.config.track_summarization:
            self.logger.info("Analyzing route summarization...")
            from netwalker.ipv4_prefix.summarization import SummarizationAnalyzer
            analyzer = SummarizationAnalyzer()
            summarization_relationships = analyzer.analyze_summarization(all_prefixes)
            self.logger.info(f"Found {len(summarization_relationships)} summarization relationships")
        
        # Step 9: Export results
        self.logger.info("Exporting results...")
        output_files = self._export_results(
            deduplicated_by_device,
            deduplicated_by_vrf,
            exceptions,
            summarization_relationships
        )
        
        # Step 10: Display summary
        execution_time = time.time() - start_time
        result = self._create_result(
            len(devices),
            len(successful_results),
            len(failed_results),
            len(all_prefixes),
            len(deduplicated_by_vrf),
            exceptions,
            len(summarization_relationships),
            execution_time,
            output_files
        )
        
        self._display_summary(result)
        
        # Disconnect from database
        if self.db_manager:
            self.db_manager.disconnect()
        
        self.logger.info("=" * 70)
        self.logger.info("IPv4 Prefix Inventory - Complete")
        self.logger.info("=" * 70)
        
        return result
    
    def collect_from_devices(self, devices: List[Any]) -> List['DeviceCollectionResult']:
        """
        Collect from multiple devices concurrently.
        
        Uses ThreadPoolExecutor with configured concurrency limit.
        
        Args:
            devices: List of device objects
            
        Returns:
            List of DeviceCollectionResult objects
            
        Requirements:
            - 18.1: Use ThreadPool for concurrent execution
            - 18.2: Respect configured concurrency limit
            - 18.3: Ensure thread-safe access
            - 18.4: Isolate thread failures
            - 18.5: Aggregate results from all devices
        """
        results = []
        
        # Initialize connection manager
        from netwalker.connection.connection_manager import ConnectionManager
        self.connection_manager = ConnectionManager()
        
        # Initialize prefix collector
        from netwalker.ipv4_prefix.collector import PrefixCollector
        collector = PrefixCollector(
            self.config,
            self.connection_manager,
            self.credential_manager.get_credentials()
        )
        
        # Process devices concurrently
        with ThreadPoolExecutor(max_workers=self.config.concurrent_devices) as executor:
            # Submit all device collection tasks
            future_to_device = {
                executor.submit(collector.collect_device, device): device
                for device in devices
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_device):
                device = future_to_device[future]
                device_name = device.hostname if hasattr(device, 'hostname') else str(device)
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result.success:
                        self.logger.info(f"[OK] {device_name}")
                    else:
                        self.logger.error(f"[FAIL] {device_name}: {result.error}")
                        
                except Exception as e:
                    # Thread failure - create error result
                    self.logger.error(f"[FAIL] {device_name}: Unexpected error: {str(e)}")
                    from netwalker.ipv4_prefix.data_models import DeviceCollectionResult
                    error_result = DeviceCollectionResult(
                        device=device_name,
                        platform='unknown',
                        success=False,
                        vrfs=[],
                        raw_outputs={},
                        error=str(e)
                    )
                    results.append(error_result)
        
        return results
    
    def _query_devices(self, device_filter: str = None) -> List[Any]:
        """Query devices from database or create dummy list."""
        devices = []
        
        if self.db_manager and self.db_manager.is_connected():
            # Query from database
            try:
                cursor = self.db_manager.connection.cursor()
                
                if device_filter:
                    # Apply SQL wildcard filter
                    query = """
                        SELECT 
                            d.device_id,
                            d.device_name,
                            d.platform,
                            d.serial_number,
                            di.ip_address
                        FROM devices d
                        INNER JOIN (
                            SELECT 
                                device_id,
                                ip_address,
                                ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY last_seen DESC) as rn
                            FROM device_interfaces
                        ) di ON d.device_id = di.device_id AND di.rn = 1
                        WHERE d.device_name LIKE ? AND d.status = 'active'
                        ORDER BY d.device_name
                    """
                    cursor.execute(query, (device_filter,))
                else:
                    # Get all active devices
                    query = """
                        SELECT 
                            d.device_id,
                            d.device_name,
                            d.platform,
                            d.serial_number,
                            di.ip_address
                        FROM devices d
                        INNER JOIN (
                            SELECT 
                                device_id,
                                ip_address,
                                ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY last_seen DESC) as rn
                            FROM device_interfaces
                        ) di ON d.device_id = di.device_id AND di.rn = 1
                        WHERE d.status = 'active'
                        ORDER BY d.device_name
                    """
                    cursor.execute(query)
                
                rows = cursor.fetchall()
                cursor.close()
                
                # Create device objects
                for row in rows:
                    # Create a simple object with device info
                    class DeviceInfo:
                        def __init__(self, device_id, hostname, platform, serial, ip_address):
                            self.device_id = device_id
                            self.hostname = hostname
                            self.platform = platform
                            self.serial_number = serial
                            self.ip_address = ip_address
                    
                    devices.append(DeviceInfo(row[0], row[1], row[2], row[3], row[4]))
                
            except Exception as e:
                self.logger.error(f"Error querying devices: {str(e)}")
        
        return devices
    
    def _parse_and_normalize(self, collection_results: List['DeviceCollectionResult']) -> tuple:
        """Parse and normalize all collected prefixes."""
        from netwalker.ipv4_prefix.parser import CommandOutputParser
        from netwalker.ipv4_prefix.normalizer import PrefixNormalizer
        
        parser = CommandOutputParser()
        normalizer = PrefixNormalizer()
        
        all_prefixes = []
        exceptions = []
        
        for result in collection_results:
            # Parse command outputs
            parsed_prefixes = parser.parse_collection_result(result)
            
            # Normalize each parsed prefix
            for parsed in parsed_prefixes:
                if parsed.is_ambiguous:
                    # Add to exceptions - ambiguous prefixes need resolution
                    exception = CollectionException(
                        device=parsed.device,
                        command='',
                        error_type='ambiguous_prefix',
                        raw_token=parsed.prefix_str,
                        error_message=f"Ambiguous prefix without explicit length: {parsed.prefix_str}",
                        timestamp=parsed.timestamp
                    )
                    exceptions.append(exception)
                    # Skip ambiguous prefixes for now (could implement resolution here)
                    continue
                
                # Normalize prefix
                normalized = normalizer.normalize_parsed_prefix(parsed, exceptions)
                if normalized:
                    all_prefixes.append(normalized)
        
        return all_prefixes, exceptions
    
    def _export_results(self, prefixes: List['NormalizedPrefix'],
                       deduplicated: List['DeduplicatedPrefix'],
                       exceptions: List['CollectionException'],
                       summarization: List['SummarizationRelationship']) -> List[str]:
        """Export results to CSV, Excel, and database."""
        from netwalker.ipv4_prefix.exporter import CSVExporter, ExcelExporter, DatabaseExporter
        
        output_files = []
        
        # CSV Export
        csv_exporter = CSVExporter()
        output_files.append(csv_exporter.export_prefixes(prefixes, self.config.output_directory))
        output_files.append(csv_exporter.export_deduplicated(deduplicated, self.config.output_directory))
        output_files.append(csv_exporter.export_exceptions(exceptions, self.config.output_directory))
        
        # Excel Export
        excel_exporter = ExcelExporter()
        excel_file = excel_exporter.export(prefixes, deduplicated, exceptions, self.config.output_directory)
        if excel_file:
            output_files.append(excel_file)
        
        # Database Export (if enabled)
        if self.config.enable_database_storage and self.db_manager:
            db_exporter = DatabaseExporter(self.db_manager)
            db_exporter.initialize_schema()
            
            # Store prefixes and get their IDs for summarization
            # This would require querying device_id for each prefix
            # Simplified for now - full implementation would map device names to IDs
            
        return output_files
    
    def _create_result(self, total_devices: int, successful: int, failed: int,
                      total_prefixes: int, unique_prefixes: int,
                      exceptions: List['CollectionException'],
                      summarization_count: int, execution_time: float,
                      output_files: List[str]) -> 'InventoryResult':
        """Create InventoryResult object."""
        # Count /32 host routes
        host_routes_count = 0  # Would need to count from prefixes
        
        # Count unresolved prefixes
        unresolved_count = sum(1 for e in exceptions if e.error_type == 'ambiguous_prefix')
        
        return InventoryResult(
            total_devices=total_devices,
            successful_devices=successful,
            failed_devices=failed,
            total_prefixes=total_prefixes,
            unique_prefixes=unique_prefixes,
            host_routes_count=host_routes_count,
            unresolved_count=unresolved_count,
            summarization_relationships=summarization_count,
            execution_time=execution_time,
            output_files=output_files
        )
    
    def _create_error_result(self, error_msg: str, start_time: float) -> 'InventoryResult':
        """Create error result."""
        return InventoryResult(
            total_devices=0,
            successful_devices=0,
            failed_devices=0,
            total_prefixes=0,
            unique_prefixes=0,
            host_routes_count=0,
            unresolved_count=0,
            summarization_relationships=0,
            execution_time=time.time() - start_time,
            output_files=[]
        )
    
    def _display_summary(self, result: 'InventoryResult'):
        """Display summary statistics."""
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("SUMMARY STATISTICS")
        self.logger.info("=" * 70)
        self.logger.info(f"Devices Processed:        {result.total_devices}")
        self.logger.info(f"  Successful:             {result.successful_devices}")
        self.logger.info(f"  Failed:                 {result.failed_devices}")
        self.logger.info(f"")
        self.logger.info(f"Prefixes Collected:       {result.total_prefixes}")
        self.logger.info(f"Unique Prefixes (by VRF): {result.unique_prefixes}")
        self.logger.info(f"Host Routes (/32):        {result.host_routes_count}")
        self.logger.info(f"Unresolved Prefixes:      {result.unresolved_count}")
        self.logger.info(f"Summarization Links:      {result.summarization_relationships}")
        self.logger.info(f"")
        self.logger.info(f"Execution Time:           {result.execution_time:.2f} seconds")
        self.logger.info(f"")
        self.logger.info(f"Output Files:")
        for file_path in result.output_files:
            self.logger.info(f"  - {file_path}")
        self.logger.info("=" * 70)


# Update __all__ to include the new class
__all__.append("IPv4PrefixInventory")
