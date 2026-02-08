# Visio Capability-Based Filtering Implementation

## Summary
Modified NetWalker to filter devices from Visio diagrams based on their CDP/LLDP capabilities instead of device names.

## Changes Made

### 1. Database Schema Updates
**File**: `netwalker/database/database_manager.py`
- Added `capabilities` column (NVARCHAR(500)) to `devices` table
- Added migration logic to add column to existing tables
- Capabilities stored as comma-separated string (e.g., "Router,Switch,IGMP")

### 2. Device Storage Updates
**File**: `netwalker/database/database_manager.py`
- Modified `upsert_device()` to accept and store capabilities from device_info dictionary
- Modified `resolve_hostname_to_device_id()` to accept capabilities and platform parameters
- Modified `store_neighbors()` to extract and pass neighbor capabilities when creating placeholder devices
- Unwalked neighbors now have their capabilities stored from CDP/LLDP discovery data

### 3. Visio Generator Updates
**File**: `netwalker/reports/visio_generator_com.py`
- Changed from device name pattern matching to capability-based filtering
- Renamed `exclude_patterns` to `exclude_capabilities`
- Modified `_should_exclude_device()` to check capabilities string instead of device name
- Updated `generate_topology_diagram()` to filter based on capabilities from database
- Uses wildcard matching (fnmatch) for capability patterns

### 4. Main Application Updates
**File**: `main.py`
- Updated device query to include `capabilities` column
- Capabilities passed to Visio generator for filtering

### 5. Configuration Updates
**File**: `netwalker.ini`
- Updated `[visio]` section comments to reflect capability-based filtering
- Changed default exclusions to capability patterns: `*phone*,*camera*,*printer*,host`
- Common CDP/LLDP capabilities: Router, Switch, Bridge, Host, Phone, Camera, Printer, IGMP, Source-Route-Bridge

## How It Works

1. **During Discovery**:
   - Devices discovered via CDP/LLDP have their capabilities captured
   - Capabilities stored in database when device is created/updated
   - Unwalked neighbors get capabilities from neighbor discovery data

2. **During Visio Generation**:
   - Devices queried from database with capabilities column
   - Each device's capabilities checked against exclusion patterns
   - Devices with matching capabilities excluded from diagram
   - Only connected devices with non-excluded capabilities appear in diagram

## Example

Device `KVUE-ntxnd03` discovered via CDP with capabilities: `["Host"]`
- Stored in database as: `capabilities = "Host"`
- INI setting: `exclude_devices = *phone*,*camera*,*printer*,host`
- Result: Device excluded from Visio diagram (matches "host" pattern)

## Testing

To test the implementation:
1. Run a discovery to populate capabilities in database
2. Generate Visio diagram for a site with diverse device types
3. Check logs for "Excluded X devices based on capability exclusion patterns"
4. Verify excluded devices don't appear in generated diagrams

## Configuration

Edit `netwalker.ini` `[visio]` section:
```ini
[visio]
# Exclude devices from Visio diagrams based on capabilities
# Supports wildcards: * (any characters), ? (single character)
# Comma-separated list of capability patterns to match
exclude_devices = *phone*,*camera*,*printer*,host
```

Common capability values from CDP/LLDP:
- Router
- Switch  
- Bridge
- Host (typically end devices, servers, workstations)
- Phone (IP phones)
- Camera (IP cameras)
- Printer
- IGMP
- Source-Route-Bridge

## Version
- Implementation: v0.6.17a
- Author: Mark Oldham
- Date: 2026-01-22
