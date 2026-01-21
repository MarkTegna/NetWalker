# NetWalker v0.6.1 Release Notes

**Release Date:** January 20, 2026  
**Author:** Mark Oldham

## Overview
This release significantly improves the Visio diagram generator by fixing connector overlap issues when multiple connections exist between the same devices. Connectors now properly distribute across different edge points on device shapes and maintain glue relationships when shapes are moved.

## New Features

### Enhanced Visio Connector Distribution
- **Multiple Connection Support**: When multiple connections exist between the same two devices, connectors now attach to different points on the device edges instead of overlapping at the center
- **8-Point Distribution System**: Connectors cycle through 8 different connection points: right, top, left, bottom, and 4 corners
- **Intelligent Opposite-Side Routing**: Source and destination use opposite sides (e.g., right→left, top→bottom) for cleaner diagram layout
- **Maintained Glue Relationships**: Connectors use formulas that reference shape positions, so they move with devices when repositioned

## Improvements

### Visio Generator (COM-based)
- Connectors now use Visio formulas (`Sheet.ID!PinX+offset`) to maintain dynamic relationships with shapes
- Connection index tracking ensures each connection to the same device uses a different attachment point
- Self-loop connections (device to itself) are now automatically filtered out
- Enhanced logging shows connection point selection for debugging

### Code Quality
- Added connection_index parameter to `_create_connection_com()` method
- Improved connection tracking with per-device-pair counters
- Better error handling for connector creation failures

## Bug Fixes
- Fixed connector overlap issue where all connections to the same device appeared as a single line
- Fixed connectors not moving with shapes when repositioned
- Resolved formula syntax errors in Visio COM automation

## Technical Details

### Connection Point Distribution
```
Point 0: Right edge → Left edge
Point 1: Top edge → Bottom edge  
Point 2: Left edge → Right edge
Point 3: Bottom edge → Top edge
Point 4: Top-right corner → Bottom-left corner
Point 5: Top-left corner → Bottom-right corner
Point 6: Bottom-left corner → Top-right corner
Point 7: Bottom-right corner → Top-left corner
```

### Formula-Based Glue
Connectors use formulas like:
```
BeginX = Sheet.5!PinX+1.0 in
BeginY = Sheet.5!PinY+0.0 in
```
This ensures connectors stay attached to shapes at specific offset points.

## Files Changed
- `netwalker/reports/visio_generator_com.py` - Enhanced connector creation with distribution logic
- `netwalker/version.py` - Version updated to 0.6.1

## Testing
Tested with BORO site topology showing 14 connections:
- All 14 connectors now visible and properly separated
- Connectors maintain attachment when devices are moved
- No overlap between multiple connections to same device

## Known Issues
- Neighbor data is only collected from seed devices, not from discovered devices during walk (separate issue, not related to Visio generation)
- Some devices in database have no neighbor connections (discovery issue, not Visio issue)

## Upgrade Notes
- No breaking changes
- Existing diagrams can be regenerated with improved connector distribution
- All previous functionality maintained

## Next Steps
- Consider addressing neighbor data collection during device walk
- Potential enhancement: Allow user-configurable connection point preferences
- Consider adding connection point labels to show which point is being used

---

For more information, see the project documentation or contact Mark Oldham.
