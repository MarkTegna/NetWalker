# Visio Connector Limitation and Solution

## Problem

The Python `vsdx` library has **limited support for creating connectors programmatically**. While it can read and modify existing Visio files, it cannot create Dynamic Connectors with glue to connection points.

### Error Messages (v0.5.17-0.5.18)
```
WARNING - Connector creation not supported by vsdx library version
```

## Root Cause

The `vsdx` library is designed primarily for:
- Reading existing Visio files
- Modifying shape properties (text, position, color)
- Copying existing shapes
- **NOT** for creating connectors from scratch

## Solutions Evaluated

### 1. ❌ vsdx Library add_connector() Method
**Status:** Not available in vsdx library

### 2. ❌ Copy Connector Shapes from Template
**Status:** Attempted but vsdx doesn't support connector shape manipulation

### 3. ✅ Generate Connection List File (Implemented in v0.5.19)
**Status:** Working solution - generates text file with connection instructions

### 4. ⚠️ Use pywin32 with COM Automation
**Status:** Requires Microsoft Visio installed on the machine
**Pros:** Full Visio API access, can create proper Dynamic Connectors
**Cons:** Requires Visio license, Windows-only, not standalone

### 5. ⚠️ Use Aspose.Diagram Library
**Status:** Commercial library ($$$)
**Pros:** Works without Visio, full connector support
**Cons:** Expensive licensing, adds dependency

## Implemented Solution (v0.5.19)

### What NetWalker Now Does:

1. **Creates Visio Diagram** with:
   - ✅ Device shapes positioned hierarchically
   - ✅ Device names only (no extra text)
   - ✅ No title, no legend
   - ✅ Proper colors by device type
   - ✅ Correct spacing and layout

2. **Generates Connection List File** with:
   - Complete list of all connections
   - Source and destination devices
   - Interface names for each connection
   - Step-by-step instructions for manual connection

### Example Output

**Visio Diagram:** `Topology_BORO_20260120-22-16.vsdx`
- Contains all device shapes positioned correctly
- Ready for manual connection

**Connection List:** `Connections_BORO_20260120-22-16.txt`
```
================================================================================
NetWalker Connection List - BORO
Generated: 2026-01-20 22:16:43
================================================================================

INSTRUCTIONS:
1. Open the corresponding Visio diagram
2. Select the Connector tool (Ctrl+3)
3. For each connection below:
   a. Click on the source device shape
   b. Drag to the destination device shape
   c. Release to create the connection
4. Use the interface names to verify correct connections

================================================================================
CONNECTIONS (15 total)
================================================================================

1. BORO-CORE-A (GigabitEthernet1/0/1) <-> BORO-DIST-A (GigabitEthernet1/0/24)
2. BORO-CORE-A (GigabitEthernet1/0/2) <-> BORO-DIST-B (GigabitEthernet1/0/24)
3. BORO-DIST-A (GigabitEthernet1/0/1) <-> BORO-IDF-01 (GigabitEthernet1/0/24)
...
```

## Usage (v0.5.19)

### Generate Diagram with Connection List

```bash
cd D:\MJODev\NetWalker\dist\NetWalker_v0.5.19
.\netwalker.exe --visio --visio-site BORO
```

### Output Files

1. **Topology_BORO_YYYYMMDD-HH-MM.vsdx** - Visio diagram with shapes
2. **Connections_BORO_YYYYMMDD-HH-MM.txt** - Connection list for manual addition

### Manual Connection Steps

1. Open the `.vsdx` file in Microsoft Visio
2. Open the `.txt` file in a text editor (side-by-side)
3. Press `Ctrl+3` to select the Connector tool
4. For each connection in the list:
   - Click on the source device shape
   - Drag to the destination device shape
   - Release to create the connection
5. Visio will automatically:
   - Glue connectors to connection points
   - Route connectors orthogonally
   - Apply Dynamic Connector behavior

## Log Messages (v0.5.19)

### Before (v0.5.17-0.5.18)
```
WARNING - Connector creation not supported by vsdx library version (repeated 15x)
INFO - Created 15 connection lines
```

### After (v0.5.19)
```
INFO - Created 14 device shapes
WARNING - vsdx library limitation: Connectors cannot be created programmatically
WARNING - Diagram will show devices positioned correctly, but connections must be added manually in Visio
INFO - Connection data available in database - 15 connections found
INFO - Logged 15 connections (manual connection required in Visio)
INFO - Connection list saved: visio_diagrams\Connections_BORO_20260120-22-16.txt
INFO - Visio diagram saved: visio_diagrams\Topology_BORO_20260120-22-16.vsdx
```

## Future Enhancements

### Option 1: Add pywin32 COM Support (Requires Visio)

```python
# Pseudo-code for COM automation
import win32com.client

visio = win32com.client.Dispatch("Visio.Application")
doc = visio.Documents.Open("diagram.vsdx")
page = doc.Pages[1]

# Create connector
connector = page.Drop(visio.ConnectorToolDataObject, 0, 0)
connector.CellsU("BeginX").GlueTo(source_shape.CellsU("PinX"))
connector.CellsU("EndX").GlueTo(dest_shape.CellsU("PinX"))
```

**Pros:** Full Visio API, proper Dynamic Connectors
**Cons:** Requires Visio installed, not standalone

### Option 2: Use Aspose.Diagram (Commercial)

```python
# Pseudo-code for Aspose.Diagram
from aspose.diagram import Diagram

diagram = Diagram("template.vsdx")
page = diagram.pages[0]

# Create connector
connector_id = page.connect_shapes_via_connector(
    source_shape.id, "Bottom",
    dest_shape.id, "Top",
    connector_master_id
)
```

**Pros:** Works without Visio, full connector support
**Cons:** Commercial license required ($$$)

### Option 3: Export to Different Format

Generate diagrams in formats that support programmatic connections:
- **GraphViz DOT** - Text-based graph description
- **Mermaid** - Markdown-based diagrams
- **Draw.io XML** - Open-source diagramming

## Recommendation

**Current Solution (v0.5.19) is the best balance:**
- ✅ Works standalone (no Visio required for generation)
- ✅ No additional licensing costs
- ✅ Provides all connection data
- ✅ Clear instructions for manual connection
- ✅ Fast generation (seconds)
- ⚠️ Requires manual connection step in Visio

**For fully automated connectors:**
- Use pywin32 COM if Visio is available
- Use Aspose.Diagram if budget allows
- Consider alternative diagram formats (GraphViz, Mermaid)

## Technical Details

### vsdx Library Limitations

The vsdx library (v0.5.21) does not provide:
- `page.add_connector()` method
- Connector shape creation
- Connection point manipulation
- Glue operations
- Dynamic routing configuration

### What vsdx CAN Do

- Read existing Visio files
- Modify shape properties (text, position, size, color)
- Copy existing shapes
- Access shape data
- Save modified files

### What vsdx CANNOT Do

- Create connectors from scratch
- Glue connectors to shapes
- Configure connector routing
- Add connection points
- Manipulate connector geometry

## Conclusion

NetWalker v0.5.19 provides the best solution given the vsdx library limitations:
1. Generates professional Visio diagrams with correct layout
2. Stores all connection data in the database
3. Provides clear connection list for manual addition
4. Eliminates repetitive warning messages
5. Maintains standalone operation (no Visio required for generation)

The manual connection step is a reasonable trade-off for maintaining standalone operation and avoiding expensive commercial libraries.

---

**Version:** 0.5.19  
**Date:** January 20, 2026  
**Author:** Mark Oldham
