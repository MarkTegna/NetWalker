# WTSP Discovery Root Cause Analysis and Fix

**Date:** January 14, 2026  
**Issue:** Devices at depth 3+ are queued but never processed  
**Status:** ROOT CAUSE IDENTIFIED

## Executive Summary

The discovery process is correctly queuing devices at depth 3 and beyond, but the **discovery timeout is being reached before these devices can be processed**. The timeout reset mechanism is working as designed but has a hard limit of 10 resets, which is insufficient for very large networks.

## Evidence from Log Analysis

### What's Working ✅
1. **Configuration is correct**: `max_discovery_depth: 99`, `discovery_timeout_seconds: 300`
2. **Depth 1 devices processed**: Multiple seed devices successfully walked
3. **Depth 2 devices processed**: KARE-CORE-A and others at depth 2 successfully walked
4. **Depth 3 devices ARE queued**: Hundreds of devices queued at depth 3
   - WCSH-SW02, WFAA-COM2-R252-SW03, WFMY-STUDIO-SW01, KARE-NEWS-SW1, etc.
5. **Timeout reset mechanism working**: 4 timeout resets performed during discovery

### What's Failing ❌
1. **Depth 3+ devices never processed**: All depth 3+ devices remain in queue as "Neighbor-only devices"
2. **Discovery stops prematurely**: 983 devices still in queue when timeout reached
3. **Timeout reached**: Discovery stopped at 307.80s (just over the 300s limit)

## Root Cause Analysis

### Timeline from Log

```
23:54:50 - Discovery starts with max_depth=99, timeout=300s
23:58:54 - Timeout reset #1 (55.9s remaining, 1 device added)
00:02:59 - Timeout reset #2 (55.8s remaining, 20 devices added)
00:07:32 - Timeout reset #3 (26.8s remaining, 21 devices added)
00:11:36 - Timeout reset #4 (55.9s remaining, 17 devices added)
00:16:44 - TIMEOUT REACHED after 307.80s
00:16:44 - Discovery stopped with 983 devices still in queue
00:16:44 - Only 76 devices discovered (processed)
```

### The Problem

The timeout reset mechanism in `discovery_engine.py` has these characteristics:

1. **Resets when < 20% time remaining**: `if remaining_time < (self.initial_discovery_timeout * 0.2)`
2. **Maximum 10 resets allowed**: `if self.timeout_resets <= 10`
3. **Each reset gives full timeout window**: Resets `discovery_start_time` to current time

**Why it failed:**
- With 5 concurrent connections and slow device responses, only ~76 devices were processed in ~22 minutes
- The timeout reset mechanism triggered 4 times but couldn't keep up with the queue growth
- After 4 resets, the 5th timeout window expired with 983 devices still queued
- The discovery stopped even though max_depth=99 should have allowed processing all queued devices

## Code Analysis

### Timeout Reset Logic (lines 813-838)

```python
def _reset_discovery_timeout_if_needed(self, new_devices_count: int):
    """Reset discovery timeout when new devices are added to handle large networks."""
    if self.discovery_start_time is None:
        return
    
    current_time = time.time()
    elapsed_time = current_time - self.discovery_start_time
    remaining_time = self.discovery_timeout - elapsed_time
    
    # Reset timeout if we're getting close to the limit and have new devices to process
    if remaining_time < (self.initial_discovery_timeout * 0.2):  # Less than 20% time remaining
        self.timeout_resets += 1
        self.devices_added_since_reset += new_devices_count
        
        # Reset the start time to give us more time for the new devices
        # But don't reset indefinitely - limit to reasonable number of resets
        if self.timeout_resets <= 10:  # Maximum 10 resets
            self.discovery_start_time = current_time
            logger.info(f"[TIMEOUT RESET] Discovery timeout reset #{self.timeout_resets}")
            # ... logging ...
            self.devices_added_since_reset = 0
        else:
            logger.warning(f"[TIMEOUT RESET LIMIT] Maximum timeout resets ({10}) reached")
```

### Discovery Loop Logic (lines 382-430)

```python
while self.discovery_queue:
    current_time = time.time()
    elapsed_time = current_time - self.discovery_start_time
    
    # Check if we've exceeded the discovery timeout
    if elapsed_time >= self.discovery_timeout:
        logger.warning(f"Discovery timeout reached after {elapsed_time:.2f}s")
        logger.info(f"Timeout resets performed: {self.timeout_resets}")
        break  # <-- STOPS HERE even with devices in queue
```

## The Issue

The timeout mechanism is **working as designed**, but the design doesn't account for:

1. **Very large networks**: With 1000+ devices across 50+ sites
2. **Slow device responses**: Some devices take 30+ seconds to respond
3. **Limited concurrency**: Only 5 concurrent connections
4. **Queue growth rate**: Queue grows faster than devices can be processed

**Math:**
- 1059 total devices discovered (queued)
- 76 devices processed in 307 seconds
- Average: ~4 seconds per device
- Time needed for all devices: 1059 × 4 = 4236 seconds (~70 minutes)
- Configured timeout: 300 seconds (5 minutes)

## Solution Options

### Option 1: Increase Discovery Timeout (RECOMMENDED)
**Change:** Increase `discovery_timeout_seconds` in config

**Pros:**
- Simple configuration change
- No code modifications needed
- Allows completion of large network discovery

**Cons:**
- Very long discovery times for large networks
- May need to be adjusted per network size

**Implementation:**
```ini
[Discovery]
discovery_timeout_seconds = 7200  ; 2 hours for large networks
```

### Option 2: Remove Timeout for Queue Processing
**Change:** Only apply timeout to individual device connections, not overall discovery

**Pros:**
- Discovery completes regardless of network size
- More predictable behavior

**Cons:**
- Requires code changes
- Could run indefinitely on network loops (though depth limit prevents this)

**Implementation:**
```python
# In discover_topology() method
while self.discovery_queue:
    # Remove timeout check - rely on depth limit instead
    current_node = self.discovery_queue.popleft()
    # ... process device ...
```

### Option 3: Increase Concurrent Connections
**Change:** Increase `max_concurrent_connections` to process devices faster

**Pros:**
- Faster discovery
- No timeout changes needed

**Cons:**
- May overwhelm network devices
- Requires more system resources
- Still may not be enough for very large networks

**Implementation:**
```ini
[Discovery]
max_concurrent_connections = 20  ; Increase from 5
```

### Option 4: Hybrid Approach (BEST)
**Combine multiple strategies:**

1. Increase timeout to reasonable value (1-2 hours)
2. Increase concurrent connections moderately (10-15)
3. Add progress-based timeout extension (reset if queue is actively being processed)

**Implementation:**
```ini
[Discovery]
discovery_timeout_seconds = 7200  ; 2 hours
max_concurrent_connections = 10   ; Moderate increase
```

Plus code change to reset timeout based on queue progress:
```python
# Reset timeout if we're making progress (processing devices)
if self.devices_processed > self.last_progress_check:
    # We're making progress - extend timeout
    self.discovery_start_time = current_time
    self.last_progress_check = self.devices_processed
```

## Recommended Fix

**Immediate Action:**
1. Increase `discovery_timeout_seconds` to 7200 (2 hours) in netwalker.ini
2. Increase `max_concurrent_connections` to 10
3. Test with WTSP-CORE-A seed device

**Long-term Enhancement:**
1. Modify timeout logic to be progress-based rather than time-based
2. Add configuration option for "unlimited" discovery (depth-limited only)
3. Add better progress reporting for long-running discoveries

## Testing Plan

1. **Update configuration:**
   ```ini
   [Discovery]
   max_discovery_depth = 99
   discovery_timeout_seconds = 7200
   max_concurrent_connections = 10
   ```

2. **Run test discovery:**
   ```
   netwalker.exe --seed WTSP-CORE-A --ip 10.36.115.120
   ```

3. **Monitor for:**
   - All depth 3+ devices being processed (not just queued)
   - KARE-NEWS-SW1 appearing in "Discovered Devices" sheet (not "Neighbor-only")
   - Discovery completing without timeout
   - Total devices discovered matching queue size

4. **Expected results:**
   - Discovery time: 60-90 minutes
   - Devices discovered: 1000+ (all queued devices processed)
   - No "Neighbor-only" devices (all queued devices walked)

## Files to Modify

1. **netwalker.ini** - Update discovery timeout and concurrency
2. **discovery_engine.py** (optional) - Enhance timeout logic for progress-based extension

## Conclusion

The issue is **NOT a bug** - it's a configuration limitation. The discovery timeout is too short for the size of your network. The timeout reset mechanism helps but has limits to prevent infinite loops.

**The fix is simple:** Increase the discovery timeout to allow sufficient time for large network discovery.

**Why WTSP-CORE-A specifically?**
- WTSP-CORE-A is likely a hub site with connections to many other sites
- This creates a very large discovery queue early in the process
- The queue grows faster than devices can be processed with current timeout/concurrency settings
