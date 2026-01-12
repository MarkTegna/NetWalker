# Implementation Plan: Site Boundary Detection Fix

## Overview

This implementation plan addresses the critical failure in NetWalker's site boundary detection system. The current implementation fails to create separate workbooks for devices matching the `*-CORE-*` pattern. This plan provides a systematic approach to diagnose and fix the pattern matching, site extraction, device association, and workbook generation components.

## Tasks

- [x] 1. Investigate current site boundary detection implementation
  - Examine the existing `_identify_site_boundaries()` method in excel_generator.py
  - Analyze the current pattern matching logic and identify failure points
  - Review configuration loading for site_boundary_pattern
  - Document current behavior and root cause of the failure
  - _Requirements: 4.1, 5.1_

- [x] 2. Fix pattern matching and site name extraction
- [x] 2.1 Implement robust pattern matching logic
  - Fix the fnmatch pattern matching to work correctly with `*-CORE-*` pattern
  - Ensure pattern matching works with cleaned hostnames
  - Add validation for pattern format and compilation
  - _Requirements: 1.1, 1.2, 4.3_

- [x] 2.2 Write property test for pattern matching
  - **Property 1: Pattern Matching Consistency**
  - **Validates: Requirements 1.1, 4.3**

- [x] 2.3 Implement site name extraction from hostnames
  - Extract site prefix from hostnames matching the pattern (e.g., "LUMT-CORE-A" → "LUMT")
  - Handle various hostname formats and edge cases
  - Integrate with hostname cleaning to avoid serial number contamination
  - _Requirements: 1.4, 6.2_

- [x] 2.4 Write property test for site name extraction
  - **Property 2: Site Name Extraction Determinism**
  - **Validates: Requirements 1.4, 6.2**

- [x] 3. Fix device association and site grouping
- [x] 3.1 Implement device-to-site association logic
  - Associate boundary devices with their extracted site names
  - Associate neighbor devices with the same site as their boundary device
  - Handle devices that cannot be associated with any site
  - _Requirements: 3.1, 3.2, 3.5_

- [x] 3.2 Write property test for device association
  - **Property 7: Device Association Completeness**
  - **Validates: Requirements 2.3, 3.1**

- [x] 3.3 Implement unique site identification
  - Identify all unique sites from the device inventory
  - Group devices by their associated sites
  - Handle multiple devices from the same site
  - _Requirements: 1.3, 2.3_

- [x] 3.4 Write property test for unique site identification
  - **Property 3: Unique Site Identification**
  - **Validates: Requirements 1.3**

- [x] 4. Fix workbook generation logic
- [x] 4.1 Implement site workbook creation
  - Create separate workbooks for each identified site
  - Use correct filename format: "Discovery_SITENAME_YYYYMMDD-HH-MM.xlsx"
  - Include all associated devices and their neighbors in site workbooks
  - _Requirements: 2.1, 2.2, 2.4_

- [x] 4.2 Write property test for workbook creation
  - **Property 5: Workbook Creation Completeness**
  - **Validates: Requirements 2.1**

- [x] 4.3 Write property test for filename format
  - **Property 6: Filename Format Consistency**
  - **Validates: Requirements 2.2**

- [x] 4.4 Implement neighbor inclusion logic
  - Ensure all neighbors of site boundary devices are included in site workbooks
  - Handle both connected and neighbor-only devices
  - Maintain referential integrity between devices and their neighbors
  - _Requirements: 2.4, 3.2, 3.4_

- [x] 4.5 Write property test for neighbor inclusion
  - **Property 8: Neighbor Inclusion Consistency**
  - **Validates: Requirements 2.4, 3.2**

- [x] 5. Checkpoint - Test site boundary detection with LUMT-CORE-A
  - Run NetWalker with a configuration containing LUMT-CORE-A
  - Verify that a separate workbook "Discovery_LUMT_YYYYMMDD-HH-MM.xlsx" is created
  - Check logs for proper site boundary detection messages
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement comprehensive logging and debugging
- [x] 6.1 Add detailed logging for site boundary detection
  - Log configured pattern and number of devices being processed
  - Log each device's pattern matching result (match/no match)
  - Log identified sites and their device counts
  - Log workbook creation and associated devices
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 6.2 Write property test for logging completeness
  - **Property 11: Logging Completeness**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**

- [x] 6.3 Implement hostname cleaning integration
  - Ensure pattern matching uses cleaned hostnames
  - Display both original and cleaned hostnames in logs
  - Handle hostname cleaning failures gracefully
  - _Requirements: 6.1, 6.3, 6.4, 6.5_

- [x] 6.4 Write property test for hostname cleaning integration
  - **Property 4: Hostname Cleaning Integration**
  - **Validates: Requirements 1.5, 6.1**

- [x] 7. Implement error handling and fallback mechanisms
- [x] 7.1 Add comprehensive error handling
  - Handle configuration errors (invalid/missing pattern)
  - Handle runtime errors (extraction failures, workbook creation failures)
  - Implement graceful degradation to main workbook generation
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 7.2 Write property test for error handling
  - **Property 10: Error Handling Graceful Degradation**
  - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

- [x] 7.3 Implement configuration validation
  - Validate site boundary pattern format
  - Handle empty or missing patterns
  - Load and apply configuration changes correctly
  - _Requirements: 4.1, 4.2, 4.4, 4.5_

- [x] 7.4 Write property test for configuration loading
  - **Property 9: Configuration Loading Reliability**
  - **Validates: Requirements 4.1**

- [x] 8. Integration testing and validation
- [x] 8.1 Test with multiple site boundaries
  - Test with devices from multiple sites (LUMT-CORE-A, BORO-CORE-B, etc.)
  - Verify separate workbooks are created for each site
  - Ensure devices are correctly associated with their respective sites
  - _Requirements: 1.3, 2.1, 3.1_

- [x] 8.2 Write integration tests for multi-site scenarios
  - Test complete site boundary detection with multiple sites
  - Verify workbook generation for complex scenarios
  - Test edge cases and error conditions

- [x] 8.3 Test with the reported 50+ CORE devices
  - Run NetWalker against the network with 50+ devices containing "-CORE-"
  - Verify that separate workbooks are created for each unique site
  - Monitor performance and memory usage with large numbers of sites
  - _Requirements: 1.3, 2.1, 2.3_

- [x] 9. Final checkpoint - Complete validation
  - Ensure all tests pass, including property-based tests
  - Verify LUMT-CORE-A and other CORE devices generate separate workbooks
  - Review logs for proper site boundary detection and workbook creation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation of the fix
- Property tests validate universal correctness properties
- Integration tests validate end-to-end functionality with real scenarios
- All testing tasks are required for comprehensive coverage

The primary goal is to fix the site boundary detection so that LUMT-CORE-A and the 50+ other devices with "-CORE-" in their names generate separate workbooks as expected.