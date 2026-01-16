# Build Cache Fix - Version 0.4.8

## Issue Identified

**Problem**: Building the executable without first clearing the Python cache was causing regression issues. PyInstaller was packaging old cached .pyc files into the executable, resulting in the built executable showing old behavior even though the source code was updated.

**Symptoms**:
- Source code is updated and correct
- Python tests pass when running source directly
- Built executable shows old behavior (doesn't reflect recent code changes)
- Version 0.4.6 and 0.4.7 had this issue with NX-OS extraction fixes

## Root Cause

PyInstaller includes Python bytecode (.pyc) files from `__pycache__` directories when building the executable. If these cached files are from an older version of the code, the executable will run the old code instead of the new code.

## Solution Implemented

### 1. Updated Build Script
Modified `build_executable.py` to automatically clear Python cache before building:

```python
# Step 0: Clear Python cache to prevent packaging old bytecode
print("Clearing Python bytecode cache...")
cache_result = subprocess.run([
    'powershell', '-ExecutionPolicy', 'Bypass', '-File', 'clear_python_cache.ps1'
], capture_output=True, text=True)
```

### 2. Updated Lessons Learned
Added comprehensive documentation to `.kiro/steering/lessons-learned.md`:

**PyInstaller build cache issues:**
- CRITICAL: PyInstaller can package old cached .pyc files into the executable, causing regression issues
- Symptoms: Source code is updated and correct, but built executable shows old behavior
- Solution: ALWAYS run clear_python_cache.ps1 BEFORE running build_executable.py
- Build process: 1) Clear cache, 2) Build executable, 3) Test
- Never skip the cache clearing step when building executables after code changes
- If a built executable doesn't reflect recent code changes, cached bytecode was likely packaged into the build

## Build Process (Now Automated)

The build script now automatically:
1. **Clears Python cache** - Removes all `__pycache__` directories and .pyc files
2. **Increments version** - Updates version number
3. **Prepares files** - Creates sample config files
4. **Creates spec file** - Generates PyInstaller spec
5. **Runs PyInstaller** - Builds executable with fresh code
6. **Tests executable** - Verifies build works
7. **Creates distribution** - Packages ZIP file

## Build Information

- **Version**: 0.4.8
- **Build Date**: 2026-01-15
- **Location**: `dist\NetWalker_v0.4.8\netwalker.exe`
- **Distribution**: `dist\NetWalker_v0.4.8.zip`
- **Archive**: `Archive\NetWalker_v0.4.8.zip`

## Changes in This Build

1. **Automatic cache clearing** - Build script now clears cache automatically
2. **NX-OS extraction fixes** - Includes all fixes from 0.4.6/0.4.7 (now properly packaged)
   - Software version extraction for NX-OS devices
   - Hardware model extraction for Nexus switches
   - Platform-specific pattern priority ordering

## Testing Instructions

Test with your network devices to verify:
1. NX-OS devices (DFW1-CORE-A, etc.) show correct version and hardware model
2. IOS/IOS-XE devices continue to work correctly
3. No regression issues from previous builds

## Prevention

Going forward, the build script automatically clears the cache, so this issue should not recur. However, if you ever need to manually build:

```powershell
# Manual build process
.\clear_python_cache.ps1
python build_executable.py
```

Never skip the cache clearing step!
