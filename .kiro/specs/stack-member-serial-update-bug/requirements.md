# Requirements Document: Stack Member Serial Number Update Bug

## Introduction

This document specifies requirements for fixing a bug in the NetWalker database manager where stack member serial numbers and hardware models are not being updated when devices are re-discovered. Currently, when a stack member already exists in the database with "Unknown" serial number or hardware model, subsequent discoveries that successfully collect this information fail to update the database, leaving the fields as "Unknown" permanently.

## Glossary

- **Stack Member**: An individual switch in a switch stack (e.g., Switch 1, Switch 2, Switch 3)
- **Database Manager**: Component responsible for storing and updating device information in the database
- **Upsert**: Database operation that either inserts a new record or updates an existing one
- **Enrichment**: Process of collecting detailed information (serial numbers, models) after initial stack detection
- **device_stack_members**: Database table storing stack member information

## Problem Statement

The `upsert_stack_members()` method in DatabaseManager has a bug where the UPDATE statement does not include `serial_number` or `hardware_model` fields. This causes the following issues:

1. Initial discovery may create stack members with "Unknown" serial/model
2. Subsequent discoveries successfully collect serial/model via enrichment
3. Database UPDATE operation ignores the new serial/model values
4. Stack members remain with "Unknown" values indefinitely

## Requirements

### Requirement 1: Update Serial Number on Re-discovery

**User Story:** As a network administrator, I want stack member serial numbers to be updated when devices are re-discovered, so that accurate inventory data is maintained.

#### Acceptance Criteria

1. WHEN a stack member exists in the database with serial_number = "Unknown"
   AND the device is re-discovered with a valid serial number
   THEN the database SHALL update the serial_number field to the new value

2. WHEN a stack member exists in the database with a valid serial number
   AND the device is re-discovered with a different serial number
   THEN the database SHALL update the serial_number field to the new value

3. WHEN a stack member exists in the database with a valid serial number
   AND the device is re-discovered with serial_number = "Unknown"
   THEN the database SHALL keep the existing valid serial number (do not overwrite with "Unknown")

### Requirement 2: Update Hardware Model on Re-discovery

**User Story:** As a network administrator, I want stack member hardware models to be updated when devices are re-discovered, so that accurate inventory data is maintained.

#### Acceptance Criteria

1. WHEN a stack member exists in the database with hardware_model = "Unknown"
   AND the device is re-discovered with a valid hardware model
   THEN the database SHALL update the hardware_model field to the new value

2. WHEN a stack member exists in the database with a valid hardware model
   AND the device is re-discovered with a different hardware model
   THEN the database SHALL update the hardware_model field to the new value

3. WHEN a stack member exists in the database with a valid hardware model
   AND the device is re-discovered with hardware_model = "Unknown"
   THEN the database SHALL keep the existing valid hardware model (do not overwrite with "Unknown")

### Requirement 3: Preserve Valid Data

**User Story:** As a network administrator, I want valid inventory data to be preserved when re-discovery fails to collect information, so that partial failures don't corrupt the database.

#### Acceptance Criteria

1. WHEN updating a stack member
   AND the new value for any field is "Unknown" or None
   AND the existing value is valid (not "Unknown" and not None)
   THEN the database SHALL keep the existing valid value

2. WHEN updating a stack member
   AND the new value for any field is valid (not "Unknown" and not None)
   THEN the database SHALL update the field regardless of the existing value

### Requirement 4: Logging and Visibility

**User Story:** As a network administrator, I want to see when stack member information is updated, so that I can verify the fix is working.

#### Acceptance Criteria

1. WHEN a stack member serial number is updated from "Unknown" to a valid value
   THEN the system SHALL log the update with old and new values

2. WHEN a stack member hardware model is updated from "Unknown" to a valid value
   THEN the system SHALL log the update with old and new values

3. WHEN a stack member update is skipped because new value is "Unknown"
   THEN the system SHALL log that the existing valid value was preserved

### Requirement 5: Backward Compatibility

**User Story:** As a network administrator, I want existing stack member update functionality to continue working, so that the bug fix doesn't break other features.

#### Acceptance Criteria

1. WHEN updating stack member role, priority, mac_address, software_version, or state
   THEN the system SHALL continue to update these fields as before

2. WHEN inserting a new stack member
   THEN the system SHALL insert all fields including serial_number and hardware_model

3. WHEN the database operation fails
   THEN the system SHALL rollback the transaction and log the error
