# New Device Tracking Feature

## Summary
Added tracking for newly discovered devices during a discovery run. The wrap-up log now includes how many new devices were discovered.

## Changes Made

### 1. Database Manager (`netwalker/database/database_manager.py`)
- Modified `upsert_device()` to return a tuple `(device_id, is_new_device)` instead of just `device_id`
- `is_new_device` is `True` when:
  - A completely new device is inserted
  - An unwalked neighbor (serial='unknown') is updated to a fully walked device
- `is_new_device` is `False` when:
  - An existing device is updated (same name and serial)
  - An unwalked neighbor is created (serial='unknown')

- Modified `process_device_discovery()` to return a tuple `(success, is_new_device)` instead of just `success`
- Passes through the `is_new_device` flag from `upsert_device()`

### 2. Discovery Engine (`netwalker/discovery/discovery_engine.py`)
- Added `self.new_devices_discovered` counter in `__init__()`
- Updated the database storage section to unpack the tuple from `process_device_discovery()`
- Increments `new_devices_discovered` counter when `is_new_device` is `True`
- Added `'new_devices'` to the discovery summary dictionary in `_generate_discovery_summary()`
- Updated the completion log message to show: `"Found X devices (Y new)"`

### 3. NetWalker App (`netwalker/netwalker_app.py`)
- Updated the discovery completion message to include new device count
- Shows: `"Discovery completed - found X devices (Y new)"`

### 4. Test Files
- Updated all test files to handle the new tuple return signatures:
  - `tests/unit/test_database_primary_ip.py`
  - `tests/property/test_database_primary_ip_properties.py`
  - `tests/integration/test_database_connection_manager_integration.py`
- Changed `result = db_manager.process_device_discovery(...)` to `success, is_new = ...`
- Changed `assert result is True` to `assert success is True`
- Updated all mocks for `upsert_device` to return tuples: `Mock(return_value=(device_id, True))`

## Example Output

### Before:
```
Discovery completed in 45.23s - Found 150 devices, Timeout resets: 0
```

### After:
```
Discovery completed in 45.23s - Found 150 devices (12 new), Timeout resets: 0
```

## Version
- Current version: 1.0.32a (automatic build)
- Ready for testing

## Testing
- All existing unit tests pass
- The feature tracks new devices vs updated devices correctly
- Unwalked neighbors (placeholders) are not counted as new devices until they are fully walked
