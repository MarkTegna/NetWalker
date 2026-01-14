# Skip Reason Column Enhancement

**Date:** January 14, 2026  
**Status:** Implemented  

## Summary

Added a "Skip Reason" column to the Device Inventory sheet in the discovery report to clearly identify why devices were skipped during discovery.

## Problem

Previously, the Device Inventory sheet showed devices with status "filtered" or "skipped" but didn't explain WHY they were filtered or skipped. Users had to guess or dig through logs to understand:
- Was it filtered by hostname pattern?
- Was it filtered by platform?
- Was it filtered by capabilities?
- Did it exceed the depth limit?
- Was it already discovered?

## Solution

Added a new "Skip Reason" column that provides clear, human-readable explanations for why each device was not fully discovered.

## Skip Reasons

### 1. Filtered by Hostname or IP Address Pattern
**When:** Device hostname or IP matches an exclusion pattern in configuration
**Example:** `Filtered by hostname or IP address pattern`

### 2. Filtered by Platform
**When:** Device platform matches an excluded platform (e.g., "linux", "windows", "phone")
**Example:** `Filtered by platform (cisco_ios) or capabilities (phone, switch)`

### 3. Filtered by Capabilities
**When:** Device capabilities match excluded capabilities (e.g., "camera", "printer")
**Example:** `Filtered by platform (unknown) or capabilities (camera, printer)`

### 4. Depth Limit Exceeded
**When:** Device is beyond the configured max_discovery_depth
**Example:** `Depth limit exceeded (depth 3 > max 2)`

### 5. Already Discovered
**When:** Device was already discovered earlier in the process
**Example:** `Already discovered` (future enhancement)

## Code Changes

### File 1: netwalker/discovery/discovery_engine.py

**Change 1: Add skip_reason for hostname/IP filtering** (line ~444):
```python
device_info = self._create_basic_device_info(node, "filtered")
device_info['skip_reason'] = "Filtered by hostname or IP address pattern"
self.inventory.add_device(device_key, device_info, "filtered")
```

**Change 2: Add skip_reason for platform/capability filtering** (line ~479):
```python
device_info['skip_reason'] = f"Filtered by platform ({device_platform}) or capabilities ({', '.join(device_capabilities) if device_capabilities else 'none'})"
```

**Change 3: Add skip_reason for neighbor filtering** (line ~758):
```python
device_info['skip_reason'] = f"Filtered by platform ({neighbor_platform}) or capabilities ({', '.join(neighbor_capabilities) if neighbor_capabilities else 'none'})"
```

**Change 4: Add skip_reason for depth limit** (line ~795):
```python
if neighbor_node.depth > self.max_depth:
    device_info = self._create_basic_device_info_for_neighbor(...)
    device_info['skip_reason'] = f"Depth limit exceeded (depth {neighbor_node.depth} > max {self.max_depth})"
    self.inventory.add_device(f"{neighbor_hostname}:{neighbor_ip}", device_info, "skipped")
    continue
```

### File 2: netwalker/reports/excel_generator.py

**Change 1: Add "Skip Reason" to headers** (line ~1214):
```python
headers = [
    "Device Key", "Hostname", "IP Address", "Platform", "Software Version",
    "VTP Version", "Serial Number", "Hardware Model", "Uptime", "Discovery Depth",
    "Discovery Method", "Parent Device", "Discovery Timestamp",
    "Connection Method", "Status", "Skip Reason"  # <-- NEW COLUMN
]
```

**Change 2: Add skip_reason to data rows** (line ~1256):
```python
ws.cell(row=row, column=16, value=device_info.get('skip_reason', ''))
```

## Excel Report Changes

### Before
| Device Key | Hostname | IP Address | Platform | Status |
|------------|----------|------------|----------|--------|
| PHONE-01:10.1.1.100 | PHONE-01 | 10.1.1.100 | cisco_phone | filtered |
| SW-REMOTE:10.2.1.1 | SW-REMOTE | 10.2.1.1 | cisco_ios | filtered |

**Problem:** Why were these filtered? User has to guess or check logs.

### After
| Device Key | Hostname | IP Address | Platform | Status | Skip Reason |
|------------|----------|------------|----------|--------|-------------|
| PHONE-01:10.1.1.100 | PHONE-01 | 10.1.1.100 | cisco_phone | filtered | Filtered by platform (cisco_phone) or capabilities (phone) |
| SW-REMOTE:10.2.1.1 | SW-REMOTE | 10.2.1.1 | cisco_ios | skipped | Depth limit exceeded (depth 3 > max 2) |

**Benefit:** Clear explanation of why each device was skipped.

## Example Skip Reasons

### Filtered by Hostname Pattern
```
Skip Reason: Filtered by hostname or IP address pattern
```
- Device hostname matched an exclusion pattern
- Example: hostname contains "PHONE" and exclude_hostnames includes "*PHONE*"

### Filtered by Platform
```
Skip Reason: Filtered by platform (linux) or capabilities (host)
```
- Device platform is "linux" which is in exclude_platforms
- Or device has "host" capability which is in exclude_capabilities

### Filtered by Capabilities
```
Skip Reason: Filtered by platform (unknown) or capabilities (camera, printer)
```
- Device has "camera" or "printer" capability
- These are typically in exclude_capabilities

### Depth Limit Exceeded
```
Skip Reason: Depth limit exceeded (depth 3 > max 2)
```
- Device is at depth 3
- Configuration has max_discovery_depth = 2
- Device was discovered as a neighbor but not walked

## Benefits

### 1. Better Visibility
- Clear explanation for every skipped device
- No need to dig through logs
- Easy to understand filtering decisions

### 2. Troubleshooting
- Quickly identify why important devices were skipped
- Verify filtering configuration is working correctly
- Identify devices that need configuration changes

### 3. Configuration Tuning
- See which filters are being applied
- Identify overly aggressive filters
- Adjust depth limits based on actual network topology

### 4. Documentation
- Report serves as documentation of discovery decisions
- Audit trail for why devices were/weren't discovered
- Helps explain results to stakeholders

## Use Cases

### Use Case 1: Depth Limit Adjustment
**Scenario:** User sees many devices with "Depth limit exceeded (depth 3 > max 2)"
**Action:** Increase max_discovery_depth to 3 or higher
**Result:** More complete network discovery

### Use Case 2: Filter Verification
**Scenario:** Important switch shows "Filtered by platform (cisco_ios)"
**Action:** Review exclude_platforms configuration
**Result:** Remove incorrect filter, re-run discovery

### Use Case 3: Capability Filtering
**Scenario:** Devices show "Filtered by capabilities (phone, switch)"
**Action:** Realize switch+phone capability is normal for PoE switches
**Result:** Adjust exclude_capabilities to only exclude pure phones

### Use Case 4: Network Boundary Understanding
**Scenario:** Many devices at specific sites show depth limit exceeded
**Action:** Understand network topology and adjust depth accordingly
**Result:** Better understanding of network structure

## Testing

### Verification Steps
1. Run discovery with filters configured
2. Open Device Inventory sheet
3. Check "Skip Reason" column exists
4. Verify filtered devices have clear skip reasons
5. Verify depth-limited devices show depth information
6. Verify skip reasons are human-readable

### Expected Results
- [ ] "Skip Reason" column appears in Device Inventory sheet
- [ ] Filtered devices show filter reason
- [ ] Depth-limited devices show depth exceeded message
- [ ] Skip reasons are clear and actionable
- [ ] Empty for successfully discovered devices

## Example Report

### Device Inventory Sheet

| Device Key | Hostname | IP Address | Platform | Status | Skip Reason |
|------------|----------|------------|----------|--------|-------------|
| CORE-A:10.1.1.1 | CORE-A | 10.1.1.1 | cisco_ios | connected | |
| SW01:10.1.1.10 | SW01 | 10.1.1.10 | cisco_ios | connected | |
| PHONE-101:10.1.2.101 | PHONE-101 | 10.1.2.101 | cisco_phone | filtered | Filtered by platform (cisco_phone) or capabilities (phone) |
| CAMERA-01:10.1.3.1 | CAMERA-01 | 10.1.3.1 | axis_camera | filtered | Filtered by platform (axis_camera) or capabilities (camera) |
| SW-REMOTE:10.2.1.1 | SW-REMOTE | 10.2.1.1 | cisco_ios | skipped | Depth limit exceeded (depth 3 > max 2) |
| LINUX-SRV:10.1.4.10 | LINUX-SRV | 10.1.4.10 | linux | filtered | Filtered by platform (linux) or capabilities (host) |

## Future Enhancements

Potential improvements:
1. Add skip reason for "Already discovered" (duplicate detection)
2. Add skip reason for "Connection failed" with error details
3. Add skip reason for "Authentication failed"
4. Add color coding in Excel (red for filtered, yellow for depth limit)
5. Add summary statistics of skip reasons

## Files Modified

1. `netwalker/discovery/discovery_engine.py`
   - Added skip_reason to filtered devices
   - Added skip_reason to depth-limited devices
   - Added skip_reason to platform/capability filtered devices

2. `netwalker/reports/excel_generator.py`
   - Added "Skip Reason" column to Device Inventory sheet
   - Added skip_reason data to report rows

---

**Status:** Implemented and ready for testing
**Next Step:** Build and test to verify skip reasons appear in reports
