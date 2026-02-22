# Requirements Document: IPv4 Prefix Inventory Module

## Introduction

The IPv4 Prefix Inventory Module extends NetWalker to collect, parse, normalize, and inventory all IPv4 prefixes in use across a mixed Cisco estate (IOS, IOS-XE, NX-OS). The module discovers VRFs, collects routing information from global and per-VRF tables, extracts BGP prefixes, normalizes all prefix formats to CIDR notation, and exports results to Excel and database storage. The module handles ambiguous prefix formats through intelligent resolution strategies and provides comprehensive error reporting.

## Glossary

- **Prefix_Inventory_Module**: The IPv4 prefix collection and inventory system
- **VRF_Discovery_Engine**: Component that discovers VRFs on network devices
- **Routing_Collector**: Component that collects routing table information
- **BGP_Collector**: Component that collects BGP routing information
- **Prefix_Parser**: Component that extracts IPv4 prefixes from command outputs
- **Prefix_Normalizer**: Component that converts prefix formats to CIDR notation
- **Ambiguity_Resolver**: Component that resolves prefixes without explicit length
- **Deduplication_Engine**: Component that removes duplicate prefix entries
- **Excel_Exporter**: Component that exports results to Excel format
- **Database_Storage**: Component that stores results in NetWalker database
- **Exception_Reporter**: Component that tracks and reports parsing errors
- **Connection_Manager**: NetWalker's existing SSH connection management system
- **Credential_Manager**: NetWalker's existing credential management system
- **Database_Manager**: NetWalker's existing database management system
- **Command_Executor**: NetWalker's existing command execution framework
- **Global_Table**: The default routing table (non-VRF)
- **CIDR_Notation**: Classless Inter-Domain Routing notation (e.g., 192.168.1.0/24)
- **Prefix**: An IPv4 network address with subnet mask or length
- **RIB**: Routing Information Base (routing table)
- **Local_Route**: Host route (/32) for local interface addresses
- **Route_Summarization**: The aggregation of multiple specific routes into a single summary route
- **Summary_Route**: A route that represents multiple more-specific routes
- **Component_Route**: A more-specific route that is part of a summary route
- **Summarization_Hierarchy**: The relationship chain from specific routes up through summary routes to the root

## Requirements

### Requirement 1: VRF Discovery

**User Story:** As a network engineer, I want to discover all VRFs on each device, so that I can collect routing information from all routing tables.

#### Acceptance Criteria

1. WHEN connecting to an IOS or IOS-XE device, THE VRF_Discovery_Engine SHALL execute `show vrf` to discover VRFs
2. WHEN connecting to an NX-OS device, THE VRF_Discovery_Engine SHALL execute `show vrf` to discover VRFs
3. WHEN VRF discovery completes, THE VRF_Discovery_Engine SHALL return a list of VRF names for the device
4. IF VRF discovery fails, THEN THE VRF_Discovery_Engine SHALL log the error and continue with global table collection only
5. WHEN a device has no VRFs configured, THE VRF_Discovery_Engine SHALL return an empty VRF list

### Requirement 2: Global Routing Table Collection

**User Story:** As a network engineer, I want to collect routing information from the global routing table, so that I can inventory prefixes in the default VRF.

#### Acceptance Criteria

1. WHEN global table collection is enabled, THE Routing_Collector SHALL execute `show ip route` on the device
2. WHEN global table collection is enabled, THE Routing_Collector SHALL execute `show ip route connected` on the device
3. WHEN BGP is configured on the device, THE BGP_Collector SHALL execute `show ip bgp` to collect BGP prefixes
4. IF BGP is not configured, THEN THE BGP_Collector SHALL handle the error gracefully and continue collection
5. WHEN global table collection completes, THE Routing_Collector SHALL tag all collected prefixes with vrf="global"

### Requirement 3: Per-VRF Routing Table Collection

**User Story:** As a network engineer, I want to collect routing information from each VRF, so that I can inventory prefixes in all routing tables.

#### Acceptance Criteria

1. WHEN per-VRF collection is enabled, THE Routing_Collector SHALL execute `show ip route vrf <VRF>` for each discovered VRF
2. WHEN per-VRF collection is enabled, THE Routing_Collector SHALL execute `show ip route vrf <VRF> connected` for each discovered VRF
3. WHEN collecting from IOS or IOS-XE devices, THE BGP_Collector SHALL execute `show ip bgp vpnv4 vrf <VRF>` for each VRF
4. WHEN collecting from NX-OS devices, THE BGP_Collector SHALL execute `show ip bgp vrf <VRF>` for each VRF
5. WHEN per-VRF collection completes, THE Routing_Collector SHALL tag all collected prefixes with the VRF name

### Requirement 4: Terminal Pagination Control

**User Story:** As a network engineer, I want command outputs to be complete without pagination, so that all prefixes are captured.

#### Acceptance Criteria

1. WHEN connecting to any Cisco device, THE Connection_Manager SHALL execute `terminal length 0` before collecting routing information
2. WHEN pagination is disabled, THE Routing_Collector SHALL receive complete command outputs without manual intervention
3. IF pagination control fails, THEN THE Connection_Manager SHALL log the error and attempt collection anyway

### Requirement 5: Prefix Extraction and Parsing

**User Story:** As a network engineer, I want to extract all IPv4 prefixes from command outputs, so that I can inventory network allocations.

#### Acceptance Criteria

1. WHEN parsing routing table output, THE Prefix_Parser SHALL extract prefixes in CIDR format (e.g., 192.168.1.0/24)
2. WHEN parsing routing table output, THE Prefix_Parser SHALL extract prefixes in mask format (e.g., 192.168.1.0 255.255.255.0)
3. WHEN parsing BGP output, THE Prefix_Parser SHALL extract network addresses with or without explicit length
4. WHEN parsing routing table output, THE Prefix_Parser SHALL extract /32 local routes (L route code)
5. WHEN parsing routing table output, THE Prefix_Parser SHALL extract loopback interface addresses
6. WHEN parsing any output, THE Prefix_Parser SHALL preserve the raw output line for debugging purposes

### Requirement 6: Prefix Normalization

**User Story:** As a network engineer, I want all prefixes normalized to CIDR notation, so that I can compare and analyze them consistently.

#### Acceptance Criteria

1. WHEN a prefix is in mask format, THE Prefix_Normalizer SHALL convert it to CIDR notation using the ipaddress library
2. WHEN a prefix is already in CIDR format, THE Prefix_Normalizer SHALL validate and preserve it
3. WHEN a prefix has an invalid format, THE Prefix_Normalizer SHALL log the error and add it to the exceptions report
4. WHEN normalizing any prefix, THE Prefix_Normalizer SHALL validate that the result is a valid IPv4 network in CIDR notation
5. WHEN normalization completes, THE Prefix_Normalizer SHALL return the prefix in standard CIDR format (e.g., 192.168.1.0/24)

### Requirement 7: Ambiguous Prefix Resolution

**User Story:** As a network engineer, I want ambiguous prefixes (without explicit length) to be resolved, so that I can determine the actual subnet mask.

#### Acceptance Criteria

1. WHEN a BGP prefix lacks explicit length, THE Ambiguity_Resolver SHALL attempt `show ip bgp <prefix>` to determine the mask
2. WHEN a BGP prefix lacks explicit length, THE Ambiguity_Resolver SHALL attempt `show ip route <prefix>` to determine the mask
3. IF both resolution attempts fail, THEN THE Ambiguity_Resolver SHALL record the prefix as unresolved in the exceptions report
4. WHEN a prefix is successfully resolved, THE Ambiguity_Resolver SHALL normalize it to CIDR notation
5. WHEN recording an unresolved prefix, THE Ambiguity_Resolver SHALL include the raw token and source command in the exceptions report

### Requirement 8: Prefix Metadata Tagging

**User Story:** As a network engineer, I want each prefix tagged with metadata, so that I can trace its origin and context.

#### Acceptance Criteria

1. WHEN collecting a prefix, THE Prefix_Parser SHALL tag it with the device name
2. WHEN collecting a prefix, THE Prefix_Parser SHALL tag it with the device platform (IOS, IOS-XE, NX-OS)
3. WHEN collecting a prefix, THE Prefix_Parser SHALL tag it with the VRF name (or "global" for global table)
4. WHEN collecting a prefix, THE Prefix_Parser SHALL tag it with the source (rib, connected, or bgp)
5. WHEN collecting a prefix, THE Prefix_Parser SHALL tag it with the routing protocol (B, D, C, L, S, or blank)
6. WHEN collecting a prefix, THE Prefix_Parser SHALL tag it with the collection timestamp
7. WHERE the raw output line is available, THE Prefix_Parser SHALL tag the prefix with the raw_line for debugging

### Requirement 9: Prefix Deduplication

**User Story:** As a network engineer, I want duplicate prefixes removed, so that I can see unique prefix allocations.

#### Acceptance Criteria

1. WHEN deduplicating prefixes, THE Deduplication_Engine SHALL consider (device, vrf, prefix, source) as the unique key
2. WHEN multiple identical entries exist, THE Deduplication_Engine SHALL keep the first occurrence and discard duplicates
3. WHEN creating the deduplicated view, THE Deduplication_Engine SHALL group by (vrf, prefix) across all devices
4. WHEN creating the deduplicated view, THE Deduplication_Engine SHALL include a list of devices where each prefix appears
5. WHEN creating the deduplicated view, THE Deduplication_Engine SHALL include a count of devices for each prefix

### Requirement 10: Primary CSV Export

**User Story:** As a network engineer, I want prefix data exported to CSV, so that I can analyze it with external tools.

#### Acceptance Criteria

1. WHEN exporting to CSV, THE Excel_Exporter SHALL create a file named `prefixes.csv`
2. WHEN exporting to CSV, THE Excel_Exporter SHALL include columns: device, platform, vrf, prefix, source, protocol, timestamp
3. WHEN exporting to CSV, THE Excel_Exporter SHALL sort rows by vrf, then prefix, then device
4. WHEN exporting to CSV, THE Excel_Exporter SHALL use UTF-8 encoding
5. WHEN export completes, THE Excel_Exporter SHALL log the output file path

### Requirement 11: Deduplicated CSV Export

**User Story:** As a network engineer, I want a deduplicated view of prefixes by VRF, so that I can see unique allocations across the network.

#### Acceptance Criteria

1. WHEN exporting deduplicated data, THE Excel_Exporter SHALL create a file named `prefixes_dedup_by_vrf.csv`
2. WHEN exporting deduplicated data, THE Excel_Exporter SHALL include columns: vrf, prefix, device_count, device_list
3. WHEN exporting deduplicated data, THE Excel_Exporter SHALL sort rows by vrf, then prefix
4. WHEN exporting deduplicated data, THE Excel_Exporter SHALL format device_list as a semicolon-separated string
5. WHEN export completes, THE Excel_Exporter SHALL log the output file path

### Requirement 12: Exceptions Report Export

**User Story:** As a network engineer, I want parsing errors and unresolved prefixes reported, so that I can investigate issues.

#### Acceptance Criteria

1. WHEN exporting exceptions, THE Exception_Reporter SHALL create a file named `exceptions.csv`
2. WHEN exporting exceptions, THE Exception_Reporter SHALL include columns: device, command, error_type, raw_token, timestamp
3. WHEN a command fails, THE Exception_Reporter SHALL record the device, command, and error message
4. WHEN a prefix cannot be resolved, THE Exception_Reporter SHALL record the device, raw token, and resolution attempts
5. WHEN a parsing error occurs, THE Exception_Reporter SHALL record the device, command, and problematic line

### Requirement 13: Excel Export with Formatting

**User Story:** As a network engineer, I want results exported to Excel with professional formatting, so that reports are presentation-ready.

#### Acceptance Criteria

1. WHEN exporting to Excel, THE Excel_Exporter SHALL create a workbook with sheets: Prefixes, Deduplicated, Exceptions
2. WHEN exporting to Excel, THE Excel_Exporter SHALL apply header formatting (bold, colored background)
3. WHEN exporting to Excel, THE Excel_Exporter SHALL apply column auto-sizing for readability
4. WHEN exporting to Excel, THE Excel_Exporter SHALL apply data filters to all columns
5. WHEN exporting to Excel, THE Excel_Exporter SHALL use the existing NetWalker Excel export patterns

### Requirement 14: Database Storage

**User Story:** As a network engineer, I want prefix data stored in the NetWalker database, so that I can track changes over time.

#### Acceptance Criteria

1. WHEN database storage is enabled, THE Database_Storage SHALL create a table named `ipv4_prefixes`
2. WHEN storing prefixes, THE Database_Storage SHALL include columns: device_id, vrf, prefix, source, protocol, first_seen, last_seen
3. WHEN storing a prefix, THE Database_Storage SHALL link it to the device via device_id foreign key
4. WHEN a prefix already exists, THE Database_Storage SHALL update the last_seen timestamp
5. WHEN a prefix is new, THE Database_Storage SHALL insert it with first_seen and last_seen timestamps
6. WHEN database storage is disabled, THE Prefix_Inventory_Module SHALL skip database operations and continue with file exports

### Requirement 15: Route Summarization Tracking

**User Story:** As a network engineer, I want to track route summarization relationships, so that I can trace how specific routes are aggregated up through the network hierarchy.

#### Acceptance Criteria

1. WHEN database storage is enabled, THE Database_Storage SHALL create a table named `ipv4_prefix_summarization`
2. WHEN storing summarization relationships, THE Database_Storage SHALL include columns: summary_prefix_id, component_prefix_id, device_id, created_at
3. WHEN a summary route is detected, THE Database_Storage SHALL identify component routes that fall within the summary prefix range
4. WHEN storing a summarization relationship, THE Database_Storage SHALL link the summary prefix to its component prefixes via foreign keys
5. WHEN storing a summarization relationship, THE Database_Storage SHALL record which device performed the summarization
6. WHEN querying summarization data, THE Database_Storage SHALL support recursive queries to trace from specific routes up to root summaries
7. WHEN a prefix is both a component and a summary, THE Database_Storage SHALL record both relationships to support multi-level hierarchies

### Requirement 16: Command Failure Handling

**User Story:** As a network engineer, I want command failures to be handled gracefully, so that collection continues for other devices and commands.

#### Acceptance Criteria

1. IF a command fails on a device, THEN THE Command_Executor SHALL log the error and continue with remaining commands
2. IF a device connection fails, THEN THE Command_Executor SHALL log the error and continue with remaining devices
3. IF a command times out, THEN THE Command_Executor SHALL log the timeout and continue with remaining commands
4. WHEN a command fails, THE Exception_Reporter SHALL record the failure in the exceptions report
5. WHEN collection completes, THE Prefix_Inventory_Module SHALL report the count of successful and failed devices

### Requirement 17: VRF Name Handling

**User Story:** As a network engineer, I want VRF names with special characters handled correctly, so that commands execute successfully.

#### Acceptance Criteria

1. WHEN a VRF name contains spaces, THE Routing_Collector SHALL quote the VRF name in commands
2. WHEN a VRF name contains special characters, THE Routing_Collector SHALL escape the characters appropriately
3. WHEN executing a VRF-specific command, THE Routing_Collector SHALL validate the VRF name format before execution
4. IF a VRF name is invalid, THEN THE Routing_Collector SHALL log the error and skip that VRF
5. WHEN VRF name handling completes, THE Routing_Collector SHALL log the sanitized VRF name used in commands

### Requirement 18: Concurrent Device Processing

**User Story:** As a network engineer, I want devices processed concurrently, so that collection completes in reasonable time.

#### Acceptance Criteria

1. WHEN processing multiple devices, THE Prefix_Inventory_Module SHALL use ThreadPool for concurrent execution
2. WHEN using concurrent processing, THE Prefix_Inventory_Module SHALL respect the configured concurrency limit from NetWalker settings
3. WHEN processing devices concurrently, THE Prefix_Inventory_Module SHALL ensure thread-safe access to shared data structures
4. WHEN a device processing thread fails, THE Prefix_Inventory_Module SHALL not affect other threads
5. WHEN all threads complete, THE Prefix_Inventory_Module SHALL aggregate results from all devices

### Requirement 19: Progress Reporting

**User Story:** As a network engineer, I want progress updates during collection, so that I can monitor the operation.

#### Acceptance Criteria

1. WHEN collection starts, THE Prefix_Inventory_Module SHALL display the total number of devices to process
2. WHEN processing each device, THE Prefix_Inventory_Module SHALL display the device name and progress count
3. WHEN a device completes successfully, THE Prefix_Inventory_Module SHALL display a success indicator
4. WHEN a device fails, THE Prefix_Inventory_Module SHALL display a failure indicator with error summary
5. WHEN collection completes, THE Prefix_Inventory_Module SHALL display a summary with total devices, successes, failures, and execution time

### Requirement 20: Configuration Integration

**User Story:** As a network engineer, I want prefix inventory configured via INI file, so that I can customize behavior without code changes.

#### Acceptance Criteria

1. WHEN loading configuration, THE Prefix_Inventory_Module SHALL read settings from the `[ipv4_prefix_inventory]` section of netwalker.ini
2. WHERE global table collection is configured, THE Prefix_Inventory_Module SHALL enable or disable global table collection
3. WHERE per-VRF collection is configured, THE Prefix_Inventory_Module SHALL enable or disable per-VRF collection
4. WHERE BGP collection is configured, THE Prefix_Inventory_Module SHALL enable or disable BGP prefix collection
5. WHERE output directory is configured, THE Prefix_Inventory_Module SHALL use the specified directory for CSV and Excel exports
6. WHERE database storage is configured, THE Prefix_Inventory_Module SHALL enable or disable database storage
7. WHERE concurrency limit is configured, THE Prefix_Inventory_Module SHALL use the specified thread pool size

### Requirement 21: Existing NetWalker Integration

**User Story:** As a network engineer, I want prefix inventory to integrate with existing NetWalker components, so that I can leverage existing infrastructure.

#### Acceptance Criteria

1. WHEN connecting to devices, THE Prefix_Inventory_Module SHALL use the existing Connection_Manager
2. WHEN authenticating to devices, THE Prefix_Inventory_Module SHALL use the existing Credential_Manager
3. WHEN querying device inventory, THE Prefix_Inventory_Module SHALL use the existing Database_Manager
4. WHEN executing commands, THE Prefix_Inventory_Module SHALL use the existing Command_Executor framework
5. WHEN exporting to Excel, THE Prefix_Inventory_Module SHALL use the existing Excel export patterns from netwalker.reports.excel_generator
6. WHEN logging operations, THE Prefix_Inventory_Module SHALL use the existing NetWalker logging infrastructure

### Requirement 22: Summary Statistics

**User Story:** As a network engineer, I want summary statistics after collection, so that I can quickly assess the inventory.

#### Acceptance Criteria

1. WHEN collection completes, THE Prefix_Inventory_Module SHALL display the total number of prefixes collected
2. WHEN collection completes, THE Prefix_Inventory_Module SHALL display the count of prefixes per VRF
3. WHEN collection completes, THE Prefix_Inventory_Module SHALL display the count of prefixes per source (rib, connected, bgp)
4. WHEN collection completes, THE Prefix_Inventory_Module SHALL display the count of /32 host routes
5. WHEN collection completes, THE Prefix_Inventory_Module SHALL display the count of unresolved prefixes
6. WHERE a summary file is configured, THE Prefix_Inventory_Module SHALL write statistics to `summary.txt`

### Requirement 23: Modular Code Structure

**User Story:** As a developer, I want the code organized in modules, so that it is maintainable and testable.

#### Acceptance Criteria

1. THE Prefix_Inventory_Module SHALL organize collection logic in `netwalker/ipv4_prefix/collector.py`
2. THE Prefix_Inventory_Module SHALL organize parsing logic in `netwalker/ipv4_prefix/parser.py`
3. THE Prefix_Inventory_Module SHALL organize normalization logic in `netwalker/ipv4_prefix/normalizer.py`
4. THE Prefix_Inventory_Module SHALL organize export logic in `netwalker/ipv4_prefix/exporter.py`
5. THE Prefix_Inventory_Module SHALL organize data models in `netwalker/ipv4_prefix/data_models.py`
6. THE Prefix_Inventory_Module SHALL provide a main entry point in `netwalker/ipv4_prefix/__init__.py`

### Requirement 24: Unit Test Coverage

**User Story:** As a developer, I want unit tests for parsers, so that I can verify correctness with sample outputs.

#### Acceptance Criteria

1. WHEN testing the Prefix_Parser, THE test suite SHALL include sample outputs from `show ip route`
2. WHEN testing the Prefix_Parser, THE test suite SHALL include sample outputs from `show ip bgp vpnv4 vrf WAN`
3. WHEN testing the Prefix_Parser, THE test suite SHALL include sample outputs with ambiguous prefixes (e.g., 10.0.0.0 without /len)
4. WHEN testing the Prefix_Normalizer, THE test suite SHALL verify conversion from mask format to CIDR
5. WHEN testing the Ambiguity_Resolver, THE test suite SHALL verify resolution attempts and exception handling
