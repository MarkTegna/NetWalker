# Stack Member Inventory Expansion Implementation

## Overview
Enhanced the Device Inventory Excel sheet to display each physical switch in a stack as a separate row, providing complete visibility into physical hardware inventory including individual serial numbers.

## Problem Solved
Previously, stack devices (like VSS configurations) were shown as a single logical device, making it difficult to track individual physical switches and their serial numbers for inventory management.

## Solution Implemented
**Option 2: Inline Expansion** - Each physical switch in a stack gets its own row in the Device Inventory sheet.

## Changes Made

### 1. Excel Generator Updates
**File:** `netwalker/reports/excel_generator.py`

#### New Columns Added:
- **Is Stack** (Column 9): "Yes" or "No" - indicates if device is part of a stack
- **Stack Role** (Column 10): "Active", "Standby", "Master", "Member" - role in the stack
- **Stack Number** (Column 11): 1, 2, 3, etc. - switch number in the stack
- **Physical Device** (Column 12): "Yes" or "No" - indicates if this is a physical switch vs logical stack device

#### Row Structure:
For a VSS stack like KGW-CORE-A with 2 members:

| Row | Device Key | Hostname | Serial Number | Is Stack | Stack Role | Stack Number | Physical Device |
|-----|------------|----------|---------------|----------|------------|--------------|-----------------|
| 2 | 10.1.1.1 | KGW-CORE-A | JAE240213DA | Yes | | | No |
| 3 | 10.1.1.1-SW1 | KGW-CORE-A-SW1 | JAE240213DA | Yes | Active | 1 | Yes |
| 4 | 10.1.1.1-SW2 | KGW-CORE-A-SW2 | JAE171504NJ | Yes | Standby | 2 | Yes |

### 2. Data Flow
1. Device collector detects stack and collects stack members
2. Stack members stored in device_info.stack_members list
3. Excel generator writes logical device row first
4. Then writes physical member rows for each stack member
5. Each physical member gets unique device key: `{parent_key}-SW{number}`

## Benefits

### For Inventory Management:
- ✓ Each physical switch has its own row with unique serial number
- ✓ Easy to count total physical devices: filter "Physical Device = Yes"
- ✓ Easy to identify all active switches: filter "Stack Role = Active"
- ✓ Serial numbers readily available for warranty tracking

### For Filtering and Reporting:
- ✓ Filter by "Is Stack = Yes" to see all stack devices
- ✓ Filter by "Physical Device = Yes" to see only physical hardware
- ✓ Filter by "Physical Device = No" to see logical devices
- ✓ Sort by "Stack Number" to see stack members in order

### For Troubleshooting:
- ✓ Quickly identify which physical switch has which serial number
- ✓ See role assignments (Active/Standby) at a glance
- ✓ Maintain relationship through hostname prefix

## Example Output

### VSS Stack (KGW-CORE-A):
```
Row 2: KGW-CORE-A           | Serial: JAE240213DA | Stack: Yes | Role: N/A     | Num: N/A | Physical: No
Row 3: KGW-CORE-A-SW1       | Serial: JAE240213DA | Stack: Yes | Role: Active  | Num: 1   | Physical: Yes
Row 4: KGW-CORE-A-SW2       | Serial: JAE171504NJ | Stack: Yes | Role: Standby | Num: 2   | Physical: Yes
```

### Standalone Switch (SWITCH-01):
```
Row 5: SWITCH-01            | Serial: FOC123456AB | Stack: No  | Role: N/A     | Num: N/A | Physical: No
```

## Testing

### Test File: `test_stack_inventory_expansion.py`

#### Test Coverage:
- ✓ Logical stack device row created correctly
- ✓ Physical member rows created for each switch
- ✓ Serial numbers correctly assigned to physical devices
- ✓ Stack role and number populated correctly
- ✓ Physical Device flag correctly set
- ✓ Standalone devices unaffected

#### Test Results:
All tests passed successfully. Test workbook saved to `test_stack_inventory.xlsx` for manual inspection.

## Compatibility

### Stack Types Supported:
- Traditional StackWise (Catalyst 2960, 3750, 3850)
- VSS (Virtual Switching System) - Catalyst 4500-X, 6500
- Modular Chassis (Nexus 9000 series)

### Backward Compatibility:
- Standalone switches (non-stack) display normally with "Is Stack = No"
- Existing reports continue to work
- No changes required to database schema
- No changes required to data collection

## Data Structure

### Logical Device Row:
- Shows aggregated information for the stack
- "Is Stack" = "Yes"
- "Physical Device" = "No"
- Stack Role and Stack Number are empty
- Serial Number shows primary switch serial (for reference)

### Physical Member Rows:
- Shows individual switch information
- "Is Stack" = "Yes"
- "Physical Device" = "Yes"
- Stack Role populated (Active/Standby/Master/Member)
- Stack Number populated (1, 2, 3, etc.)
- Serial Number shows actual physical switch serial
- Parent Device shows logical stack hostname

## Use Cases

### 1. Physical Inventory Count
Filter: "Physical Device = Yes"
Result: Count of all physical switches including stack members

### 2. Serial Number Lookup
Search: Serial number in column 7
Result: Find which device and stack position

### 3. Stack Configuration Review
Filter: "Is Stack = Yes" AND "Physical Device = No"
Result: All logical stack devices

### 4. Active Switch Identification
Filter: "Stack Role = Active"
Result: All active switches in VSS/stack configurations

### 5. Warranty Tracking
Export: "Physical Device = Yes" rows
Result: All physical devices with serial numbers for warranty management

## Version
- Current Version: 1.0.20a (automatic build)
- Build Type: Development/troubleshooting
- Python cache cleared before testing

## Files Modified
1. `netwalker/reports/excel_generator.py` - Added stack member expansion logic

## Files Created
1. `test_stack_inventory_expansion.py` - Test script
2. `test_stack_inventory.xlsx` - Test output workbook
3. `STACK_INVENTORY_EXPANSION_SUMMARY.md` - This document

## Next Steps
1. Test with actual discovery data from KGW-CORE-A
2. Verify Excel formatting and column widths
3. Consider adding conditional formatting to highlight physical devices
4. Update user documentation with new columns and filtering examples
