# Implementation Plan: Inventory and Credentials Improvements

## Overview

Implement three improvements: exclude skipped devices from inventory sheets, discover credential files in parent directory, and make enable password prompts optional.

## Tasks

- [x] 1. Filter skipped devices from inventory sheets
  - Modify `_create_device_inventory_sheet()` in `excel_generator.py`
  - Add status filtering to exclude "skipped" devices
  - Keep all devices in discovery sheets
  - Test with mixed device statuses
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Implement parent directory credential file discovery
  - Add `_find_credential_file()` method to `config_manager.py`
  - Check current directory first, then parent directory
  - Modify `load_credentials()` to use new method
  - Add logging for which location was used
  - Test with file in various locations
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 3. Add optional enable password configuration
  - Add `prompt_for_enable_password` option to INI file
  - Add `--enable-password` CLI argument to `main.py`
  - Modify credential prompt logic in `netwalker_app.py`
  - Default to false (no prompt)
  - Test with various configurations
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Update default configuration file
  - Add `prompt_for_enable_password = false` to default INI
  - Update configuration documentation
  - _Requirements: 3.1_

- [x] 5. Integration testing
  - Test complete workflow with all three improvements
  - Verify skipped devices excluded from inventory
  - Verify credential file discovery from parent directory
  - Verify enable password prompt behavior
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5_

## Notes

- Each task references specific requirements for traceability
- Tasks should be implemented in order
- Test each component before moving to next task
- All three improvements are independent and can be tested separately
