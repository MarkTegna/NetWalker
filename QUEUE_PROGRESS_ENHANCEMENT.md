# Queue Progress Status Enhancement

**Date:** January 14, 2026  
**Status:** Implemented  

## Summary

Added a new queue progress status line to console and log file showing:
- Number of devices remaining in queue
- Total devices added to queue (after deduplication)
- Percentage remaining
- Visual markers (******) for easy visibility in scrolling console

## Implementation Details

### New Tracking Variables

Added to `DiscoveryEngine.__init__()`:
```python
# Queue progress tracking
self.total_queued = 0      # Total devices added to queue (after dedupe)
self.total_completed = 0   # Total devices completed (removed from queue)
```

### Increment Points

1. **When device added to queue (after dedupe):**
   - `add_seed_device()` - Increments `total_queued` when seed device added
   - `_process_neighbors()` - Increments `total_queued` when neighbor passes dedupe check

2. **When device completed:**
   - `discover_topology()` - Increments `total_completed` after device is walked

### Progress Display Format

**Queue Status Line:**
```
****** Queue: (100 of 200) 50.0% remaining ******
```

**Components:**
- `******` - Visual markers (6 asterisks before and after)
- `(100 of 200)` - (remaining / total queued)
- `50.0%` - Percentage remaining
- `******` - Closing visual markers

**Example Console Output:**
```
****** Queue: (150 of 200) 75.0% remaining ******
[PROGRESS] Processing device 50 of 200 (25.0% complete) - Queue: 150 remaining
****** Queue: (149 of 200) 74.5% remaining ******
[PROGRESS] Processing device 51 of 200 (25.5% complete) - Queue: 149 remaining
****** Queue: (148 of 200) 74.0% remaining ******
[PROGRESS] Processing device 52 of 200 (26.0% complete) - Queue: 148 remaining
```

## Code Changes

### File Modified
- `netwalker/discovery/discovery_engine.py`

### Changes Made

1. **Added tracking variables** (lines ~260-263):
```python
# Queue progress tracking
self.total_queued = 0  # Total devices added to queue (after dedupe)
self.total_completed = 0  # Total devices completed (removed from queue)
```

2. **Increment total_queued in add_seed_device()** (line ~278):
```python
self.total_queued += 1  # Increment total queued
```

3. **Increment total_completed in discover_topology()** (line ~320):
```python
# Update completed count after device is processed
self.total_completed += 1
```

4. **Increment total_queued in _process_neighbors()** (line ~786):
```python
self.total_queued += 1  # Increment total queued after dedupe
```

5. **Updated _update_progress_display()** (lines ~840-880):
```python
def _update_progress_display(self):
    """
    Update and display discovery progress information.
    Shows current progress with device count and percentage completion.
    Also shows queue progress: (remaining / total) = percent remaining
    """
    if not self.progress_enabled:
        return
    
    queue_size = len(self.discovery_queue)
    
    # Calculate queue progress
    if self.total_queued > 0:
        remaining = self.total_queued - self.total_completed
        percent_remaining = (remaining / self.total_queued) * 100
        
        # Create queue status message with visual markers
        queue_status = f"****** Queue: ({remaining} of {self.total_queued}) {percent_remaining:.1f}% remaining ******"
        
        # Log to file
        logger.info(queue_status)
        
        # Print to console for immediate visibility
        print(queue_status)
    
    # ... existing progress display code ...
```

## Benefits

1. **Better Visibility**
   - Visual markers (******) make status easy to spot in scrolling console
   - Clear indication of progress through queue

2. **Accurate Tracking**
   - Counts only devices actually added to queue (after deduplication)
   - Shows true remaining work

3. **Both Console and Log**
   - Status appears in both console (real-time) and log file (historical)
   - Easy to monitor during discovery and review after completion

4. **Percentage Calculation**
   - Shows percentage remaining (not percentage complete)
   - Intuitive understanding of work left to do

## Testing

### Test Scenarios

1. **Single Seed Device**
   - Should show: `****** Queue: (1 of 1) 100.0% remaining ******`
   - After completion: `****** Queue: (0 of 1) 0.0% remaining ******`

2. **Multiple Devices**
   - Should increment total_queued as neighbors are added
   - Should decrement remaining as devices are completed
   - Percentage should decrease from 100% to 0%

3. **Large Network (1000+ devices)**
   - Should accurately track progress through large queue
   - Visual markers should make status easy to find in logs

### Verification

Run discovery and check:
- [ ] Queue status appears in console
- [ ] Queue status appears in log file
- [ ] Visual markers (******) are present
- [ ] Format is: `(remaining of total) percent% remaining`
- [ ] Remaining count decreases as devices are processed
- [ ] Total queued increases as neighbors are added
- [ ] Percentage accurately reflects remaining work

## Example Log Output

```
2026-01-14 10:00:00,000 - netwalker.discovery.discovery_engine - INFO - Added seed device: CORE-A:10.1.1.1
2026-01-14 10:00:00,001 - netwalker.discovery.discovery_engine - INFO - ****** Queue: (1 of 1) 100.0% remaining ******
2026-01-14 10:00:05,000 - netwalker.discovery.discovery_engine - INFO -     [NEIGHBOR QUEUED] Added SW01:10.1.1.10 to discovery queue (depth 1)
2026-01-14 10:00:05,001 - netwalker.discovery.discovery_engine - INFO - ****** Queue: (2 of 2) 100.0% remaining ******
2026-01-14 10:00:10,000 - netwalker.discovery.discovery_engine - INFO - ****** Queue: (1 of 2) 50.0% remaining ******
2026-01-14 10:00:10,001 - netwalker.discovery.discovery_engine - INFO - [PROGRESS] Processing device 1 of 2 (50.0% complete) - Queue: 1 remaining
2026-01-14 10:00:15,000 - netwalker.discovery.discovery_engine - INFO - ****** Queue: (0 of 2) 0.0% remaining ******
2026-01-14 10:00:15,001 - netwalker.discovery.discovery_engine - INFO - [PROGRESS] Processing device 2 of 2 (100.0% complete) - Queue: 0 remaining
```

## Configuration

This feature respects the existing `enable_progress_tracking` configuration:

```ini
[discovery]
enable_progress_tracking = true  # Enable queue progress display
```

If set to `false`, no progress messages (including queue status) will be displayed.

## Future Enhancements

Potential improvements:
1. Add estimated time remaining based on average device processing time
2. Add rate of progress (devices per minute)
3. Add color coding for console output (green = good progress, yellow = slow, red = stalled)
4. Add summary at end showing total queued, total completed, total filtered

---

**Status:** Ready for testing
**Next Step:** Build and test with real discovery to verify queue progress tracking
