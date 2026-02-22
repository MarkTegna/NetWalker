# Design Document: IPv4 Prefix Inventory Module

## Overview

The IPv4 Prefix Inventory Module extends NetWalker with comprehensive IPv4 prefix collection and analysis capabilities. The module discovers VRFs, collects routing information from global and per-VRF routing tables, extracts BGP prefixes, normalizes all formats to CIDR notation, resolves ambiguous prefixes, tracks route summarization hierarchies, and exports results to Excel and database storage.

The design follows NetWalker's existing patterns for connection management, credential handling, database operations, and Excel export. The module is implemented as a new package under `netwalker/ipv4_prefix/` with clear separation of concerns across collector, parser, normalizer, and exporter components.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    IPv4 Prefix Inventory Module                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Collector  │→ │    Parser    │→ │  Normalizer  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         ↓                                      ↓                 │
│  ┌──────────────┐                    ┌──────────────┐          │
│  │  Ambiguity   │                    │ Deduplicator │          │
│  │  Resolver    │                    └──────────────┘          │
│  └──────────────┘                             ↓                 │
│                                      ┌──────────────┐          │
│                                      │   Exporter   │          │
│                                      └──────────────┘          │
│                                               ↓                 │
│                              ┌────────────────┴────────────┐   │
│                              ↓                              ↓   │
│                    ┌──────────────┐              ┌──────────────┐
│                    │ Excel Export │              │   Database   │
│                    └──────────────┘              └──────────────┘
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Existing NetWalker Infrastructure                   │
├─────────────────────────────────────────────────────────────────┤
│  Connection Manager │ Credential Manager │ Database Manager     │
│  Command Executor   │ Excel Generator    │ Logging Config       │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **Configuration Loading**: Load settings from `[ipv4_prefix_inventory]` section in netwalker.ini
2. **Device Discovery**: Query NetWalker database for device inventory
3. **Concurrent Collection**: Process devices in parallel using ThreadPool
4. **Per-Device Workflow**:
   - Connect using existing Connection Manager
   - Discover VRFs on device
   - Collect global routing table (if enabled)
   - Collect per-VRF routing tables (if enabled)
   - Collect BGP prefixes (if enabled)
   - Parse command outputs to extract prefixes
   - Normalize prefixes to CIDR notation
   - Resolve ambiguous prefixes
   - Tag prefixes with metadata
5. **Aggregation**: Combine results from all devices
6. **Deduplication**: Remove duplicates and create deduplicated views
7. **Summarization Analysis**: Identify and record route summarization relationships
8. **Export**: Write to CSV, Excel, and database

## Components and Interfaces

### 1. Configuration Manager Integration

**Purpose**: Load IPv4 prefix inventory settings from netwalker.ini

**Configuration Section**:
```ini
[ipv4_prefix_inventory]
# Enable/disable collection types
collect_global_table = true
collect_per_vrf = true
collect_bgp = true

# Output settings
output_directory = ./reports
create_summary_file = true

# Database settings
enable_database_storage = true
track_summarization = true

# Performance settings
concurrent_devices = 5
command_timeout = 30
```

**Interface**:
```python
class IPv4PrefixConfig:
    collect_global_table: bool
    collect_per_vrf: bool
    collect_bgp: bool
    output_directory: str
    create_summary_file: bool
    enable_database_storage: bool
    track_summarization: bool
    concurrent_devices: int
    command_timeout: int
```

### 2. Collector Component

**Purpose**: Execute commands on devices and collect raw outputs

**Module**: `netwalker/ipv4_prefix/collector.py`

**Key Classes**:

```python
class VRFDiscovery:
    """Discovers VRFs on network devices"""
    
    def discover_vrfs(self, connection, platform: str) -> List[str]:
        """
        Execute 'show vrf' and parse VRF names
        
        Args:
            connection: Active device connection
            platform: Device platform (ios, iosxe, nxos)
            
        Returns:
            List of VRF names
        """
        pass

class RoutingCollector:
    """Collects routing table information"""
    
    def collect_global_routes(self, connection) -> str:
        """Execute 'show ip route' for global table"""
        pass
    
    def collect_global_connected(self, connection) -> str:
        """Execute 'show ip route connected' for global table"""
        pass
    
    def collect_vrf_routes(self, connection, vrf: str) -> str:
        """Execute 'show ip route vrf <VRF>'"""
        pass
    
    def collect_vrf_connected(self, connection, vrf: str) -> str:
        """Execute 'show ip route vrf <VRF> connected'"""
        pass

class BGPCollector:
    """Collects BGP routing information"""
    
    def collect_global_bgp(self, connection) -> Optional[str]:
        """
        Execute 'show ip bgp' for global table
        Returns None if BGP not configured
        """
        pass
    
    def collect_vrf_bgp(self, connection, vrf: str, platform: str) -> Optional[str]:
        """
        Execute platform-specific BGP VRF command:
        - IOS/IOS-XE: 'show ip bgp vpnv4 vrf <VRF>'
        - NX-OS: 'show ip bgp vrf <VRF>'
        """
        pass

class PrefixCollector:
    """Orchestrates collection workflow for a single device"""
    
    def __init__(self, config: IPv4PrefixConfig, 
                 connection_manager: ConnectionManager,
                 credentials: Credentials):
        self.config = config
        self.connection_manager = connection_manager
        self.credentials = credentials
        self.vrf_discovery = VRFDiscovery()
        self.routing_collector = RoutingCollector()
        self.bgp_collector = BGPCollector()
    
    def collect_device(self, device: DeviceInfo) -> DeviceCollectionResult:
        """
        Collect all prefix data from a single device
        
        Returns:
            DeviceCollectionResult with raw command outputs and metadata
        """
        pass
```

### 3. Parser Component

**Purpose**: Extract IPv4 prefixes from command outputs

**Module**: `netwalker/ipv4_prefix/parser.py`

**Key Classes**:

```python
class PrefixExtractor:
    """Extracts prefixes from command output lines"""
    
    def extract_from_route_line(self, line: str) -> Optional[RawPrefix]:
        """
        Extract prefix from routing table line
        Handles formats:
        - 192.168.1.0/24
        - 192.168.1.0 255.255.255.0
        - L    10.0.0.1/32 (local route)
        """
        pass
    
    def extract_from_bgp_line(self, line: str) -> Optional[RawPrefix]:
        """
        Extract prefix from BGP output line
        Handles formats:
        - 10.0.0.0/24
        - 10.0.0.0 (ambiguous - no length)
        """
        pass

class RoutingTableParser:
    """Parses 'show ip route' output"""
    
    def parse(self, output: str, device: str, platform: str, 
              vrf: str) -> List[ParsedPrefix]:
        """
        Parse routing table output and extract all prefixes
        
        Returns:
            List of ParsedPrefix objects with metadata
        """
        pass

class BGPParser:
    """Parses 'show ip bgp' output"""
    
    def parse(self, output: str, device: str, platform: str, 
              vrf: str) -> List[ParsedPrefix]:
        """
        Parse BGP output and extract all prefixes
        Marks ambiguous prefixes for resolution
        """
        pass

class CommandOutputParser:
    """Main parser orchestrator"""
    
    def __init__(self):
        self.route_parser = RoutingTableParser()
        self.bgp_parser = BGPParser()
    
    def parse_collection_result(self, result: DeviceCollectionResult) -> List[ParsedPrefix]:
        """
        Parse all command outputs from a device collection
        
        Returns:
            List of all parsed prefixes with metadata
        """
        pass
```

### 4. Normalizer Component

**Purpose**: Convert all prefix formats to CIDR notation

**Module**: `netwalker/ipv4_prefix/normalizer.py`

**Key Classes**:

```python
class PrefixNormalizer:
    """Normalizes prefixes to CIDR notation"""
    
    def normalize(self, raw_prefix: str) -> Optional[str]:
        """
        Convert prefix to CIDR notation using ipaddress library
        
        Handles:
        - 192.168.1.0/24 → 192.168.1.0/24 (validate)
        - 192.168.1.0 255.255.255.0 → 192.168.1.0/24 (convert)
        - 10.0.0.1/32 → 10.0.0.1/32 (preserve host routes)
        
        Returns:
            CIDR notation string or None if invalid
        """
        pass
    
    def mask_to_cidr(self, ip: str, mask: str) -> Optional[str]:
        """Convert IP + mask to CIDR notation"""
        pass
    
    def validate_cidr(self, cidr: str) -> bool:
        """Validate CIDR notation format"""
        pass

class AmbiguityResolver:
    """Resolves prefixes without explicit length"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    def resolve(self, connection, prefix: str, vrf: str) -> Optional[str]:
        """
        Resolve ambiguous prefix by querying device
        
        Strategy:
        1. Try 'show ip bgp <prefix>' (or vrf variant)
        2. Try 'show ip route <prefix>' (or vrf variant)
        3. If both fail, mark as unresolved
        
        Returns:
            Resolved CIDR notation or None if unresolved
        """
        pass
```

### 5. Deduplication Component

**Purpose**: Remove duplicate prefix entries

**Module**: `netwalker/ipv4_prefix/normalizer.py`

**Key Classes**:

```python
class PrefixDeduplicator:
    """Removes duplicate prefix entries"""
    
    def deduplicate_by_device(self, prefixes: List[NormalizedPrefix]) -> List[NormalizedPrefix]:
        """
        Remove duplicates within device scope
        Key: (device, vrf, prefix, source)
        """
        pass
    
    def deduplicate_by_vrf(self, prefixes: List[NormalizedPrefix]) -> List[DeduplicatedPrefix]:
        """
        Create deduplicated view across devices
        Key: (vrf, prefix)
        Aggregates: device_list, device_count
        """
        pass
```

### 6. Summarization Analyzer Component

**Purpose**: Identify and track route summarization relationships

**Module**: `netwalker/ipv4_prefix/summarization.py`

**Key Classes**:

```python
class SummarizationAnalyzer:
    """Analyzes route summarization relationships"""
    
    def analyze_summarization(self, prefixes: List[NormalizedPrefix]) -> List[SummarizationRelationship]:
        """
        Identify summary routes and their component routes
        
        Algorithm:
        1. Sort prefixes by prefix length (shortest first)
        2. For each prefix, find all more-specific prefixes that fall within its range
        3. Record relationships where a device advertises both summary and components
        
        Returns:
            List of SummarizationRelationship objects
        """
        pass
    
    def is_component_of(self, component: str, summary: str) -> bool:
        """
        Check if component prefix falls within summary prefix range
        
        Example:
        - 192.168.1.0/24 is component of 192.168.0.0/16
        - 10.1.1.0/24 is component of 10.0.0.0/8
        """
        pass
    
    def find_components(self, summary: str, all_prefixes: List[NormalizedPrefix]) -> List[NormalizedPrefix]:
        """Find all component prefixes for a given summary"""
        pass
```

### 7. Exporter Component

**Purpose**: Export results to CSV, Excel, and database

**Module**: `netwalker/ipv4_prefix/exporter.py`

**Key Classes**:

```python
class CSVExporter:
    """Exports prefix data to CSV files"""
    
    def export_prefixes(self, prefixes: List[NormalizedPrefix], 
                       output_dir: str) -> str:
        """
        Export to prefixes.csv
        Columns: device, platform, vrf, prefix, source, protocol, timestamp
        """
        pass
    
    def export_deduplicated(self, prefixes: List[DeduplicatedPrefix], 
                           output_dir: str) -> str:
        """
        Export to prefixes_dedup_by_vrf.csv
        Columns: vrf, prefix, device_count, device_list
        """
        pass
    
    def export_exceptions(self, exceptions: List[Exception], 
                         output_dir: str) -> str:
        """
        Export to exceptions.csv
        Columns: device, command, error_type, raw_token, timestamp
        """
        pass

class ExcelExporter:
    """Exports prefix data to Excel with formatting"""
    
    def __init__(self):
        # Use existing NetWalker Excel patterns
        from netwalker.reports.excel_generator import ExcelGenerator
        self.excel_gen = ExcelGenerator()
    
    def export(self, prefixes: List[NormalizedPrefix],
               deduplicated: List[DeduplicatedPrefix],
               exceptions: List[Exception],
               output_dir: str) -> str:
        """
        Export to Excel workbook with three sheets:
        - Prefixes: All collected prefixes
        - Deduplicated: Unique prefixes by VRF
        - Exceptions: Errors and unresolved prefixes
        
        Apply NetWalker formatting:
        - Header row: bold, colored background
        - Auto-sized columns
        - Data filters
        """
        pass

class DatabaseExporter:
    """Exports prefix data to NetWalker database"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def initialize_schema(self) -> bool:
        """
        Create tables if they don't exist:
        - ipv4_prefixes
        - ipv4_prefix_summarization
        """
        pass
    
    def upsert_prefix(self, prefix: NormalizedPrefix) -> Optional[int]:
        """
        Insert or update prefix record
        Returns prefix_id
        """
        pass
    
    def upsert_summarization(self, relationship: SummarizationRelationship) -> bool:
        """
        Insert or update summarization relationship
        Links summary_prefix_id to component_prefix_id
        """
        pass
```

### 8. Main Orchestrator

**Purpose**: Coordinate the entire collection workflow

**Module**: `netwalker/ipv4_prefix/__init__.py`

**Key Classes**:

```python
class IPv4PrefixInventory:
    """Main orchestrator for IPv4 prefix inventory"""
    
    def __init__(self, config_file: str = "netwalker.ini"):
        self.config_file = config_file
        self.config = None
        self.connection_manager = None
        self.credential_manager = None
        self.db_manager = None
        self.logger = logging.getLogger(__name__)
    
    def run(self) -> InventoryResult:
        """
        Execute complete inventory workflow
        
        Steps:
        1. Load configuration
        2. Get credentials
        3. Connect to database
        4. Query device inventory
        5. Collect from devices (concurrent)
        6. Parse and normalize
        7. Deduplicate
        8. Analyze summarization
        9. Export results
        10. Display summary
        
        Returns:
            InventoryResult with statistics and output paths
        """
        pass
    
    def collect_from_devices(self, devices: List[DeviceInfo]) -> List[DeviceCollectionResult]:
        """
        Collect from multiple devices concurrently
        Uses ThreadPoolExecutor with configured concurrency limit
        """
        pass
    
    def process_device(self, device: DeviceInfo) -> DeviceCollectionResult:
        """Process a single device (called by thread pool)"""
        pass
```

## Data Models

**Module**: `netwalker/ipv4_prefix/data_models.py`

```python
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class IPv4PrefixConfig:
    """Configuration for IPv4 prefix inventory"""
    collect_global_table: bool
    collect_per_vrf: bool
    collect_bgp: bool
    output_directory: str
    create_summary_file: bool
    enable_database_storage: bool
    track_summarization: bool
    concurrent_devices: int
    command_timeout: int

@dataclass
class RawPrefix:
    """Raw prefix extracted from command output"""
    prefix_str: str
    raw_line: str
    is_ambiguous: bool

@dataclass
class ParsedPrefix:
    """Parsed prefix with metadata"""
    device: str
    platform: str
    vrf: str
    prefix_str: str
    source: str  # 'rib', 'connected', 'bgp'
    protocol: str  # 'B', 'D', 'C', 'L', 'S', ''
    raw_line: str
    is_ambiguous: bool
    timestamp: datetime

@dataclass
class NormalizedPrefix:
    """Normalized prefix in CIDR notation"""
    device: str
    platform: str
    vrf: str
    prefix: str  # CIDR notation
    source: str
    protocol: str
    raw_line: str
    timestamp: datetime

@dataclass
class DeduplicatedPrefix:
    """Deduplicated prefix view"""
    vrf: str
    prefix: str
    device_count: int
    device_list: List[str]

@dataclass
class SummarizationRelationship:
    """Route summarization relationship"""
    summary_prefix: str
    component_prefix: str
    device: str
    vrf: str

@dataclass
class CollectionException:
    """Collection or parsing exception"""
    device: str
    command: str
    error_type: str
    raw_token: Optional[str]
    error_message: str
    timestamp: datetime

@dataclass
class DeviceCollectionResult:
    """Result of collecting from a single device"""
    device: str
    platform: str
    success: bool
    vrfs: List[str]
    raw_outputs: dict  # command -> output
    error: Optional[str]

@dataclass
class InventoryResult:
    """Final inventory result"""
    total_devices: int
    successful_devices: int
    failed_devices: int
    total_prefixes: int
    unique_prefixes: int
    host_routes_count: int
    unresolved_count: int
    summarization_relationships: int
    execution_time: float
    output_files: List[str]
```

## Database Schema

### Table: ipv4_prefixes

```sql
CREATE TABLE ipv4_prefixes (
    prefix_id INT IDENTITY(1,1) PRIMARY KEY,
    device_id INT NOT NULL,
    vrf NVARCHAR(100) NOT NULL,
    prefix NVARCHAR(50) NOT NULL,
    source NVARCHAR(20) NOT NULL,  -- 'rib', 'connected', 'bgp'
    protocol NVARCHAR(10) NULL,     -- 'B', 'D', 'C', 'L', 'S'
    first_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
    last_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_ipv4_prefixes_device FOREIGN KEY (device_id)
        REFERENCES devices(device_id) ON DELETE CASCADE,
    CONSTRAINT UQ_device_vrf_prefix_source UNIQUE (device_id, vrf, prefix, source)
);

CREATE INDEX IX_ipv4_prefixes_vrf ON ipv4_prefixes(vrf);
CREATE INDEX IX_ipv4_prefixes_prefix ON ipv4_prefixes(prefix);
CREATE INDEX IX_ipv4_prefixes_source ON ipv4_prefixes(source);
CREATE INDEX IX_ipv4_prefixes_last_seen ON ipv4_prefixes(last_seen);
```

### Table: ipv4_prefix_summarization

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
        REFERENCES devices(device_id) ON DELETE CASCADE,
    CONSTRAINT UQ_summarization_relationship UNIQUE (
        summary_prefix_id, component_prefix_id, device_id
    )
);

CREATE INDEX IX_summarization_summary ON ipv4_prefix_summarization(summary_prefix_id);
CREATE INDEX IX_summarization_component ON ipv4_prefix_summarization(component_prefix_id);
CREATE INDEX IX_summarization_device ON ipv4_prefix_summarization(device_id);
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: VRF Discovery Execution

*For any* Cisco device (IOS, IOS-XE, or NX-OS), when VRF discovery is initiated, the system should execute `show vrf` and return a list of VRF names (which may be empty if no VRFs are configured).

**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: VRF Discovery Error Handling

*For any* device where VRF discovery fails, the system should log the error and continue with global table collection without terminating the collection process.

**Validates: Requirements 1.4**

### Property 3: Global Table Command Execution

*For any* device where global table collection is enabled, the system should execute both `show ip route` and `show ip route connected` commands.

**Validates: Requirements 2.1, 2.2**

### Property 4: BGP Collection with Graceful Degradation

*For any* device, when BGP collection is attempted, the system should execute `show ip bgp` if BGP is configured, or handle the error gracefully and continue if BGP is not configured.

**Validates: Requirements 2.3, 2.4**

### Property 5: Global Table VRF Tagging

*For any* prefix collected from global table commands, the prefix should be tagged with vrf="global".

**Validates: Requirements 2.5**

### Property 6: Per-VRF Command Execution

*For any* discovered VRF when per-VRF collection is enabled, the system should execute both `show ip route vrf <VRF>` and `show ip route vrf <VRF> connected` commands.

**Validates: Requirements 3.1, 3.2**

### Property 7: Platform-Specific BGP VRF Commands

*For any* VRF on a device, the system should execute the platform-appropriate BGP command: `show ip bgp vpnv4 vrf <VRF>` for IOS/IOS-XE devices, or `show ip bgp vrf <VRF>` for NX-OS devices.

**Validates: Requirements 3.3, 3.4**

### Property 8: Per-VRF Prefix Tagging

*For any* prefix collected from per-VRF commands, the prefix should be tagged with the correct VRF name.

**Validates: Requirements 3.5**

### Property 9: Pagination Control

*For any* Cisco device connection, the system should execute `terminal length 0` before collecting routing information.

**Validates: Requirements 4.1**

### Property 10: Pagination Control Error Handling

*For any* device where pagination control fails, the system should log the error and attempt collection anyway.

**Validates: Requirements 4.3**

### Property 11: Multi-Format Prefix Extraction

*For any* routing table output line containing a prefix in CIDR format (192.168.1.0/24) or mask format (192.168.1.0 255.255.255.0), the parser should successfully extract the prefix.

**Validates: Requirements 5.1, 5.2**

### Property 12: BGP Prefix Extraction

*For any* BGP output line containing a network address (with or without explicit length), the parser should extract the prefix and mark it as ambiguous if length is missing.

**Validates: Requirements 5.3**

### Property 13: Raw Line Preservation

*For any* parsed prefix, the system should preserve the raw output line from which it was extracted.

**Validates: Requirements 5.6**

### Property 14: Mask to CIDR Conversion

*For any* prefix in mask format (IP + subnet mask), normalization should convert it to valid CIDR notation using the ipaddress library.

**Validates: Requirements 6.1**

### Property 15: CIDR Idempotence

*For any* prefix already in valid CIDR format, normalization should validate and preserve it unchanged.

**Validates: Requirements 6.2**

### Property 16: Invalid Prefix Handling

*For any* prefix with invalid format, normalization should log the error and add it to the exceptions report without terminating processing.

**Validates: Requirements 6.3**

### Property 17: Normalization Output Validity

*For any* successfully normalized prefix, the output should be a valid IPv4 network in CIDR notation.

**Validates: Requirements 6.4**

### Property 18: Ambiguity Resolution Strategy

*For any* ambiguous BGP prefix (lacking explicit length), the resolver should attempt resolution using `show ip bgp <prefix>` followed by `show ip route <prefix>` (with VRF variants as appropriate).

**Validates: Requirements 7.1, 7.2**

### Property 19: Unresolved Prefix Recording

*For any* prefix where both resolution attempts fail, the system should record it as unresolved in the exceptions report with the raw token and source command.

**Validates: Requirements 7.3, 7.5**

### Property 20: Resolved Prefix Normalization

*For any* successfully resolved ambiguous prefix, the system should normalize it to CIDR notation.

**Validates: Requirements 7.4**

### Property 21: Complete Metadata Tagging

*For any* collected prefix, the system should tag it with all required metadata: device name, platform, VRF name, source (rib/connected/bgp), protocol (B/D/C/L/S or blank), timestamp, and raw_line (where available).

**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7**

### Property 22: Deduplication Key

*For any* set of prefixes, deduplication should use (device, vrf, prefix, source) as the unique key, keeping the first occurrence of duplicates.

**Validates: Requirements 9.1, 9.2**

### Property 23: VRF-Level Aggregation

*For any* deduplicated view, prefixes should be grouped by (vrf, prefix) across all devices, with each group including a device list and device count.

**Validates: Requirements 9.3, 9.4, 9.5**

### Property 24: CSV Column Structure

*For any* CSV export (prefixes, deduplicated, or exceptions), the output should contain the specified columns in the correct order.

**Validates: Requirements 10.2, 11.2, 12.2**

### Property 25: CSV Sort Order

*For any* CSV export, rows should be sorted according to the specification: prefixes by (vrf, prefix, device), deduplicated by (vrf, prefix).

**Validates: Requirements 10.3, 11.3**

### Property 26: Device List Formatting

*For any* deduplicated CSV export, the device_list column should contain semicolon-separated device names.

**Validates: Requirements 11.4**

### Property 27: Export Logging

*For any* completed export operation, the system should log the output file path.

**Validates: Requirements 10.5, 11.5**

### Property 28: Exception Recording Completeness

*For any* command failure, unresolved prefix, or parsing error, the exception reporter should record all required information (device, command/raw_token, error type/message, timestamp).

**Validates: Requirements 12.3, 12.4, 12.5**

### Property 29: Excel Filter Application

*For any* Excel export, all data columns should have filters applied.

**Validates: Requirements 13.4**

### Property 30: Database Upsert Behavior

*For any* prefix being stored, if it already exists (same device_id, vrf, prefix, source), the system should update last_seen; if new, it should insert with both first_seen and last_seen timestamps.

**Validates: Requirements 14.4, 14.5**

### Property 31: Database Storage Conditional Execution

*For any* collection run where database storage is disabled, the system should skip all database operations and continue with file exports.

**Validates: Requirements 14.6**

### Property 32: Summarization Detection

*For any* summary route and set of component routes, if a component prefix falls within the summary prefix range and both exist on the same device, the system should identify and record the summarization relationship.

**Validates: Requirements 15.3**

### Property 33: Summarization Metadata

*For any* recorded summarization relationship, the system should include the device_id that performed the summarization.

**Validates: Requirements 15.5**

### Property 34: Recursive Summarization Query Support

*For any* multi-level summarization hierarchy (where a prefix is both a component and a summary), the database should support recursive queries to trace from specific routes up to root summaries.

**Validates: Requirements 15.6, 15.7**

### Property 35: Command Failure Isolation

*For any* command failure on a device, the system should log the error, continue with remaining commands on that device, and continue with remaining devices.

**Validates: Requirements 16.1, 16.2, 16.3**

### Property 36: Failure Exception Recording

*For any* command failure, the exception reporter should record the failure in the exceptions report.

**Validates: Requirements 16.4**

### Property 37: Collection Summary Reporting

*For any* completed collection, the system should report counts of successful and failed devices.

**Validates: Requirements 16.5**

### Property 38: VRF Name Sanitization

*For any* VRF name containing spaces or special characters, the system should properly quote or escape the name when constructing commands.

**Validates: Requirements 17.1, 17.2**

### Property 39: VRF Name Validation

*For any* VRF name, the system should validate the format before executing VRF-specific commands, logging errors and skipping invalid VRFs.

**Validates: Requirements 17.3, 17.4**

### Property 40: VRF Name Logging

*For any* VRF-specific command execution, the system should log the sanitized VRF name used in the command.

**Validates: Requirements 17.5**

### Property 41: Concurrency Limit Enforcement

*For any* concurrent device processing, the number of active threads should not exceed the configured concurrency limit.

**Validates: Requirements 18.2**

### Property 42: Thread Failure Isolation

*For any* device processing thread that fails, other threads should continue processing without interruption.

**Validates: Requirements 18.4**

### Property 43: Result Aggregation Completeness

*For any* completed concurrent collection, the final results should include data from all processed devices.

**Validates: Requirements 18.5**

### Property 44: Progress Reporting Completeness

*For any* collection run, the system should display progress information including: total devices at start, device name and progress during processing, success/failure indicators per device, and final summary with counts and execution time.

**Validates: Requirements 19.1, 19.2, 19.3, 19.4, 19.5**

### Property 45: Configuration Loading

*For any* configuration file with an [ipv4_prefix_inventory] section, the system should load all settings from that section.

**Validates: Requirements 20.1**

### Property 46: Configuration Application

*For any* configuration setting (global table, per-VRF, BGP, output directory, database storage, concurrency), the system should apply the configured value to control behavior.

**Validates: Requirements 20.2, 20.3, 20.4, 20.5, 20.6, 20.7**

### Property 47: Summary Statistics Completeness

*For any* completed collection, the system should display all summary statistics: total prefixes, prefixes per VRF, prefixes per source, /32 host routes count, and unresolved prefixes count.

**Validates: Requirements 22.1, 22.2, 22.3, 22.4, 22.5**

### Property 48: Summary File Creation

*For any* collection run where summary file is configured, the system should write statistics to summary.txt.

**Validates: Requirements 22.6**

## Error Handling

### Connection Errors

- **SSH Connection Failure**: Log error, mark device as failed, continue with remaining devices
- **Authentication Failure**: Log error with credential hint, mark device as failed, continue
- **Connection Timeout**: Log timeout, mark device as failed, continue

### Command Execution Errors

- **Command Not Supported**: Log warning, skip command, continue with remaining commands
- **Command Timeout**: Log timeout, skip command, continue with remaining commands
- **Privilege Level Insufficient**: Log error, attempt remaining commands, mark device as failed if critical commands fail

### Parsing Errors

- **Invalid Prefix Format**: Log error, add to exceptions report, continue parsing
- **Ambiguous Prefix Unresolved**: Log warning, add to exceptions report, continue
- **Unexpected Output Format**: Log error, add to exceptions report, continue

### Database Errors

- **Connection Failure**: Log error, disable database storage for this run, continue with file exports
- **Schema Creation Failure**: Log error, disable database storage, continue with file exports
- **Insert/Update Failure**: Log error for specific prefix, continue with remaining prefixes

### Export Errors

- **File Permission Error**: Log error, attempt alternative output location, fail gracefully if all attempts fail
- **Disk Space Error**: Log error, fail gracefully with clear message
- **Excel Library Error**: Log error, fall back to CSV-only export

## Testing Strategy

### Unit Testing

Unit tests will focus on specific examples, edge cases, and error conditions:

- **Parser Tests**: Test with sample outputs from real devices (IOS, IOS-XE, NX-OS)
  - `show ip route` with various route types (C, L, B, D, S)
  - `show ip bgp vpnv4 vrf WAN` with ambiguous prefixes (10.0.0.0 without /len)
  - `show vrf` with various VRF name formats
  - Edge cases: empty outputs, malformed lines, special characters

- **Normalizer Tests**: Test format conversions
  - Mask to CIDR: 192.168.1.0 255.255.255.0 → 192.168.1.0/24
  - CIDR validation: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
  - Invalid formats: 999.999.999.999/32, 10.0.0.0/33
  - Edge cases: /32 host routes, /0 default route

- **Ambiguity Resolver Tests**: Test resolution strategies
  - Successful resolution via `show ip bgp <prefix>`
  - Fallback to `show ip route <prefix>`
  - Unresolved prefix handling
  - VRF-specific resolution commands

- **Deduplicator Tests**: Test deduplication logic
  - Exact duplicates (same device, vrf, prefix, source)
  - Cross-device duplicates (same vrf, prefix, different devices)
  - Edge cases: empty input, single prefix, all duplicates

- **Summarization Analyzer Tests**: Test hierarchy detection
  - Simple summarization: 192.168.1.0/24 + 192.168.2.0/24 → 192.168.0.0/16
  - Multi-level hierarchies: /24 → /16 → /8
  - Edge cases: no summarization, overlapping prefixes

- **Exporter Tests**: Test output formatting
  - CSV structure and encoding
  - Excel workbook structure and sheets
  - Sort order verification
  - Edge cases: empty data, special characters in device names

### Property-Based Testing

Property tests will verify universal properties across all inputs using a Python property-based testing library (Hypothesis). Each test will run a minimum of 100 iterations with randomized inputs.

**Test Configuration**:
- Library: Hypothesis (Python)
- Minimum iterations: 100 per property
- Tag format: `# Feature: ipv4-prefix-inventory, Property N: <property_text>`

**Property Test Examples**:

```python
# Feature: ipv4-prefix-inventory, Property 14: Mask to CIDR Conversion
@given(valid_ipv4_address(), valid_subnet_mask())
def test_mask_to_cidr_conversion(ip, mask):
    """For any valid IP and subnet mask, normalization should produce valid CIDR"""
    normalizer = PrefixNormalizer()
    result = normalizer.mask_to_cidr(ip, mask)
    assert result is not None
    assert is_valid_cidr(result)
    # Verify round-trip: CIDR back to mask should match original
    assert cidr_to_mask(result) == mask

# Feature: ipv4-prefix-inventory, Property 15: CIDR Idempotence
@given(valid_cidr_prefix())
def test_cidr_idempotence(cidr):
    """For any valid CIDR prefix, normalization should preserve it unchanged"""
    normalizer = PrefixNormalizer()
    result = normalizer.normalize(cidr)
    assert result == cidr

# Feature: ipv4-prefix-inventory, Property 22: Deduplication Key
@given(lists(normalized_prefix()))
def test_deduplication_key(prefixes):
    """For any set of prefixes, deduplication should use correct unique key"""
    deduplicator = PrefixDeduplicator()
    result = deduplicator.deduplicate_by_device(prefixes)
    # Verify no duplicates by key (device, vrf, prefix, source)
    keys = [(p.device, p.vrf, p.prefix, p.source) for p in result]
    assert len(keys) == len(set(keys))

# Feature: ipv4-prefix-inventory, Property 32: Summarization Detection
@given(summary_prefix(), lists(component_prefix()))
def test_summarization_detection(summary, components):
    """For any summary and component prefixes, detection should identify relationships"""
    analyzer = SummarizationAnalyzer()
    # Filter components that actually fall within summary
    expected_components = [c for c in components if is_component_of(c, summary)]
    result = analyzer.find_components(summary, components)
    assert set(result) == set(expected_components)

# Feature: ipv4-prefix-inventory, Property 38: VRF Name Sanitization
@given(vrf_name_with_special_chars())
def test_vrf_name_sanitization(vrf_name):
    """For any VRF name with special characters, sanitization should produce valid command"""
    collector = RoutingCollector()
    command = collector.build_vrf_command("show ip route vrf", vrf_name)
    # Verify command is properly quoted/escaped
    assert is_valid_command_syntax(command)
    # Verify VRF name is preserved (can be extracted back)
    assert extract_vrf_from_command(command) == vrf_name
```

**Generators for Property Tests**:

```python
@composite
def valid_ipv4_address(draw):
    """Generate valid IPv4 addresses"""
    octets = [draw(integers(min_value=0, max_value=255)) for _ in range(4)]
    return '.'.join(map(str, octets))

@composite
def valid_subnet_mask(draw):
    """Generate valid subnet masks"""
    prefix_len = draw(integers(min_value=0, max_value=32))
    mask_int = (0xFFFFFFFF << (32 - prefix_len)) & 0xFFFFFFFF
    octets = [(mask_int >> (24 - 8*i)) & 0xFF for i in range(4)]
    return '.'.join(map(str, octets))

@composite
def valid_cidr_prefix(draw):
    """Generate valid CIDR prefixes"""
    ip = draw(valid_ipv4_address())
    prefix_len = draw(integers(min_value=0, max_value=32))
    return f"{ip}/{prefix_len}"

@composite
def vrf_name_with_special_chars(draw):
    """Generate VRF names with spaces and special characters"""
    base = draw(text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20))
    special = draw(sampled_from([' ', '-', '_', '.', ':', '']))
    return base + special + base
```

### Integration Testing

Integration tests will verify end-to-end workflows:

- **Full Collection Workflow**: Test complete collection from device inventory through export
- **Database Integration**: Test schema creation, upsert operations, and query functionality
- **Concurrent Processing**: Test thread pool execution with multiple devices
- **Error Recovery**: Test graceful degradation when components fail

### Test Data

Sample command outputs will be collected from real devices and stored in `tests/fixtures/`:

- `show_ip_route_ios.txt`: IOS routing table output
- `show_ip_route_nxos.txt`: NX-OS routing table output
- `show_ip_bgp_vpnv4_vrf.txt`: BGP VPNv4 output with ambiguous prefixes
- `show_vrf_ios.txt`: IOS VRF list
- `show_vrf_nxos.txt`: NX-OS VRF list

## Performance Considerations

### Scalability

- **Device Count**: Designed to handle 100+ devices concurrently
- **Prefix Count**: Efficient handling of 10,000+ prefixes per device
- **VRF Count**: Support for 100+ VRFs per device

### Optimization Strategies

- **Concurrent Collection**: ThreadPool for parallel device processing
- **Batch Database Operations**: Bulk insert/update for prefixes
- **Streaming Parsing**: Process command outputs line-by-line to minimize memory
- **Lazy Evaluation**: Parse and normalize only when needed

### Resource Limits

- **Memory**: Approximately 100MB per 10,000 prefixes
- **Database Connections**: Reuse single connection per thread
- **Thread Pool Size**: Configurable, default 5 concurrent devices

## Security Considerations

### Credential Handling

- Use existing NetWalker Credential_Manager
- Never log passwords or credentials
- Support encrypted credential storage

### Database Security

- Use parameterized queries to prevent SQL injection
- Enforce foreign key constraints for data integrity
- Support encrypted database connections (TLS)

### File Permissions

- Create output files with restrictive permissions (0600)
- Validate output directory paths to prevent directory traversal
- Handle file permission errors gracefully

## Future Enhancements

### IPv6 Support

- Extend to collect IPv6 prefixes
- Support IPv6 CIDR notation
- Handle IPv6 summarization

### Historical Tracking

- Track prefix changes over time
- Generate diff reports between collection runs
- Alert on unexpected prefix changes

### Advanced Analytics

- Identify unused IP space
- Detect overlapping prefixes
- Recommend summarization opportunities
- Visualize prefix hierarchies

### API Integration

- REST API for querying prefix inventory
- Webhook notifications for changes
- Integration with IPAM systems
