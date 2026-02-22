# Implementation Tasks: Stack Member Incomplete Data Collection

## Task 1: Fix CLI Argument Override Bug
**Status**: Completed
**Validates**: Requirement 7.1, 7.4

Fix the bug where `--max-depth` CLI argument was not overriding the config file `max_depth` setting.

**Implementation Details**:
- Modified `netwalker/netwalker_app.py` to apply CLI overrides after config loading
- Added debug logging to trace CLI argument processing
- Verified CLI override works correctly with `--max-depth 9`

**Verification**:
- [x] CLI argument `--max-depth 9` overrides config file setting
- [x] Debug logs show both initial and final max_discovery_depth values
- [x] Discovery respects CLI-specified depth

## Task 2: Verify Stack Member Collection
**Status**: Completed
**Validates**: Requirement 1.1, 1.2, 1.5

Verify that stack member data is being collected correctly with real serial numbers and models.

**Implementation Details**:
- Run discovery on KARE-CORE-A with `--max-depth 0`
- Check that "show switch" and "show inventory" commands are executed
- Verify stack members are parsed correctly
- Confirm serial numbers and models are extracted from inventory

**Verification**:
- [x] "show switch" command executes successfully
- [x] "show inventory" command executes successfully
- [x] Stack members are parsed with correct switch numbers
- [x] Serial numbers are extracted (not "Unknown")
- [x] Models are extracted (not "Unknown")
- [x] Network modules are filtered out (no "-NM-" models)

**Notes**:
- Per-stack-member uptime is NOT available from standard Cisco IOS commands
- The uptime field in StackMemberInfo will remain NULL (not populated)
- Device uptime (from show version) is stored in the devices table

## Task 3: Verify Database Persistence
**Status**: Completed
**Validates**: Requirement 2.1, 2.2, 2.4

Verify that stack member data is being persisted to the database correctly.

**Implementation Details**:
- Query the stack_members table after discovery
- Verify records exist for KARE-CORE-A stack members
- Check that serial numbers and models are populated
- Verify referential integrity with devices table

**Verification**:
- [x] stack_members table contains records for KARE-CORE-A
- [x] Each stack member has correct switch_number
- [x] Serial numbers are populated (not "Unknown")
- [x] Models are populated (not "Unknown")
- [x] device_id foreign key references correct device
- [x] last_seen timestamp is recent

**Results**:
- Switch 1: Model=C9500-48Y4C, Serial=FDO281500VJ, Role=Active
- Switch 2: Model=C9500-48Y4C, Serial=FDO281509H3, Role=Standby

## Task 4: Verify Excel Report Generation
**Status**: Completed
**Validates**: Requirement 3.1, 3.2, 3.5

Verify that Excel reports include complete stack member information.

**Implementation Details**:
- Generate Excel report after discovery
- Check for "Stack Members" sheet
- Verify all stack members are included
- Confirm serial numbers and models are displayed

**Verification**:
- [x] Excel report contains "Stack Members" sheet
- [x] Sheet includes all stack members from database
- [x] Columns include: Device Name, Member Number, Serial Number, Model, Role, Priority, State
- [x] Serial numbers are displayed (not "Unknown")
- [x] Models are displayed (not "Unknown")

**Results**:
- Reports generated: Discovery_20260222-16-54.xlsx, Seed_KARE-CORE-A_20260222-16-54.xlsx, Inventory_20260222-16-54.xlsx
- Stack Members sheet created with 2 entries
- All data populated correctly

## Task 5: Add Unit Tests for Stack Parsing
**Status**: Not Started
**Validates**: Requirement 1.2, 6.2

Add unit tests for stack member parsing logic.

**Implementation Details**:
- Create test file: `tests/test_stack_collector.py`
- Add test cases for "show switch" parsing
- Add test cases for "show inventory" parsing
- Add test cases for VSS "show mod" parsing
- Add test cases for network module filtering

**Test Cases**:
- [ ] Test parsing "show switch" output with 3 members
- [ ] Test parsing "show inventory" output with serial numbers
- [ ] Test matching inventory data to stack members
- [ ] Test filtering network modules (models with "-NM-")
- [ ] Test VSS "show mod" parsing
- [ ] Test handling missing data (graceful degradation)

## Task 6: Add Unit Tests for CLI Override
**Status**: Not Started
**Validates**: Requirement 7.1, 7.4

Add unit tests for CLI argument override logic.

**Implementation Details**:
- Create test file: `tests/test_cli_override.py`
- Test CLI arguments override config file settings
- Test config file settings used when CLI args not provided
- Test multiple CLI arguments work together

**Test Cases**:
- [ ] Test `--max-depth` overrides config file `max_depth`
- [ ] Test `--seed-devices` overrides seed file
- [ ] Test `--config` loads specified config file
- [ ] Test config file values used when CLI args not provided
- [ ] Test multiple CLI overrides work together

## Task 7: Add Integration Test for Complete Flow
**Status**: Not Started
**Validates**: All Requirements

Add integration test that verifies complete stack member collection flow.

**Implementation Details**:
- Create test file: `tests/integration/test_stack_collection_flow.py`
- Use mock device output for "show switch" and "show inventory"
- Verify database persistence
- Verify Excel report generation

**Test Cases**:
- [ ] Test complete flow from discovery to Excel report
- [ ] Test stack member data persists to database
- [ ] Test Excel report includes stack members
- [ ] Test CLI override affects discovery depth
- [ ] Test error handling (command failures, missing data)

## Task 8: Update Documentation
**Status**: Completed

Update documentation to reflect stack member collection feature.

**Implementation Details**:
- Update README.md with stack member collection details
- Update user guide with Excel report Stack Members sheet
- Document CLI argument override behavior
- Add troubleshooting section for stack collection issues

**Documentation Updates**:
- [x] README.md includes stack member collection feature
- [x] User guide documents Stack Members sheet in Excel reports
- [x] CLI arguments documented with override behavior
- [x] Troubleshooting section added for stack collection

**Changes Made**:
- Added "Stack Member Detection" to Core Functionality
- Added "Stack Members Sheet" to Reporting & Output
- Updated Supported Platforms to include StackWise and VSS
- Added comprehensive "Stack Member Detection" section with:
  - Supported stack types
  - Collected information details
  - Stack Members sheet example
  - Detection process overview
  - Important notes about limitations

## Task 9: Performance Testing
**Status**: Not Started
**Validates**: Requirement 1.5, 6.1

Test performance impact of stack member collection.

**Implementation Details**:
- Measure discovery time with and without stack collection
- Measure database insert time for stack members
- Measure Excel generation time with stack members
- Identify any performance bottlenecks

**Performance Metrics**:
- [ ] Discovery time increase is acceptable (<10% overhead)
- [ ] Database inserts complete in reasonable time (<1s per device)
- [ ] Excel generation time is acceptable (<5s for 100 devices)
- [ ] No memory leaks or resource exhaustion

## Task 10: Error Handling Improvements
**Status**: Not Started
**Validates**: Requirement 6.1, 6.2, 6.3

Improve error handling and logging for stack collection.

**Implementation Details**:
- Add try-catch blocks around command execution
- Log errors with full context (device, command, error)
- Handle missing data gracefully (use "Unknown")
- Continue processing on individual failures

**Error Handling**:
- [ ] Command execution failures are caught and logged
- [ ] Parsing errors are caught and logged
- [ ] Database errors are caught and logged
- [ ] Missing data uses "Unknown" placeholder
- [ ] Individual failures don't stop overall processing

## Notes

- Task 1 is already completed (CLI override bug fix)
- Tasks 2-4 are verification tasks to confirm the fix works end-to-end
- Tasks 5-7 add automated tests for regression prevention
- Tasks 8-10 are polish and documentation tasks

## Testing Framework

- Unit tests: pytest
- Integration tests: pytest with database fixtures
- Test coverage target: >80% for stack_collector.py
- Mock framework: unittest.mock for device connections
