# Seed File CLI Override Fix - Design

## Architecture Overview
This fix modifies the seed device loading logic in `NetWalkerApp._load_seed_devices()` to support CLI-provided seed file paths. The change is minimal and focused on adding a single check in the priority chain.

## Component Design

### Modified Component: NetWalkerApp._load_seed_devices()

**Current Logic:**
```python
def _load_seed_devices(self):
    # 1. Check for CLI seed_devices (comma-separated string)
    seed_config = self.config.get('seed_devices', '')
    if seed_config:
        self.seed_devices = [device.strip() for device in seed_config.split(',')]
        return
    
    # 2. Check for default files
    seed_files = ['seed_device.ini', 'seed_file.csv']
    for seed_file in seed_files:
        if os.path.exists(seed_file):
            self.seed_devices = self._parse_seed_file(seed_file)
            break
```

**New Logic:**
```python
def _load_seed_devices(self):
    # Priority 1: CLI seed_devices (comma-separated string)
    seed_config = self.config.get('seed_devices', '')
    if seed_config:
        self.seed_devices = [device.strip() for device in seed_config.split(',')]
        logger.info(f"Loaded {len(self.seed_devices)} seed devices from CLI arguments")
        return
    
    # Priority 2: CLI seed_file (custom path)
    seed_file_path = self.config.get('seed_file', '')
    if seed_file_path:
        if os.path.exists(seed_file_path):
            self.seed_devices = self._parse_seed_file(seed_file_path)
            logger.info(f"Loaded {len(self.seed_devices)} seed devices from CLI-specified file: {seed_file_path}")
            return
        else:
            logger.error(f"CLI-specified seed file not found: {seed_file_path}")
            # Continue to check default files as fallback
    
    # Priority 3: Default files
    seed_files = ['seed_device.ini', 'seed_file.csv']
    for seed_file in seed_files:
        if os.path.exists(seed_file):
            self.seed_devices = self._parse_seed_file(seed_file)
            logger.info(f"Loaded {len(self.seed_devices)} seed devices from {seed_file}")
            return
    
    # No seed devices found
    logger.warning("No seed devices configured")
```

## Data Flow

### Database-Driven Discovery Flow
```
1. User runs: netwalker --rewalk-stale 2
2. main.py queries database for stale devices
3. main.py creates temporary seed file: /tmp/tmpXXXXXX.csv
4. main.py sets cli_config['seed_file'] = '/tmp/tmpXXXXXX.csv'
5. NetWalkerApp.__init__ receives cli_args with seed_file
6. _initialize_configuration() applies CLI overrides to self.config
7. _load_seed_devices() checks self.config.get('seed_file')
8. Temporary seed file is loaded and parsed
9. Discovery runs with devices from database
10. Temporary file is cleaned up
```

### Priority Chain
```
┌─────────────────────────────────────┐
│ Check CLI seed_devices (string)    │
│ Priority: 1 (Highest)               │
└──────────┬──────────────────────────┘
           │ Not found
           ▼
┌─────────────────────────────────────┐
│ Check CLI seed_file (path)          │
│ Priority: 2                         │
└──────────┬──────────────────────────┘
           │ Not found or doesn't exist
           ▼
┌─────────────────────────────────────┐
│ Check default files                 │
│ - seed_device.ini                   │
│ - seed_file.csv                     │
│ Priority: 3 (Lowest)                │
└──────────┬──────────────────────────┘
           │ Not found
           ▼
┌─────────────────────────────────────┐
│ No seed devices configured          │
│ (Warning logged)                    │
└─────────────────────────────────────┘
```

## Error Handling

### Missing CLI Seed File
- **Scenario**: User specifies `seed_file` but file doesn't exist
- **Behavior**: Log error, continue to check default files as fallback
- **Rationale**: Graceful degradation - don't fail completely if custom path is wrong

### Empty Seed File
- **Scenario**: Seed file exists but contains no valid devices
- **Behavior**: `self.seed_devices` will be empty list, warning logged
- **Rationale**: Existing behavior maintained

### Invalid Seed File Format
- **Scenario**: Seed file has malformed CSV
- **Behavior**: `_parse_seed_file()` handles exceptions, returns empty list
- **Rationale**: Existing error handling maintained

## Logging Strategy

### Log Messages
1. **CLI seed_devices used**: `"Loaded {count} seed devices from CLI arguments"`
2. **CLI seed_file used**: `"Loaded {count} seed devices from CLI-specified file: {path}"`
3. **CLI seed_file not found**: `"CLI-specified seed file not found: {path}"`
4. **Default file used**: `"Loaded {count} seed devices from {filename}"`
5. **No seeds found**: `"No seed devices configured"`

### Log Levels
- INFO: Successful seed loading
- ERROR: CLI-specified file not found
- WARNING: No seed devices configured

## Testing Strategy

### Unit Tests
1. Test CLI `seed_devices` takes priority over `seed_file`
2. Test CLI `seed_file` is used when `seed_devices` not provided
3. Test default files used when no CLI overrides
4. Test error handling for missing CLI seed file
5. Test empty seed file handling

### Integration Tests
1. Test `--rewalk-stale` with real database
2. Test `--walk-unwalked` with real database
3. Test temporary seed file creation and cleanup
4. Test discovery runs with database-queried devices

## Backwards Compatibility
- **Existing behavior preserved**: Default file checking unchanged
- **No breaking changes**: All existing seed file formats still work
- **CLI additions only**: New functionality via CLI, no config file changes

## Performance Considerations
- **Minimal overhead**: Single additional `config.get()` call
- **No new I/O**: Only reads file if path is provided
- **Same parsing logic**: Uses existing `_parse_seed_file()` method

## Security Considerations
- **Path validation**: Use `os.path.exists()` to verify file exists
- **No path traversal**: Python's file operations handle this safely
- **Temporary file cleanup**: Handled by `main.py` using `try/finally`

## Correctness Properties

### Property 1: Seed Source Priority
**Property**: CLI seed_devices takes precedence over CLI seed_file, which takes precedence over default files

**Validation**: Unit test that sets all three sources and verifies CLI seed_devices is used

### Property 2: Seed File Loading
**Property**: When seed_file is set in config and file exists, devices are loaded from that file

**Validation**: Integration test with temporary seed file

### Property 3: Graceful Degradation
**Property**: If CLI seed_file doesn't exist, system falls back to default files

**Validation**: Unit test with non-existent CLI seed_file path

## Implementation Notes

### Code Location
- **File**: `netwalker/netwalker_app.py`
- **Method**: `_load_seed_devices()` (lines 428-453)
- **Change type**: Insert new check between existing checks

### Dependencies
- No new dependencies required
- Uses existing `os.path.exists()` and `_parse_seed_file()` method

### Rollback Plan
- Simple revert: Remove the added check
- No database changes required
- No config file changes required
