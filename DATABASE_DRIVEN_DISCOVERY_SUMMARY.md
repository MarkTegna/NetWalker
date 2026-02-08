# Database-Driven Discovery Feature

## Summary
Added capability to perform discovery based on devices in the database, rather than requiring a seed file. This enables automated re-walking of stale devices and walking of previously unwalked neighbors.

## New CLI Options

### 1. Rewalk Stale Devices
**Command**: `--rewalk-stale DAYS [--rewalk-depth DEPTH]`

Walks devices that haven't been walked in X days.

**Parameters**:
- `--rewalk-stale DAYS`: Number of days threshold (required)
- `--rewalk-depth DEPTH`: Discovery depth for rewalking (default: 1)

**Behavior**:
- Queries database for devices with `last_seen` older than X days
- Excludes devices with `hardware_model='Unwalked Neighbor'`
- Only includes devices with `status='active'`
- Ignores seed file when this option is used
- Creates temporary seed file from database query results

**Example**:
```bash
# Rewalk devices not seen in 30 days with depth 2
netwalker.exe --rewalk-stale 30 --rewalk-depth 2

# Rewalk devices not seen in 7 days with default depth 1
netwalker.exe --rewalk-stale 7
```

### 2. Walk Unwalked Devices
**Command**: `--walk-unwalked [--walk-unwalked-depth DEPTH]`

Walks devices that have been discovered via CDP/LLDP but never directly connected to.

**Parameters**:
- `--walk-unwalked`: Enable unwalked device discovery (flag)
- `--walk-unwalked-depth DEPTH`: Discovery depth for walking (default: 1)

**Behavior**:
- Queries database for devices with `hardware_model='Unwalked Neighbor'`
- Only includes devices with `status='active'`
- Ignores seed file when this option is used
- Creates temporary seed file from database query results
- Shows device capabilities from CDP/LLDP discovery

**Example**:
```bash
# Walk all unwalked neighbors with depth 2
netwalker.exe --walk-unwalked --walk-unwalked-depth 2

# Walk all unwalked neighbors with default depth 1
netwalker.exe --walk-unwalked
```

## Implementation Details

### Database Methods Added
**File**: `netwalker/database/database_manager.py`

#### `get_stale_devices(days: int)`
- Returns devices not walked in X days
- Excludes 'Unwalked Neighbor' devices
- Returns: List of dicts with device_name, last_seen, platform, hardware_model

#### `get_unwalked_devices()`
- Returns devices with hardware_model='Unwalked Neighbor'
- Returns: List of dicts with device_name, platform, capabilities, first_seen, last_seen

### Main Application Updates
**File**: `main.py`

- Added CLI argument parsing for new options
- Added database query logic before normal discovery flow
- Creates temporary seed file from database results
- Overrides max_discovery_depth from CLI parameters
- Cleans up temporary seed file after discovery

## Use Cases

### 1. Scheduled Maintenance Discovery
Periodically rewalk devices to keep database fresh:
```bash
# Daily: Rewalk devices not seen in 7 days
netwalker.exe --rewalk-stale 7 --rewalk-depth 1

# Weekly: Rewalk devices not seen in 30 days with deeper discovery
netwalker.exe --rewalk-stale 30 --rewalk-depth 2
```

### 2. Complete Network Coverage
Walk devices discovered as neighbors but never directly accessed:
```bash
# Walk all unwalked neighbors to complete network map
netwalker.exe --walk-unwalked --walk-unwalked-depth 1
```

### 3. Automated Workflows
Combine with task scheduler for automated discovery:
```powershell
# Task 1: Daily rewalk of stale devices
schtasks /create /tn "NetWalker-Rewalk-Stale" /tr "C:\NetWalker\netwalker.exe --rewalk-stale 7" /sc daily

# Task 2: Weekly walk of unwalked devices
schtasks /create /tn "NetWalker-Walk-Unwalked" /tr "C:\NetWalker\netwalker.exe --walk-unwalked" /sc weekly
```

## Output Example

### Rewalk Stale Devices
```
Querying devices not walked in 30 days...
Found 15 stale devices:
  KVUE-CORE-A (last seen: 2025-12-15 10:30:00)
  KARE-DIST-SW1 (last seen: 2025-12-20 14:22:00)
  ...

Created temporary seed file with 15 devices
Starting discovery...

NetWalker 0.6.20 - Database-Driven Discovery
Author: Mark Oldham
------------------------------------------------------------
[Discovery proceeds normally]
```

### Walk Unwalked Devices
```
Querying unwalked devices (discovered but never walked)...
Found 8 unwalked devices:
  KVUE-ntxnd03 (platform: Unknown, capabilities: Host)
  KARE-AP-01 (platform: Unknown, capabilities: Bridge,Host)
  ...

Walking unwalked devices with depth: 1

Created temporary seed file with 8 devices
Starting discovery...

NetWalker 0.6.20 - Database-Driven Discovery
Author: Mark Oldham
------------------------------------------------------------
[Discovery proceeds normally]
```

## Benefits

1. **No Manual Seed File Management**: Automatically discovers devices from database
2. **Automated Maintenance**: Schedule periodic rewalking of stale devices
3. **Complete Coverage**: Easily walk previously unreachable neighbors
4. **Flexible Depth Control**: Specify discovery depth per operation
5. **Database-Centric**: Leverages existing database for intelligent discovery

## Notes

- Seed file is completely ignored when using these options
- Temporary seed file is automatically created and cleaned up
- Discovery depth can be controlled independently for each operation
- All normal discovery features (filtering, database storage, reporting) work as usual
- Credentials still come from configuration file or CLI arguments

## Version
- Implementation: v0.6.20
- Author: Mark Oldham
- Date: 2026-01-22
