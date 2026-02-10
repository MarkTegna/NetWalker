# Implementation Plan: Command Executor

## Overview

This implementation plan breaks down the Command Executor feature into discrete, incremental tasks. Each task builds on previous work and includes testing to validate functionality early. The implementation follows NetWalker's existing patterns and reuses components where possible.

## Tasks

- [x] 1. Create command executor package structure and data models
  - Create `netwalker/executor/` directory
  - Create `netwalker/executor/__init__.py`
  - Create `netwalker/executor/data_models.py` with DeviceInfo, CommandResult, and ExecutionSummary dataclasses
  - _Requirements: 8.1, 8.5_

- [ ] 2. Implement device filtering functionality
  - [x] 2.1 Create device filter module in `netwalker/executor/device_filter.py`
    - Implement `DeviceFilter` class with `filter_devices()` method
    - Use DatabaseManager to query devices table with SQL LIKE pattern
    - Join with device_interfaces to get primary IP (most recent last_seen)
    - Return list of DeviceInfo objects
    - _Requirements: 2.1, 2.2, 2.4, 2.5_

  - [ ]* 2.2 Write property test for SQL wildcard pattern matching
    - **Property 1: SQL Wildcard Pattern Matching**
    - **Validates: Requirements 2.1, 2.2**
    - Test with random patterns containing % and _ wildcards
    - Verify only matching devices are returned

  - [ ]* 2.3 Write property test for device information retrieval
    - **Property 2: Device Information Retrieval**
    - **Validates: Requirements 2.4, 2.5**
    - Test with random device sets having multiple IPs
    - Verify both name and most recent IP are retrieved

  - [ ]* 2.4 Write unit tests for device filtering edge cases
    - Test empty result set (no matching devices)
    - Test devices with no IP addresses
    - Test devices with multiple IP addresses
    - _Requirements: 2.3_

- [ ] 3. Implement command execution functionality
  - [x] 3.1 Create command executor core module in `netwalker/executor/command_executor.py`
    - Implement `CommandExecutor` class with initialization
    - Implement `_load_configuration()` method using existing config patterns
    - Implement `_get_credentials()` method using CredentialManager
    - _Requirements: 3.1, 3.2, 3.3, 3.5, 3.6, 9.1, 9.2, 9.3, 9.4_

  - [x] 3.2 Implement single device command execution
    - Implement `_execute_on_device()` method
    - Use ConnectionManager to establish connection
    - Execute command and capture output
    - Handle connection failures gracefully
    - Close connection after execution
    - Return CommandResult with status and output
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

  - [ ]* 3.3 Write property test for successful command execution
    - **Property 4: Successful Command Execution**
    - **Validates: Requirements 4.4, 4.5**
    - Test with random commands on mock devices
    - Verify output is captured and status is success

  - [ ]* 3.4 Write property test for error handling and continuation
    - **Property 5: Error Handling and Continuation**
    - **Validates: Requirements 4.6, 4.7, 7.2, 7.3**
    - Test with random failure scenarios
    - Verify errors are recorded and execution continues

  - [ ]* 3.5 Write property test for connection cleanup
    - **Property 6: Connection Cleanup**
    - **Validates: Requirements 4.8**
    - Test with random connection scenarios
    - Verify connections are always closed

- [x] 4. Checkpoint - Ensure core execution logic works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement progress reporting
  - [x] 5.1 Create progress reporter module in `netwalker/executor/progress_reporter.py`
    - Implement `ProgressReporter` class
    - Implement `report_start()`, `report_success()`, `report_failure()` methods
    - Use ASCII characters ([OK], [FAIL]) for Windows compatibility
    - Display device name, IP, and status for each device
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 5.2 Write property test for progress reporting completeness
    - **Property 7: Progress Reporting Completeness**
    - **Validates: Requirements 5.2, 5.3, 5.4**
    - Test with random device lists
    - Verify progress information is displayed for all devices

  - [ ]* 5.3 Write unit tests for progress reporting
    - Test initial message with device count
    - Test success message format
    - Test failure message format
    - Test summary message format
    - _Requirements: 5.1, 5.5_

- [ ] 6. Implement Excel export functionality
  - [x] 6.1 Create Excel exporter module in `netwalker/executor/excel_exporter.py`
    - Implement `CommandResultExporter` class
    - Implement `export()` method to create Excel file
    - Use timestamp format: Command_Results_YYYYMMDD-HH-MM.xlsx
    - Create worksheet with columns: Device Name, Device IP, Status, Command Output, Execution Time
    - Apply header formatting (bold white on blue #366092)
    - Auto-adjust column widths (max 100 characters)
    - Preserve line breaks in command output (wrap text)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9_

  - [ ]* 6.2 Write property test for Excel export generation
    - **Property 8: Excel Export Generation**
    - **Validates: Requirements 6.1, 6.2**
    - Test with random execution results
    - Verify Excel file is created with correct filename format

  - [ ]* 6.3 Write property test for status recording accuracy
    - **Property 9: Status Recording Accuracy**
    - **Validates: Requirements 6.6, 6.7**
    - Test with random success/failure results
    - Verify status is recorded correctly with error messages

  - [ ]* 6.4 Write property test for output preservation
    - **Property 10: Output Preservation**
    - **Validates: Requirements 6.8**
    - Test with random multi-line outputs
    - Verify line breaks are preserved in Excel

  - [ ]* 6.5 Write property test for column width adjustment
    - **Property 11: Column Width Adjustment**
    - **Validates: Requirements 6.5**
    - Test with random content lengths
    - Verify widths are adjusted correctly (max 100)

  - [ ]* 6.6 Write unit tests for Excel export
    - Test header formatting
    - Test worksheet structure
    - Test file path display
    - Test export error handling
    - _Requirements: 6.3, 6.4, 6.9, 7.5_

- [ ] 7. Implement main orchestration logic
  - [x] 7.1 Complete CommandExecutor.execute() method
    - Load configuration and credentials
    - Filter devices from database
    - Initialize progress reporter
    - Loop through devices and execute commands sequentially
    - Collect all results
    - Export results to Excel
    - Display summary
    - Return ExecutionSummary
    - _Requirements: 1.1, 2.1, 3.1, 4.4, 5.1, 6.1_

  - [ ]* 7.2 Write property test for command error capture
    - **Property 12: Command Error Capture**
    - **Validates: Requirements 7.4**
    - Test with random error commands
    - Verify error output is captured with success status

  - [ ]* 7.3 Write unit tests for orchestration
    - Test complete execution flow with mock components
    - Test database connection failure handling
    - Test empty device list handling
    - Test configuration validation
    - _Requirements: 7.1, 9.5_

- [ ] 8. Integrate with CLI
  - [x] 8.1 Add "execute" subcommand to netwalker/cli.py
    - Add execute_parser with required arguments: --filter, --command
    - Add optional arguments: --config, --output
    - Set default values: config=netwalker.ini, output=current directory
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 8.2 Create CLI handler in main entry point
    - Import CommandExecutor
    - Handle "execute" command routing
    - Pass CLI arguments to CommandExecutor
    - Handle exceptions and display user-friendly errors
    - _Requirements: 1.1, 8.5_

  - [ ]* 8.3 Write unit tests for CLI integration
    - Test argument parsing with various combinations
    - Test required argument validation
    - Test default value handling
    - Test command routing
    - _Requirements: 1.2, 1.3, 1.4, 1.5_

- [ ] 9. Add error handling and validation
  - [x] 9.1 Implement comprehensive error handling
    - Add database connection error handling with clear messages
    - Add device connection timeout handling
    - Add authentication failure handling
    - Add Excel export error handling
    - Add configuration validation
    - Ensure all errors are logged appropriately
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 9.5_

  - [ ]* 9.2 Write unit tests for error scenarios
    - Test database connection failure (edge case)
    - Test empty device list (edge case)
    - Test Excel export failure (edge case)
    - Test missing configuration (edge case)
    - _Requirements: 2.3, 7.1, 7.5, 9.5_

- [x] 10. Checkpoint - Ensure complete integration works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Add configuration support
  - [x] 11.1 Extend netwalker.ini with command executor section
    - Add [command_executor] section
    - Add connection_timeout parameter
    - Add ssh_strict_key parameter
    - Add output_directory parameter
    - Document all parameters with comments
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ]* 11.2 Write unit tests for configuration loading
    - Test loading from specified config file
    - Test default values when parameters missing
    - Test configuration validation
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 12. Add logging and documentation
  - [x] 12.1 Add comprehensive logging
    - Log database queries (without sensitive data)
    - Log connection attempts and results
    - Log command execution (without sensitive output)
    - Log errors with stack traces
    - Use existing NetWalker logging configuration
    - _Requirements: 8.4_

  - [x] 12.2 Add docstrings and code comments
    - Add module docstrings to all new files
    - Add class and method docstrings
    - Add inline comments for complex logic
    - Follow existing NetWalker documentation patterns

  - [x] 12.3 Update README with command executor usage
    - Add "execute" command documentation
    - Add usage examples
    - Add configuration examples
    - Add troubleshooting section

- [ ] 13. Integration testing with real devices
  - [x] 13.1 Test with real NetWalker database
    - Use secret_creds.ini for credentials
    - Test with filter pattern "*-uw*"
    - Test with command "show ip eigrp vrf WAN neigh"
    - Verify Excel file is created correctly
    - Verify progress reporting is accurate
    - _Requirements: 3.6_

  - [x] 13.2 Test error scenarios with real devices
    - Test with unreachable device (timeout)
    - Test with invalid credentials (auth failure)
    - Test with invalid command (command error)
    - Verify error handling works correctly

  - [x] 13.3 Test edge cases
    - Test with filter matching zero devices
    - Test with filter matching single device
    - Test with filter matching many devices
    - Test with very long command output

- [x] 14. Final checkpoint - Complete feature validation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based and unit tests that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples and edge cases
- Integration tests use real devices from NetWalker database with secret_creds.ini
- All code follows existing NetWalker patterns and conventions
- Windows compatibility is ensured (ASCII characters, path handling)
