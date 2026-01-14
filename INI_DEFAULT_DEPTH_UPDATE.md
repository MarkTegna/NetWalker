# INI Configuration Default Depth Update

**Date:** January 14, 2026  
**Version:** 0.3.37  

## Summary

Reset default max_depth in distribution and main ini files from 99 to 2 for safer default behavior. Users can still configure any depth they want - no hard limits added to the software.

## Changes Made

### Files Updated

1. **netwalker.ini** (main configuration)
   - Changed: `max_depth = 99` → `max_depth = 2`
   - Reason: Safer default for general use

2. **dist/NetWalker_v0.3.37/netwalker.ini** (distribution)
   - Changed: `max_depth = 99` → `max_depth = 2`
   - Reason: Safer default for new users

3. **dist/NetWalker_v0.3.37.zip** (distribution package)
   - Recreated with updated ini file
   - Copied to Archive/NetWalker_v0.3.37.zip

### Files NOT Changed

- **integration_test.ini** - Already has `max_depth = 1` (appropriate for testing)
- **Software code** - NO hard limits added, users can configure any depth

## Configuration Flexibility

Users can configure any max_depth value they need:

### For Single Site Discovery (Default)
```ini
[discovery]
max_depth = 2
```
- Discovers seed device + 2 levels of neighbors
- Typical for single site/building
- Fast discovery (minutes)

### For Multi-Site Discovery
```ini
[discovery]
max_depth = 5
```
- Discovers across multiple connected sites
- Moderate discovery time (10-30 minutes)

### For Full Network Discovery
```ini
[discovery]
max_depth = 99
```
- Discovers entire network topology
- Long discovery time (60-90+ minutes for large networks)
- Requires increased timeout: `discovery_timeout = 7200`

## Important Notes

1. **No Hard Limits**: The software does NOT enforce any maximum depth limit
2. **User Configurable**: Users can set max_depth to any value (1-999+)
3. **Timeout Consideration**: Higher depths require longer timeouts
4. **Performance Impact**: Higher depths = more devices = longer discovery time

## Recommended Settings by Use Case

### Quick Site Survey (Default)
```ini
max_depth = 2
concurrent_connections = 10
discovery_timeout = 300  # 5 minutes
```

### Multi-Site Discovery
```ini
max_depth = 5
concurrent_connections = 10
discovery_timeout = 1800  # 30 minutes
```

### Full Enterprise Network
```ini
max_depth = 99
concurrent_connections = 10
discovery_timeout = 7200  # 2 hours
```

## Distribution Package

The updated distribution package includes:
- NetWalker.exe v0.3.37
- netwalker.ini with max_depth = 2 (default)
- All supporting files
- Documentation

**Location:**
- dist/NetWalker_v0.3.37.zip
- Archive/NetWalker_v0.3.37.zip

## Testing

Users who need deeper discovery (like WTSP-CORE-A testing) should:
1. Extract the distribution
2. Edit netwalker.ini
3. Change `max_depth = 2` to `max_depth = 99`
4. Ensure `discovery_timeout = 7200` for large networks
5. Run discovery

## Rationale

**Why default to 2?**
- Safer for new users (prevents accidental full network discovery)
- Faster discovery times (minutes vs hours)
- Reduces load on network infrastructure
- Still provides useful topology information (seed + 2 hops)
- Easy to increase when needed

**Why not hard limit?**
- Users may legitimately need full network discovery
- Different networks have different requirements
- Configuration flexibility is important
- Software should not restrict valid use cases

---

**Summary:** Default max_depth changed from 99 to 2 in distribution files. No hard limits added to software - users can configure any depth they need.
