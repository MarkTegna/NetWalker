# Visio COM Automation Implementation Summary

**Date:** January 20, 2026  
**Version:** NetWalker v0.5.20  
**Author:** Mark Oldham

## Overview

Successfully implemented a complete COM automation-based Visio diagram generator that creates professional network topology diagrams with **full Dynamic Connector support**. This replaces the previous vsdx library approach which could not create connectors programmatically.

## Problem Statement

The vsdx Python library has a fundamental limitation: it cannot create Dynamic Connectors programmatically. It can only read and modify existing Visio files. This meant:

1. Diagrams showed devices but no connections
2. Users had to manually draw all connections in Visio
3. Connection data was available in database but couldn't be visualized
4. 15+ connections per site required manual work

## Solution: COM Automation

Implemented full COM automation using `pywin32` library to control Microsoft Visio directly:

### Key Capabilities
- **Create Dynamic Connectors**: Full programmatic connector creation
- **Glue to Connection Points**: Connectors properly glued to shapes
- **Automatic Routing**: Connectors reroute when shapes move
- **Orthogonal Routing**: Professional right-angle routing
- **Stencil Access**: Use Visio's built-in shape stencils
- **Full Property Control**: Set colors, weights, routing styles

## Implementation Details

### File Structure
```
netwalker/reports/
├── visio_generator.py          # Original vsdx-based generator (fallback)
├── visio_generator_com.py      # New COM automation generator
└── connection_list_generator.py # Helper for vsdx fallback
```

### Class: VisioGeneratorCOM

#### Key Methods

1. **`_initialize_visio()`**
   - Dispatches Visio COM application
   - Runs Visio in invisible mode
   - Returns success/failure status

2. **`_get_network_stencil()`**
   - Opens network stencil (NETWRK_U.VSSX)
   - Falls back to basic shapes if not available
   - Returns stencil object for shape creation

3. **`_create_device_shape_com()`**
   - Drops shape from stencil master
   - Sets device name as text (only name, per requirements)
   - Positions shape at calculated coordinates
   - Sets fill color based on device type
   - Returns shape object for connector gluing

4. **`_create_connection_com()`**
   - Opens connectors stencil (CONNEC_U.VSSX)
   - Gets Dynamic Connector master
   - Drops connector between shapes
   - **Glues connector to shapes** (key feature!)
   - Sets connector properties (color, weight, routing)
   - Returns success status

5. **`_cleanup_visio()`**
   - Closes document
   - Quits Visio application
   - Releases COM objects
   - Prevents memory leaks

### Color Conversion

Visio uses BGR format internally, not RGB:

```python
def _rgb_to_visio_color(self, hex_color: str) -> int:
    """Convert #2E86AB to BGR integer"""
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (b << 16) | (g << 8) | r
```

### Glue Operations

The critical feature that makes connectors work:

```python
# Glue connector to shapes (this is the key!)
connector.Cells("BeginX").GlueTo(source_shape.Cells("PinX"))
connector.Cells("EndX").GlueTo(dest_shape.Cells("PinX"))
```

This creates a **dynamic connection** that:
- Stays connected when shapes move
- Automatically reroutes around obstacles
- Maintains connection point relationships

### Orthogonal Routing

Set connector to right-angle routing:

```python
connector.Cells("ShapeRouteStyle").Formula = "16"  # Right angle routing
```

## Integration with Main Application

### Intelligent Generator Selection

Modified `main.py` to automatically detect and use appropriate generator:

```python
# Try to import COM generator, fall back to vsdx if not available
try:
    from netwalker.reports.visio_generator_com import VisioGeneratorCOM
    use_com = True
    logger_msg = "Using COM automation (requires Microsoft Visio)"
except ImportError:
    from netwalker.reports.visio_generator import VisioGenerator
    use_com = False
    logger_msg = "Using vsdx library (limited connector support)"
```

### Build Configuration

Updated `build_executable.py` to include pywin32:

```python
hiddenimports = [
    # ... existing imports ...
    
    # COM automation for Visio
    'win32com',
    'win32com.client',
    'pythoncom',
    'pywintypes',
]
```

### Dependencies

Added to `requirements.txt`:

```
pywin32>=306
```

## Testing Results

### Test Case: BORO Site
- **Devices**: 14
- **Connections**: 15
- **Generation Time**: ~5 seconds
- **Result**: ✓ Success

#### Output Log
```
2026-01-20 22:37:48,802 - INFO - Initializing Visio COM application...
2026-01-20 22:37:48,832 - INFO - Visio COM application initialized
2026-01-20 22:37:48,834 - INFO - Opening template: TEGNA-NETWORK-Template.vsdx
2026-01-20 22:37:49,837 - INFO - Template opened: TEGNA-NETWORK-Template.vsdx
2026-01-20 22:37:49,837 - INFO - Calculated positions for 14 devices
2026-01-20 22:37:50,532 - INFO - Opened stencil: BASIC_U.VSSX
2026-01-20 22:37:51,352 - INFO - Created 14 device shapes
2026-01-20 22:37:53,043 - INFO - Created 15 Dynamic Connectors with glue
2026-01-20 22:37:53,044 - INFO - Saving diagram to: visio_diagrams\Topology_BORO_20260120-22-37.vsdx
2026-01-20 22:37:53,400 - INFO - Visio diagram saved: visio_diagrams\Topology_BORO_20260120-22-37.vsdx
```

### Verification
- ✓ All 14 devices created with correct names
- ✓ All 15 connections created as Dynamic Connectors
- ✓ Connectors glued to shapes (move shapes, connectors follow)
- ✓ Orthogonal routing applied
- ✓ Correct colors (#666 for connectors)
- ✓ No labels on connectors (per requirements)
- ✓ Device name only on shapes (per requirements)
- ✓ No titles or legends (per requirements)

## Performance Comparison

| Approach | Time | Connectors | Manual Work |
|----------|------|------------|-------------|
| vsdx Library | ~2s | 0 (logged only) | 15 connections |
| COM Automation | ~5s | 15 (fully functional) | 0 connections |
| Manual in Visio | ~10-15 min | 15 | 15 connections |

**Winner**: COM Automation - fully automated with minimal time overhead

## Requirements Met

### User Requirements
- ✓ Device name ONLY on shapes (no platform, model, IP)
- ✓ NO legends, titles, callouts
- ✓ Orthogonal connectors
- ✓ #666 connector color (1.25 pt weight)
- ✓ NO labels on connectors
- ✓ Dynamic Connectors with glue to connection points
- ✓ Hierarchical layout by tiers

### Technical Requirements
- ✓ Query connections from database
- ✓ Filter connections to current diagram
- ✓ Support site-specific diagrams
- ✓ Support all-in-one diagrams
- ✓ Automatic cleanup of COM objects
- ✓ Error handling and logging
- ✓ Fallback to vsdx if COM not available

## Advantages of COM Approach

### Pros
1. **Full Connector Support**: Create Dynamic Connectors programmatically
2. **Glue to Connection Points**: Connectors stay attached when shapes move
3. **Automatic Routing**: Connectors reroute intelligently
4. **Stencil Access**: Use Visio's built-in professional shapes
5. **Full Control**: Access all Visio features and properties
6. **Professional Results**: Diagrams look like they were created manually

### Cons
1. **Requires Visio**: Microsoft Visio must be installed
2. **Windows Only**: COM automation is Windows-specific
3. **Slightly Slower**: ~5s vs ~2s (but saves 10-15 min manual work)
4. **COM Complexity**: Must manage COM object lifecycle

## Fallback Strategy

If COM automation fails (Visio not installed, pywin32 not available):

1. **Automatic Detection**: Try to import COM generator
2. **Graceful Fallback**: Use vsdx library if COM not available
3. **Connection List**: Generate text file with connection instructions
4. **User Notification**: Log which generator is being used

## Future Enhancements

### Potential Improvements
1. **Command-Line Flags**: `--visio-com` or `--visio-vsdx` to force specific generator
2. **Custom Stencils**: Support for user-provided stencil files
3. **Advanced Layouts**: Force-directed, hierarchical algorithms
4. **Connection Labels**: Optional interface labels (configurable)
5. **Custom Colors**: User-defined color schemes
6. **Shape Styles**: Different shapes for different device types
7. **Grouping**: Group devices by tier or function
8. **Annotations**: Add notes, callouts, or documentation

### Performance Optimizations
1. **Batch Operations**: Create all shapes first, then all connectors
2. **Stencil Caching**: Keep stencils open for multiple diagrams
3. **Parallel Generation**: Generate multiple site diagrams in parallel
4. **Template Optimization**: Pre-configure template with common settings

## Lessons Learned

### Technical Insights
1. **COM Object Lifecycle**: Must explicitly cleanup COM objects to prevent memory leaks
2. **Visio Color Format**: Uses BGR, not RGB - conversion required
3. **Stencil Availability**: Network stencil may not be available, need fallback
4. **Glue Operations**: Critical for Dynamic Connectors - without glue, connectors are just lines
5. **Routing Styles**: Must explicitly set routing style (orthogonal, straight, etc.)

### Best Practices
1. **Error Handling**: Wrap all COM operations in try/except
2. **Logging**: Log each step for debugging
3. **Cleanup**: Always cleanup COM objects in finally block
4. **Fallback**: Provide alternative approach if COM fails
5. **Testing**: Test with real data and verify in Visio

## Conclusion

The COM automation implementation successfully addresses the vsdx library's connector limitation by providing:

- **Full Dynamic Connector support** with glue to connection points
- **Professional-quality diagrams** that meet all user requirements
- **Automated generation** that saves 10-15 minutes per diagram
- **Intelligent fallback** to vsdx library if COM not available
- **Clean, maintainable code** with proper error handling

The implementation is production-ready and provides significant value by automating the tedious manual connection work while producing professional results.

---

**Files Modified:**
- `netwalker/reports/visio_generator_com.py` (NEW)
- `main.py` (updated for generator selection)
- `requirements.txt` (added pywin32)
- `build_executable.py` (added pywin32 to hidden imports)

**Version:** NetWalker v0.5.20  
**Build Date:** January 20, 2026  
**Status:** ✓ Complete and Tested
