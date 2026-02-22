# Design Document: Stack Member Incomplete Data Collection

## Overview

This design addresses the issue where stack member data (serial numbers, models) are showing as "Unknown" in Excel exports when discovering stack devices. The root cause has been identified as a CLI argument override bug where `--max-depth` was not properly overriding the config file setting. This design documents the fix and ensures complete stack member data collection.

## Architecture

### Component Interaction

```
NetWalkerApp (CLI Parsing)
    ↓
ConfigurationManager (Config Loading)
    ↓
DiscoveryEngine (Device Discovery)
    ↓
StackCollector (Stack Member Collection)
    ↓
DatabaseManager (Data Persistence)
    ↓
ExcelReportGenerator (Report Generation)
```

### Key Components

1. **NetWalkerApp**: Main application class that handles CLI argument parsing and configuration initialization
2. **StackCollector**: Collects stack member information using "show switch" and "show inventory" commands
3. **DatabaseManager**: Persists stack member data to the database
4. **ExcelReportGenerator**: Generates Excel reports with Stack Members sheet

## Design Decisions

### 1. CLI Argument Override Priority

**Decision**: Command-line arguments must always override config file settings.

**Rationale**: Users need the ability to override config file settings without editing files, especially for testing and troubleshooting.

**Implementation**:
- Load config file settings first
- Apply CLI argument overrides after config loading
- Log both initial and final values for debugging

### 2. Stack Member Data Enrichment

**Decision**: Use "show inventory" command to enrich stack member data with serial numbers and models.

**Rationale**: The "show switch" command provides basic stack information but often lacks serial numbers and models. The "show inventory" command provides complete hardware details.

**Implementation**:
- Collect basic stack info from "show switch"
- Enrich with detailed info from "show inventory"
- Filter out network modules (models containing "-NM-")
- Handle missing data gracefully with "Unknown" placeholders

### 3. VSS Detection and Support

**Decision**: Support VSS (Virtual Switching System) in addition to StackWise.

**Rationale**: Catalyst 4500-X and 6500 devices use VSS instead of StackWise, and these should also be detected as stacks.

**Implementation**:
- Fallback to "show mod" if "show switch" fails
- Parse VSS output to extract switch members
- Filter chassis/supervisor modules only (skip network modules)

### 4. Error Handling Strategy

**Decision**: Continue processing on errors, log warnings, use "Unknown" for missing data.

**Rationale**: Partial data is better than no data. Network devices may have connectivity issues or command failures, but we should still collect what we can.

**Implementation**:
- Try-catch blocks around command execution
- Log errors with context
- Use "Unknown" as default for missing fields
- Continue with next member on individual failures

## Data Models

### StackMemberInfo

```python
class StackMemberInfo:
    switch_number: int          # Stack member number (1, 2, 3, etc.)
    role: str                   # Master, Member, Active, Standby
    priority: Optional[int]     # Stack priority (StackWise only)
    hardware_model: str         # Model number (e.g., C9300-48P)
    serial_number: str          # Serial number (e.g., FOC2432L6G4)
    mac_address: Optional[str]  # MAC address
    software_version: Optional[str]  # Software version
    state: str                  # Ready, Ok, Active, etc.
```

### Database Schema

```sql
CREATE TABLE stack_members (
    id INT PRIMARY KEY IDENTITY,
    device_id INT FOREIGN KEY REFERENCES devices(id),
    switch_number INT NOT NULL,
    role VARCHAR(50),
    priority INT,
    hardware_model VARCHAR(100),
    serial_number VARCHAR(50),
    mac_address VARCHAR(20),
    software_version VARCHAR(100),
    state VARCHAR(50),
    last_seen DATETIME DEFAULT GETDATE(),
    UNIQUE(device_id, switch_number)
);
```

## Command Execution Flow

### IOS/IOS-XE Stack Collection

1. Execute "show switch" command
2. Parse output to extract basic stack info (switch number, role, state)
3. Execute "show inventory" command
4. Parse inventory output to extract serial numbers and models
5. Match inventory data to stack members by switch number
6. Filter out network modules (models with "-NM-")
7. Return enriched stack member list

### VSS Collection (Fallback)

1. Execute "show mod" command
2. Parse output to identify VSS switch sections
3. Extract chassis/supervisor modules only
4. Skip network modules
5. Return VSS member list (requires 2 switches)

## Configuration

### CLI Arguments

```
--max-depth N          Maximum discovery depth (overrides config file)
--seed-devices HOST    Comma-separated seed devices (overrides config file)
--config FILE          Config file path (default: netwalker.ini)
```

### Config File Settings

```ini
[discovery]
max_depth = 0          # 0 = unlimited, N = max depth
```

## Testing Strategy

### Unit Tests

1. Test CLI argument parsing and override logic
2. Test stack member parsing from "show switch" output
3. Test inventory parsing from "show inventory" output
4. Test VSS parsing from "show mod" output
5. Test network module filtering

### Integration Tests

1. Test complete stack collection flow with real device output
2. Test database persistence of stack members
3. Test Excel report generation with stack members
4. Test CLI override behavior

### Property-Based Tests

Property-based testing is not applicable for this feature as it involves:
- External device communication (non-deterministic)
- Complex parsing of device-specific output formats
- Database operations with side effects

## Correctness Properties

Since this feature involves external device communication and complex parsing, we will rely on unit tests and integration tests rather than property-based tests. However, we can define correctness properties that should hold:

### Property 1: CLI Override Consistency
**Validates: Requirement 7.1**

**Property**: For any config file setting and CLI argument, if the CLI argument is provided, the final configuration value must equal the CLI argument value.

**Test Strategy**: Unit test with various config/CLI combinations

### Property 2: Stack Member Completeness
**Validates: Requirement 1.2**

**Property**: For each stack member in "show switch" output, there must be a corresponding StackMemberInfo object with all required fields populated (switch_number, role, state).

**Test Strategy**: Unit test with sample "show switch" outputs

### Property 3: Inventory Enrichment Accuracy
**Validates: Requirement 1.2**

**Property**: For each stack member with inventory data, the serial_number and hardware_model fields must match the corresponding "show inventory" entry.

**Test Strategy**: Unit test with sample "show inventory" outputs

### Property 4: Network Module Filtering
**Validates: Requirement 1.2**

**Property**: No StackMemberInfo object should have a hardware_model containing "-NM-" (network modules should be filtered out).

**Test Strategy**: Unit test with inventory outputs containing network modules

### Property 5: Database Referential Integrity
**Validates: Requirement 2.4**

**Property**: For each stack_members record, there must exist a corresponding devices record with matching device_id.

**Test Strategy**: Integration test with database queries

### Property 6: Excel Export Completeness
**Validates: Requirement 3.2**

**Property**: For each stack member in the database, there must be a corresponding row in the "Stack Members" sheet of the Excel report.

**Test Strategy**: Integration test comparing database records to Excel rows

## Implementation Notes

### Logging Strategy

- Log CLI arguments at INFO level for debugging
- Log config file values before and after CLI overrides
- Log stack member collection progress (number of members found)
- Log inventory parsing details at DEBUG level
- Log errors with full context (device, command, error message)

### Performance Considerations

- Stack collection adds 2 additional commands per stack device ("show switch", "show inventory")
- Inventory parsing is O(n) where n is number of lines in output
- Database inserts are batched per device (all members inserted together)
- Excel generation processes all stack members in a single pass

### Backward Compatibility

- Existing config files continue to work
- CLI arguments are optional (config file values used if not provided)
- Database schema is additive (new table, no changes to existing tables)
- Excel reports include new sheet but don't modify existing sheets

## Success Metrics

1. All stack member serial numbers are collected (no "Unknown" values)
2. All stack member models are collected (no "Unknown" values)
3. CLI arguments properly override config file settings
4. Excel reports include complete Stack Members sheet
5. Database contains complete stack member records

## Future Enhancements

- Stack member port-level configuration
- Stack member firmware version tracking
- Stack member power supply status
- Stack member temperature monitoring
- Stack member fan status
- Stack member uptime tracking
