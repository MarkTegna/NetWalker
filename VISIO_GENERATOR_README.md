# NetWalker Visio Diagram Generator

**Author:** Mark Oldham  
**Version:** 0.5.12

## Overview

The NetWalker Visio Diagram Generator is a standalone program that creates network topology diagrams in Microsoft Visio format (.vsdx) using data from the NetWalker database. It does not require Microsoft Visio to be installed.

## Features

- **Database-Driven**: Reads device and connection data from NetWalker SQL Server database
- **No Visio Required**: Uses the `vsdx` Python library to generate .vsdx files programmatically
- **Hierarchical Layout**: Automatically organizes devices by type (core, distribution, access)
- **Color Coding**: Visual distinction between device types
- **Site-Based Diagrams**: Generate separate diagrams per site or a single diagram for all devices
- **Connection Labels**: Shows port information on connection lines
- **Professional Output**: Includes title, legend, and timestamp

## Installation

### Prerequisites

1. Python 3.8 or higher
2. Access to NetWalker SQL Server database
3. ODBC Driver 17 or 18 for SQL Server

### Install Dependencies

```powershell
pip install vsdx pyodbc
```

Or install from requirements.txt:
```powershell
pip install -r requirements.txt
```

## Configuration

The program uses the same `netwalker.ini` configuration file as the main NetWalker application.

### Database Configuration

```ini
[database]
server = eit-prisqldb01.tgna.tegna.com
port = 1433
database = NetWalker
username = NetWalker
password = FluffyBunnyHitbyaBus
# Or encrypted: password = ENC:Rmx1ZmZ5QnVubnlIaXRieWFCdXM=
```

If no configuration file is found, the program uses default values.

## Usage

### Basic Usage

Generate diagrams for all sites:
```powershell
python netwalker_visio.py
```

### Generate Diagram for Specific Site

```powershell
python netwalker_visio.py --site BORO
```

### Generate Single Diagram with All Devices

```powershell
python netwalker_visio.py --all-in-one
```

### Specify Custom Output Directory

```powershell
python netwalker_visio.py --output ./my_diagrams
```

### Use Custom Configuration File

```powershell
python netwalker_visio.py --config custom.ini
```

## Command Line Options

```
usage: netwalker_visio.py [-h] [--config CONFIG] [--output OUTPUT] 
                          [--site SITE] [--all-in-one]

optional arguments:
  -h, --help         Show help message and exit
  --config CONFIG    Configuration file path (default: netwalker.ini)
  --output OUTPUT    Output directory for Visio files (default: ./visio_diagrams)
  --site SITE        Generate diagram for specific site only (e.g., BORO)
  --all-in-one       Generate single diagram with all devices instead of per-site diagrams
```

## Output

### File Naming Convention

Generated Visio files follow this naming pattern:
```
Topology_{SiteName}_{YYYYMMDD-HH-MM}.vsdx
```

Examples:
- `Topology_BORO_20260119-14-30.vsdx`
- `Topology_Complete Network_20260119-14-35.vsdx`

### Diagram Features

Each generated diagram includes:

1. **Device Shapes**
   - Rectangular shapes representing network devices
   - Color-coded by device type:
     - Blue: Core devices (CORE in name)
     - Purple: Distribution devices (DIST, MDF in name)
     - Orange: Access devices (IDF, ACCESS in name)
     - Red: Unknown/other devices
   - Shows device name, platform, and hardware model

2. **Connection Lines**
   - Lines connecting related devices
   - Labels showing port information (when available)

3. **Hierarchical Layout**
   - Core devices at top
   - Distribution devices in middle
   - Access devices at bottom
   - Automatic spacing and positioning

4. **Title and Legend**
   - Diagram title with site name
   - Generation timestamp
   - Color-coded legend explaining device types

## Database Schema Requirements

The program expects the following tables in the NetWalker database:

### devices Table
```sql
- device_name (NVARCHAR)
- platform (NVARCHAR)
- hardware_model (NVARCHAR)
- serial_number (NVARCHAR)
- status (NVARCHAR) -- 'active' or 'purge'
```

### Connections/Neighbors Table (Optional)
If you have a connections or neighbors table, update the `get_device_connections()` method in `netwalker_visio.py` to query it properly.

## Site Detection

The program automatically groups devices by site based on hostname prefixes:
- Extracts first 4 characters of hostname as site code
- Example: `BORO-CORE-A` → Site code: `BORO`

To customize site detection logic, modify the `get_devices_by_site()` method.

## Troubleshooting

### Database Connection Failed

**Error:** "Database connection failed"

**Solutions:**
1. Verify you're on the network with access to the SQL Server
2. Check ODBC driver is installed: `odbcad32.exe`
3. Verify credentials in `netwalker.ini`
4. Test connection with SQL Server Management Studio

### ODBC Driver Not Found

**Error:** "Data source name not found"

**Solution:** Install ODBC Driver 17 or 18 for SQL Server from:
https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

### No Devices Found

**Error:** "Retrieved 0 active devices from database"

**Solutions:**
1. Verify devices exist in database with `status = 'active'`
2. Check database name is correct in configuration
3. Verify user has SELECT permissions on devices table

### vsdx Library Errors

**Error:** "ModuleNotFoundError: No module named 'vsdx'"

**Solution:**
```powershell
pip install vsdx
```

### Empty Diagrams

**Issue:** Diagram is generated but shows no connections

**Solution:** The `get_device_connections()` method needs to be updated to match your database schema. Edit the SQL query in `netwalker_visio.py` to properly retrieve connection data.

## Customization

### Modify Device Colors

Edit the color constants in `netwalker/reports/visio_generator.py`:

```python
COLOR_CORE = "#2E86AB"          # Blue
COLOR_DISTRIBUTION = "#A23B72"  # Purple
COLOR_ACCESS = "#F18F01"        # Orange
COLOR_UNKNOWN = "#C73E1D"       # Red
```

### Modify Layout Spacing

Edit the spacing constants in `netwalker/reports/visio_generator.py`:

```python
DEVICE_WIDTH = 2.0
DEVICE_HEIGHT = 1.0
HORIZONTAL_SPACING = 3.0
VERTICAL_SPACING = 2.0
```

### Modify Site Detection Logic

Edit the `get_devices_by_site()` method in `netwalker_visio.py` to match your naming convention.

## Examples

### Example 1: Generate All Site Diagrams

```powershell
PS> python netwalker_visio.py
======================================================================
NetWalker Visio Diagram Generator v0.5.12
Author: Mark Oldham
======================================================================

2026-01-19 14:30:15 - INFO - Loading configuration...
2026-01-19 14:30:15 - INFO - Connecting to NetWalker database...
2026-01-19 14:30:15 - INFO - Connected to database: eit-prisqldb01.tgna.tegna.com/NetWalker
2026-01-19 14:30:15 - INFO - Initializing Visio generator (output: ./visio_diagrams)...
2026-01-19 14:30:15 - INFO - Generating diagrams for all sites...
2026-01-19 14:30:15 - INFO - Retrieved 45 active devices from database
2026-01-19 14:30:15 - INFO - Grouped devices into 5 sites
2026-01-19 14:30:16 - INFO - Generating Visio topology diagram for BORO
2026-01-19 14:30:17 - INFO - Visio diagram saved: ./visio_diagrams/Topology_BORO_20260119-14-30.vsdx
...

[OK] Generated 5 diagram(s):
  - ./visio_diagrams/Topology_BORO_20260119-14-30.vsdx
  - ./visio_diagrams/Topology_KENS_20260119-14-30.vsdx
  - ./visio_diagrams/Topology_WLTX_20260119-14-30.vsdx
  - ./visio_diagrams/Topology_WPMT_20260119-14-30.vsdx
  - ./visio_diagrams/Topology_WTSP_20260119-14-30.vsdx

Visio diagram generation complete!
```

### Example 2: Generate Single Site Diagram

```powershell
PS> python netwalker_visio.py --site BORO --output ./boro_diagram

[OK] Generated diagram: ./boro_diagram/Topology_BORO_20260119-14-35.vsdx

Visio diagram generation complete!
```

### Example 3: Generate Complete Network Diagram

```powershell
PS> python netwalker_visio.py --all-in-one

[OK] Generated diagram: ./visio_diagrams/Topology_Complete Network_20260119-14-40.vsdx

Visio diagram generation complete!
```

## Integration with NetWalker

This is a standalone program that can be run independently of the main NetWalker discovery tool. It reads from the same database that NetWalker populates during discovery.

**Typical Workflow:**
1. Run NetWalker discovery to populate database
2. Run Visio generator to create diagrams from database data
3. Regenerate diagrams anytime without running new discovery

## Future Enhancements

Potential features for future versions:
- Interactive diagram generation (select specific devices)
- Custom device grouping (by platform, location, etc.)
- Export to other formats (PNG, PDF, SVG)
- Comparison diagrams (show changes over time)
- Integration with NetWalker web interface

## Support

For questions or issues:
- Author: Mark Oldham
- Repository: https://github.com/MarkTegna/NetWalker

## Version History

- **v0.5.12 (2026-01-19)**: Initial release
  - Standalone Visio diagram generator
  - Database-driven topology diagrams
  - Site-based and all-in-one diagram modes
  - Hierarchical layout with color coding
  - No Microsoft Visio installation required
