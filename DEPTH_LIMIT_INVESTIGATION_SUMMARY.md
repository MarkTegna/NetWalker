# Depth Limit Investigation Summary

## Issue Report
User reported that devices like BORO-ROAM-SW01 are being discovered but not walked, even though `max_depth = 99` is set in the configuration file.

## Investigation Findings

### Log Analysis
From `logs/netwalker_20260113-17-53.log`:
```
2026-01-13 17:53:27,619 - netwalker.discovery.discovery_engine - INFO - DiscoveryEngine initialized with max_depth=1, timeout=300s
...
2026-01-13 17:56:10,132 - netwalker.discovery.discovery_engine - INFO -     [NEIGHBOR DEPTH LIMIT] BORO-ROAM-SW01:10.4.97.41 at depth 2 exceeds max_depth 1
```

**Key Finding**: DiscoveryEngine is being initialized with `max_depth=1` despite config file showing `max_depth=99`.

### Configuration File Verification
Both `netwalker.ini` and `dist/NetWalker_v0.3.30/netwalker.ini` correctly show:
```ini
[discovery]
max_depth = 99
```

### Code Verification
1. `netwalker/config/config_manager.py` correctly reads `max_depth` from INI file
2. `netwalker/netwalker_app.py` correctly flattens config as `max_discovery_depth`
3. `netwalker/discovery/discovery_engine.py` correctly reads `max_discovery_depth` from config
4. Test script confirms config loading works correctly with `max_depth=99`

## Root Cause Analysis

The issue is **Python bytecode caching**. The user is running the source code with Python, and there are cached `.pyc` files in `__pycache__` directories that contain old code.

### Evidence:
1. Config files are correct (verified)
2. Current source code is correct (verified)
3. Test script loads config correctly (verified)
4. But actual run shows `max_depth=1` (from log)
5. Debug print statements added to code don't appear in log (indicating old code is running)

## Solution

Clear Python bytecode cache and restart:

```powershell
# Remove all __pycache__ directories
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# Remove all .pyc files
Get-ChildItem -Path . -Recurse -File -Filter "*.pyc" | Remove-Item -Force

# Verify cleanup
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__"
```

## Alternative Solution

If clearing cache doesn't work, rebuild the executable:
```powershell
python build_executable.py
```

Then run from the newly built `dist/` directory.

## Prevention

To prevent this issue in the future:
1. Always clear `__pycache__` after making code changes
2. Use `python -B` flag to prevent bytecode generation during development
3. Prefer running built executables for testing rather than source code

## Expected Behavior After Fix

After clearing cache, the log should show:
```
DiscoveryEngine initialized with max_depth=99, timeout=300s
```

And devices at depth 2+ should be walked:
- BORO-ROAM-SW01 (depth 2) - should be walked
- WTSP-CORE-A (depth 3) - should be walked
- All other discovered devices - should be walked up to depth 99

## Files Involved
- `netwalker/discovery/discovery_engine.py` - Discovery engine initialization
- `netwalker/netwalker_app.py` - Config flattening
- `netwalker/config/config_manager.py` - Config loading
- `netwalker/config/data_models.py` - Config data models
- `netwalker.ini` - Configuration file

## Date
January 13, 2026
