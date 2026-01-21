# NetWalker v0.6.11 Release Notes

**Release Date:** January 21, 2026  
**Author:** Mark Oldham

## Overview
This release adds support for unwalked neighbor discovery, allowing devices discovered via CDP/LLDP but not successfully connected to appear as leaf nodes in Visio diagrams.

## New Features

### Unwalked Neighbor Discovery
- **Placeholder Device Creation**: When a neighbor is discovered via CDP/LLDP but cannot be walked (connection fails or not attempted), a placeholder device record is automatically created in the database
- **Visio Diagram Integration**: Unwalked neighbors now appear as leaf nodes in Visio topology diagrams, providing a complete view of the network topology
- **Device Attributes**: Placeholder devices are marked with:
  - Serial Number: "unknown"
  - Platform: "Unknown"
  - Hardware Model: "Unwalked Neighbor"
  - Status: "active"

### "EVERYTHING" Site Support
- **Bulk Diagram Generation**: Use `--visio-site EVERYTHING` to generate diagrams for all sites in a single command
- **Explicit Syntax**: Provides a clear way to request all-site diagram generation

## Technical Improvements

### Database Manager Enhancements
- Modified `resolve_hostname_to_device_id()` to accept `create_if_missing` parameter
- Updated `upsert_device_neighbors()` to automatically create placeholder devices for unwalked neighbors
- Ensures complete topology representation in database

### Visio Generator
- Hierarchical layout with intelligent device positioning
- Multi-row support for devices at same hierarchy level
- Smart connector attachment based on relative device positions
- 8-point distribution system for multiple connections to same device

## Usage Examples

### Discover with Unwalked Neighbors
```bash
netwalker.exe --seed-devices device-name --max-depth 1
```
Unwalked neighbors will be automatically added to the database as placeholders.

### Generate Diagram for Specific Site
```bash
netwalker.exe --visio --visio-site REED
```
Diagram will include both walked devices and unwalked neighbors.

### Generate Diagrams for All Sites
```bash
netwalker.exe --visio --visio-site EVERYTHING
```

## Bug Fixes
- None in this release

## Known Issues
- Visio must be installed on the system for diagram generation
- COM automation requires Windows platform

## Upgrade Notes
- No database schema changes required
- Existing installations can upgrade directly
- Placeholder devices will be created automatically on next discovery run

## Files Changed
- `netwalker/database/database_manager.py` - Added placeholder device creation
- `netwalker/reports/visio_generator_com.py` - Hierarchical layout improvements
- `main.py` - Added EVERYTHING site support
- `netwalker_visio.py` - Added EVERYTHING site support
- `netwalker/version.py` - Version bump to 0.6.11

## Testing
- Tested with REED site discovery (2 devices, 1 unwalked neighbor)
- Verified placeholder device creation in database
- Confirmed Visio diagram generation with unwalked neighbors
- Validated hierarchical layout with multiple connection types

---

For more information, see the [NetWalker Comprehensive Guide](NETWALKER_COMPREHENSIVE_GUIDE.md).
