# Seed File CLI Override Fix - Tasks

## Task List

- [x] 1. Update `_load_seed_devices()` method to support CLI seed_file override
  - [x] 1.1 Add check for `self.config.get('seed_file')` after CLI seed_devices check
  - [x] 1.2 Verify file exists before attempting to load
  - [x] 1.3 Add appropriate logging for each seed source used
  - [x] 1.4 Handle missing CLI seed file gracefully (log error, continue to defaults)

- [x] 2. Test the fix with database-driven discovery
  - [x] 2.1 Test `--rewalk-stale X` command with production data
  - [x] 2.2 Test `--walk-unwalked` command with production data
  - [x] 2.3 Verify temporary seed file is loaded correctly
  - [x] 2.4 Verify discovery runs with queried devices

- [ ] 3. Verify backwards compatibility
  - [ ] 3.1 Test with default seed_file.csv (no CLI overrides)
  - [ ] 3.2 Test with CLI seed_devices (comma-separated string)
  - [ ] 3.3 Verify existing seed file formats still work

## Task Details

### Task 1: Update `_load_seed_devices()` method
**Location**: `netwalker/netwalker_app.py`, method `_load_seed_devices()` (around line 428)

**Changes Required**:
1. After the CLI `seed_devices` check, add a new check for CLI `seed_file`
2. Use `os.path.exists()` to verify the file exists
3. Call `self._parse_seed_file()` with the CLI-provided path
4. Add logging to indicate which seed source was used
5. If CLI seed file doesn't exist, log error and continue to default files

**Expected Outcome**: CLI seed_file override is properly checked and used when provided

### Task 2: Test with database-driven discovery
**Prerequisites**: Task 1 completed

**Test Steps**:
1. Build automatic version (letter increment)
2. Run `netwalker --rewalk-stale 2` with production database
3. Verify devices are loaded from database query
4. Verify discovery runs successfully
5. Run `netwalker --walk-unwalked` with production database
6. Verify unwalked devices are loaded and walked

**Expected Outcome**: Database-driven discovery works correctly with temporary seed files

### Task 3: Verify backwards compatibility
**Prerequisites**: Task 1 completed

**Test Steps**:
1. Test with default `seed_file.csv` (no CLI args)
2. Test with `--seed-devices "device1,device2"` CLI arg
3. Verify both scenarios work as before

**Expected Outcome**: No regression in existing seed file loading behavior

## Success Criteria
- [ ] CLI seed_file override is properly supported
- [ ] Database-driven discovery (`--rewalk-stale`, `--walk-unwalked`) works correctly
- [ ] Backwards compatibility maintained
- [ ] Clear logging shows which seed source was used
- [ ] No "No seed devices configured" error when temporary seed file is provided

## Notes
- This is a minimal fix focused on adding one check to the priority chain
- No changes to seed file format or parsing logic
- No changes to database query logic
- Temporary file cleanup is handled by `main.py`, not this fix
