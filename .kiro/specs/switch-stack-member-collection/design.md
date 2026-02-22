# Design Document: Switch Stack Member Collection - Reporting Enhancement

## Overview

This design addresses Requirement 8 (Stack Member Reporting) from the requirements document. The stack member collection functionality is already implemented and working - devices are being discovered, stack members are being collected and stored in the database, and basic stack information is displayed inline in the Device Inventory sheet.

This design focuses on enhancing the reporting capabilities by adding a dedicated "Stack Members" sheet to the Excel inventory reports, providing a consolidated view of all physical switches in the network including their stack configurations.

### Current State

- Stack member data is collected during device discovery
- Stack members are stored in the `device_stack_members` database table
- Stack members are displayed inline in the Device Inventory sheet (each physical switch gets its own row)
- The inline display includes: Device Key, Hostname, Stack Role, Stack Number, Serial Number, Hardware Model

### Enhancement Scope

- Add a dedicated "Stack Members" sheet to Excel inventory reports
- Provide a consolidated view of all stack configurations across the network
- Display comprehensive stack member details in a structured format
- Maintain the existing inline display in Device Inventory sheet (no changes)

## Architecture

### Component Overview

The enhancement involves modifying the Excel report generator to add a new sheet creation method. The architecture follows the existing pattern used for other dedicated sheets (VLANs, Connections, etc.).

```
┌─────────────────────────────────────────────────────────────┐
│                  Excel Report Generator                      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  generate_inventory_report()                       │    │
│  │  - Creates workbook                                │    │
│  │  - Calls sheet creation methods                    │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ├─→ _create_device_inventory_sheet()│
│                          ├─→ _create_vlan_inventory_sheet() │
│                          ├─→ _create_connections_sheet()    │
│                          └─→ _create_stack_members_sheet()  │ ← NEW
│                                                              │
└─────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
                        ┌───────────────────────┐
                        │  Inventory Dictionary │
                        │  - device_info        │
                        │  - stack_members[]    │
                        │  - is_stack           │
                        └───────────────────────┘
```

### Data Flow

1. **Input**: Inventory dictionary containing device information with stack_members lists
2. **Processing**: Iterate through all devices, extract stack member information
3. **Output**: Excel sheet with one row per physical stack member

## Components and Interfaces

### New Method: `_create_stack_members_sheet()`

**Purpose**: Create a dedicated sheet showing all stack members across all discovered devices.

**Signature**:
```python
def _create_stack_members_sheet(self, workbook: Workbook, inventory: Dict[str, Dict[str, Any]]) -> None
```

**Parameters**:
- `workbook`: openpyxl Workbook object to add the sheet to
- `inventory`: Dictionary of device information keyed by device identifier

**Behavior**:
- Creates a new worksheet named "Stack Members"
- Iterates through all devices in inventory
- For each device where `is_stack == True` and `stack_members` list is not empty:
  - Extracts parent device information (hostname, IP, platform)
  - Iterates through each stack member
  - Writes one row per stack member with comprehensive details
- Applies table formatting with filters and styling
- Auto-sizes columns for readability
- If no stack members found across all devices, creates sheet with headers only

### Integration Point

**Method**: `generate_inventory_report()`

**Location**: After `_create_device_inventory_sheet()` and before `_create_vlan_inventory_sheet()`

**Modification**:
```python
# Create device inventory sheet
self._create_device_inventory_sheet(workbook, inventory)

# Create stack members sheet (NEW)
self._create_stack_members_sheet(workbook, inventory)

# Create VLAN inventory sheet
self._create_vlan_inventory_sheet(workbook, inventory)
```

## Data Models

### Input Data Structure

The inventory dictionary contains device entries with the following relevant fields:

```python
{
    "device_key": {
        "hostname": str,              # Device hostname
        "ip_address": str,            # Management IP
        "platform": str,              # Cisco platform (e.g., "cisco_ios")
        "is_stack": bool,             # True if device is a stack
        "stack_members": [            # List of StackMemberInfo objects
            {
                "switch_number": int,      # 1-9
                "role": str,               # "Master", "Member", "Active", "Standby"
                "priority": int,           # 1-15 (may be None)
                "hardware_model": str,     # e.g., "WS-C3850-48P"
                "serial_number": str,      # Physical switch serial
                "mac_address": str,        # May be None
                "software_version": str,   # May be None
                "state": str              # "Ready", "Provisioned", etc.
            },
            ...
        ],
        ...
    },
    ...
}
```

### Output Sheet Structure

**Sheet Name**: "Stack Members"

**Columns** (in order):
1. Stack Device - Logical stack hostname
2. Stack IP - Management IP address of the logical stack
3. Platform - Device platform
4. Switch Number - Stack member number (1-9)
5. Role - Stack role (Master/Member/Active/Standby)
6. Priority - Stack priority (1-15, may be empty)
7. Hardware Model - Physical switch model
8. Serial Number - Physical switch serial number
9. MAC Address - Stack member MAC (may be empty)
10. Software Version - Member software version (may be empty)
11. State - Operational state (Ready/Provisioned/etc.)

**Formatting**:
- Header row with bold text and background color
- Excel Table with filters enabled
- Alternating row colors for readability
- Auto-sized columns
- Sorted by Stack Device, then Switch Number

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system - essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Stack Member Completeness

*For any* device in the inventory where `is_stack == True` and `stack_members` is not empty, all stack members from that device's `stack_members` list should appear as rows in the Stack Members sheet.

**Validates: Requirements 8.1, 8.2**

### Property 2: Non-Stack Device Exclusion

*For any* device in the inventory where `is_stack == False` or `stack_members` is empty, that device should not contribute any rows to the Stack Members sheet.

**Validates: Requirements 8.4**

### Property 3: Required Field Presence

*For any* row in the Stack Members sheet, the following fields must be non-empty: Stack Device, Stack IP, Platform, Switch Number, Hardware Model, and Serial Number.

**Validates: Requirements 8.2**

### Property 4: Stack Role Identification

*For any* stack in the inventory, at least one stack member should have a role indicating master/primary status (Master, Active, or similar), and this should be clearly visible in the Role column.

**Validates: Requirements 8.3**

### Property 5: Sheet Creation Consistency

*For any* inventory report generation, if at least one device has `is_stack == True` with non-empty `stack_members`, the Stack Members sheet must exist in the workbook.

**Validates: Requirements 8.5**

### Property 6: Empty Sheet Handling

*For any* inventory where no devices have stack members, the Stack Members sheet should still be created with headers but contain no data rows.

**Validates: Requirements 8.4**

## Error Handling

### Missing or Incomplete Data

**Scenario**: Stack member object has None or missing values for optional fields (priority, MAC address, software version, state)

**Handling**: 
- Write empty string to Excel cell
- Log debug message indicating which field was missing for which device
- Continue processing remaining stack members

**Rationale**: Optional fields should not prevent report generation. Empty cells are acceptable for optional data.

### Malformed Stack Member Data

**Scenario**: Stack member object is missing required fields (switch_number, hardware_model, serial_number)

**Handling**:
- Log warning message with device hostname and stack member details
- Skip that specific stack member (do not write row)
- Continue processing remaining stack members

**Rationale**: Required fields are essential for meaningful reporting. Invalid data should be logged but not crash the report.

### Device Missing Stack Context

**Scenario**: Device has `is_stack == True` but `stack_members` list is None or empty

**Handling**:
- Log info message indicating device marked as stack but no members found
- Skip device (do not write any rows)
- Continue processing remaining devices

**Rationale**: This indicates incomplete discovery data. The device should not appear in the stack members sheet without actual member data.

### Excel Writing Errors

**Scenario**: Error occurs while writing to Excel (disk full, permission denied, etc.)

**Handling**:
- Allow exception to propagate to calling method
- Existing error handling in `generate_inventory_report()` will catch and log
- Report generation will fail with appropriate error message

**Rationale**: Excel writing errors are fatal for report generation and should be handled at the top level.

## Testing Strategy

### Unit Testing Approach

Unit tests will focus on specific scenarios and edge cases:

1. **Empty Inventory Test**: Verify sheet created with headers only when inventory is empty
2. **No Stacks Test**: Verify sheet created with headers only when no devices are stacks
3. **Single Stack Test**: Verify correct row creation for a device with 2 stack members
4. **Multiple Stacks Test**: Verify correct rows for multiple stacked devices
5. **Missing Optional Fields Test**: Verify empty cells for None values in optional fields
6. **Missing Required Fields Test**: Verify stack member skipped when required field missing
7. **Mixed Inventory Test**: Verify only stack devices contribute rows (non-stacks excluded)

### Property-Based Testing Approach

Property-based tests will verify universal correctness properties across randomized inputs:

**Test Configuration**:
- Library: Hypothesis (Python property-based testing library)
- Minimum iterations: 100 per property test
- Each test tagged with: **Feature: switch-stack-member-collection, Property N: [property text]**

**Property Test 1: Stack Member Completeness**
- Generate random inventory with random number of stacked devices
- Each stacked device has random number of stack members (1-9)
- Create sheet and verify row count equals total stack members across all devices
- Tag: **Feature: switch-stack-member-collection, Property 1: Stack Member Completeness**

**Property Test 2: Non-Stack Device Exclusion**
- Generate random inventory with mix of stacked and non-stacked devices
- Create sheet and verify no rows reference non-stacked device hostnames
- Tag: **Feature: switch-stack-member-collection, Property 2: Non-Stack Device Exclusion**

**Property Test 3: Required Field Presence**
- Generate random inventory with random stack configurations
- Create sheet and verify all rows have non-empty values for required columns
- Tag: **Feature: switch-stack-member-collection, Property 3: Required Field Presence**

**Property Test 4: Stack Role Identification**
- Generate random inventory where each stack has at least one master/active member
- Create sheet and verify each unique stack device has at least one row with master role
- Tag: **Feature: switch-stack-member-collection, Property 4: Stack Role Identification**

**Property Test 5: Sheet Creation Consistency**
- Generate random inventory (some with stacks, some without)
- Create report and verify Stack Members sheet exists in workbook
- Tag: **Feature: switch-stack-member-collection, Property 5: Sheet Creation Consistency**

**Property Test 6: Empty Sheet Handling**
- Generate random inventory with no stacked devices
- Create sheet and verify it has headers but zero data rows
- Tag: **Feature: switch-stack-member-collection, Property 6: Empty Sheet Handling**

### Integration Testing

Integration tests will verify the enhancement works within the full report generation flow:

1. **Full Report Generation**: Generate complete inventory report and verify Stack Members sheet present
2. **Sheet Ordering**: Verify Stack Members sheet appears in correct position (after Device Inventory)
3. **Table Formatting**: Verify Excel table created with correct name and styling
4. **Column Sizing**: Verify columns are auto-sized appropriately

### Test Data Requirements

Test data should include:
- Traditional StackWise configurations (Catalyst 3850, 9300)
- VSS configurations (Catalyst 4500-X, 6500)
- Single-member "stacks" (edge case)
- Maximum-size stacks (9 members)
- Stacks with missing optional data
- Mixed environments (stacks and standalone devices)

## Implementation Notes

### Code Location

File: `netwalker/reports/excel_generator.py`
Class: `ExcelReportGenerator`
New Method: `_create_stack_members_sheet()`
Modified Method: `generate_inventory_report()`

### Dependencies

- openpyxl library (already in use)
- Existing helper methods: `_apply_header_style()`, `_auto_size_columns()`, `_clean_hostname()`, `_extract_ip_address()`

### Performance Considerations

- Method iterates through all devices once: O(n) where n = number of devices
- For each stacked device, iterates through stack members: O(m) where m = members per stack
- Overall complexity: O(n * m) where m is typically small (2-9)
- Expected performance: Negligible impact on report generation time

### Backward Compatibility

- No changes to existing sheets or data structures
- No changes to database schema or queries
- No changes to discovery or collection logic
- Only adds new sheet to existing reports
- Fully backward compatible with existing code

## Configuration

No new configuration options required. The feature uses existing inventory data and follows existing report generation patterns.

## Future Enhancements

Potential future improvements (out of scope for this design):

1. **Stack Health Indicators**: Add visual indicators for stack health (all members ready, missing members, etc.)
2. **Stack Topology Diagram**: Generate visual representation of stack configurations
3. **Historical Stack Changes**: Track and report on stack membership changes over time
4. **Stack Capacity Analysis**: Show available stack capacity (e.g., "3 of 9 slots used")
5. **Cross-Reference Links**: Hyperlinks between Stack Members sheet and Device Inventory sheet
