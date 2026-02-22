# Stack Member Collection Fixes

## Issues Found

### 1. NX-OS Duplicate Stack Members
**Problem**: NX-OS devices were showing duplicate stack member entries with invalid data
- Every module/line card was being treated as a "stack member"
- Supervisor modules, line cards, fabric modules, and power supplies all appeared as separate entries
- Roles showed as "Standby" and "NA" which don't make sense

**Root Cause**: NX-OS devices don't support traditional stacking like IOS devices. They use modular chassis with supervisor modules and line cards. The code was incorrectly treating "show module" output as stack information.

**Fix**: Modified `_collect_nxos_stack()` to return empty list since NX-OS doesn't have traditional stacking.

### 2. IOS-XE Stack Members Showing "Unknown"
**Problem**: Some IOS-XE devices (like CMCH-CORE-B) show "Unknown" for hardware model and serial number

**Root Cause**: These devices were walked before the stack collection fix was implemented (version 1.0.31). The old code used "show switch detail" which doesn't provide hardware/serial info.

**Solution**: Re-walk these devices to collect proper hardware model and serial numbers using "show inventory"

### 3. Stack Member Software Version
**Problem**: Stack members were showing VTP version (V02, V03) instead of IOS version

**Root Cause**: Code was setting software_version to hardware_version field from "show switch" output

**Fix**: Modified code to set software_version from parent device since all switches in a stack run the same IOS version

## Files Modified

1. `netwalker/discovery/stack_collector.py`
   - Line 185: Changed `software_version=hardware_version` to `software_version=None`
   - Line 193-205: Modified `_collect_nxos_stack()` to return empty list

2. `netwalker/discovery/device_collector.py`
   - Lines 107-113: Added code to set software_version from parent device for all stack members

## Testing Required

1. **Re-walk IOS-XE stacks** that show "Unknown" values:
   - CMCH-CORE-B (10.122.59.2)
   - Any other IOS-XE stacks with "Unknown" hardware/serial

2. **Verify NX-OS devices** no longer show stack members:
   - DFW1-ACCESS-SW01
   - DFW1-ACCESS-SW02
   - DFW1-CORE-A
   - DFW1-HUB-SW01

3. **Verify software version** shows correctly for all stack members (should match parent device IOS version, not VTP version)

## Version
- Current version: 1.0.34
- Fixes included in this build

## Commands to Re-walk Devices

To update devices with "Unknown" values:
```
.\netwalker.exe --seed-file cmch_devices.csv --depth 0
```

Where cmch_devices.csv contains:
```
10.122.59.2
```
