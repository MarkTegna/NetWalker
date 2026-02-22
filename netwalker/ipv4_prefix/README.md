# IPv4 Prefix Inventory Module

## Overview

The IPv4 Prefix Inventory Module provides comprehensive IPv4 prefix collection and analysis capabilities for NetWalker. It discovers VRFs, collects routing information from global and per-VRF routing tables, extracts BGP prefixes, normalizes all formats to CIDR notation, and exports results to Excel and database storage.

## Features

- **VRF Discovery**: Automatically discovers all VRFs configured on network devices
- **Multi-Source Collection**: Collects prefixes from:
  - Global routing table (`show ip route`)
  - Per-VRF routing tables (`show ip route vrf <VRF>`)
  - BGP routing information (`show ip bgp`)
  - Connected routes and local interfaces
- **Format Normalization**: Converts all prefix formats to standard CIDR notation
- **Deduplication**: Removes duplicate entries and provides aggregated views
- **Route Summarization Tracking**: Identifies and records hierarchical summarization relationships
- **Multiple Export Formats**: Exports to CSV, Excel, and SQL Server database
- **Concurrent Processing**: Processes multiple devices in parallel for efficiency
- **Comprehensive Error Reporting**: Tracks and reports all collection and parsing exceptions

## Supported Platforms

- Cisco IOS
- Cisco IOS-XE
- Cisco NX-OS

## Configuration

Add the following section to your `netwalker.ini` configuration file:

```ini
[ipv4_prefix_inventory]
# Enable collection from global routing table (true/false)
collect_global_table = true

# Enable collection from per-VRF routing tables (true/false)
collect_per_vrf = true

# Enable collection of BGP prefixes (true/false)
collect_bgp = true

# Output directory for CSV and Excel exports
output_directory = ./reports

# Create summary statistics file (true/false)
create_summary_file = true

# Enable database storage of prefix data (true/false)
enable_database_storage = true

# Track route summarization relationships (true/false)
track_summarization = true

# Number of devices to process concurrently
concurrent_devices = 5

# Command timeout in seconds
command_timeout = 30
```

## Usage

### Command Line

Run IPv4 prefix inventory on all devices:

```bash
python main.py ipv4-prefix-inventory
```

Run on filtered devices (SQL wildcard syntax):

```bash
python main.py ipv4-prefix-inventory --filter "%-CORE-%"
```

Specify custom configuration file:

```bash
python main.py ipv4-prefix-inventory --config custom_config.ini
```

Override output directory:

```bash
python main.py ipv4-prefix-inventory --output ./custom_reports
```

### Programmatic Usage

```python
from netwalker.ipv4_prefix import IPv4PrefixInventory

# Create inventory instance
inventory = IPv4PrefixInventory(config_file="netwalker.ini")

# Run collection on all devices
result = inventory.run()

# Run collection on filtered devices
result = inventory.run(device_filter="%-CORE-%")

# Access results
print(f"Total prefixes collected: {result.total_prefixes}")
print(f"Unique prefixes: {result.unique_prefixes}")
print(f"Execution time: {result.execution_time:.2f} seconds")
```

## Output Files

The module generates the following output files:

### 1. prefixes.csv

Contains all collected prefixes with complete metadata:

- `device`: Device hostname
- `platform`: Device platform (ios, iosxe, nxos)
- `vrf`: VRF name (or "global" for global table)
- `prefix`: IPv4 prefix in CIDR notation
- `source`: Source of prefix (rib, connected, bgp)
- `protocol`: Routing protocol code (B, D, C, L, S, O, etc.)
- `timestamp`: Collection timestamp

### 2. prefixes_dedup_by_vrf.csv

Contains unique prefixes aggregated by VRF:

- `vrf`: VRF name
- `prefix`: IPv4 prefix in CIDR notation
- `device_count`: Number of devices where prefix appears
- `device_list`: Semicolon-separated list of device names

### 3. exceptions.csv

Contains collection and parsing errors:

- `device`: Device hostname
- `command`: Command that failed (if applicable)
- `error_type`: Type of error (command_failure, parse_error, unresolved_prefix, etc.)
- `raw_token`: Problematic token or prefix string
- `error_message`: Detailed error message
- `timestamp`: Error timestamp

### 4. ipv4_prefix_inventory_YYYYMMDD-HHMM.xlsx

Excel workbook with three sheets:
- **Prefixes**: All collected prefixes
- **Deduplicated**: Unique prefixes by VRF
- **Exceptions**: Errors and unresolved prefixes

All sheets include:
- Professional formatting with colored headers
- Auto-sized columns
- Data filters on all columns

## Database Schema

When database storage is enabled, the module creates two tables:

### ipv4_prefixes

Stores collected IPv4 prefixes with metadata:

```sql
CREATE TABLE ipv4_prefixes (
    prefix_id INT IDENTITY(1,1) PRIMARY KEY,
    device_id INT NOT NULL,
    vrf NVARCHAR(100) NOT NULL,
    prefix NVARCHAR(50) NOT NULL,
    source NVARCHAR(20) NOT NULL,
    protocol NVARCHAR(10) NULL,
    first_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
    last_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_ipv4_prefixes_device FOREIGN KEY (device_id)
        REFERENCES devices(device_id) ON DELETE CASCADE,
    CONSTRAINT UQ_device_vrf_prefix_source UNIQUE (device_id, vrf, prefix, source)
);
```

### ipv4_prefix_summarization

Stores route summarization relationships:

```sql
CREATE TABLE ipv4_prefix_summarization (
    summarization_id INT IDENTITY(1,1) PRIMARY KEY,
    summary_prefix_id INT NOT NULL,
    component_prefix_id INT NOT NULL,
    device_id INT NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_summarization_summary FOREIGN KEY (summary_prefix_id)
        REFERENCES ipv4_prefixes(prefix_id) ON DELETE CASCADE,
    CONSTRAINT FK_summarization_component FOREIGN KEY (component_prefix_id)
        REFERENCES ipv4_prefixes(prefix_id) ON DELETE NO ACTION,
    CONSTRAINT FK_summarization_device FOREIGN KEY (device_id)
        REFERENCES devices(device_id) ON DELETE CASCADE
);
```

## Architecture

The module is organized into the following components:

### Collector (`collector.py`)

Handles SSH connections and command execution:
- `VRFDiscovery`: Discovers VRFs on devices
- `RoutingCollector`: Collects routing table information
- `BGPCollector`: Collects BGP routing information
- `PrefixCollector`: Orchestrates collection workflow for single device

### Parser (`parser.py`)

Extracts IPv4 prefixes from command outputs:
- `PrefixExtractor`: Extracts prefixes from individual lines
- `RoutingTableParser`: Parses routing table output
- `BGPParser`: Parses BGP output
- `CommandOutputParser`: Main parser orchestrator

### Normalizer (`normalizer.py`)

Normalizes prefixes and removes duplicates:
- `PrefixNormalizer`: Converts all formats to CIDR notation
- `AmbiguityResolver`: Resolves prefixes without explicit length
- `PrefixDeduplicator`: Removes duplicate entries

### Summarization Analyzer (`summarization.py`)

Analyzes route summarization relationships:
- `SummarizationAnalyzer`: Identifies summary/component relationships

### Exporter (`exporter.py`)

Exports results to various formats:
- `CSVExporter`: Exports to CSV files
- `ExcelExporter`: Exports to Excel with formatting
- `DatabaseExporter`: Stores in SQL Server database

### Main Orchestrator (`__init__.py`)

Coordinates the complete workflow:
- `IPv4PrefixInventory`: Main orchestrator class

## Data Models

All data structures are defined in `data_models.py`:

- `IPv4PrefixConfig`: Configuration settings
- `RawPrefix`: Raw prefix before normalization
- `ParsedPrefix`: Parsed prefix with metadata
- `NormalizedPrefix`: Normalized prefix in CIDR notation
- `DeduplicatedPrefix`: Deduplicated prefix view
- `SummarizationRelationship`: Route summarization relationship
- `CollectionException`: Collection or parsing exception
- `DeviceCollectionResult`: Result from single device
- `InventoryResult`: Final inventory result with statistics

## Error Handling

The module implements comprehensive error handling:

- **Connection Failures**: Logged and reported, other devices continue processing
- **Command Failures**: Logged and added to exceptions report
- **Parsing Errors**: Logged and added to exceptions report
- **Ambiguous Prefixes**: Marked for resolution or added to exceptions
- **Thread Failures**: Isolated to prevent affecting other devices

## Performance

- **Concurrent Processing**: Processes multiple devices in parallel (configurable)
- **Efficient Parsing**: Uses regex patterns for fast prefix extraction
- **Batch Database Operations**: Minimizes database round-trips
- **Memory Efficient**: Streams large outputs without loading entirely into memory

## Requirements

- Python 3.7+
- NetWalker core modules (connection, credentials, database)
- openpyxl (for Excel export)
- pyodbc (for database storage)
- ipaddress (standard library)

## Troubleshooting

### No prefixes collected

- Verify devices are reachable and credentials are correct
- Check that routing tables contain prefixes
- Review exceptions.csv for collection errors

### Ambiguous prefixes not resolved

- BGP prefixes without explicit length require resolution
- Check that devices respond to `show ip bgp <prefix>` commands
- Review exceptions.csv for unresolved prefixes

### Database connection failures

- Verify database configuration in netwalker.ini
- Check SQL Server connectivity and credentials
- Ensure database exists or user has CREATE DATABASE permission

### Excel export fails

- Verify openpyxl library is installed: `pip install openpyxl`
- Check output directory permissions
- Review logs for detailed error messages

## Author

Mark Oldham

## Version

See `netwalker/version.py` for current version information.
