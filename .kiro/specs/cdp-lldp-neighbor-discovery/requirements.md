# Requirements Document

## Introduction

This specification defines the requirements for adding CDP/LLDP neighbor database storage to NetWalker. NetWalker currently collects neighbor information during device discovery using CDP and LLDP protocols, but this data is not persisted to the SQL Server database. This feature will enable storing neighbor/connection data in the database to support network topology visualization and analysis.

## Glossary

- **NetWalker**: Network topology discovery tool that collects device inventory and neighbor information
- **CDP**: Cisco Discovery Protocol - Layer 2 protocol for discovering directly connected Cisco devices
- **LLDP**: Link Layer Discovery Protocol - Vendor-neutral Layer 2 protocol for discovering directly connected devices
- **Neighbor**: A directly connected network device discovered via CDP or LLDP
- **Connection**: A bidirectional link between two network devices
- **Database_Manager**: Component responsible for SQL Server database operations
- **Device_Collector**: Component that collects device information including neighbors
- **Protocol_Parser**: Component that parses CDP and LLDP output
- **NeighborInfo**: Data structure containing neighbor information (device_id, local_interface, remote_interface, platform, capabilities, ip_address, protocol)
- **Topology**: The physical or logical arrangement of network devices and their connections

## Requirements

### Requirement 1: Database Schema for Neighbor Storage

**User Story:** As a network administrator, I want neighbor connection data stored in the database, so that I can query and analyze network topology over time.

#### Acceptance Criteria

1. THE Database_Manager SHALL create a device_neighbors table with columns for source_device_id, source_interface, destination_device_id, destination_interface, protocol, first_seen, last_seen, created_at, updated_at
2. THE device_neighbors table SHALL enforce foreign key constraints to the devices table for both source and destination devices
3. THE device_neighbors table SHALL include a unique constraint on (source_device_id, source_interface, destination_device_id, destination_interface) to prevent duplicate connections
4. THE device_neighbors table SHALL include indexes on source_device_id, destination_device_id, and last_seen columns for query performance
5. THE Database_Manager SHALL create the device_neighbors table during database initialization if it does not exist

### Requirement 2: Neighbor Data Persistence

**User Story:** As a network administrator, I want neighbor data automatically saved to the database during discovery, so that I have a historical record of network connections.

#### Acceptance Criteria

1. WHEN a device is successfully discovered, THE Database_Manager SHALL store all neighbor connections for that device in the device_neighbors table
2. WHEN storing neighbor data, THE Database_Manager SHALL resolve device hostnames to device_ids using the devices table
3. IF a destination device does not exist in the devices table, THEN THE Database_Manager SHALL skip storing that neighbor connection and log a warning
4. WHEN a neighbor connection already exists in the database, THE Database_Manager SHALL update the last_seen timestamp
5. WHEN a neighbor connection does not exist in the database, THE Database_Manager SHALL insert a new record with first_seen and last_seen timestamps set to the current time

### Requirement 3: Interface Name Normalization

**User Story:** As a network administrator, I want interface names stored consistently, so that I can reliably match connections discovered from both ends.

#### Acceptance Criteria

1. THE Protocol_Parser SHALL normalize interface names before storing them in the database
2. WHEN normalizing interface names, THE Protocol_Parser SHALL convert common abbreviations to standard formats (e.g., "Gi1/0/1" to "GigabitEthernet1/0/1", "Eth1/1" to "Ethernet1/1")
3. WHEN normalizing interface names, THE Protocol_Parser SHALL preserve the original interface format for NEXUS devices (e.g., "Ethernet1/1" remains "Ethernet1/1")
4. THE Protocol_Parser SHALL handle port-channel interfaces consistently (e.g., "Po1" and "port-channel1" both normalize to "Port-channel1")
5. THE Protocol_Parser SHALL handle management interfaces consistently (e.g., "mgmt0" and "Mgmt0" both normalize to "Management0")

### Requirement 4: Bidirectional Connection Deduplication

**User Story:** As a network administrator, I want each physical connection stored only once, so that I don't see duplicate connections in topology diagrams.

#### Acceptance Criteria

1. WHEN storing a neighbor connection, THE Database_Manager SHALL check if the reverse connection already exists (destination→source)
2. IF the reverse connection exists, THEN THE Database_Manager SHALL update the existing record's last_seen timestamp instead of creating a duplicate
3. IF the reverse connection does not exist, THEN THE Database_Manager SHALL create a new connection record
4. THE Database_Manager SHALL store connections in a consistent direction (lower device_id as source, higher device_id as destination) to ensure deduplication
5. WHEN querying connections, THE Database_Manager SHALL provide a method to retrieve all connections for a device regardless of direction

### Requirement 5: Discovery Integration

**User Story:** As a network administrator, I want neighbor data collection to integrate seamlessly with existing discovery, so that I don't need to change my workflow.

#### Acceptance Criteria

1. WHEN the Database_Manager processes device discovery, THE Database_Manager SHALL automatically store neighbor data if database storage is enabled
2. IF neighbor data storage fails, THEN THE Database_Manager SHALL log an error but continue processing other device data
3. THE Database_Manager SHALL store neighbor data in the same database transaction as device data to ensure consistency
4. WHEN database storage is disabled, THE Discovery_Engine SHALL continue collecting neighbor data for in-memory use
5. THE Database_Manager SHALL provide a method to query all neighbors for a specific device by device_id

### Requirement 6: Hostname Resolution and Validation

**User Story:** As a network administrator, I want neighbor hostnames properly resolved to database device IDs, so that connections reference the correct devices.

#### Acceptance Criteria

1. WHEN resolving a neighbor hostname to a device_id, THE Database_Manager SHALL query the devices table by device_name
2. IF multiple devices match the hostname, THE Database_Manager SHALL use the device with the most recent last_seen timestamp
3. IF no device matches the hostname, THE Database_Manager SHALL log a warning and skip storing that neighbor connection
4. THE Database_Manager SHALL handle hostname variations (FQDN vs short name) by stripping domain suffixes before lookup
5. THE Database_Manager SHALL provide a method to retrieve unresolved neighbors (neighbors whose destination device is not in the database)

### Requirement 7: Protocol Tracking

**User Story:** As a network administrator, I want to know which protocol discovered each connection, so that I can troubleshoot discovery issues.

#### Acceptance Criteria

1. THE device_neighbors table SHALL store the protocol (CDP or LLDP) used to discover each connection
2. WHEN a connection is discovered by both CDP and LLDP, THE Database_Manager SHALL prefer CDP for Cisco devices
3. WHEN a connection is discovered by both CDP and LLDP, THE Database_Manager SHALL update the protocol field to reflect the most recent discovery
4. THE Database_Manager SHALL provide a method to query connections by protocol type
5. THE Database_Manager SHALL include protocol information in connection query results

### Requirement 8: Error Handling and Logging

**User Story:** As a network administrator, I want detailed logging of neighbor storage operations, so that I can troubleshoot issues.

#### Acceptance Criteria

1. WHEN neighbor data storage succeeds, THE Database_Manager SHALL log an info message with the count of connections stored
2. WHEN neighbor data storage fails, THE Database_Manager SHALL log an error message with the specific failure reason
3. IF a destination device cannot be resolved, THE Database_Manager SHALL log a warning with the unresolved hostname
4. WHEN database constraints are violated, THE Database_Manager SHALL log the constraint violation details
5. THE Database_Manager SHALL continue processing remaining neighbors even if individual neighbor storage fails

### Requirement 9: Visio Integration Support

**User Story:** As a network administrator, I want Visio diagrams to show connections between devices, so that I can visualize network topology.

#### Acceptance Criteria

1. THE Database_Manager SHALL provide a method to retrieve all connections for devices in a specific discovery session
2. THE connection query method SHALL return source device name, source interface, destination device name, destination interface, and protocol
3. THE Visio_Generator SHALL query neighbor data from the database when generating topology diagrams
4. WHEN drawing connections, THE Visio_Generator SHALL use the interface names from the database to label connectors
5. THE Visio_Generator SHALL handle cases where destination devices are not included in the current diagram by omitting those connections

### Requirement 10: Data Retention and Cleanup

**User Story:** As a network administrator, I want old neighbor data automatically cleaned up, so that the database doesn't grow indefinitely.

#### Acceptance Criteria

1. THE Database_Manager SHALL provide a method to mark connections as stale if not seen within a configurable time period
2. THE Database_Manager SHALL provide a method to delete connections marked as stale
3. WHEN purging the database, THE Database_Manager SHALL delete all records from the device_neighbors table
4. WHEN deleting a device, THE Database_Manager SHALL automatically delete all neighbor connections for that device via CASCADE constraints
5. THE Database_Manager SHALL log the count of connections deleted during cleanup operations

### Requirement 11: Documentation Updates

**User Story:** As a developer, I want the database schema documentation updated, so that I can understand the complete database structure.

#### Acceptance Criteria

1. THE DATABASE_STRUCTURE.md file SHALL be updated to include the device_neighbors table schema
2. THE device_neighbors table documentation SHALL include all columns, data types, constraints, and indexes
3. THE DATABASE_STRUCTURE.md file SHALL include business rules for neighbor connection storage and deduplication
4. THE DATABASE_STRUCTURE.md file SHALL include the data flow for neighbor discovery and storage
5. THE DATABASE_STRUCTURE.md file SHALL update the "Future Enhancements" section to remove device_neighbors as it will be implemented
