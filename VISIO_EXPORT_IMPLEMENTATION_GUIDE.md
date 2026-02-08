# Visio Export Implementation Guide

**Author:** Mark Oldham  
**Date:** January 27, 2026  
**Source Project:** NetWalker Network Discovery Tool  
**Purpose:** Complete guide for implementing Visio diagram generation in other projects

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Dependencies](#dependencies)
4. [Implementation Approaches](#implementation-approaches)
5. [File Structure](#file-structure)
6. [Core Components](#core-components)
7. [Code Examples](#code-examples)
8. [Configuration](#configuration)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)
12. [Lessons Learned](#lessons-learned)

---

## Overview

This guide documents the complete implementation of Visio diagram generation used in NetWalker, including:

- **Two implementation approaches**: vsdx library (standalone) and COM automation (full-featured)
- **Automatic fallback mechanism** between approaches
- **Hierarchical layout algorithms** for network topology
- **Dynamic connector creation** with proper glue to connection points
- **Device capability filtering** for diagram customization
- **Automatic scaling** for large diagrams
- **Connection list generation** for manual fallback

### Key Features Implemented

✅ Programmatic Visio file generation  
✅ Dynamic Connector creation with glue  
✅ Hierarchical device positioning  
✅ Color-coded device types  
✅ Orthogonal connector routing  
✅ Interface label abbreviation  
✅ Automatic diagram scaling  
✅ Device capability filtering  
✅ Fallback to vsdx library  
✅ Connection list generation  

---

## Architecture

### Dual-Generator Design


```
┌─────────────────────────────────────────────────────────────┐
│                    Main Application                          │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Try: Import VisioGeneratorCOM (pywin32)          │    │
│  │  Except: Import VisioGenerator (vsdx)             │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│              ┌───────────────────────┐                      │
│              │  Generator Selection  │                      │
│              └───────────────────────┘                      │
│                          │                                   │
│         ┌────────────────┴────────────────┐                │
│         ▼                                  ▼                │
│  ┌──────────────────┐           ┌──────────────────┐      │
│  │ VisioGeneratorCOM│           │ VisioGenerator   │      │
│  │  (Full Features) │           │  (Fallback)      │      │
│  │                  │           │                  │      │
│  │ • COM Automation │           │ • vsdx Library   │      │
│  │ • Dynamic Connec │           │ • Shape Creation │      │
│  │ • Glue Support   │           │ • No Connectors  │      │
│  │ • Full Visio API │           │ • Conn List Gen  │      │
│  └──────────────────┘           └──────────────────┘      │
│         │                                  │                │
│         └────────────────┬─────────────────┘                │
│                          ▼                                   │
│              ┌───────────────────────┐                      │
│              │  Generated .vsdx File │                      │
│              └───────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### Why Two Approaches?

**vsdx Library (Fallback)**
- ✅ No Visio installation required
- ✅ Standalone operation
- ✅ Cross-platform (Windows, Linux, Mac)
- ❌ Cannot create Dynamic Connectors
- ❌ Limited shape manipulation

**COM Automation (Primary)**
- ✅ Full Visio API access
- ✅ Dynamic Connectors with glue
- ✅ Professional results
- ❌ Requires Visio installed
- ❌ Windows-only
- ❌ Slower execution (~5s vs ~2s)

---

## Dependencies

### Required Python Packages

```python
# requirements.txt

# For vsdx library approach (fallback)
vsdx>=0.5.0

# For COM automation approach (primary)
pywin32>=306

# For database connectivity (if needed)
pyodbc>=5.0.0

# Standard libraries (included with Python)
# - pathlib
# - datetime
# - typing
# - logging
```

### System Requirements

**For vsdx Library:**
- Python 3.8+
- No additional software

**For COM Automation:**
- Python 3.8+
- Microsoft Visio 2016 or later
- Windows OS
- pywin32 library

### Installation Commands

```powershell
# Install all dependencies
pip install vsdx pywin32 pyodbc

# Or from requirements.txt
pip install -r requirements.txt
```

---

## Implementation Approaches

### Approach 1: vsdx Library (Standalone)

**Use When:**
- Visio is not installed
- Cross-platform support needed
- Standalone operation required
- Connectors can be added manually

**Limitations:**
- Cannot create Dynamic Connectors programmatically
- Limited shape property manipulation
- Must generate connection list for manual addition

**Example:**
```python
from vsdx import VisioFile
import shutil

# Copy template
shutil.copy2("template.vsdx", "output.vsdx")

# Open file
vis = VisioFile("output.vsdx")
page = vis.pages[0]

# Create shapes by copying template shape
template_shape = page.all_shapes[0]
new_shape = template_shape.copy(page)
new_shape.text = "Device Name"
new_shape.x = 5.0
new_shape.y = 3.0

# Save
vis.save_vsdx("output.vsdx")
```

### Approach 2: COM Automation (Full-Featured)

**Use When:**
- Visio is installed
- Full automation required
- Dynamic Connectors needed
- Professional results required

**Advantages:**
- Full Visio API access
- Dynamic Connectors with glue
- Automatic routing
- Complete shape control

**Example:**
```python
import win32com.client

# Initialize Visio
visio = win32com.client.Dispatch("Visio.Application")
visio.Visible = False

# Open template
doc = visio.Documents.Open("C:\\path\\to\\template.vsdx")
page = doc.Pages[1]

# Create shape
stencil = visio.Documents.OpenEx("BASIC_U.VSSX", 64)
master = stencil.Masters("Rectangle")
shape = page.Drop(master, 5.0, 3.0)
shape.Text = "Device Name"

# Create connector
conn_stencil = visio.Documents.OpenEx("CONNEC_U.VSSX", 64)
conn_master = conn_stencil.Masters("Dynamic connector")
connector = page.Drop(conn_master, 4.0, 4.0)

# Glue connector to shapes
connector.Cells("BeginX").GlueTo(shape1.Cells("PinX"))
connector.Cells("EndX").GlueTo(shape2.Cells("PinX"))

# Save and cleanup
doc.SaveAs("C:\\path\\to\\output.vsdx")
doc.Close()
visio.Quit()
```

---


## File Structure

### Recommended Project Layout

```
your_project/
├── requirements.txt
├── your_app.py
├── config.ini
├── TEMPLATE.vsdx                    # Visio template file
└── reports/                         # Report generation module
    ├── __init__.py
    ├── visio_generator.py           # vsdx library implementation
    ├── visio_generator_com.py       # COM automation implementation
    └── connection_list_generator.py # Helper for manual connections
```

### Template File Requirements

Your Visio template (`TEMPLATE.vsdx`) should contain:

1. **At least one page** with a background
2. **At least one shape** to use as a template for copying (vsdx approach)
3. **Proper page dimensions** (e.g., 11" x 8.5" landscape)
4. **No protection** on pages or document

**Creating a Template:**
1. Open Microsoft Visio
2. Create a new blank drawing
3. Set page size (File → Page Setup → Page Size)
4. Add one rectangle shape (for vsdx library to copy)
5. Save as `.vsdx` format
6. Place in project root directory

---

## Core Components

### Component 1: Generator Selection Logic

**File:** `your_app.py` or `main.py`

```python
import logging

logger = logging.getLogger(__name__)

# Try to import COM generator, fall back to vsdx if not available
try:
    from reports.visio_generator_com import VisioGeneratorCOM
    use_com = True
    logger.info("Using COM automation (requires Microsoft Visio)")
except ImportError:
    from reports.visio_generator import VisioGenerator
    use_com = False
    logger.info("Using vsdx library (limited connector support)")

# Initialize appropriate generator
if use_com:
    visio_gen = VisioGeneratorCOM(
        output_directory="./diagrams",
        database_manager=db_manager,  # Optional
        config=config                  # Optional
    )
else:
    visio_gen = VisioGenerator(
        output_directory="./diagrams",
        database_manager=db_manager   # Optional
    )

# Generate diagram
filepath = visio_gen.generate_topology_diagram(
    devices=device_list,
    connections=connection_list,
    site_name="My Network"
)
```

### Component 2: vsdx Library Generator

**File:** `reports/visio_generator.py`

**Key Methods:**

1. **`__init__(output_directory, database_manager=None)`**
   - Initialize generator
   - Create output directory
   - Check template exists

2. **`generate_topology_diagram(devices, connections, site_name)`**
   - Main entry point
   - Copy template to output location
   - Calculate device positions
   - Create device shapes
   - Log connections (cannot create)
   - Generate connection list file
   - Save diagram

3. **`_calculate_device_positions(devices, connections)`**
   - Categorize devices by type
   - Build connection map
   - Position devices hierarchically
   - Return position dictionary

4. **`_create_device_shape(page, device_name, platform, hardware_model, x, y)`**
   - Copy template shape
   - Set device name as text
   - Position shape
   - Set color based on device type
   - Return shape object

5. **`_get_connections_for_devices(devices)`**
   - Query database for connections
   - Filter to devices in current diagram
   - Return connection list

**Minimal Implementation:**

```python
"""Visio Generator using vsdx library"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from vsdx import VisioFile
import shutil

logger = logging.getLogger(__name__)

class VisioGenerator:
    """Generates Visio diagrams using vsdx library"""
    
    TEMPLATE_FILE = "TEMPLATE.vsdx"
    DEVICE_WIDTH = 2.0
    DEVICE_HEIGHT = 1.0
    HORIZONTAL_SPACING = 3.0
    VERTICAL_SPACING = 2.0
    
    COLOR_CORE = "#2E86AB"
    COLOR_DISTRIBUTION = "#A23B72"
    COLOR_ACCESS = "#F18F01"
    COLOR_UNKNOWN = "#C73E1D"
    
    def __init__(self, output_directory: str, database_manager=None):
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.database_manager = database_manager
        self.template_path = Path(self.TEMPLATE_FILE)
        
        if not self.template_path.exists():
            logger.error(f"Template not found: {self.TEMPLATE_FILE}")
    
    def generate_topology_diagram(
        self,
        devices: List[Dict],
        connections: List[Tuple[str, str, str, str]] = None,
        site_name: str = "Network"
    ) -> Optional[str]:
        """Generate Visio diagram"""
        try:
            logger.info(f"Generating diagram for {site_name}")
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d-%H-%M")
            filename = f"Topology_{site_name}_{timestamp}.vsdx"
            filepath = self.output_directory / filename
            
            # Copy template
            shutil.copy2(self.template_path, filepath)
            
            # Open file
            vis = VisioFile(str(filepath))
            page = vis.pages[0]
            page.name = f"{site_name} Topology"
            
            # Calculate positions
            positions = self._calculate_device_positions(devices, connections or [])
            
            # Create shapes
            device_shapes = {}
            for device in devices:
                device_name = device.get('device_name', 'Unknown')
                if device_name in positions:
                    x, y = positions[device_name]
                    shape = self._create_device_shape(
                        page, device_name,
                        device.get('platform', 'Unknown'),
                        device.get('hardware_model', ''),
                        x, y
                    )
                    if shape:
                        device_shapes[device_name] = shape
            
            logger.info(f"Created {len(device_shapes)} shapes")
            
            # Note: vsdx cannot create connectors
            if connections:
                logger.warning("vsdx library cannot create connectors")
                logger.info(f"{len(connections)} connections available")
            
            # Save
            vis.save_vsdx(str(filepath))
            logger.info(f"Saved: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate diagram: {e}")
            return None
    
    def _calculate_device_positions(
        self,
        devices: List[Dict],
        connections: List[Tuple[str, str, str, str]]
    ) -> Dict[str, Tuple[float, float]]:
        """Calculate device positions"""
        positions = {}
        
        # Simple layout: arrange in rows
        devices_per_row = 4
        x_start = 2.0
        y_start = 6.0
        
        for i, device in enumerate(devices):
            device_name = device.get('device_name', '')
            row = i // devices_per_row
            col = i % devices_per_row
            
            x = x_start + (col * self.HORIZONTAL_SPACING)
            y = y_start - (row * self.VERTICAL_SPACING)
            
            positions[device_name] = (x, y)
        
        return positions
    
    def _create_device_shape(
        self,
        page,
        device_name: str,
        platform: str,
        hardware_model: str,
        x: float,
        y: float
    ):
        """Create device shape"""
        try:
            if not page.all_shapes:
                logger.error("No template shapes available")
                return None
            
            # Copy template shape
            template_shape = page.all_shapes[0]
            shape = template_shape.copy(page)
            
            # Set properties
            shape.text = device_name
            shape.x = x
            shape.y = y
            shape.width = self.DEVICE_WIDTH
            shape.height = self.DEVICE_HEIGHT
            
            # Set color
            if 'CORE' in device_name.upper():
                color = self.COLOR_CORE
            elif 'DIST' in device_name.upper():
                color = self.COLOR_DISTRIBUTION
            elif 'ACCESS' in device_name.upper():
                color = self.COLOR_ACCESS
            else:
                color = self.COLOR_UNKNOWN
            
            try:
                shape.fill_color = color
            except AttributeError:
                pass
            
            return shape
            
        except Exception as e:
            logger.error(f"Failed to create shape: {e}")
            return None
```

---


### Component 3: COM Automation Generator

**File:** `reports/visio_generator_com.py`

**Key Methods:**

1. **`__init__(output_directory, database_manager=None, config=None)`**
   - Initialize generator
   - Load capability exclusion patterns from config
   - Check template exists

2. **`_initialize_visio()`**
   - Dispatch Visio COM application
   - Set invisible mode
   - Return success status

3. **`_cleanup_visio()`**
   - Close document
   - Quit Visio application
   - Release COM objects

4. **`generate_topology_diagram(devices, connections, site_name)`**
   - Initialize Visio COM
   - Open template
   - Create new page
   - Calculate positions with scaling
   - Create device shapes
   - Create Dynamic Connectors with glue
   - Save and cleanup

5. **`_create_device_shape_com(device_name, platform, x, y, stencil, scale_factor)`**
   - Drop shape from stencil master
   - Set device name
   - Position and size shape
   - Set fill color
   - Unlock shape
   - Return shape object

6. **`_create_connection_com(source_shape, dest_shape, source_port, dest_port, connection_index, scale_factor)`**
   - Open connectors stencil
   - Get Dynamic Connector master
   - Calculate connection points
   - Drop connector on page
   - **Glue connector to shapes** (critical!)
   - Set connector properties
   - Add interface labels
   - Return success status

7. **`_calculate_scale_factor(num_devices)`**
   - Calculate scale based on device count
   - Return scale factor (1.0 = normal, 0.5 = half)

8. **`_abbreviate_interface(interface_name)`**
   - Convert long interface names to abbreviations
   - Example: "TenGigabitEthernet1/0/1" → "Te1/0/1"

**Critical COM Operations:**

```python
# Initialize Visio
self.visio_app = win32com.client.Dispatch("Visio.Application")
self.visio_app.Visible = False

# Open template
self.doc = self.visio_app.Documents.Open(str(template_path.absolute()))

# Create page
self.page = self.doc.Pages.Add()
self.page.Name = "My Topology"

# Get stencil
stencil = self.visio_app.Documents.OpenEx("BASIC_U.VSSX", 64)
master = stencil.Masters("Rectangle")

# Drop shape
shape = self.page.Drop(master, x, y)
shape.Text = "Device Name"

# Set color (BGR format!)
color_bgr = (b << 16) | (g << 8) | r
shape.Cells("FillForegnd").Formula = str(color_bgr)

# Create connector
conn_stencil = self.visio_app.Documents.OpenEx("CONNEC_U.VSSX", 64)
conn_master = conn_stencil.Masters("Dynamic connector")
connector = self.page.Drop(conn_master, mid_x, mid_y)

# CRITICAL: Glue connector to shapes
source_id = source_shape.ID
dest_id = dest_shape.ID
connector.Cells("BeginX").Formula = f"Sheet.{source_id}!PinX"
connector.Cells("BeginY").Formula = f"Sheet.{source_id}!PinY"
connector.Cells("EndX").Formula = f"Sheet.{dest_id}!PinX"
connector.Cells("EndY").Formula = f"Sheet.{dest_id}!PinY"

# Set orthogonal routing
connector.Cells("ShapeRouteStyle").Formula = "16"

# Save
self.doc.SaveAs(str(output_path.absolute()))
self.doc.Close()
self.visio_app.Quit()
```

**Color Conversion (RGB to BGR):**

```python
def _rgb_to_visio_color(self, hex_color: str) -> int:
    """Convert #2E86AB to BGR integer"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (b << 16) | (g << 8) | r
```

### Component 4: Connection List Generator

**File:** `reports/connection_list_generator.py`

**Purpose:** Generate text file with connection instructions for manual addition in Visio (fallback for vsdx library)

```python
"""Connection List Generator"""
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

logger = logging.getLogger(__name__)

class ConnectionListGenerator:
    """Generates connection list files"""
    
    def __init__(self, output_directory: str):
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
    
    def generate_connection_list(
        self,
        connections: List[Tuple[str, str, str, str]],
        site_name: str = "Network"
    ) -> str:
        """Generate connection list file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d-%H-%M")
            filename = f"Connections_{site_name}_{timestamp}.txt"
            filepath = self.output_directory / filename
            
            with open(filepath, 'w') as f:
                f.write("=" * 80 + "\n")
                f.write(f"Connection List - {site_name}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                
                f.write("INSTRUCTIONS:\n")
                f.write("1. Open the Visio diagram\n")
                f.write("2. Select Connector tool (Ctrl+3)\n")
                f.write("3. For each connection:\n")
                f.write("   a. Click source device\n")
                f.write("   b. Drag to destination device\n")
                f.write("   c. Release to create connection\n\n")
                
                f.write("=" * 80 + "\n")
                f.write(f"CONNECTIONS ({len(connections)} total)\n")
                f.write("=" * 80 + "\n\n")
                
                for i, (src_dev, src_port, dst_dev, dst_port) in enumerate(connections, 1):
                    f.write(f"{i}. {src_dev} ({src_port}) <-> {dst_dev} ({dst_port})\n")
                
                f.write("\n" + "=" * 80 + "\n")
            
            logger.info(f"Connection list saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate connection list: {e}")
            return None
```

---

## Configuration

### Configuration File Format

**File:** `config.ini`

```ini
[visio]
# Device capability exclusion patterns (comma-separated)
# Devices with these capabilities will be excluded from diagrams
exclude_devices = phone,camera,printer

# Template file path
template = TEMPLATE.vsdx

# Output directory
output_directory = ./diagrams

# Color scheme (hex colors)
color_core = #2E86AB
color_distribution = #A23B72
color_access = #F18F01
color_unknown = #C73E1D
color_connector = #666666

# Layout settings
device_width = 2.0
device_height = 1.0
horizontal_spacing = 3.0
vertical_spacing = 2.0

# Scaling settings
scale_threshold = 20
min_scale_factor = 0.4

[database]
# Database connection (if needed)
server = your-server.com
port = 1433
database = YourDatabase
username = YourUser
password = YourPassword
```

### Loading Configuration

```python
import configparser
from pathlib import Path

def load_config(config_file: str = "config.ini") -> dict:
    """Load configuration from INI file"""
    config = configparser.ConfigParser()
    
    # Defaults
    defaults = {
        'visio': {
            'exclude_devices': '',
            'template': 'TEMPLATE.vsdx',
            'output_directory': './diagrams',
            'color_core': '#2E86AB',
            'color_distribution': '#A23B72',
            'color_access': '#F18F01',
            'color_unknown': '#C73E1D',
            'color_connector': '#666666',
            'device_width': '2.0',
            'device_height': '1.0',
            'horizontal_spacing': '3.0',
            'vertical_spacing': '2.0',
            'scale_threshold': '20',
            'min_scale_factor': '0.4'
        }
    }
    
    # Load from file if exists
    if Path(config_file).exists():
        config.read(config_file)
    
    # Merge with defaults
    result = {}
    for section in defaults:
        result[section] = {}
        for key, default_value in defaults[section].items():
            result[section][key] = config.get(section, key, fallback=default_value)
    
    return result
```

---


## Code Examples

### Example 1: Basic Usage

```python
"""Basic Visio diagram generation"""
import logging
from reports.visio_generator import VisioGenerator

# Setup logging
logging.basicConfig(level=logging.INFO)

# Sample data
devices = [
    {'device_name': 'CORE-SW-01', 'platform': 'IOS-XE', 'hardware_model': 'C9300'},
    {'device_name': 'DIST-SW-01', 'platform': 'IOS', 'hardware_model': 'C3850'},
    {'device_name': 'ACCESS-SW-01', 'platform': 'IOS', 'hardware_model': 'C2960'},
]

connections = [
    ('CORE-SW-01', 'Gi1/0/1', 'DIST-SW-01', 'Gi1/0/24'),
    ('DIST-SW-01', 'Gi1/0/1', 'ACCESS-SW-01', 'Gi1/0/24'),
]

# Generate diagram
generator = VisioGenerator(output_directory="./diagrams")
filepath = generator.generate_topology_diagram(
    devices=devices,
    connections=connections,
    site_name="Main Office"
)

print(f"Diagram saved: {filepath}")
```

### Example 2: With Database Integration

```python
"""Visio generation with database"""
import logging
from reports.visio_generator_com import VisioGeneratorCOM
from database.database_manager import DatabaseManager

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to database
db_manager = DatabaseManager(config)
if not db_manager.connect():
    logger.error("Database connection failed")
    exit(1)

# Get devices from database
devices = db_manager.get_active_devices()
logger.info(f"Retrieved {len(devices)} devices")

# Initialize generator with database manager
# (will automatically query connections)
generator = VisioGeneratorCOM(
    output_directory="./diagrams",
    database_manager=db_manager
)

# Generate diagram (connections queried automatically)
filepath = generator.generate_topology_diagram(
    devices=devices,
    connections=None,  # Will be queried from database
    site_name="Production Network"
)

print(f"Diagram saved: {filepath}")

# Cleanup
db_manager.disconnect()
```

### Example 3: Multiple Site Diagrams

```python
"""Generate diagrams for multiple sites"""
import logging
from reports.visio_generator_com import VisioGeneratorCOM

logging.basicConfig(level=logging.INFO)

# Group devices by site
devices_by_site = {
    'SITE-A': [
        {'device_name': 'SITE-A-CORE-01', 'platform': 'IOS-XE', 'hardware_model': 'C9300'},
        {'device_name': 'SITE-A-ACCESS-01', 'platform': 'IOS', 'hardware_model': 'C2960'},
    ],
    'SITE-B': [
        {'device_name': 'SITE-B-CORE-01', 'platform': 'IOS-XE', 'hardware_model': 'C9300'},
        {'device_name': 'SITE-B-ACCESS-01', 'platform': 'IOS', 'hardware_model': 'C2960'},
    ],
}

connections_by_site = {
    'SITE-A': [
        ('SITE-A-CORE-01', 'Gi1/0/1', 'SITE-A-ACCESS-01', 'Gi1/0/24'),
    ],
    'SITE-B': [
        ('SITE-B-CORE-01', 'Gi1/0/1', 'SITE-B-ACCESS-01', 'Gi1/0/24'),
    ],
}

# Generate diagrams
generator = VisioGeneratorCOM(output_directory="./diagrams")

for site_name, devices in devices_by_site.items():
    connections = connections_by_site.get(site_name, [])
    
    filepath = generator.generate_topology_diagram(
        devices=devices,
        connections=connections,
        site_name=site_name
    )
    
    print(f"Generated: {filepath}")
```

### Example 4: With Configuration

```python
"""Visio generation with configuration file"""
import logging
import configparser
from pathlib import Path
from reports.visio_generator_com import VisioGeneratorCOM

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Setup logging
logging.basicConfig(level=logging.INFO)

# Get devices (from your data source)
devices = get_devices_from_somewhere()
connections = get_connections_from_somewhere()

# Initialize generator with config
generator = VisioGeneratorCOM(
    output_directory=config.get('visio', 'output_directory', fallback='./diagrams'),
    database_manager=None,
    config=config
)

# Generate diagram
filepath = generator.generate_topology_diagram(
    devices=devices,
    connections=connections,
    site_name="My Network"
)

print(f"Diagram saved: {filepath}")
```

### Example 5: Hierarchical Layout Algorithm

```python
"""Advanced hierarchical layout"""
from typing import Dict, List, Tuple, Set

def calculate_hierarchical_positions(
    devices: List[Dict],
    connections: List[Tuple[str, str, str, str]],
    page_width: float = 11.0,
    page_height: float = 8.5
) -> Dict[str, Tuple[float, float]]:
    """
    Calculate device positions using BFS hierarchy
    
    Args:
        devices: List of device dictionaries
        connections: List of connection tuples
        page_width: Page width in inches
        page_height: Page height in inches
        
    Returns:
        Dictionary mapping device names to (x, y) positions
    """
    # Build connection map
    connection_map = {}
    connection_counts = {}
    
    for source, _, dest, _ in connections:
        if source not in connection_map:
            connection_map[source] = set()
            connection_counts[source] = 0
        if dest not in connection_map:
            connection_map[dest] = set()
            connection_counts[dest] = 0
        
        connection_map[source].add(dest)
        connection_map[dest].add(source)
        connection_counts[source] += 1
        connection_counts[dest] += 1
    
    # Find root device (most connections)
    device_names = [d.get('device_name', '') for d in devices]
    root_device = max(device_names, key=lambda d: connection_counts.get(d, 0))
    
    # Build hierarchy using BFS
    levels = {}
    visited = set()
    queue = [(root_device, 0)]
    visited.add(root_device)
    
    while queue:
        device, level = queue.pop(0)
        
        if level not in levels:
            levels[level] = []
        levels[level].append(device)
        
        # Add neighbors to next level
        neighbors = connection_map.get(device, set())
        for neighbor in sorted(neighbors):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, level + 1))
    
    # Calculate positions
    positions = {}
    margin = 0.75
    usable_width = page_width - (2 * margin)
    usable_height = page_height - (2 * margin)
    
    max_devices_per_row = 4
    root_y = page_height - margin
    
    for level_num, level_devices in sorted(levels.items()):
        if level_num == 0:
            # Root device centered at top
            x = page_width / 2
            y = root_y
            positions[level_devices[0]] = (x, y)
        else:
            # Distribute devices in rows
            num_devices = len(level_devices)
            num_rows = (num_devices + max_devices_per_row - 1) // max_devices_per_row
            
            for row_idx in range(num_rows):
                start_idx = row_idx * max_devices_per_row
                end_idx = min(start_idx + max_devices_per_row, num_devices)
                row_devices = level_devices[start_idx:end_idx]
                
                # Calculate Y position
                row_y = root_y - (level_num * 2.0) - (row_idx * 0.5)
                
                # Calculate X positions
                if len(row_devices) == 1:
                    x_positions = [page_width / 2]
                else:
                    spacing = usable_width / (len(row_devices) - 1)
                    start_x = margin
                    x_positions = [start_x + (i * spacing) for i in range(len(row_devices))]
                
                # Assign positions
                for i, device_name in enumerate(row_devices):
                    positions[device_name] = (x_positions[i], row_y)
    
    return positions
```

---

## Testing

### Unit Tests

**File:** `tests/test_visio_generator.py`

```python
"""Unit tests for Visio generator"""
import unittest
from pathlib import Path
from reports.visio_generator import VisioGenerator

class TestVisioGenerator(unittest.TestCase):
    
    def setUp(self):
        """Setup test fixtures"""
        self.output_dir = Path("./test_output")
        self.output_dir.mkdir(exist_ok=True)
        self.generator = VisioGenerator(str(self.output_dir))
    
    def tearDown(self):
        """Cleanup test files"""
        import shutil
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
    
    def test_generator_initialization(self):
        """Test generator initializes correctly"""
        self.assertIsNotNone(self.generator)
        self.assertTrue(self.output_dir.exists())
    
    def test_calculate_positions(self):
        """Test position calculation"""
        devices = [
            {'device_name': 'CORE-01'},
            {'device_name': 'ACCESS-01'},
        ]
        connections = [
            ('CORE-01', 'Gi1/0/1', 'ACCESS-01', 'Gi1/0/24'),
        ]
        
        positions = self.generator._calculate_device_positions(devices, connections)
        
        self.assertEqual(len(positions), 2)
        self.assertIn('CORE-01', positions)
        self.assertIn('ACCESS-01', positions)
        
        # Core should be higher (larger Y) than access
        core_y = positions['CORE-01'][1]
        access_y = positions['ACCESS-01'][1]
        self.assertGreater(core_y, access_y)
    
    def test_generate_diagram(self):
        """Test diagram generation"""
        devices = [
            {'device_name': 'TEST-DEVICE', 'platform': 'IOS', 'hardware_model': 'C2960'},
        ]
        
        filepath = self.generator.generate_topology_diagram(
            devices=devices,
            connections=[],
            site_name="Test"
        )
        
        self.assertIsNotNone(filepath)
        self.assertTrue(Path(filepath).exists())
        self.assertTrue(filepath.endswith('.vsdx'))

if __name__ == '__main__':
    unittest.main()
```

### Integration Tests

```python
"""Integration tests with real Visio"""
import unittest
from pathlib import Path
from reports.visio_generator_com import VisioGeneratorCOM

class TestVisioGeneratorCOM(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Check if Visio is available"""
        try:
            import win32com.client
            visio = win32com.client.Dispatch("Visio.Application")
            visio.Quit()
            cls.visio_available = True
        except:
            cls.visio_available = False
    
    def setUp(self):
        """Setup test fixtures"""
        if not self.visio_available:
            self.skipTest("Microsoft Visio not available")
        
        self.output_dir = Path("./test_output")
        self.output_dir.mkdir(exist_ok=True)
        self.generator = VisioGeneratorCOM(str(self.output_dir))
    
    def test_com_initialization(self):
        """Test COM initialization"""
        result = self.generator._initialize_visio()
        self.assertTrue(result)
        self.generator._cleanup_visio()
    
    def test_generate_with_connectors(self):
        """Test diagram generation with connectors"""
        devices = [
            {'device_name': 'CORE-01', 'platform': 'IOS-XE', 'hardware_model': 'C9300'},
            {'device_name': 'ACCESS-01', 'platform': 'IOS', 'hardware_model': 'C2960'},
        ]
        connections = [
            ('CORE-01', 'Gi1/0/1', 'ACCESS-01', 'Gi1/0/24'),
        ]
        
        filepath = self.generator.generate_topology_diagram(
            devices=devices,
            connections=connections,
            site_name="Test"
        )
        
        self.assertIsNotNone(filepath)
        self.assertTrue(Path(filepath).exists())

if __name__ == '__main__':
    unittest.main()
```

---


## Troubleshooting

### Common Issues and Solutions

#### Issue 1: "Template file not found"

**Error:**
```
ERROR - Template file not found: TEMPLATE.vsdx
```

**Solution:**
1. Create a Visio template file named `TEMPLATE.vsdx`
2. Place it in the project root directory
3. Or update `TEMPLATE_FILE` constant to point to correct location

**Creating Template:**
```python
# In Visio:
# 1. File → New → Blank Drawing
# 2. Add one rectangle shape
# 3. File → Save As → TEMPLATE.vsdx
```

#### Issue 2: "ModuleNotFoundError: No module named 'win32com'"

**Error:**
```
ModuleNotFoundError: No module named 'win32com'
```

**Solution:**
```powershell
pip install pywin32

# If that fails, try:
pip install --upgrade pywin32

# After installation, run:
python Scripts/pywin32_postinstall.py -install
```

#### Issue 3: COM Automation Fails

**Error:**
```
ERROR - Failed to initialize Visio COM
```

**Possible Causes:**
1. Microsoft Visio not installed
2. Visio not properly registered
3. Permission issues

**Solutions:**
```powershell
# Check if Visio is installed
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | 
    Where-Object {$_.DisplayName -like "*Visio*"}

# Re-register Visio (run as Administrator)
cd "C:\Program Files\Microsoft Office\root\Office16"
.\VISIO.EXE /regserver

# Or use vsdx library as fallback (automatic)
```

#### Issue 4: "No shapes available in template"

**Error:**
```
ERROR - No shapes available in template to copy
```

**Solution:**
1. Open `TEMPLATE.vsdx` in Visio
2. Add at least one shape (rectangle, circle, etc.)
3. Save the template
4. Ensure shape is on the first page

#### Issue 5: Connectors Not Created (vsdx)

**Expected Behavior:**
```
WARNING - vsdx library cannot create connectors programmatically
INFO - Connection list saved: Connections_Site_20260127.txt
```

**Solution:**
This is expected behavior for vsdx library. Two options:

1. **Use COM automation** (requires Visio):
   ```python
   from reports.visio_generator_com import VisioGeneratorCOM
   generator = VisioGeneratorCOM(output_directory)
   ```

2. **Manual connection** using generated connection list:
   - Open `.vsdx` file in Visio
   - Open `.txt` connection list file
   - Press `Ctrl+3` for Connector tool
   - Follow instructions in connection list

#### Issue 6: Colors Not Applied

**Issue:** Shapes appear with default colors

**Solution (vsdx):**
```python
# vsdx library has limited color support
# Try setting fill_color:
try:
    shape.fill_color = "#2E86AB"
except AttributeError:
    # Not supported in this vsdx version
    pass
```

**Solution (COM):**
```python
# Use BGR format, not RGB
def rgb_to_bgr(hex_color):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (b << 16) | (g << 8) | r

color = rgb_to_bgr("#2E86AB")
shape.Cells("FillForegnd").Formula = str(color)
```

#### Issue 7: Shapes Overlap

**Issue:** Devices positioned on top of each other

**Solution:**
Adjust spacing constants:
```python
HORIZONTAL_SPACING = 3.0  # Increase for more horizontal space
VERTICAL_SPACING = 2.0    # Increase for more vertical space
```

Or implement better layout algorithm (see hierarchical layout example).

#### Issue 8: Diagram Too Large

**Issue:** Devices don't fit on page

**Solution:**
Implement automatic scaling:
```python
def _calculate_scale_factor(self, num_devices: int) -> float:
    """Scale shapes based on device count"""
    if num_devices <= 20:
        return 1.0
    
    # Reduce size for large diagrams
    scale_reduction = (num_devices - 20) / 20 * 0.6
    return max(0.4, 1.0 - scale_reduction)

# Apply to shape dimensions
scaled_width = DEVICE_WIDTH * scale_factor
scaled_height = DEVICE_HEIGHT * scale_factor
```

#### Issue 9: Permission Denied Saving File

**Error:**
```
PermissionError: [Errno 13] Permission denied: 'output.vsdx'
```

**Solution:**
1. Close the file in Visio if it's open
2. Check file permissions
3. Use different output directory
4. Run with administrator privileges

#### Issue 10: Database Connection Fails

**Error:**
```
ERROR - Database connection failed
```

**Solution:**
```python
# Check connection string
connection_string = (
    f"DRIVER={{SQL Server}};"
    f"SERVER={server},{port};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "TrustServerCertificate=yes;"
)

# Test connection
import pyodbc
try:
    conn = pyodbc.connect(connection_string, timeout=10)
    print("Connection successful")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
```

---

## Best Practices

### 1. Error Handling

Always wrap Visio operations in try/except blocks:

```python
def generate_topology_diagram(self, devices, connections, site_name):
    """Generate diagram with proper error handling"""
    try:
        # Initialize
        if not self._initialize_visio():
            logger.error("Failed to initialize Visio")
            return None
        
        # Generate diagram
        # ... diagram generation code ...
        
        # Save
        self.doc.SaveAs(str(filepath))
        logger.info(f"Saved: {filepath}")
        
        return str(filepath)
        
    except Exception as e:
        logger.error(f"Failed to generate diagram: {e}")
        logger.exception("Full traceback:")
        return None
        
    finally:
        # Always cleanup COM objects
        self._cleanup_visio()
```

### 2. Logging

Use comprehensive logging for debugging:

```python
import logging

logger = logging.getLogger(__name__)

# Log at different levels
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning messages")
logger.error("Error messages")
logger.exception("Error with full traceback")

# Example
logger.info(f"Generating diagram for {site_name}")
logger.info(f"Devices: {len(devices)}")
logger.info(f"Connections: {len(connections)}")
logger.debug(f"Device list: {[d['device_name'] for d in devices]}")
```

### 3. Resource Cleanup

Always cleanup COM objects to prevent memory leaks:

```python
def _cleanup_visio(self):
    """Cleanup COM objects"""
    try:
        if self.doc:
            self.doc.Close()
            self.doc = None
        if self.page:
            self.page = None
        if self.visio_app:
            self.visio_app.Quit()
            self.visio_app = None
        logger.debug("COM objects cleaned up")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
```

### 4. Configuration Management

Use configuration files for flexibility:

```python
# Load from config
config = load_config("config.ini")

# Use config values
output_dir = config.get('visio', 'output_directory', fallback='./diagrams')
template = config.get('visio', 'template', fallback='TEMPLATE.vsdx')
exclude_devices = config.get('visio', 'exclude_devices', fallback='')

# Parse comma-separated values
exclude_list = [x.strip() for x in exclude_devices.split(',') if x.strip()]
```

### 5. Validation

Validate inputs before processing:

```python
def generate_topology_diagram(self, devices, connections, site_name):
    """Generate diagram with validation"""
    # Validate inputs
    if not devices:
        logger.error("No devices provided")
        return None
    
    if not site_name:
        logger.warning("No site name provided, using default")
        site_name = "Network"
    
    # Validate template exists
    if not self.template_path.exists():
        logger.error(f"Template not found: {self.template_path}")
        return None
    
    # Continue with generation...
```

### 6. Performance Optimization

For large diagrams, optimize performance:

```python
# Batch operations
shapes = []
for device in devices:
    shape = self._create_device_shape(...)
    shapes.append(shape)

# Create all shapes first, then all connectors
for connection in connections:
    self._create_connection(...)

# Disable screen updating during generation (COM)
self.visio_app.ScreenUpdating = False
try:
    # ... generate diagram ...
finally:
    self.visio_app.ScreenUpdating = True
```

### 7. Testing

Write comprehensive tests:

```python
# Unit tests for logic
def test_calculate_positions(self):
    positions = self.generator._calculate_device_positions(devices, connections)
    self.assertEqual(len(positions), len(devices))

# Integration tests for actual generation
def test_generate_diagram(self):
    filepath = self.generator.generate_topology_diagram(...)
    self.assertIsNotNone(filepath)
    self.assertTrue(Path(filepath).exists())

# Property-based tests for edge cases
from hypothesis import given, strategies as st

@given(st.lists(st.text(), min_size=1, max_size=100))
def test_handles_any_device_count(self, device_names):
    devices = [{'device_name': name} for name in device_names]
    positions = self.generator._calculate_device_positions(devices, [])
    assert len(positions) == len(devices)
```

### 8. Documentation

Document your code thoroughly:

```python
def generate_topology_diagram(
    self,
    devices: List[Dict],
    connections: List[Tuple[str, str, str, str]] = None,
    site_name: str = "Network"
) -> Optional[str]:
    """
    Generate a network topology diagram in Visio format
    
    Args:
        devices: List of device dictionaries with keys:
            - device_name (str): Device hostname
            - platform (str): Platform type (IOS, IOS-XE, NX-OS)
            - hardware_model (str): Hardware model number
        connections: Optional list of connection tuples:
            (source_device, source_port, dest_device, dest_port)
            If None, will query from database if available
        site_name: Name of the site/network for the diagram title
        
    Returns:
        Path to generated Visio file, or None if generation failed
        
    Example:
        >>> devices = [{'device_name': 'CORE-01', 'platform': 'IOS-XE', 'hardware_model': 'C9300'}]
        >>> connections = [('CORE-01', 'Gi1/0/1', 'ACCESS-01', 'Gi1/0/24')]
        >>> filepath = generator.generate_topology_diagram(devices, connections, "Main Office")
        >>> print(filepath)
        './diagrams/Topology_Main Office_20260127-14-30.vsdx'
    """
    # Implementation...
```

---


## Lessons Learned

### Technical Insights

#### 1. vsdx Library Limitations

**Discovery:** The vsdx library cannot create Dynamic Connectors programmatically.

**Impact:** Diagrams show devices but no connections.

**Solution:** 
- Use COM automation for full connector support
- Generate connection list file for manual addition
- Implement automatic fallback mechanism

**Code:**
```python
# Automatic fallback
try:
    from reports.visio_generator_com import VisioGeneratorCOM
    use_com = True
except ImportError:
    from reports.visio_generator import VisioGenerator
    use_com = False
```

#### 2. Visio Color Format (BGR vs RGB)

**Discovery:** Visio uses BGR format internally, not RGB.

**Impact:** Colors appear incorrect if using RGB values directly.

**Solution:** Convert RGB to BGR before setting colors.

**Code:**
```python
def _rgb_to_visio_color(self, hex_color: str) -> int:
    """Convert #RRGGBB to BGR integer"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    # BGR format: (blue << 16) | (green << 8) | red
    return (b << 16) | (g << 8) | r
```

#### 3. Glue Operations Are Critical

**Discovery:** Connectors must be glued to shapes to be dynamic.

**Impact:** Without glue, connectors are just static lines.

**Solution:** Use formula-based gluing to connection points.

**Code:**
```python
# Get shape IDs
source_id = source_shape.ID
dest_id = dest_shape.ID

# Glue connector endpoints using formulas
connector.Cells("BeginX").Formula = f"Sheet.{source_id}!PinX"
connector.Cells("BeginY").Formula = f"Sheet.{source_id}!PinY"
connector.Cells("EndX").Formula = f"Sheet.{dest_id}!PinX"
connector.Cells("EndY").Formula = f"Sheet.{dest_id}!PinY"
```

#### 4. COM Object Lifecycle Management

**Discovery:** COM objects must be explicitly released to prevent memory leaks.

**Impact:** Visio processes remain in memory after script ends.

**Solution:** Always cleanup in finally block.

**Code:**
```python
try:
    # Generate diagram
    self._initialize_visio()
    # ... diagram generation ...
finally:
    # Always cleanup
    self._cleanup_visio()
```

#### 5. Stencil Availability

**Discovery:** Network stencil (NETWRK_U.VSSX) may not be available.

**Impact:** Cannot create network-specific shapes.

**Solution:** Fallback to basic shapes stencil.

**Code:**
```python
stencil_paths = [
    "NETWRK_U.VSSX",  # Network stencil (preferred)
    "BASIC_U.VSSX",   # Basic shapes (fallback)
]

for stencil_name in stencil_paths:
    try:
        stencil = self.visio_app.Documents.OpenEx(stencil_name, 64)
        return stencil
    except:
        continue
```

#### 6. Hierarchical Layout Complexity

**Discovery:** Simple grid layout doesn't work well for network topologies.

**Impact:** Diagrams don't reflect network hierarchy.

**Solution:** Use BFS algorithm to build hierarchy levels.

**Key Points:**
- Find root device (most connections)
- Use BFS to assign devices to levels
- Position devices by level and row
- Center root device at top

#### 7. Scaling for Large Diagrams

**Discovery:** Fixed-size shapes don't work for large device counts.

**Impact:** Devices don't fit on page or overlap.

**Solution:** Implement automatic scaling based on device count.

**Code:**
```python
def _calculate_scale_factor(self, num_devices: int) -> float:
    """Scale shapes for large diagrams"""
    if num_devices <= 20:
        return 1.0
    
    # Linear scaling
    excess = num_devices - 20
    reduction = (excess / 20) * 0.6
    return max(0.4, 1.0 - reduction)
```

#### 8. Interface Name Abbreviation

**Discovery:** Full interface names are too long for connector labels.

**Impact:** Labels overlap and are unreadable.

**Solution:** Use Cisco standard abbreviations.

**Code:**
```python
abbreviations = {
    'TenGigabitEthernet': 'Te',
    'GigabitEthernet': 'Gi',
    'FastEthernet': 'Fa',
    'Port-channel': 'Po',
}

for full, abbrev in abbreviations.items():
    if interface.startswith(full):
        return interface.replace(full, abbrev, 1)
```

#### 9. Multiple Connections Between Devices

**Discovery:** Multiple connections between same devices overlap.

**Impact:** Connectors appear as single line.

**Solution:** Offset connection points based on connection index.

**Code:**
```python
# Track connection counts per device pair
connection_counts = {}
pair_key = f"{source_dev}:{dest_dev}"
connection_index = connection_counts.get(pair_key, 0)
connection_counts[pair_key] = connection_index + 1

# Offset connection point
if connection_index > 0:
    offset_direction = 1 if (connection_index % 2) == 1 else -1
    offset_amount = ((connection_index + 1) // 2) * 0.3
    # Apply offset perpendicular to edge
```

#### 10. Device Capability Filtering

**Discovery:** Not all devices should appear in diagrams (phones, cameras, etc.).

**Impact:** Diagrams cluttered with non-network devices.

**Solution:** Implement capability-based filtering.

**Code:**
```python
# In config.ini
[visio]
exclude_devices = phone,camera,printer

# In generator
def _should_exclude_device(self, capabilities: str) -> bool:
    """Check if device should be excluded"""
    if not self.exclude_capabilities or not capabilities:
        return False
    
    caps_list = [c.strip().lower() for c in capabilities.split(',')]
    
    for device_cap in caps_list:
        for exclude_cap in self.exclude_capabilities:
            import fnmatch
            if fnmatch.fnmatch(device_cap, exclude_cap):
                return True
    
    return False
```

### Development Best Practices

#### 1. Start with vsdx Library

Begin implementation with vsdx library:
- Simpler to implement
- No external dependencies
- Good for prototyping
- Add COM automation later for full features

#### 2. Use Template Files

Always use template files:
- Consistent styling
- Pre-configured page settings
- Reusable across projects
- Easy to customize

#### 3. Implement Fallback Mechanism

Always provide fallback:
- Try COM automation first
- Fall back to vsdx library
- Generate connection list for manual work
- Inform user which method is being used

#### 4. Log Everything

Comprehensive logging is essential:
- Log each step of generation
- Log device and connection counts
- Log errors with full tracebacks
- Use different log levels appropriately

#### 5. Test with Real Data

Test with production-like data:
- Large device counts (50+)
- Complex topologies
- Multiple connection types
- Edge cases (disconnected devices, self-loops)

#### 6. Handle Edge Cases

Common edge cases to handle:
- No devices
- No connections
- Disconnected devices
- Self-loops (device connected to itself)
- Duplicate connections
- Missing device properties

#### 7. Performance Considerations

For large diagrams:
- Disable screen updating during generation
- Batch operations where possible
- Use efficient data structures (sets, dicts)
- Consider parallel generation for multiple sites

#### 8. User Experience

Improve user experience:
- Show progress messages
- Provide clear error messages
- Generate connection lists for manual work
- Include instructions in output files

### Common Pitfalls to Avoid

#### 1. ❌ Not Cleaning Up COM Objects

**Problem:** Memory leaks, Visio processes remain running

**Solution:** Always cleanup in finally block

#### 2. ❌ Using RGB Instead of BGR

**Problem:** Colors appear incorrect

**Solution:** Convert RGB to BGR for Visio

#### 3. ❌ Not Gluing Connectors

**Problem:** Connectors don't move with shapes

**Solution:** Use formula-based gluing

#### 4. ❌ Hardcoding Paths

**Problem:** Code breaks on different systems

**Solution:** Use Path objects and configuration

#### 5. ❌ Ignoring vsdx Limitations

**Problem:** Expecting connectors to work with vsdx

**Solution:** Implement fallback mechanism

#### 6. ❌ Not Validating Inputs

**Problem:** Crashes on invalid data

**Solution:** Validate all inputs before processing

#### 7. ❌ Poor Error Handling

**Problem:** Cryptic error messages, no recovery

**Solution:** Wrap operations in try/except, provide clear messages

#### 8. ❌ Fixed Layout for All Sizes

**Problem:** Diagrams don't scale well

**Solution:** Implement automatic scaling

---

## Summary

### Key Takeaways

1. **Dual Implementation**: Use both vsdx library (fallback) and COM automation (full-featured)
2. **Automatic Fallback**: Detect available libraries and choose appropriate generator
3. **Glue is Critical**: Connectors must be glued to shapes for dynamic behavior
4. **BGR Color Format**: Visio uses BGR, not RGB
5. **Hierarchical Layout**: Use BFS algorithm for network topology
6. **Automatic Scaling**: Scale shapes based on device count
7. **Cleanup COM Objects**: Always release COM objects to prevent memory leaks
8. **Comprehensive Logging**: Log everything for debugging
9. **Handle Edge Cases**: Test with real data and edge cases
10. **User Experience**: Provide clear messages and fallback options

### Implementation Checklist

- [ ] Install dependencies (vsdx, pywin32)
- [ ] Create Visio template file
- [ ] Implement vsdx generator (fallback)
- [ ] Implement COM generator (full-featured)
- [ ] Add automatic fallback mechanism
- [ ] Implement hierarchical layout algorithm
- [ ] Add automatic scaling for large diagrams
- [ ] Implement device capability filtering
- [ ] Add connection list generation
- [ ] Write comprehensive tests
- [ ] Add logging throughout
- [ ] Handle all edge cases
- [ ] Document code thoroughly
- [ ] Test with real data

### Next Steps

1. **Copy this guide** to your project
2. **Install dependencies** from requirements.txt
3. **Create template file** in Visio
4. **Implement vsdx generator** first (simpler)
5. **Add COM generator** for full features
6. **Test thoroughly** with real data
7. **Customize** for your specific needs

---

## Additional Resources

### Documentation

- **vsdx Library**: https://pypi.org/project/vsdx/
- **pywin32**: https://github.com/mhammond/pywin32
- **Visio COM API**: https://docs.microsoft.com/en-us/office/vba/api/overview/visio
- **Visio File Format**: https://docs.microsoft.com/en-us/office/client-developer/visio/introduction-to-the-visio-file-formatvsdx

### Example Projects

- **NetWalker**: Network discovery tool with Visio export
  - Repository: https://github.com/MarkTegna/NetWalker
  - Files: `netwalker/reports/visio_generator*.py`

### Tools

- **Microsoft Visio**: Required for COM automation
- **Visual Studio Code**: Recommended IDE
- **Python 3.8+**: Required Python version

---

**Document Version:** 1.0  
**Last Updated:** January 27, 2026  
**Author:** Mark Oldham  
**Source Project:** NetWalker v0.6.24

---

## License

This implementation guide is provided as-is for educational and development purposes. The code examples are based on the NetWalker project and follow the same licensing terms.

---

**End of Guide**

