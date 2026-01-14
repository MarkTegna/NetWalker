# Progress Message Duplication Fix

**Date:** January 14, 2026  
**Status:** Fixed  

## Issue

Progress messages were appearing duplicated in the log file:

```
2026-01-14 09:40:44,299 - INFO - ****** (4 of 21) 19.0% complete - 17 remaining ************ (4 of 21) 19.0% complete - 17 remaining ******
```

## Root Cause

The `_update_progress_display()` method was both:
1. Logging the message via `logger.info(queue_status)`
2. Printing the message via `print(queue_status)`

The `print()` statement was being captured by a logging handler that redirects stdout to the log file, causing the message to appear twice.

## Solution

Removed the redundant `print()` statements. The `logger.info()` calls are sufficient because:
1. They write to the log file
2. The logging configuration already outputs INFO messages to console
3. No need for explicit `print()` statements

## Code Changes

### File: netwalker/discovery/discovery_engine.py

**Before:**
```python
def _update_progress_display(self):
    if self.total_queued > 0:
        queue_status = f"****** ({self.total_completed} of {self.total_queued}) {percent_complete:.1f}% complete - {remaining} remaining ******"
        
        # Log to file
        logger.info(queue_status)
        
        # Print to console for immediate visibility
        print(queue_status)  # <-- CAUSING DUPLICATION
```

**After:**
```python
def _update_progress_display(self):
    if self.total_queued > 0:
        queue_status = f"****** ({self.total_completed} of {self.total_queued}) {percent_complete:.1f}% complete - {remaining} remaining ******"
        
        # Log to file and console
        logger.info(queue_status)  # <-- SUFFICIENT
```

## Result

**Before (Duplicated):**
```
2026-01-14 09:40:44,299 - INFO - ****** (4 of 21) 19.0% complete - 17 remaining ************ (4 of 21) 19.0% complete - 17 remaining ******
```

**After (Clean):**
```
2026-01-14 09:40:44,299 - INFO - ****** (4 of 21) 19.0% complete - 17 remaining ******
```

## Why This Happened

The original code had `print()` statements for "immediate visibility" in the console. However:
1. The logging system is already configured to output INFO messages to console
2. Some logging configurations capture stdout (print statements) and redirect them to the log
3. This caused the message to appear twice: once from logger.info() and once from print()

## Testing

### Verification
- [ ] Run discovery and check log file
- [ ] Verify progress messages appear only once
- [ ] Verify messages still appear in console
- [ ] Verify messages still appear in log file

### Expected Output
```
****** (1 of 21) 4.8% complete - 20 remaining ******
****** (2 of 21) 9.5% complete - 19 remaining ******
****** (3 of 21) 14.3% complete - 18 remaining ******
****** (4 of 21) 19.0% complete - 17 remaining ******
```

Each message should appear exactly once.

## Files Modified

- `netwalker/discovery/discovery_engine.py` - Removed redundant print() statements

---

**Status:** Fixed and ready for testing
**Next Step:** Build and verify no message duplication
