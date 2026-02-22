# Implementation Plan: Stack Member Serial Number Update Bug Fix

## Overview

This implementation plan fixes the bug where stack member serial numbers and hardware models are not updated during re-discovery. The fix modifies the `upsert_stack_members()` method in DatabaseManager to include `serial_number` in the UPDATE statement and add logging for visibility.

## Tasks

- [x] 1. Fix upsert_stack_members UPDATE statement
  - [x] 1.1 Modify SELECT query to retrieve existing serial_number and hardware_model
    - Change WHERE clause from `device_id = ? AND switch_number = ? AND serial_number = ?`
    - To: `device_id = ? AND switch_number = ?`
    - Add `serial_number, hardware_model` to SELECT columns
    - _Requirements: 1.1, 2.1_
  
  - [x] 1.2 Add serial_number to UPDATE statement
    - Add `serial_number = ?` to SET clause
    - Add `serial_number` parameter to execute() call in correct position
    - _Requirements: 1.1, 1.2_
  
  - [x] 1.3 Verify hardware_model in UPDATE statement
    - Ensure `hardware_model = ?` is in SET clause
    - Ensure `hardware_model` parameter is in correct position
    - _Requirements: 2.1, 2.2_
  
  - [x] 1.4 Add logging for updates
    - Log when serial_number changes (old -> new)
    - Log when hardware_model changes (old -> new)
    - Log when inserting new stack member
    - _Requirements: 4.1, 4.2_

- [ ] 2. Test the fix with real device
  - [ ] 2.1 Clear Python cache
    - Run `.\clear_python_cache.ps1`
    - _Requirements: All_
  
  - [ ] 2.2 Build executable
    - Run `python build_executable.py`
    - _Requirements: All_
  
  - [ ] 2.3 Test with KARE-CORE-A device
    - Run `.\dist\netwalker.exe --seed-devices KARE-CORE-A --max-depth 9 --config .\netwalker.ini`
    - Verify stack members show correct serial numbers and models
    - Check logs for update messages
    - _Requirements: 1.1, 2.1, 4.1, 4.2_

- [ ] 3. Verify database updates
  - [ ] 3.1 Query device_stack_members table
    - Check serial_number field for KARE-CORE-A stack members
    - Check hardware_model field for KARE-CORE-A stack members
    - Verify values are not "Unknown"
    - _Requirements: 1.1, 2.1_

- [ ] 4. Write unit tests (optional)
  - [ ]* 4.1 Test UPDATE with Unknown to Valid
    - Create stack member with serial="Unknown", model="Unknown"
    - Update with valid values
    - Verify database contains new values
    - _Requirements: 1.1, 2.1_
  
  - [ ]* 4.2 Test UPDATE with Valid to Different Valid
    - Create stack member with valid values
    - Update with different valid values
    - Verify database contains new values
    - _Requirements: 1.2, 2.2_
  
  - [ ]* 4.3 Test INSERT new member
    - Insert new stack member with all fields
    - Verify all fields stored correctly
    - _Requirements: 5.2_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster fix
- This is a critical bug fix that should be tested immediately
- The fix is minimal and low-risk
- Logging will help verify the fix is working
- After fix, re-discovery should update "Unknown" values to actual serial numbers and models
