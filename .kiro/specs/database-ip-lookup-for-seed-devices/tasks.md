# Implementation Plan: Database IP Lookup for Seed Devices

## Overview

This implementation adds automatic IP resolution for hostname-only seed file entries by querying the database for previously discovered primary IPs, with DNS fallback. The implementation modifies seed file parsing in `netwalker_app.py` and adds a new database query method to `DatabaseManager`, enabling seamless re-discovery of devices using only hostnames.

## Tasks

- [x] 1. Add database query method for hostname-to-IP lookup
  - [x] 1.1 Implement `get_primary_ip_by_hostname()` in DatabaseManager
    - Add method to query devices table for primary IP by hostname
    - Return None for missing entries or database errors
    - Include comprehensive error handling (connection errors, query errors, exceptions)
    - Log errors without raising exceptions
    - _Requirements: 2.1, 2.2, 2.3, 6.1, 6.2, 6.4_

  - [x] 1.2 Write property test for database lookup with stored IPs
    - **Property 2: Database Lookup Returns Stored IP**
    - **Validates: Requirements 2.2**

  - [x] 1.3 Write property test for database lookup with missing entries
    - **Property 3: Database Lookup Returns None for Missing Entries**
    - **Validates: Requirements 2.3**

  - [x] 1.4 Write property test for database error handling
    - **Property 13: Database Error Handling**
    - **Validates: Requirements 6.1, 6.2, 6.4**

  - [x] 1.5 Write unit tests for database query method
    - Test with existing hostname (returns IP)
    - Test with non-existent hostname (returns None)
    - Test with database connection error (returns None, logs error)
    - Test with query error (returns None, logs error)
    - _Requirements: 2.2, 2.3, 6.1, 6.2_

- [x] 2. Implement IP resolution method with fallback chain
  - [x] 2.1 Add `_resolve_ip_for_hostname()` method to NetWalker
    - Implement database lookup as first resolution attempt
    - Implement DNS lookup as fallback when database returns None
    - Return None if both methods fail
    - Add logging for each resolution method (INFO for success, WARNING for failure)
    - Include resolved IP and resolution source in log messages
    - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 2.2 Write property test for resolution fallback chain order
    - **Property 4: Resolution Fallback Chain Order**
    - **Validates: Requirements 2.1, 3.1, 3.2**

  - [x] 2.3 Write property test for database error fallback
    - **Property 14: Database Error Fallback**
    - **Validates: Requirements 6.3**

  - [x] 2.4 Write property test for database resolution logging
    - **Property 7: Database Resolution Logging**
    - **Validates: Requirements 4.1, 4.4**

  - [x] 2.5 Write property test for DNS resolution logging
    - **Property 8: DNS Resolution Logging**
    - **Validates: Requirements 4.2, 4.4**

  - [x] 2.6 Write property test for resolution failure logging
    - **Property 9: Resolution Failure Logging**
    - **Validates: Requirements 4.3, 4.5**

  - [x] 2.7 Write unit tests for IP resolution method
    - Test database resolution success (returns IP, logs "database")
    - Test DNS fallback success (database fails, DNS returns IP, logs "DNS")
    - Test complete failure (both fail, returns None, logs warning)
    - Test DNS error handling (socket.gaierror, socket.timeout)
    - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 4.3_

- [x] 3. Checkpoint - Ensure resolution methods work correctly
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Enhance seed file parser to detect and resolve blank IPs
  - [x] 4.1 Modify `_parse_seed_file()` to detect blank IP addresses
    - Check if IP field is empty or contains only whitespace
    - Call `_resolve_ip_for_hostname()` for entries with blank IPs
    - Skip devices that cannot be resolved (log warning)
    - Use explicit IPs without resolution for entries with non-blank IPs
    - Preserve all other seed file attributes (hostname, status)
    - Maintain entry order in discovery queue
    - _Requirements: 1.1, 1.2, 1.3, 3.3, 3.4, 5.1, 5.3, 5.4, 7.1, 7.2, 7.4_

  - [x] 4.2 Write property test for blank IP detection
    - **Property 1: Blank IP Detection**
    - **Validates: Requirements 1.1, 1.2, 1.3**

  - [x] 4.3 Write property test for resolved IP usage
    - **Property 6: Resolved IP Usage**
    - **Validates: Requirements 3.4, 7.1**

  - [x] 4.4 Write property test for complete resolution failure handling
    - **Property 5: Complete Resolution Failure Handling**
    - **Validates: Requirements 3.3**

  - [x] 4.5 Write property test for explicit IP bypass
    - **Property 10: Explicit IP Bypass**
    - **Validates: Requirements 5.1**

  - [x] 4.6 Write property test for explicit IP preservation
    - **Property 12: Explicit IP Preservation**
    - **Validates: Requirements 5.4**

  - [x] 4.7 Write property test for attribute preservation
    - **Property 15: Attribute Preservation**
    - **Validates: Requirements 7.2**

  - [x] 4.8 Write property test for entry order preservation
    - **Property 17: Entry Order Preservation**
    - **Validates: Requirements 7.4**

  - [x] 4.9 Write unit tests for seed file parser enhancements
    - Test blank IP detection (empty string, whitespace variations)
    - Test explicit IP bypass (no resolution triggered)
    - Test device skipping on resolution failure
    - Test attribute preservation during resolution
    - Test entry order preservation
    - _Requirements: 1.1, 1.2, 1.3, 3.3, 5.1, 7.2, 7.4_

- [x] 5. Add integration tests for end-to-end scenarios
  - [x] 5.1 Write property test for mixed seed file processing
    - **Property 11: Mixed Seed File Processing**
    - **Validates: Requirements 5.3**

  - [x] 5.2 Write property test for format consistency
    - **Property 16: Format Consistency**
    - **Validates: Requirements 7.3**

  - [x] 5.3 Write integration test for database-resolved IPs
    - Create seed file with hostname-only entries
    - Pre-populate database with primary IPs for those hostnames
    - Verify devices are added to discovery queue with database IPs
    - Verify logs show "database" as resolution source
    - _Requirements: 2.2, 3.1, 4.1, 7.1_

  - [x] 5.4 Write integration test for DNS fallback
    - Create seed file with hostname-only entries
    - Ensure hostnames are NOT in database
    - Mock DNS to return IPs
    - Verify devices are added to discovery queue with DNS IPs
    - Verify logs show "DNS" as resolution source
    - _Requirements: 3.2, 4.2, 7.1_

  - [x] 5.5 Write integration test for mixed seed file
    - Create seed file with explicit IPs, database IPs, and DNS IPs
    - Verify all devices are processed correctly
    - Verify explicit IPs bypass resolution
    - Verify resolution methods are logged correctly
    - _Requirements: 5.3, 7.3_

  - [x] 5.6 Write integration test for complete resolution failure
    - Create seed file with unresolvable hostname
    - Ensure hostname is NOT in database
    - Mock DNS to fail
    - Verify device is skipped
    - Verify warning is logged
    - _Requirements: 3.3, 4.3_

- [x] 6. Final checkpoint - Ensure all tests pass and feature works end-to-end
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Each task references specific requirements for traceability
- Property tests validate universal correctness properties across randomized inputs
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end scenarios with real components
- The implementation maintains full backward compatibility with existing seed files
- Database errors gracefully fall back to DNS without breaking discovery
