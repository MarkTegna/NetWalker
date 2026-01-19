# NetWalker v0.5.12 Release Notes

**Release Date:** January 19, 2026  
**Author:** Mark Oldham

## Overview
This release adds connected port tracking to VLAN inventory, providing visibility into which VLAN ports are actively connected versus just configured.

## New Features

### Connected Ports Column in VLAN Inventory
- Added "Connected Ports" column to both VLAN Inventory and Master VLAN Inventory sheets
- Shows count of ports in each VLAN that have "connected" status
- Positioned between "Port Count" and "PortChannel Count" columns
- Provides insight into VLAN port utilization

**Example:**
- VLAN 20 with 4 configured ports (Gi1/0/1, Gi1/0/2, Twe4/1/1, Gi1/0/5)
- If Twe4/1/1 and Gi1/0/5 are "connected"
- Report shows: Port Count=4, Connected Ports=2

## Technical Implementation

### Interface Status Collection
- Added `show interfaces status` command execution during VLAN collection
- Parses interface status output to identify connected interfaces
- Matches connected interfaces to VLAN port assignments
- Counts connected ports per VLAN

### Interface Name Normalization
- Handles various interface name formats (Gi, Te, Twe, Fa, Eth, etc.)
- Normalizes names for accurate matching between VLAN and status data
- Supports both short and long interface name formats

### Data Model Updates
- Added `connected_port_count` field to `VLANInfo` dataclass
- Updated VLAN collector to gather interface status
- Enhanced VLAN parser with status parsing capabilities

## Files Modified
- `netwalker/connection/data_models.py` - Added connected_port_count field
- `netwalker/vlan/platform_handler.py` - Added interface status commands
- `netwalker/vlan/vlan_parser.py` - Added status parsing and port counting
- `netwalker/vlan/vlan_collector.py` - Added status collection and count updates
- `netwalker/reports/excel_generator.py` - Updated VLAN inventory sheets

## Testing
Successfully tested against production systems:
- BORO-CORE-A with depth 9
- 23 devices discovered
- 714 VLAN entries collected
- Interface status collection working correctly
- Connected port counts accurate

## Upgrade Notes
- No configuration changes required
- Existing INI files remain compatible
- Reports will automatically include new "Connected Ports" column
- No database schema changes

## Known Issues
None

## Future Enhancements
- Consider adding port utilization percentage
- Add trending for connected port counts over time
- Include port speed/duplex information in reports

---

For questions or issues, contact Mark Oldham.
