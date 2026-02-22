# Implementation Plan: IPv4 Prefix Inventory Module

## Overview

This implementation plan breaks down the IPv4 Prefix Inventory Module into discrete coding tasks. The module will be implemented as a new package under `netwalker/ipv4_prefix/` following NetWalker's existing patterns for connection management, database operations, and Excel export. Tasks are organized to build incrementally, with early validation through testing.

## Tasks

- [x] 1. Create module structure and data models
  - Create `netwalker/ipv4_prefix/` directory
  - Create `__init__.py` with module exports
  - Create `data_models.py` with all dataclasses: IPv4PrefixConfig, RawPrefix, ParsedPrefix, NormalizedPrefix, DeduplicatedPrefix, SummarizationRelationship, CollectionException, DeviceCollectionResult, InventoryResult
  - Add type hints and docstrings for all data models
  - _Requirements: 22.1, 22.5_

- [ ]* 1.1 Write property test for data model validation
  - **Property 21: Complete Metadata Tagging**
  - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7**

- [x] 2. Implement configuration management
  - [x] 2.1 Add IPv4PrefixConfig loading to ConfigurationManager
    - Add `_build_ipv4_prefix_config()` method to `netwalker/config/config_manager.py`
    - Load settings from `[ipv4_prefix_inventory]` section
    - Handle defaults for all configuration options
    - _Requirements: 20.1_

  - [ ]* 2.2 Write property test for configuration loading
    - **Property 45: Configuration Loading**
    - **Validates: Requirements 20.1**

  - [ ]* 2.3 Write property test for configuration application
    - **Property 46: Configuration Application**
    - **Validates: Requirements 20.2, 20.3, 20.4, 20.5, 20.6, 20.7**

- [x] 3. Implement VRF discovery component
  - [x] 3.1 Create `netwalker/ipv4_prefix/collector.py`
    - Implement VRFDiscovery class with `discover_vrfs()` method
    - Handle platform-specific VRF discovery (IOS, IOS-XE, NX-OS all use `show vrf`)
    - Parse VRF names from command output
    - Handle empty VRF lists and errors gracefully
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ]* 3.2 Write property test for VRF discovery
    - **Property 1: VRF Discovery Execution**
    - **Validates: Requirements 1.1, 1.2, 1.3**

  - [ ]* 3.3 Write property test for VRF discovery error handling
    - **Property 2: VRF Discovery Error Handling**
    - **Validates: Requirements 1.4**

- [x] 4. Implement routing table collection
  - [x] 4.1 Implement RoutingCollector class in `collector.py`
    - Implement `collect_global_routes()` - execute `show ip route`
    - Implement `collect_global_connected()` - execute `show ip route connected`
    - Implement `collect_vrf_routes()` - execute `show ip route vrf <VRF>`
    - Implement `collect_vrf_connected()` - execute `show ip route vrf <VRF> connected`
    - Handle VRF names with spaces and special characters (quoting/escaping)
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 17.1, 17.2, 17.3, 17.4, 17.5_

  - [ ]* 4.2 Write property test for global table commands
    - **Property 3: Global Table Command Execution**
    - **Validates: Requirements 2.1, 2.2**

  - [ ]* 4.3 Write property test for per-VRF commands
    - **Property 6: Per-VRF Command Execution**
    - **Validates: Requirements 3.1, 3.2**

  - [ ]* 4.4 Write property test for VRF name sanitization
    - **Property 38: VRF Name Sanitization**
    - **Validates: Requirements 17.1, 17.2**

  - [ ]* 4.5 Write property test for VRF name validation
    - **Property 39: VRF Name Validation**
    - **Validates: Requirements 17.3, 17.4**


- [x] 5. Implement BGP collection
  - [x] 5.1 Implement BGPCollector class in `collector.py`
    - Implement `collect_global_bgp()` - execute `show ip bgp` with graceful failure handling
    - Implement `collect_vrf_bgp()` - execute platform-specific BGP VRF commands
    - Handle IOS/IOS-XE: `show ip bgp vpnv4 vrf <VRF>`
    - Handle NX-OS: `show ip bgp vrf <VRF>`
    - Return None if BGP not configured (graceful degradation)
    - _Requirements: 2.3, 2.4, 3.3, 3.4_

  - [ ]* 5.2 Write property test for BGP collection with graceful degradation
    - **Property 4: BGP Collection with Graceful Degradation**
    - **Validates: Requirements 2.3, 2.4**

  - [ ]* 5.3 Write property test for platform-specific BGP commands
    - **Property 7: Platform-Specific BGP VRF Commands**
    - **Validates: Requirements 3.3, 3.4**

- [x] 6. Implement pagination control
  - [x] 6.1 Add pagination control to PrefixCollector
    - Execute `terminal length 0` before collection
    - Handle pagination control failures gracefully
    - Log errors and continue with collection
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ]* 6.2 Write property test for pagination control
    - **Property 9: Pagination Control**
    - **Validates: Requirements 4.1**

  - [ ]* 6.3 Write property test for pagination error handling
    - **Property 10: Pagination Control Error Handling**
    - **Validates: Requirements 4.3**

- [x] 7. Checkpoint - Ensure collection components work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement prefix parsing
  - [x] 8.1 Create `netwalker/ipv4_prefix/parser.py`
    - Implement PrefixExtractor class with `extract_from_route_line()` and `extract_from_bgp_line()`
    - Handle CIDR format: 192.168.1.0/24
    - Handle mask format: 192.168.1.0 255.255.255.0
    - Handle ambiguous BGP prefixes: 10.0.0.0 (no length)
    - Extract /32 local routes (L route code)
    - Extract loopback interface addresses
    - Preserve raw output lines
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 8.2 Implement RoutingTableParser class
    - Parse `show ip route` output line by line
    - Extract prefixes with metadata (device, platform, vrf, source, protocol)
    - Handle various route codes (C, L, B, D, S)
    - _Requirements: 5.1, 5.2, 5.4, 5.5, 5.6, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

  - [x] 8.3 Implement BGPParser class
    - Parse `show ip bgp` output line by line
    - Extract prefixes and mark ambiguous ones (no explicit length)
    - Tag with metadata
    - _Requirements: 5.3, 5.6, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

  - [x] 8.4 Implement CommandOutputParser orchestrator
    - Coordinate parsing of all command outputs
    - Return list of ParsedPrefix objects
    - _Requirements: 5.1, 5.2, 5.3, 5.6_

  - [ ]* 8.5 Write property test for multi-format prefix extraction
    - **Property 11: Multi-Format Prefix Extraction**
    - **Validates: Requirements 5.1, 5.2**

  - [ ]* 8.6 Write property test for BGP prefix extraction
    - **Property 12: BGP Prefix Extraction**
    - **Validates: Requirements 5.3**

  - [ ]* 8.7 Write property test for raw line preservation
    - **Property 13: Raw Line Preservation**
    - **Validates: Requirements 5.6**

  - [ ]* 8.8 Write unit tests for parser with sample outputs
    - Test with `show ip route` sample from IOS device
    - Test with `show ip route` sample from NX-OS device
    - Test with `show ip bgp vpnv4 vrf WAN` sample with ambiguous prefixes
    - Test edge cases: empty output, malformed lines
    - _Requirements: 24.1, 24.2, 24.3_

- [x] 9. Implement prefix normalization
  - [x] 9.1 Create `netwalker/ipv4_prefix/normalizer.py`
    - Implement PrefixNormalizer class
    - Implement `normalize()` method using Python ipaddress library
    - Implement `mask_to_cidr()` for mask format conversion
    - Implement `validate_cidr()` for CIDR validation
    - Handle invalid formats gracefully (log and add to exceptions)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 9.2 Write property test for mask to CIDR conversion
    - **Property 14: Mask to CIDR Conversion**
    - **Validates: Requirements 6.1**

  - [ ]* 9.3 Write property test for CIDR idempotence
    - **Property 15: CIDR Idempotence**
    - **Validates: Requirements 6.2**

  - [ ]* 9.4 Write property test for invalid prefix handling
    - **Property 16: Invalid Prefix Handling**
    - **Validates: Requirements 6.3**

  - [ ]* 9.5 Write property test for normalization output validity
    - **Property 17: Normalization Output Validity**
    - **Validates: Requirements 6.4**

  - [ ]* 9.6 Write unit tests for normalizer
    - Test mask to CIDR: 192.168.1.0 255.255.255.0 → 192.168.1.0/24
    - Test CIDR validation: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
    - Test invalid formats: 999.999.999.999/32, 10.0.0.0/33
    - Test edge cases: /32 host routes, /0 default route
    - _Requirements: 24.4_

- [x] 10. Implement ambiguity resolution
  - [x] 10.1 Implement AmbiguityResolver class in `normalizer.py`
    - Implement `resolve()` method with two-step strategy
    - Try `show ip bgp <prefix>` (or VRF variant) first
    - Try `show ip route <prefix>` (or VRF variant) second
    - Mark as unresolved if both fail
    - Normalize resolved prefixes to CIDR
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 10.2 Write property test for ambiguity resolution strategy
    - **Property 18: Ambiguity Resolution Strategy**
    - **Validates: Requirements 7.1, 7.2**

  - [ ]* 10.3 Write property test for unresolved prefix recording
    - **Property 19: Unresolved Prefix Recording**
    - **Validates: Requirements 7.3, 7.5**

  - [ ]* 10.4 Write property test for resolved prefix normalization
    - **Property 20: Resolved Prefix Normalization**
    - **Validates: Requirements 7.4**

  - [ ]* 10.5 Write unit tests for ambiguity resolver
    - Test successful resolution via `show ip bgp <prefix>`
    - Test fallback to `show ip route <prefix>`
    - Test unresolved prefix handling
    - Test VRF-specific resolution commands
    - _Requirements: 24.5_

- [x] 11. Checkpoint - Ensure parsing and normalization work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Implement deduplication
  - [x] 12.1 Implement PrefixDeduplicator class in `normalizer.py`
    - Implement `deduplicate_by_device()` using (device, vrf, prefix, source) as key
    - Keep first occurrence of duplicates
    - Implement `deduplicate_by_vrf()` for cross-device aggregation
    - Group by (vrf, prefix) with device_list and device_count
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 12.2 Write property test for deduplication key
    - **Property 22: Deduplication Key**
    - **Validates: Requirements 9.1, 9.2**

  - [ ]* 12.3 Write property test for VRF-level aggregation
    - **Property 23: VRF-Level Aggregation**
    - **Validates: Requirements 9.3, 9.4, 9.5**

  - [ ]* 12.4 Write unit tests for deduplicator
    - Test exact duplicates (same device, vrf, prefix, source)
    - Test cross-device duplicates (same vrf, prefix, different devices)
    - Test edge cases: empty input, single prefix, all duplicates
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 13. Implement summarization analysis
  - [x] 13.1 Create `netwalker/ipv4_prefix/summarization.py`
    - Implement SummarizationAnalyzer class
    - Implement `analyze_summarization()` to identify summary/component relationships
    - Implement `is_component_of()` to check if prefix falls within summary range
    - Implement `find_components()` to find all components for a summary
    - Sort prefixes by length (shortest first) for efficient analysis
    - _Requirements: 15.3, 15.5, 15.6, 15.7_

  - [ ]* 13.2 Write property test for summarization detection
    - **Property 32: Summarization Detection**
    - **Validates: Requirements 15.3**

  - [ ]* 13.3 Write property test for summarization metadata
    - **Property 33: Summarization Metadata**
    - **Validates: Requirements 15.5**

  - [ ]* 13.4 Write property test for recursive summarization queries
    - **Property 34: Recursive Summarization Query Support**
    - **Validates: Requirements 15.6, 15.7**

  - [ ]* 13.5 Write unit tests for summarization analyzer
    - Test simple summarization: 192.168.1.0/24 + 192.168.2.0/24 → 192.168.0.0/16
    - Test multi-level hierarchies: /24 → /16 → /8
    - Test edge cases: no summarization, overlapping prefixes
    - _Requirements: 15.3, 15.5, 15.6, 15.7_

- [x] 14. Implement CSV export
  - [x] 14.1 Create `netwalker/ipv4_prefix/exporter.py`
    - Implement CSVExporter class
    - Implement `export_prefixes()` - create prefixes.csv with specified columns
    - Implement `export_deduplicated()` - create prefixes_dedup_by_vrf.csv
    - Implement `export_exceptions()` - create exceptions.csv
    - Apply correct sort order for each export
    - Use UTF-8 encoding
    - Format device_list as semicolon-separated string
    - Log output file paths
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 11.1, 11.2, 11.3, 11.4, 11.5, 12.1, 12.2_

  - [ ]* 14.2 Write property test for CSV column structure
    - **Property 24: CSV Column Structure**
    - **Validates: Requirements 10.2, 11.2, 12.2**

  - [ ]* 14.3 Write property test for CSV sort order
    - **Property 25: CSV Sort Order**
    - **Validates: Requirements 10.3, 11.3**

  - [ ]* 14.4 Write property test for device list formatting
    - **Property 26: Device List Formatting**
    - **Validates: Requirements 11.4**

  - [ ]* 14.5 Write property test for export logging
    - **Property 27: Export Logging**
    - **Validates: Requirements 10.5, 11.5**

  - [ ]* 14.6 Write unit tests for CSV exporter
    - Test CSV structure and encoding
    - Test sort order verification
    - Test edge cases: empty data, special characters in device names
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 15. Implement Excel export
  - [x] 15.1 Implement ExcelExporter class in `exporter.py`
    - Use existing NetWalker Excel patterns from `netwalker.reports.excel_generator`
    - Create workbook with three sheets: Prefixes, Deduplicated, Exceptions
    - Apply header formatting (bold, colored background)
    - Apply column auto-sizing
    - Apply data filters to all columns
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 21.5_

  - [ ]* 15.2 Write property test for Excel filter application
    - **Property 29: Excel Filter Application**
    - **Validates: Requirements 13.4**

  - [ ]* 15.3 Write unit tests for Excel exporter
    - Test workbook structure and sheets
    - Test edge cases: empty data, special characters
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [x] 16. Checkpoint - Ensure export components work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 17. Implement database schema
  - [x] 17.1 Add schema creation to DatabaseManager
    - Add `initialize_ipv4_prefix_schema()` method to `netwalker/database/database_manager.py`
    - Create `ipv4_prefixes` table with specified columns and indexes
    - Create `ipv4_prefix_summarization` table with foreign keys
    - Handle schema already exists gracefully
    - _Requirements: 14.1, 14.2, 14.3, 15.1, 15.2, 15.4_

  - [ ]* 17.2 Write unit tests for database schema
    - Test table creation
    - Test column names and types
    - Test foreign key constraints
    - _Requirements: 14.1, 14.2, 14.3, 15.1, 15.2, 15.4_

- [x] 18. Implement database storage
  - [x] 18.1 Implement DatabaseExporter class in `exporter.py`
    - Implement `initialize_schema()` to create tables
    - Implement `upsert_prefix()` with first_seen/last_seen logic
    - Update last_seen for existing prefixes
    - Insert with both timestamps for new prefixes
    - Link to device via device_id foreign key
    - Implement `upsert_summarization()` to store relationships
    - Handle database disabled gracefully (skip operations)
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7_

  - [ ]* 18.2 Write property test for database upsert behavior
    - **Property 30: Database Upsert Behavior**
    - **Validates: Requirements 14.4, 14.5**

  - [ ]* 18.3 Write property test for database conditional execution
    - **Property 31: Database Storage Conditional Execution**
    - **Validates: Requirements 14.6**

  - [ ]* 18.4 Write unit tests for database storage
    - Test upsert operations
    - Test timestamp handling
    - Test foreign key relationships
    - Test database disabled scenario
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 15.1, 15.2, 15.3, 15.4, 15.5_

- [x] 19. Implement exception reporting
  - [x] 19.1 Add exception tracking to all components
    - Track command failures with device, command, error message
    - Track unresolved prefixes with device, raw token, resolution attempts
    - Track parsing errors with device, command, problematic line
    - Collect all exceptions in CollectionException list
    - _Requirements: 12.3, 12.4, 12.5, 16.4_

  - [ ]* 19.2 Write property test for exception recording completeness
    - **Property 28: Exception Recording Completeness**
    - **Validates: Requirements 12.3, 12.4, 12.5**

  - [ ]* 19.3 Write property test for failure exception recording
    - **Property 36: Failure Exception Recording**
    - **Validates: Requirements 16.4**

- [x] 20. Implement main orchestrator
  - [x] 20.1 Implement IPv4PrefixInventory class in `netwalker/ipv4_prefix/__init__.py`
    - Implement `run()` method with complete workflow
    - Load configuration from netwalker.ini
    - Get credentials using existing Credential_Manager
    - Connect to database using existing Database_Manager
    - Query device inventory from database
    - Implement `collect_from_devices()` with ThreadPoolExecutor
    - Implement `process_device()` for single device processing
    - Aggregate results from all devices
    - Call parser, normalizer, deduplicator, summarization analyzer
    - Call exporters (CSV, Excel, Database)
    - Display summary statistics
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7, 21.1, 21.2, 21.3, 21.4, 21.5, 21.6_

  - [x] 20.2 Implement PrefixCollector class in `collector.py`
    - Orchestrate collection workflow for single device
    - Connect using existing Connection_Manager
    - Disable pagination with `terminal length 0`
    - Discover VRFs
    - Collect global table (if enabled)
    - Collect per-VRF tables (if enabled)
    - Collect BGP (if enabled)
    - Handle connection failures gracefully
    - Handle command failures gracefully
    - Return DeviceCollectionResult
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.3, 16.1, 16.2, 16.3, 21.1, 21.2, 21.4_

  - [ ]* 20.3 Write property test for concurrency limit enforcement
    - **Property 41: Concurrency Limit Enforcement**
    - **Validates: Requirements 18.2**

  - [ ]* 20.4 Write property test for thread failure isolation
    - **Property 42: Thread Failure Isolation**
    - **Validates: Requirements 18.4**

  - [ ]* 20.5 Write property test for result aggregation completeness
    - **Property 43: Result Aggregation Completeness**
    - **Validates: Requirements 18.5**

  - [ ]* 20.6 Write property test for command failure isolation
    - **Property 35: Command Failure Isolation**
    - **Validates: Requirements 16.1, 16.2, 16.3**

- [x] 21. Implement progress reporting
  - [x] 21.1 Add progress reporting to IPv4PrefixInventory
    - Display total devices at start
    - Display device name and progress during processing
    - Display success/failure indicators per device
    - Display final summary with counts and execution time
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_

  - [ ]* 21.2 Write property test for progress reporting completeness
    - **Property 44: Progress Reporting Completeness**
    - **Validates: Requirements 19.1, 19.2, 19.3, 19.4, 19.5**

  - [ ]* 21.3 Write property test for collection summary reporting
    - **Property 37: Collection Summary Reporting**
    - **Validates: Requirements 16.5**

- [x] 22. Implement summary statistics
  - [x] 22.1 Add statistics calculation to IPv4PrefixInventory
    - Calculate total prefixes collected
    - Calculate prefixes per VRF
    - Calculate prefixes per source (rib, connected, bgp)
    - Calculate /32 host routes count
    - Calculate unresolved prefixes count
    - Display all statistics
    - Write to summary.txt if configured
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6_

  - [ ]* 22.2 Write property test for summary statistics completeness
    - **Property 47: Summary Statistics Completeness**
    - **Validates: Requirements 22.1, 22.2, 22.3, 22.4, 22.5**

  - [ ]* 22.3 Write property test for summary file creation
    - **Property 48: Summary File Creation**
    - **Validates: Requirements 22.6**

- [x] 23. Implement VRF tagging validation
  - [ ]* 23.1 Write property test for global table VRF tagging
    - **Property 5: Global Table VRF Tagging**
    - **Validates: Requirements 2.5**

  - [ ]* 23.2 Write property test for per-VRF prefix tagging
    - **Property 8: Per-VRF Prefix Tagging**
    - **Validates: Requirements 3.5**

  - [ ]* 23.3 Write property test for VRF name logging
    - **Property 40: VRF Name Logging**
    - **Validates: Requirements 17.5**

- [x] 24. Checkpoint - Ensure orchestration works end-to-end
  - Ensure all tests pass, ask the user if questions arise.

- [x] 25. Add CLI integration
  - [x] 25.1 Add IPv4 prefix inventory command to `netwalker/cli.py`
    - Add `ipv4-prefix-inventory` subcommand
    - Add options for device filter (optional, default: all devices)
    - Add options for output directory (optional, default from config)
    - Wire to IPv4PrefixInventory.run()
    - _Requirements: 20.1, 20.5_

  - [ ]* 25.2 Write integration test for CLI
    - Test CLI invocation with various options
    - Test end-to-end workflow
    - _Requirements: 20.1, 20.5_

- [x] 26. Add default configuration to netwalker.ini
  - [x] 26.1 Update default config generation in ConfigurationManager
    - Add `[ipv4_prefix_inventory]` section with all options
    - Set sensible defaults
    - Add comments explaining each option
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7_

- [x] 27. Create documentation
  - [x] 27.1 Create README for ipv4_prefix module
    - Document module purpose and features
    - Document configuration options
    - Document output files and formats
    - Document database schema
    - Provide usage examples
    - _Requirements: All_

  - [x] 27.2 Update main NetWalker documentation
    - Add IPv4 prefix inventory to feature list
    - Add configuration section
    - Add usage examples
    - _Requirements: All_

- [x] 28. Final integration testing
  - [ ]* 28.1 Run full integration test with real devices
    - Test with IOS devices
    - Test with IOS-XE devices
    - Test with NX-OS devices
    - Test with devices having VRFs
    - Test with devices having BGP
    - Verify all outputs (CSV, Excel, Database)
    - Verify summarization tracking
    - _Requirements: All_

  - [ ]* 28.2 Run performance testing
    - Test with 100+ devices
    - Test with 10,000+ prefixes
    - Test with 100+ VRFs
    - Verify memory usage
    - Verify execution time
    - _Requirements: 18.1, 18.2_

- [x] 29. Final checkpoint - Complete feature validation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- The implementation follows NetWalker's existing patterns for consistency
