# Seed File CLI Override Fix - Requirements

## Overview
Fix the seed file loading mechanism to properly support CLI overrides for custom seed file paths. Currently, when using `--rewalk-stale` or `--walk-unwalked`, a temporary seed file is created but not loaded because the `_load_seed_devices()` method doesn't check for the `seed_file` CLI override.

## Problem Statement
The database-driven discovery features (`--rewalk-stale` and `--walk-unwalked`) create a temporary seed file and set `cli_config['seed_file']` to point to it. However, `NetWalkerApp._load_seed_devices()` only checks for:
1. `seed_devices` config (comma-separated string)
2. Hardcoded filenames: `seed_device.ini` or `seed_file.csv`

It never checks `self.config.get('seed_file')`, so the temporary seed file is ignored and the app reports "No seed devices configured".

## User Stories

### 1. CLI Seed File Override
**As a** NetWalker user  
**I want** to specify a custom seed file path via CLI configuration  
**So that** I can use database-driven discovery with temporary seed files

**Acceptance Criteria:**
- 1.1: When `seed_file` is set in CLI config, `_load_seed_devices()` uses that path
- 1.2: CLI `seed_file` override takes precedence over default filenames
- 1.3: If the specified seed file doesn't exist, log an error and continue
- 1.4: The seed file path can be absolute or relative

### 2. Seed File Loading Priority
**As a** NetWalker developer  
**I want** a clear priority order for seed device sources  
**So that** the behavior is predictable and documented

**Acceptance Criteria:**
- 2.1: Priority order is: CLI `seed_devices` > CLI `seed_file` > default files
- 2.2: The priority order is documented in code comments
- 2.3: Log messages indicate which source was used
- 2.4: Only one source is used (first match wins)

### 3. Database-Driven Discovery Integration
**As a** NetWalker user  
**I want** `--rewalk-stale` and `--walk-unwalked` to work correctly  
**So that** I can rediscover stale devices and walk unwalked neighbors

**Acceptance Criteria:**
- 3.1: Temporary seed file created by database queries is loaded
- 3.2: Discovery runs with the devices from the database query
- 3.3: Reports are generated for the discovered devices
- 3.4: Temporary seed file is cleaned up after discovery

## Technical Requirements

### Code Changes Required
1. Modify `NetWalkerApp._load_seed_devices()` to check for `seed_file` CLI override
2. Implement priority order: `seed_devices` (CLI) → `seed_file` (CLI) → default files
3. Add logging to show which seed source was used
4. Handle missing seed file gracefully

### Files to Modify
- `netwalker/netwalker_app.py` - Update `_load_seed_devices()` method

## Success Criteria
- `--rewalk-stale X` successfully loads devices from database and runs discovery
- `--walk-unwalked` successfully loads unwalked devices and runs discovery
- Custom seed file paths work via CLI configuration
- Clear log messages indicate which seed source was used
- No regression in existing seed file loading behavior

## Out of Scope
- Changes to seed file format
- Changes to database query logic
- Changes to temporary file creation logic
- UI/UX improvements for seed file selection
