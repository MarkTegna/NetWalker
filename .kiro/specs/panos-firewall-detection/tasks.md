# Implementation Plan: PAN-OS Firewall Detection Enhancement

## Overview

This implementation plan enhances NetWalker to properly detect, connect to, and collect data from PAN-OS firewalls. The approach focuses on early detection in the Connection Manager before SSH connection establishment, using the correct netmiko device_type, and executing PAN-OS-specific commands with appropriate data extraction patterns.

## Tasks

- [x] 1. Add database platform lookup method
  - Add `get_device_platform()` method to DatabaseManager class
  - Query devices table by hostname or primary_ip
  - Return platform string or None if not found
  - _Requirements: 1.2, 1.3_

- [ ]* 1.1 Write property test for database platform lookup
  - **Property 7: Database Query Consistency**
  - **Validates: Requirements 4.4**

- [x] 2. Implement PAN-OS detection in Connection Manager
  - [x] 2.1 Add `_detect_panos_from_context()` method to ConnectionManager
    - Check hostname for "-fw" pattern (case-insensitive)
    - Check database platform for PAN-OS patterns if db_manager available
    - Log detection method and reason
    - Return boolean indicating PAN-OS detection
    - _Requirements: 1.1, 1.2, 1.3, 6.1_
  
  - [ ] 2.2 Write property test for PAN-OS detection
    - **Property 1: Device Type Selection Based on Detection**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
  
  - [x] 2.3 Modify `_try_netmiko_ssh_connection()` to use detection
    - Add db_manager parameter
    - Call `_detect_panos_from_context()` before connection
    - Set device_type to 'paloalto_panos' or 'cisco_ios' based on detection
    - Log device_type selection
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [x] 2.4 Modify `connect_device()` to pass db_manager
    - Add db_manager parameter
    - Pass db_manager to `_try_netmiko_ssh_connection()`
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [ ]* 2.5 Write unit tests for connection manager changes
    - Test hostname detection with various patterns
    - Test database platform detection
    - Test device_type selection logic
    - Test error handling for missing database
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 6.1, 6.2_

- [x] 3. Checkpoint - Ensure connection manager tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Enhance Device Collector for PAN-OS
  - [x] 4.1 Modify `collect_device_information()` for PAN-OS detection
    - Detect PAN-OS from connection.device_type attribute
    - Execute "set cli pager off" for PAN-OS devices
    - Execute "show system info" with 60-second timeout for PAN-OS
    - Execute "show version" for non-PAN-OS devices
    - Add "PAN-OS\n" marker to output for platform detection
    - Skip VTP collection for PAN-OS devices
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 5.2_
  
  - [ ] 4.2 Write property test for command selection
    - **Property 2: Platform-Specific Command Selection**
    - **Validates: Requirements 2.2, 5.2**
  
  - [ ]* 4.3 Write unit tests for PAN-OS command execution
    - Test "set cli pager off" execution
    - Test "show system info" with timeout
    - Test command failure handling
    - Test timeout error logging
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.3_

- [x] 5. Update capability determination for PAN-OS
  - [x] 5.1 Modify `_determine_capabilities()` method
    - Add PAN-OS platform check
    - Return ["Firewall", "Router"] for PAN-OS devices
    - Maintain existing logic for other platforms
    - _Requirements: 4.2, 5.3_
  
  - [ ]* 5.2 Write property test for capability assignment
    - **Property 5: PAN-OS Capability Assignment**
    - **Validates: Requirements 4.2**
  
  - [ ]* 5.3 Write unit tests for capability determination
    - Test PAN-OS capability assignment
    - Test non-PAN-OS capability assignment unchanged
    - _Requirements: 4.2, 5.3_

- [x] 6. Verify PAN-OS data extraction patterns
  - [x] 6.1 Review existing extraction methods
    - Verify `_extract_hostname()` handles "hostname: VALUE" pattern
    - Verify `_extract_hardware_model()` handles "model: VALUE" pattern
    - Verify `_extract_serial_number()` handles "serial: VALUE" pattern
    - Verify `_extract_software_version()` handles "sw-version: VALUE" pattern
    - Verify `_detect_platform()` handles PAN-OS patterns
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1_
  
  - [ ]* 6.2 Write property test for PAN-OS data extraction
    - **Property 3: PAN-OS Data Extraction Completeness**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
  
  - [ ]* 6.3 Write property test for platform detection
    - **Property 4: PAN-OS Platform Detection**
    - **Validates: Requirements 4.1, 4.3**
  
  - [ ]* 6.4 Write unit tests for extraction edge cases
    - Test extraction with missing fields (should return "Unknown")
    - Test extraction with extra whitespace
    - Test extraction with multiple matches
    - Test extraction failure logging
    - _Requirements: 3.5, 6.4_

- [x] 7. Checkpoint - Ensure device collector tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Update NetWalker app integration
  - [x] 8.1 Modify discovery loop to pass db_manager
    - Update connection_manager.connect_device() calls
    - Pass database_manager instance to connect_device()
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [ ]* 8.2 Write integration tests
    - Test end-to-end PAN-OS device discovery
    - Test database platform lookup during connection
    - Test device data storage with correct platform
    - _Requirements: 4.3, 7.1, 7.2, 7.3, 7.4_

- [x] 9. Add backward compatibility verification
  - [ ]* 9.1 Write property test for backward compatibility
    - **Property 6: Backward Compatibility for Non-PAN-OS Devices**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
  
  - [ ] 9.2 Write regression tests for existing platforms
    - Test IOS device discovery unchanged
    - Test IOS-XE device discovery unchanged
    - Test NX-OS device discovery unchanged
    - Compare results with baseline data
    - _Requirements: 5.5_

- [x] 10. Final checkpoint - Run all tests and verify functionality
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- Integration tests verify end-to-end functionality
- Backward compatibility tests ensure existing functionality is preserved
