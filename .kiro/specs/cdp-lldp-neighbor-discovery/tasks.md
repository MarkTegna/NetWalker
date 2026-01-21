# Implementation Plan: CDP/LLDP Neighbor Discovery Database Storage

## Overview

This implementation plan adds database storage for CDP/LLDP neighbor connections to NetWalker. The feature leverages existing neighbor collection code and adds persistence to the SQL Server database, enabling topology visualization and historical tracking.

## Tasks

- [-] 1. Create database schema and models
  - [x] 1.1 Add DeviceNeighbor data model to models.py
    - Create DeviceNeighbor dataclass with all required fields
    - Include neighbor_id, source_device_id, source_interface, destination_device_id, destination_interface, protocol, timestamps
    - _Requirements: 1.1_

  - [x] 1.2 Add device_neighbors table creation to DatabaseManager.initialize_database()
    - Create table with all columns, constraints, and indexes
    - Add foreign key constraints to devices table (source CASCADE, destination NO ACTION)
    - Add unique constraint on (source_device_id, source_interface, destination_device_id, destination_interface)
    - Add indexes on source_device_id, destination_device_id, last_seen, protocol
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ] 1.3 Write property test for foreign key constraint enforcement
    - **Property 1: Foreign Key Constraint Enforcement**
    - **Validates: Requirements 1.2**

  - [ ] 1.4 Write property test for unique constraint enforcement
    - **Property 2: Unique Connection Constraint**
    - **Validates: Requirements 1.3**

- [-] 2. Implement interface name normalization
  - [x] 2.1 Enhance ProtocolParser.normalize_interface_name() method
    - Add platform parameter to method signature
    - Implement IOS abbreviation expansion (Gi→GigabitEthernet, Te→TenGigabitEthernet, Fa→FastEthernet)
    - Preserve NX-OS formats (Ethernet1/1 stays as-is)
    - Standardize port-channels to "Port-channel" format
    - Standardize management interfaces to "Management" format
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ] 2.2 Write unit tests for interface normalization
    - Test IOS abbreviation expansion examples
    - Test NX-OS format preservation
    - Test port-channel standardization
    - Test management interface standardization
    - _Requirements: 3.2, 3.4, 3.5_

  - [ ] 2.3 Write property test for interface normalization
    - **Property 7: Interface Name Normalization**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

- [-] 3. Implement hostname resolution
  - [x] 3.1 Add DatabaseManager.resolve_hostname_to_device_id() method
    - Strip domain suffix from FQDN (e.g., "router.example.com" → "router")
    - Query devices table by device_name
    - If multiple matches, return device with most recent last_seen
    - Return None if no match found
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ] 3.2 Write unit tests for hostname resolution
    - Test FQDN stripping
    - Test multiple matches returning most recent
    - Test unresolved hostname returning None
    - _Requirements: 6.2, 6.4_

  - [ ] 3.3 Write property test for hostname resolution
    - **Property 4: Hostname Resolution**
    - **Validates: Requirements 2.2, 6.1, 6.2, 6.4**

- [-] 4. Implement bidirectional connection deduplication
  - [x] 4.1 Add DatabaseManager.check_reverse_connection() method
    - Query device_neighbors for reverse connection (dest→source with swapped interfaces)
    - Return neighbor_id if reverse exists, None otherwise
    - _Requirements: 4.1_

  - [x] 4.2 Add DatabaseManager.get_consistent_direction() helper method
    - Compare source_device_id and destination_device_id
    - Return connection with lower device_id as source
    - Swap interfaces if direction is reversed
    - _Requirements: 4.4_

  - [ ] 4.3 Write unit tests for deduplication logic
    - Test reverse connection detection
    - Test consistent direction ordering
    - _Requirements: 4.1, 4.4_

  - [ ] 4.4 Write property test for bidirectional deduplication
    - **Property 8: Bidirectional Connection Deduplication**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [-] 5. Implement neighbor upsert operations
  - [x] 5.1 Add DatabaseManager.upsert_neighbor_connection() method
    - Check if connection exists (exact match on source, source_if, dest, dest_if)
    - If exists, update last_seen timestamp
    - If not exists, insert new record with first_seen and last_seen set to current time
    - Handle database errors gracefully, log and continue
    - _Requirements: 2.4, 2.5_

  - [x] 5.2 Add DatabaseManager.upsert_device_neighbors() method
    - Accept device_id and list of NeighborInfo objects
    - For each neighbor:
      - Resolve hostname to destination_device_id
      - Skip if resolution fails (log warning)
      - Normalize interface names
      - Check for reverse connection
      - If reverse exists, update it
      - If not, insert with consistent direction
    - Return count of successfully stored neighbors
    - Continue processing on individual failures
    - _Requirements: 2.1, 2.2, 2.3, 5.2, 8.5_

  - [ ] 5.3 Write unit tests for upsert operations
    - Test update existing connection
    - Test insert new connection
    - Test error handling for individual failures
    - _Requirements: 2.4, 2.5, 5.2_

  - [ ] 5.4 Write property test for upsert behavior
    - **Property 6: Neighbor Upsert Behavior**
    - **Validates: Requirements 2.4, 2.5**

  - [ ] 5.5 Write property test for neighbor storage completeness
    - **Property 3: Neighbor Storage During Discovery**
    - **Validates: Requirements 2.1, 5.1**

  - [ ] 5.6 Write property test for unresolved neighbor handling
    - **Property 5: Unresolved Neighbor Handling**
    - **Validates: Requirements 2.3, 6.3**

  - [ ] 5.7 Write property test for error resilience
    - **Property 10: Error Resilience**
    - **Validates: Requirements 5.2, 8.5**

- [-] 6. Integrate neighbor storage with discovery workflow
  - [x] 6.1 Modify DatabaseManager.process_device_discovery() to store neighbors
    - After storing device, versions, interfaces, and VLANs, call upsert_device_neighbors()
    - Pass device_id and neighbors list from device_info
    - Log success/failure with neighbor count
    - Continue discovery even if neighbor storage fails
    - _Requirements: 5.1, 8.1, 8.2_

  - [ ] 6.2 Write integration test for discovery workflow
    - Test full device discovery with neighbors
    - Verify neighbors are stored in database
    - Verify discovery continues on neighbor storage failure
    - _Requirements: 5.1, 5.2_

- [-] 7. Implement neighbor query operations
  - [x] 7.1 Add DatabaseManager.get_device_neighbors() method
    - Query device_neighbors where device is source OR destination
    - Join with devices table to get device names
    - Return list of dictionaries with source_name, source_interface, dest_name, dest_interface, protocol
    - _Requirements: 4.5, 5.5, 9.1, 9.2_

  - [x] 7.2 Add DatabaseManager.get_neighbors_by_protocol() method
    - Query device_neighbors filtered by protocol (CDP or LLDP)
    - Return list of connections with all fields
    - _Requirements: 7.4_

  - [ ] 7.3 Add DatabaseManager.get_unresolved_neighbors() method
    - Track unresolved neighbors during upsert operations
    - Return list of neighbors that couldn't be resolved
    - Include hostname, source device, and reason
    - _Requirements: 6.5_

  - [ ] 7.4 Write unit tests for query operations
    - Test bidirectional neighbor queries
    - Test protocol filtering
    - Test unresolved neighbor tracking
    - _Requirements: 4.5, 7.4, 6.5_

  - [ ] 7.5 Write property test for bidirectional queries
    - **Property 9: Bidirectional Connection Queries**
    - **Validates: Requirements 4.5, 5.5**

  - [ ] 7.6 Write property test for protocol filtering
    - **Property 12: Protocol Query Filtering**
    - **Validates: Requirements 7.4**

  - [ ] 7.7 Write property test for query result completeness
    - **Property 13: Connection Query Results**
    - **Validates: Requirements 9.1, 9.2**

- [ ] 8. Implement protocol tracking and preference
  - [ ] 8.1 Update upsert_neighbor_connection() to handle protocol preference
    - When updating existing connection, check if new protocol is CDP and device is Cisco
    - If so, update protocol field to CDP (prefer CDP over LLDP for Cisco)
    - Otherwise, update protocol to most recent discovery
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ] 8.2 Write unit tests for protocol preference
    - Test CDP preference for Cisco devices
    - Test protocol update on re-discovery
    - _Requirements: 7.2, 7.3_

  - [ ] 8.3 Write property test for protocol storage
    - **Property 11: Protocol Storage and Preference**
    - **Validates: Requirements 7.1, 7.2, 7.3**

- [-] 9. Implement data cleanup operations
  - [x] 9.1 Add DatabaseManager.cleanup_stale_neighbors() method
    - Accept days parameter
    - Delete neighbors where last_seen < (current_date - days)
    - Return count of deleted neighbors
    - Log deletion count
    - _Requirements: 10.1, 10.2_

  - [x] 9.2 Update DatabaseManager.purge_database() to include device_neighbors
    - Add DELETE FROM device_neighbors to purge operation
    - Ensure proper order (delete neighbors before devices)
    - _Requirements: 10.3_

  - [ ] 9.3 Write unit tests for cleanup operations
    - Test stale neighbor deletion
    - Test purge includes neighbors
    - Test cascade deletion on device removal
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [ ] 9.4 Write property test for stale connection cleanup
    - **Property 15: Stale Connection Cleanup**
    - **Validates: Requirements 10.1, 10.2**

  - [ ] 9.5 Write property test for cascade deletion
    - **Property 16: Cascade Deletion**
    - **Validates: Requirements 10.4**

- [-] 10. Update Visio generator for topology visualization
  - [x] 10.1 Modify VisioGenerator to query neighbor data from database
    - Add method to retrieve connections for devices in current diagram
    - Filter out connections where destination device is not in diagram
    - _Requirements: 9.3, 9.5_

  - [x] 10.2 Add connection drawing to Visio diagram generation
    - For each connection, draw connector between source and destination shapes
    - Label connector with source and destination interface names
    - Handle missing destination devices gracefully (skip connection)
    - _Requirements: 9.4, 9.5_

  - [ ] 10.3 Write property test for missing destination handling
    - **Property 14: Missing Destination Handling**
    - **Validates: Requirements 9.5**

  - [ ] 10.4 Write integration test for Visio generation with connections
    - Generate diagram from database with neighbor data
    - Verify connections are drawn
    - Verify interface labels are correct
    - _Requirements: 9.3, 9.4_

- [ ] 11. Update DATABASE_STRUCTURE.md documentation
  - [ ] 11.1 Add device_neighbors table schema documentation
    - Document all columns, data types, constraints, and indexes
    - Include business rules for deduplication and consistent direction
    - Add data flow diagram for neighbor discovery and storage
    - Update "Future Enhancements" section to remove device_neighbors
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 12. Final integration and testing
  - [ ] 12.1 Run full discovery on test network
    - Verify neighbors are collected and stored correctly
    - Check database for expected connections
    - Verify deduplication is working
    - Test with both CDP and LLDP devices

  - [ ] 12.2 Generate Visio diagram with connections
    - Verify connections appear on diagram
    - Verify interface labels are correct
    - Test with various network topologies

  - [ ] 12.3 Test cleanup operations
    - Mark some connections as stale
    - Run cleanup and verify deletion
    - Test cascade deletion by removing devices

  - [ ] 12.4 Ensure all tests pass
    - Run all unit tests
    - Run all property tests (minimum 100 iterations each)
    - Run all integration tests
    - Fix any failures

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties with minimum 100 iterations
- Unit tests validate specific examples and edge cases
- Integration tests verify end-to-end workflows
- The design leverages existing neighbor collection code, minimizing changes to discovery workflow
- Database operations use upsert pattern to handle both new and existing connections
- Deduplication ensures each physical connection is stored only once
- Interface normalization enables reliable matching across different device platforms
