# Requirements Document: Stack Member Incomplete Data Collection

## Introduction

This document specifies requirements for ensuring complete stack member data collection in NetWalker. Currently, when discovering stack devices like KARE-CORE-A, not all stack member information (serial numbers, models) is being collected and exported to Excel reports. This enhancement will ensure all stack member data is properly collected, stored, and exported.

## Glossary

- **Stack Device**: A network device composed of multiple physical switches operating as a single logical unit
- **Stack Member**: An individual physical switch within a stack
- **Stack Collector**: Component responsible for collecting stack member information
- **Device Collector**: Component responsible for collecting general device information
- **Stack Members Table**: Database table storing individual stack member details

## Requirements

### Requirement 1: Complete Stack Member Data Collection

**User Story:** As a network administrator, I want all stack member information to be collected during discovery, so that I have complete inventory data for stacked switches.

#### Acceptance Criteria

1. WHEN a stack device is discovered, THEN THE Stack_Collector SHALL execute "show switch" command
2. WHEN "show switch" output is parsed, THEN THE Stack_Collector SHALL extract member number, serial number, model, role, priority, and state for EACH member
3. WHEN any stack member field is missing from output, THEN THE Stack_Collector SHALL set that field to "Unknown"
4. WHEN stack member data is collected, THEN THE Stack_Collector SHALL store ALL members in the stack_members table
5. WHEN stack member collection completes, THEN THE Stack_Collector SHALL log the number of members collected

### Requirement 2: Stack Member Data Persistence

**User Story:** As a network administrator, I want stack member data to persist in the database, so that I can query and report on individual stack members.

#### Acceptance Criteria

1. WHEN stack member data is collected, THEN THE Database_Manager SHALL insert or update records in the stack_members table
2. WHEN a stack member already exists in the database, THEN THE Database_Manager SHALL update the record with new data
3. WHEN a stack member is removed from a stack, THEN THE Database_Manager SHALL mark the member as inactive or delete the record
4. WHEN stack member data is stored, THEN THE Database_Manager SHALL maintain referential integrity with the parent device
5. WHEN database operations fail, THEN THE Database_Manager SHALL log the error and continue processing other members

### Requirement 3: Stack Member Data Export

**User Story:** As a network administrator, I want stack member data included in Excel reports, so that I can review complete inventory information.

#### Acceptance Criteria

1. WHEN generating an Excel report, THEN THE Excel_Generator SHALL create a "Stack Members" sheet
2. WHEN populating the Stack Members sheet, THEN THE Excel_Generator SHALL include ALL stack members from the database
3. WHEN a stack member has no serial number, THEN THE Excel_Generator SHALL display "Unknown" in the serial number column
4. WHEN a stack member has no model, THEN THE Excel_Generator SHALL display "Unknown" in the model column
5. WHEN the Stack Members sheet is created, THEN THE Excel_Generator SHALL include columns: Device Name, Member Number, Serial Number, Model, Role, Priority, State

### Requirement 4: Stack Detection Accuracy

**User Story:** As a network administrator, I want stack devices to be accurately detected, so that stack member collection is triggered appropriately.

#### Acceptance Criteria

1. WHEN device output contains "Switch/Stack", THEN THE Device_Collector SHALL set is_stack flag to True
2. WHEN device output contains stack-related keywords, THEN THE Device_Collector SHALL set is_stack flag to True
3. WHEN is_stack flag is True, THEN THE Device_Collector SHALL trigger stack member collection
4. WHEN is_stack flag is False, THEN THE Device_Collector SHALL skip stack member collection
5. WHEN stack detection occurs, THEN THE Device_Collector SHALL log the detection method

### Requirement 5: Stack Member Update on Re-Discovery

**User Story:** As a network administrator, I want stack member data to be updated when devices are re-discovered, so that inventory reflects current state.

#### Acceptance Criteria

1. WHEN a stack device is re-discovered, THEN THE Stack_Collector SHALL collect fresh stack member data
2. WHEN stack member serial numbers change, THEN THE Stack_Collector SHALL update the database records
3. WHEN stack member models change, THEN THE Stack_Collector SHALL update the database records
4. WHEN stack member roles change, THEN THE Stack_Collector SHALL update the database records
5. WHEN stack member updates complete, THEN THE Stack_Collector SHALL log the number of members updated

### Requirement 6: Error Handling and Logging

**User Story:** As a network administrator, I want clear error messages and logging for stack collection issues, so that I can troubleshoot problems effectively.

#### Acceptance Criteria

1. WHEN "show switch" command fails, THEN THE Stack_Collector SHALL log the error and continue with device collection
2. WHEN stack member parsing fails, THEN THE Stack_Collector SHALL log which field failed and the pattern used
3. WHEN database insert/update fails, THEN THE Database_Manager SHALL log the error with member details
4. WHEN stack member collection completes, THEN THE Stack_Collector SHALL log success with member count
5. WHEN Excel export includes stack members, THEN THE Excel_Generator SHALL log the number of members exported

### Requirement 7: Command-Line Argument Handling

**User Story:** As a network administrator, I want command-line arguments to override config file settings, so that I can control discovery behavior without editing config files.

#### Acceptance Criteria

1. WHEN --max-depth argument is provided, THEN THE NetWalker_App SHALL use the command-line value instead of config file value
2. WHEN --seed-devices argument is provided, THEN THE NetWalker_App SHALL use the command-line devices instead of seed file
3. WHEN --config argument is provided, THEN THE NetWalker_App SHALL load the specified config file
4. WHEN command-line arguments conflict with config file, THEN THE NetWalker_App SHALL prioritize command-line arguments
5. WHEN command-line argument parsing fails, THEN THE NetWalker_App SHALL log the error and exit with non-zero status

## Out of Scope

- Stack member port-level configuration
- Stack member firmware version tracking
- Stack member power supply status
- Stack member temperature monitoring
- Stack member fan status

## Success Criteria

1. All stack member serial numbers and models are collected and stored in the database
2. Excel reports include complete stack member information
3. Command-line arguments properly override config file settings
4. Re-discovery updates stack member data correctly
5. Error handling provides clear diagnostic information
