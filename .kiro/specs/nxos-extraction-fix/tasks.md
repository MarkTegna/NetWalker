# Implementation Plan: NX-OS Device Information Extraction Fix

## Overview

Enhance the DeviceCollector to correctly extract software version and hardware model from NX-OS devices by adding platform-specific patterns with priority ordering, while maintaining backward compatibility with IOS and IOS-XE devices.

## Tasks

- [x] 1. Update software version extraction method
  - Modify `_extract_software_version()` in `device_collector.py`
  - Add NX-OS version pattern as highest priority
  - Add System version pattern as NX-OS fallback
  - Keep generic Version pattern for IOS/IOS-XE
  - Return first match in priority order
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ]* 1.1 Write unit tests for software version extraction
  - Test NX-OS version extraction with license text present
  - Test IOS-XE version extraction (backward compatibility)
  - Test IOS version extraction (backward compatibility)
  - Test edge cases (empty output, no version)
  - _Requirements: 1.1, 1.3, 1.4_

- [ ]* 1.2 Write property test for version extraction
  - **Property 1: NX-OS Version Extraction Accuracy**
  - **Validates: Requirements 1.1, 1.3**
  - Generate random NX-OS outputs with license text
  - Verify NX-OS version extracted over license version

- [x] 2. Update hardware model extraction method
  - Modify `_extract_hardware_model()` in `device_collector.py`
  - Add NX-OS chassis pattern after Model Number pattern
  - Ensure processor pattern (ISR/ASR) still works
  - Ensure IOS switch pattern still works
  - Return first match in priority order
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ]* 2.1 Write unit tests for hardware model extraction
  - Test NX-OS chassis extraction (Nexus 9000, 5000, 7000)
  - Test ISR router extraction (backward compatibility)
  - Test Catalyst switch extraction (backward compatibility)
  - Test edge cases (empty output, no model)
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ]* 2.2 Write property test for hardware model extraction
  - **Property 2: NX-OS Hardware Model Extraction Accuracy**
  - **Validates: Requirements 2.1, 2.2**
  - Generate random NX-OS chassis outputs
  - Verify model extracted without "Chassis" suffix

- [x] 3. Checkpoint - Run all tests
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 3.1 Write property test for backward compatibility
  - **Property 3: IOS/IOS-XE Backward Compatibility**
  - **Validates: Requirements 1.4, 2.3, 2.4**
  - Generate random IOS/IOS-XE outputs
  - Verify extraction matches expected behavior

- [x] 4. Integration testing with real devices
  - Test with DFW1-CORE-A (NX-OS device)
  - Test with BORO-UW01 (IOS-XE device)
  - Verify inventory report shows correct data
  - Verify database stores correct information
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4_

- [x] 5. Final checkpoint - Verify all requirements met
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests verify real-world device compatibility
