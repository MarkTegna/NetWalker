# System Information Banner Enhancement

## Summary
Added hostname, execution path, program name, and version information to both console output and log files at startup.

## Changes Made

### 1. Console Output (main.py)
- Added `print_console_banner()` function that displays:
  - Program name: "NetWalker"
  - Version number (from version.py)
  - Author name
  - Hostname (computer name where program is executed)
  - Execution path (working directory)
- Banner is displayed at the very beginning of program execution
- Applied to all execution modes:
  - Regular discovery
  - Database-driven discovery (--rewalk-stale, --walk-unwalked)
  - Visio diagram generation

### 2. Log Files (netwalker/logging_config.py)
- Updated `log_startup_banner()` function to include:
  - Program name: "NetWalker"
  - Hostname (computer name)
  - Executable path
  - Working directory (execution path)
  - Command line arguments
  - Python version
  - Platform information
- This information is logged at the top of every log file

## Example Console Output
```
================================================================================
Program: NetWalker
Version: 0.6.22
Author: Mark Oldham
--------------------------------------------------------------------------------
Hostname: DESKTOP-ABC123
Execution Path: C:\Users\Mark\NetWalker
================================================================================

Starting Network Topology Discovery...
--------------------------------------------------------------------------------
```

## Example Log File Output
```
2026-01-27 10:30:00 - netwalker.logging_config - INFO - ================================================================================
2026-01-27 10:30:00 - netwalker.logging_config - INFO - NetWalker Network Topology Discovery Tool
2026-01-27 10:30:00 - netwalker.logging_config - INFO - ================================================================================
2026-01-27 10:30:00 - netwalker.logging_config - INFO - Program: NetWalker
2026-01-27 10:30:00 - netwalker.logging_config - INFO - Version: 0.6.22
2026-01-27 10:30:00 - netwalker.logging_config - INFO - Author: Mark Oldham
2026-01-27 10:30:00 - netwalker.logging_config - INFO - Compile Date: 2026-01-27
2026-01-27 10:30:00 - netwalker.logging_config - INFO - Start Time: 2026-01-27 10:30:00
2026-01-27 10:30:00 - netwalker.logging_config - INFO - --------------------------------------------------------------------------------
2026-01-27 10:30:00 - netwalker.logging_config - INFO - Execution Information:
2026-01-27 10:30:00 - netwalker.logging_config - INFO -   Hostname: DESKTOP-ABC123
2026-01-27 10:30:00 - netwalker.logging_config - INFO -   Executable: main.py
2026-01-27 10:30:00 - netwalker.logging_config - INFO -   Working Directory: C:\Users\Mark\NetWalker
2026-01-27 10:30:00 - netwalker.logging_config - INFO -   Command Line: main.py --config netwalker.ini
2026-01-27 10:30:00 - netwalker.logging_config - INFO -   Python Version: 3.11.0
2026-01-27 10:30:00 - netwalker.logging_config - INFO -   Platform: win32
```

## Files Modified
1. `main.py` - Added console banner function and calls
2. `netwalker/logging_config.py` - Enhanced log startup banner with hostname

## Benefits
- Easy identification of which computer ran the program (useful in multi-user environments)
- Clear visibility of execution context (path, version, etc.)
- Improved troubleshooting and debugging capabilities
- Consistent information display across console and log files
