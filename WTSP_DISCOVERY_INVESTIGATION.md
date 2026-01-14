# WTSP-CORE-A Discovery Investigation

## Issue Report
User reported: "when running with depth 99 and seed boro-core-a I am seeing wtsp-core-a being discovered at level 2 but it is not being walked."

## Investigation Results

### Root Cause Found
**WTSP-CORE-A is being blocked by the depth limit, NOT by site boundary filtering.**

### Evidence from Logs
From `logs/netwalker_20260113-17-53.log`:

```
Line 30689: [FINAL DECISION] Device WTSP-CORE-A:10.36.115.120 will NOT be filtered - proceeding
Line 30690: [NEIGHBOR PASSED] WTSP-CORE-A:10.36.115.120 passed filtering checks
Line 30691: [NEIGHBOR CHECK] Checking if WTSP-CORE-A:10.36.115.120 should be queued
Line 30694: [NEIGHBOR DEPTH LIMIT] WTSP-CORE-A:10.36.115.120 at depth 2 exceeds max_depth
```

### Discovery Flow
1. **Depth 0**: BORO-CORE-A (seed device) is discovered
2. **Depth 1**: BORO-CORE-A's neighbors are discovered and walked
3. **Depth 2**: WTSP-CORE-A is discovered as a neighbor at depth 2
4. **Filtering**: WTSP-CORE-A passes ALL filtering checks
5. **Depth Check**: WTSP-CORE-A is rejected because depth 2 exceeds the configured max_depth

### Configuration Issue
The log shows that the actual max_depth being used is **1**, not 99 as expected.

This could be due to:
1. The configuration file has `max_depth = 1` instead of `max_depth = 99`
2. The configuration was not saved properly
3. A different configuration file is being used

## Solution

### Check Your Configuration
Open your `netwalker.ini` file and verify the `max_depth` setting:

```ini
[discovery]
max_depth = 99  # Should be 99, not 1
```

### Verify Configuration Loading
Run NetWalker with the `--verbose` flag to see what configuration is being loaded:

```bash
.\dist\netwalker.exe --config netwalker.ini --verbose
```

Look for log lines like:
```
Maximum discovery depth: 99
```

### Test with Correct Depth
After fixing the configuration:
1. Set `max_depth = 99` in your configuration file
2. Save the file
3. Run NetWalker again with BORO-CORE-A as seed
4. WTSP-CORE-A should now be walked at depth 2

## Additional Notes

### Site Boundary Pattern
WTSP-CORE-A **does** match the site boundary pattern `*-CORE-*`, but this is NOT preventing it from being walked in this case. The site boundary pattern is used for:
- Organizing devices into site-specific workbooks
- Determining site boundaries for reporting
- NOT for filtering devices from discovery (unless site collection mode is enabled)

### Depth Calculation
- **Depth 0**: Seed devices
- **Depth 1**: Direct neighbors of seed devices
- **Depth 2**: Neighbors of depth 1 devices
- **Depth 3**: Neighbors of depth 2 devices
- etc.

With `max_depth = 1`, only the seed and its direct neighbors are walked.
With `max_depth = 99`, virtually all reachable devices will be walked.

## Recommendation
1. **Verify** your `netwalker.ini` file has `max_depth = 99`
2. **Confirm** the correct configuration file is being used
3. **Re-run** the discovery with the corrected configuration
4. **Check** the logs to confirm WTSP-CORE-A is now being walked