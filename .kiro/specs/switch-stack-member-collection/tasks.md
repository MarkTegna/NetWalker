# Implementation Plan: Switch Stack Member Collection - Reporting Enhancement

## Overview

This implementation plan adds a dedicated "Stack Members" sheet to Excel inventory reports. The sheet will provide a consolidated view of all physical switches in stack configurations across the network. Stack member data is already being collected and stored - this enhancement focuses solely on improving the reporting output.

## Tasks

- [x] 1. Create the _create_stack_members_sheet() method
  - Add new method to ExcelReportGenerator class
  - Implement sheet creation with proper headers
  - Extract stack member data from inventory dictionary
  - Write one row per physical stack member
  - Apply Excel table formatting and styling
  - Handle empty inventory (headers only)
  - _Requirements: 8.1, 8.2, 8.4, 8.5_

- [ ]* 1.1 Write property test for stack member completeness
  - **Property 1: Stack Member Completeness**
  - **Validates: Requirements 8.1, 8.2**

- [ ]* 1.2 Write property test for non-stack device exclusion
  - **Property 2: Non-Stack Device Exclusion**
  - **Validates: Requirements 8.4**

- [ ]* 1.3 Write property test for required field presence
  - **Property 3: Required Field Presence**
  - **Validates: Requirements 8.2**

- [x] 2. Integrate stack members sheet into report generation
  - Modify generate_inventory_report() method
  - Call _create_stack_members_sheet() after device inventory sheet
  - Ensure proper sheet ordering in workbook
  - _Requirements: 8.5_

- [ ]* 2.1 Write unit test for sheet ordering
  - Verify Stack Members sheet appears after Device Inventory
  - Verify sheet exists in generated workbook
  - _Requirements: 8.5_

- [x] 3. Implement error handling for edge cases
  - Handle devices marked as stack but with no members
  - Handle stack members with missing optional fields (priority, MAC, software version)
  - Handle stack members with missing required fields (skip with warning)
  - Add appropriate logging for debugging
  - _Requirements: 8.2, 8.4_

- [ ]* 3.1 Write unit test for missing optional fields
  - Test stack members with None values for optional fields
  - Verify empty cells created without errors
  - _Requirements: 8.2_

- [ ]* 3.2 Write unit test for missing required fields
  - Test stack member with missing serial number
  - Verify member skipped with warning logged
  - _Requirements: 8.2_

- [x] 4. Add stack role identification
  - Ensure master/active roles are clearly displayed
  - Verify role column shows Master, Member, Active, Standby correctly
  - _Requirements: 8.3_

- [ ]* 4.1 Write property test for stack role identification
  - **Property 4: Stack Role Identification**
  - **Validates: Requirements 8.3**

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 6. Write integration tests for full report generation
  - Test complete inventory report with Stack Members sheet
  - Test mixed inventory (stacks and non-stacks)
  - Test empty inventory
  - Verify Excel table formatting applied correctly
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ]* 6.1 Write property test for sheet creation consistency
  - **Property 5: Sheet Creation Consistency**
  - **Validates: Requirements 8.5**

- [ ]* 6.2 Write property test for empty sheet handling
  - **Property 6: Empty Sheet Handling**
  - **Validates: Requirements 8.4**

- [x] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The implementation builds incrementally: core functionality first, then error handling, then comprehensive testing
- Property tests validate universal correctness properties across randomized inputs
- Unit tests validate specific examples and edge cases
- Stack member data collection is already complete - this implementation only adds reporting
