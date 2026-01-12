# Queue Progress Tracking Enhancement

## Overview
Add real-time progress tracking to NetWalker's discovery engine to show queue processing status with device count and percentage completion.

## User Story
As a NetWalker user, I want to see real-time progress of the discovery process including:
- Current device being processed
- Number of devices processed vs total discovered
- Percentage completion
- Queue size remaining

## Requirements

### Functional Requirements
1. **Progress Display Format**: Show progress as "Processing device X of Y (Z% complete)"
2. **Console Output**: Display progress updates in real-time to console
3. **Log Output**: Include progress information in log files
4. **Dynamic Totals**: Update total device count as new neighbors are discovered
5. **Queue Status**: Show remaining queue size

### Technical Requirements
1. **Non-Blocking**: Progress updates should not significantly impact discovery performance
2. **Thread-Safe**: Progress tracking should work with concurrent operations
3. **Configurable**: Allow enabling/disabling progress tracking via configuration
4. **Consistent Format**: Use consistent formatting for all progress messages

## Implementation Plan

### Phase 1: Core Progress Tracking
1. Add progress tracking variables to `DiscoveryEngine` class
2. Implement progress calculation logic
3. Add progress logging to main discovery loop

### Phase 2: Enhanced Display
1. Add console progress updates
2. Implement percentage calculations
3. Add queue size tracking

### Phase 3: Configuration
1. Add configuration option to enable/disable progress tracking
2. Add configuration for progress update frequency

## Acceptance Criteria

### AC1: Basic Progress Display
- **Given** discovery is running
- **When** a device is being processed
- **Then** console shows "Processing device X of Y (Z% complete)"

### AC2: Queue Status
- **Given** discovery is running
- **When** devices are in the queue
- **Then** console shows "Queue: X devices remaining"

### AC3: Dynamic Updates
- **Given** new neighbors are discovered
- **When** they are added to the queue
- **Then** total device count is updated in progress display

### AC4: Log Integration
- **Given** progress tracking is enabled
- **When** progress updates occur
- **Then** progress information is logged to file

## Technical Design

### Progress Tracking Variables
```python
# Add to DiscoveryEngine.__init__()
self.total_devices_discovered = 0
self.devices_processed = 0
self.progress_enabled = config.get('enable_progress_tracking', True)
```

### Progress Calculation
```python
def _update_progress(self):
    if self.progress_enabled and self.total_devices_discovered > 0:
        percentage = (self.devices_processed / self.total_devices_discovered) * 100
        queue_size = len(self.discovery_queue)
        
        progress_msg = f"Processing device {self.devices_processed} of {self.total_devices_discovered} ({percentage:.1f}% complete) - Queue: {queue_size} remaining"
        
        logger.info(progress_msg)
        print(progress_msg)  # Direct console output
```

### Integration Points
1. **Main Discovery Loop**: Update progress after each device is processed
2. **Neighbor Processing**: Update total count when new devices are added to queue
3. **Queue Management**: Track queue size changes

## Files to Modify
1. `netwalker/discovery/discovery_engine.py` - Core progress tracking logic
2. `netwalker.ini` - Add configuration option for progress tracking
3. `netwalker/config/config_manager.py` - Handle new configuration option

## Testing Strategy
1. **Unit Tests**: Test progress calculation logic
2. **Integration Tests**: Test progress display during actual discovery
3. **Performance Tests**: Ensure progress tracking doesn't impact discovery speed
4. **Configuration Tests**: Test enabling/disabling progress tracking

## Success Metrics
1. Progress updates appear in console output
2. Progress information is logged to files
3. Progress calculations are accurate
4. No significant performance impact on discovery process
5. Configuration option works correctly