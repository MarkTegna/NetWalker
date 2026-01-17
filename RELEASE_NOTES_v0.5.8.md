# NetWalker v0.5.8 Release Notes

**Release Date:** January 17, 2026  
**Author:** Mark Oldham

## Overview

This release enhances DNS validation with improved hostname mismatch detection and consistent device filtering across all reports.

## New Features

### DNS Hostname Mismatch Detection
- **Enhanced Reverse DNS Validation**: DNS validation now explicitly tracks hostname mismatches
- **Clear Visual Indicators**: Excel report "Reverse DNS Success" column now shows:
  - `Yes` - Reverse DNS succeeded and hostname matches expected
  - `No` - Reverse DNS lookup failed
  - `Mismatch` - Reverse DNS succeeded but hostname doesn't match expected device name
- **Example**: Device `WPMT-NETWORK-SW01` with reverse DNS returning `WPMT-MGMT02` will show "Mismatch"

### Consistent Device Filtering
- **Unified Filtering Logic**: DNS validation now uses the same device filtering as Device Inventory sheet
- **Quality Focus**: Only validates devices with complete discovery data (status: `connected`, `discovered`, `success`)
- **Excludes Incomplete Data**: Skips devices with `skipped` status that have incomplete/inaccurate information
- **Logging Enhancement**: Shows count of excluded devices: "Starting DNS validation for X devices (Y skipped devices excluded)"

## Improvements

### Credentials File Search
- Extended search path to include grandparent directory (`..\..\secret_creds.ini`)
- Search order: current directory → parent directory → grandparent directory

### Hardware Detection
- **Nexus Switches**: Fixed hardware model extraction for devices with hyphens (e.g., C9336C-FX2)
- **Catalyst 4500X**: Added detection for WS-C4500X-16 series switches

### VLAN Parsing
- **NX-OS Fix**: Resolved duplicate VLAN warnings on Nexus devices
- Parser now correctly stops at "VLAN Type" section to avoid treating type information as VLAN names

## Technical Details

### DNS Validation Changes
- Added `reverse_dns_hostname_mismatch` field to `DNSValidationResult` dataclass
- Hostname comparison uses short names (before first dot) for flexibility
- Mismatch detection logs INFO level messages for troubleshooting

### Report Consistency
- DNS Validation report now contains same devices as Device Inventory sheet
- Both reports exclude skipped devices with incomplete data
- Provides consistent view across all generated reports

## Bug Fixes

- Fixed duplicate VLAN warnings on Nexus devices (VLAN Type section parsing)
- Fixed hardware model detection for Nexus switches with hyphenated model numbers
- Fixed credentials file search to properly check grandparent directory

## Files Changed

- `netwalker/validation/dns_validator.py` - Added hostname mismatch tracking
- `netwalker/reports/excel_generator.py` - Updated DNS report to show "Mismatch" status
- `netwalker/netwalker_app.py` - Applied device filtering to DNS validation
- `netwalker/config/credentials.py` - Extended credentials file search path
- `netwalker/discovery/device_collector.py` - Fixed hardware model extraction
- `netwalker/vlan/vlan_parser.py` - Fixed NX-OS VLAN Type section parsing

## Upgrade Notes

- No configuration changes required
- Existing `.ini` files remain compatible
- DNS validation reports will now show fewer devices (only those with complete data)
- "Mismatch" status in DNS reports indicates reverse DNS hostname doesn't match device hostname

## Known Issues

None

## Distribution

- **Executable**: `netwalker.exe`
- **Distribution Package**: `NetWalker_v0.5.8.zip`
- **Archive**: `Archive/NetWalker_v0.5.8.zip`

---

For questions or issues, contact Mark Oldham.
