# NetWalker v0.5.20 Release Notes

**Release Date:** January 20, 2026  
**Author:** Mark Oldham

## Major Enhancement: COM-Based Visio Generator with Full Dynamic Connector Support

### Overview
This release introduces a complete COM automation-based Visio diagram generator that creates professional network topology diagrams with **full Dynamic Connector support**, including glue to connection points. This replaces the previous vsdx library approach which had limited connector capabilities.

### Key Features

#### 1. Full Dynamic Connector Support
- **Dynamic Connectors with Glue**: Connectors are properly glued to device shapes at connection points
- **Automatic Routing**: Connectors automatically reroute when shapes are moved
- **Orthogonal Routing**: Right-angle connector routing for professional appearance
- **No Manual Connection Required**: All connections are created automatically from database

#### 2. COM Automation Implementation
- Uses `pywin32` library for Microsoft Visio COM automation
- Requires Microsoft Visio installed on the machine
- Runs Visio in background (invisible mode)
- Automatic cleanup of COM objects after generation

#### 3. Intelligent Fallback
- Automatically detects if COM automation is available
- Falls back to vsdx library if pywin32 not available
- Logs which generator is being used (COM or vsdx)

#### 4. Professional Diagram Features
- **Hierarchical Layout**: Devices organized by tier (Core, Distribution, Access)
- **Color Coding**: Different colors for device types
  - Core: Blue (#2E86AB)
  - Distribution: Purple (#A23B72)
  - Access: Orange (#F18F01)
  - Unknown: Red (#C73E1D)
- **Clean Design**: Device name only on shapes (no clutter)
- **Connector Styling**: Gray (#666) connectors with 1.25 pt weight
- **No Labels**: Clean connectors without interface labels (per requirements)
- **No Titles/Legends**: Minimal design without unnecessary elements

#### 5. Database Integration
- Queries device connections from `device_neighbors` table
- Filters connections to only include devices in current diagram
- Supports site-specific diagrams and all-in-one diagrams

### Technical Implementation

#### New Files
- `netwalker/reports/visio_generator_com.py` - Complete COM automation implementation

#### Updated Files
- `main.py` - Intelligent generator selection (COM vs vsdx)
- `requirements.txt` - Added pywin32>=306
- `build_executable.py` - Added pywin32 to hidden imports

#### COM Generator Features
- **Shape Creation**: Uses Visio stencils (Network, Basic shapes)
- **Connector Creation**: Creates Dynamic Connectors from Connectors stencil
- **Glue Operations**: Properly glues connectors to shape connection points
- **Color Conversion**: Converts hex colors to Visio BGR format
- **Property Setting**: Sets line weight, routing style, colors
- **Error Handling**: Graceful fallback if stencils not available

### Performance
- **BORO Site (14 devices, 15 connections)**: ~5 seconds
- **All Sites (231 devices, 65 sites)**: Expected ~2-3 minutes
- Significant improvement over manual connection approach

### Usage

#### Generate Diagram for Specific Site
```bash
netwalker.exe --visio --visio-site BORO
```

#### Generate Diagrams for All Sites
```bash
netwalker.exe --visio
```

#### Generate Single All-in-One Diagram
```bash
netwalker.exe --visio --visio-all-in-one
```

#### Specify Output Directory
```bash
netwalker.exe --visio --visio-site BORO --visio-output ./my_diagrams
```

### Requirements
- **Microsoft Visio** must be installed on the machine
- **pywin32** library (included in distribution)
- **Database connection** with device and connection data

### Comparison: COM vs vsdx Library

| Feature | COM Automation | vsdx Library |
|---------|---------------|--------------|
| Dynamic Connectors | ✓ Full support | ✗ Not supported |
| Glue to Connection Points | ✓ Yes | ✗ No |
| Automatic Routing | ✓ Yes | ✗ No |
| Requires Visio Installed | ✓ Yes | ✗ No |
| Shape Creation | ✓ Full control | ✓ Limited |
| Stencil Support | ✓ Full access | ✗ Limited |
| Performance | Fast (~5s for 14 devices) | Fast (~2s for 14 devices) |

### Migration Notes
- Existing vsdx-based generator remains available as fallback
- No configuration changes required
- Automatic detection and selection of appropriate generator
- If Visio not installed, falls back to vsdx library with connection list file

### Known Limitations
- Requires Microsoft Visio installed (COM automation requirement)
- Runs Visio in background (may briefly show in task manager)
- COM objects must be properly cleaned up (handled automatically)

### Future Enhancements
- Add command-line flag to force specific generator (--visio-com, --visio-vsdx)
- Support for custom stencils and shapes
- Advanced layout algorithms (force-directed, hierarchical)
- Connection labels (optional, configurable)
- Custom color schemes

### Bug Fixes
None - this is a new feature release

### Breaking Changes
None - fully backward compatible

---

## Previous Features (Retained)

### CDP/LLDP Neighbor Discovery (v0.5.17)
- Database storage of neighbor relationships
- Bidirectional connection deduplication
- Interface name normalization
- Hostname resolution with FQDN handling

### Connected Ports Feature (v0.5.12)
- Shows which ports have active connections
- Helps identify unused ports for cleanup

### Database Integration (v0.5.1)
- SQL Server database storage
- Device inventory tracking
- Discovery history
- DNS validation

---

**For complete documentation, see:**
- `VISIO_GENERATOR_README.md` - Visio generation guide
- `VISIO_CONNECTOR_LIMITATION.md` - Technical details on connector approaches
- `CDP_LLDP_NEIGHBOR_IMPLEMENTATION_SUMMARY.md` - Neighbor discovery details
- `NETWALKER_COMPREHENSIVE_GUIDE.md` - Complete user guide

**GitHub Repository:** https://github.com/MarkTegna/NetWalker
