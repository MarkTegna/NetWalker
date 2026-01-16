# Nexus Hardware Model Extraction Fix - v0.4.15

## Issue
Hardware model extraction was failing for Cisco Nexus devices with model numbers containing hyphens (e.g., C9336C-FX2). The pattern was incorrectly matching "Nexus9000" instead of the actual chassis model.

## Root Cause
The regex pattern `cisco\s+Nexus\s+([\w-]+)\s+Chassis` was matching the first word after "Nexus", which could be:
- "Nexus9000" in format: `cisco Nexus9000 C9336C-FX2 Chassis`
- The actual model in format: `cisco Nexus 56128P Chassis`

This caused inconsistent results depending on whether the Nexus series number was present.

## Solution
Updated the pattern to `cisco\s+Nexus\d*\s+([\w-]+)\s+Chassis` which:
- Uses `\d*` to optionally match and skip the Nexus series number (e.g., "9000", "5000")
- Captures the actual chassis model that follows
- Handles models with hyphens (C9336C-FX2) and without (56128P, C9396PX)

## Changes Made

### File: `netwalker/discovery/device_collector.py`

**Pattern 2 (NX-OS Chassis with Chassis keyword):**
```python
# Before:
nexus_match = re.search(r'cisco\s+Nexus\s+([\w-]+)\s+Chassis', version_output, re.IGNORECASE)

# After:
nexus_match = re.search(r'cisco\s+Nexus\d*\s+([\w-]+)\s+Chassis', version_output, re.IGNORECASE)
```

**Pattern 2b (NX-OS without Chassis keyword):**
```python
# Before:
nexus_no_chassis = re.search(r'cisco\s+Nexus\s+([\w-]+)', version_output, re.IGNORECASE)

# After:
nexus_no_chassis = re.search(r'cisco\s+Nexus\d*\s+([\w-]+)', version_output, re.IGNORECASE)
```

## Testing

### Regression Test: DFW1-CORE-A
Real device test against DFW1-CORE-A (Cisco Nexus 9000):
- **Platform**: NX-OS ✓
- **Software Version**: 9.3(9) ✓
- **Hardware Model**: C9336C-FX2 ✓
- **Serial Number**: FDO23240FVE ✓

### Test Coverage
The fix now correctly handles:
1. `cisco Nexus9000 C9336C-FX2 Chassis` → Extracts: C9336C-FX2
2. `cisco Nexus 56128P Chassis` → Extracts: 56128P
3. `cisco Nexus9000 C9396PX Chassis` → Extracts: C9396PX

## Version History
- **v0.4.14**: Previous version with incorrect pattern
- **v0.4.15**: Fixed Nexus hardware model extraction pattern

## Files Modified
- `netwalker/discovery/device_collector.py` - Updated `_extract_hardware_model()` method
- `test_dfw1_core_a.py` - Updated expected hardware model to match actual device

## Build Information
- **Version**: 0.4.15
- **Build Date**: 2026-01-15
- **Author**: Mark Oldham
- **Distribution**: dist/NetWalker_v0.4.15.zip
- **Archive**: Archive/NetWalker_v0.4.15.zip

## Next Steps
User should test the executable with their full device inventory to verify:
1. NX-OS devices show correct hardware models
2. IOS-XE devices continue to work correctly (ISR4451-X/K9, etc.)
3. All device information appears correctly in inventory spreadsheets
