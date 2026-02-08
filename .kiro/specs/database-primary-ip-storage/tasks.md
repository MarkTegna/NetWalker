# Implementation Plan: Database Primary IP Storage

## Overview

This implementation adds storage of the primary management IP address during device discovery. The changes are minimal and focused on the DatabaseManager.process_device_discovery() method. The existing database schema and query methods require no modifications.

## Tasks

- [x] 1. Modify process_device_discovery() to store primary_ip
  - Extract primary_ip from device_info dictionary
  - Create interface record with interface_name='Primary Management' and interface_type='management'
  - Call upsert_device_interface() to store primary_ip before processing other interfaces
  - Add validation to skip storage if primary_ip is None or empty
  - Add debug logging for primary_ip extraction and storage
  - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.2_

- [x] 1.1 Write property test for primary IP storage completeness
  - **Property 1: Primary IP Storage Completeness**
  - **Validates: Requirements 1.1, 1.2, 1.3, 4.2**

- [x] 1.2 Write property test for primary IP storage idempotence
  - **Property 2: Primary IP Storage Idempotence**
  - **Validates: Requirements 1.4**

- [x] 1.3 Write unit test for primary IP storage example
  - Test specific device_info with known primary_ip
  - Verify storage in device_interfaces table
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Checkpoint - Verify primary IP storage works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Write property test for database query returns valid IPs
  - **Property 3: Database Query Returns Valid IPs**
  - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

- [x] 3.1 Write unit test for query integration
  - Store device with only primary_ip
  - Query using get_stale_devices() and get_unwalked_devices()
  - Verify primary_ip is returned
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 4. Write property test for IP address format validation
  - **Property 4: IP Address Format Validation**
  - **Validates: Requirements 4.1**

- [x] 5. Write property test for primary IP update on rediscovery
  - **Property 5: Primary IP Update on Rediscovery**
  - **Validates: Requirements 4.3**

- [x] 5.1 Write unit test for backward compatibility
  - Query legacy devices without primary_ip
  - Verify graceful handling with no errors
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 6. Write integration test for connection manager compatibility
  - Get devices from database queries
  - Verify format is compatible with Connection Manager
  - _Requirements: 3.1, 3.2_

- [x] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks are required for comprehensive testing and validation
- The core implementation is minimal (only task 1) - just adding primary_ip storage to existing method
- No database schema changes required - uses existing device_interfaces table
- No changes required to query methods - they already prioritize 'Management' interfaces
- Property tests validate universal correctness across many inputs
- Unit tests validate specific examples and integration points
- Backward compatibility is maintained - legacy devices without primary_ip will continue to work
