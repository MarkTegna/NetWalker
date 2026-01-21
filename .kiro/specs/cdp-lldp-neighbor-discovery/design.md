# Design Document: CDP/LLDP Neighbor Discovery Database Storage

## Overview

This design extends NetWalker's existing CDP/LLDP neighbor discovery capabilities by adding persistent database storage for neighbor connection data. Currently, NetWalker collects neighbor information during device discovery but only stores it in memory. This enhancement will persist neighbor data to the SQL Server database, enabling historical tracking, topology visualization, and network analysis.

### Current State

NetWalker already implements:
- CDP and LLDP neighbor discovery via `ProtocolParser`
- Neighbor data collection via `DeviceCollector`
- In-memory storage of neighbor information in `NeighborInfo` objects
- Integration with discovery workflow via `DiscoveryEngine`

### What's New

This design adds:
- Database schema for storing neighbor connections (`device_neighbors` table)
- Database operations for upserting and querying neighbor data
- Interface name normalization for consistent storage
- Bidirectional connection deduplication
- Hostname resolution for linking neighbors to database devices
- Integration with Visio diagram generation

### Design Principles

1. **Minimal Disruption**: Leverage existing neighbor collection code; only add database persistence
2. **Data Integrity**: Use foreign keys and constraints to maintain referential integrity
3. **Deduplication**: Store each physical connection once, regardless of discovery direction
4. **Consistency**: Normalize interface names for reliable matching
5. **Resilience**: Continue discovery even if neighbor storage fails

## Architecture

### Component Interaction

```
┌─────────────────┐
│ DiscoveryEngine │
└────────┬────────┘
         │ discovers device
         ▼
┌─────────────────┐
│ DeviceCollector │
└────────┬────────┘
         │ collects neighbors
         ▼
┌─────────────────┐
│ ProtocolParser  │──────┐
└────────┬────────┘      │ parses CDP/LLDP
         │               │ normalizes interfaces
         │               │
         ▼               ▼
┌─────────────────────────┐
│   NeighborInfo List     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────┐
│ DatabaseManager │
└────────┬────────┘
         │ stores neighbors
         ▼
┌─────────────────┐
│ device_neighbors│
│     table       │
└─────────────────┘
```

### Data Flow

1. **Discovery**: `DiscoveryEngine` discovers a device
2. **Collection**: `DeviceCollector` executes CDP/LLDP commands
3. **Parsing**: `ProtocolParser` parses output into `NeighborInfo` objects
4. **Normalization**: Interface names are normalized during parsing
5. **Storage**: `DatabaseManager` stores neighbors in `device_neighbors` table
6. **Resolution**: Hostnames are resolved to `device_id` values
7. **Deduplication**: Reverse connections are checked to prevent duplicates

## Components and Interfaces

### Database Schema Extension

#### device_neighbors Table

```sql
CREATE TABLE device_neighbors (
    neighbor_id INT IDENTITY(1,1) PRIMARY KEY,
    source_device_id INT NOT NULL,
    source_interface NVARCHAR(100) NOT NULL,
    destination_device_id INT NOT NULL,
    destination_interface NVARCHAR(100) NOT NULL,
    protocol NVARCHAR(10) NOT NULL,  -- 'CDP' or 'LLDP'
    first_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
    last_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT FK_neighbor_source FOREIGN KEY (source_device_id) 
        REFERENCES devices(device_id) ON DELETE CASCADE,
    CONSTRAINT FK_neighbor_destination FOREIGN KEY (destination_device_id) 
        REFERENCES devices(device_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_neighbor_connection UNIQUE (
        source_device_id, source_interface, 
        destination_device_id, destination_interface
    )
);

CREATE INDEX IX_neighbors_source ON device_neighbors(source_device_id);
CREATE INDEX IX_neighbors_destination ON device_neighbors(destination_device_id);
CREATE INDEX IX_neighbors_last_seen ON device_neighbors(last_seen);
CREATE INDEX IX_neighbors_protocol ON device_neighbors(protocol);
```

**Design Rationale**:
- `source_device_id` and `destination_device_id`: Foreign keys to `devices` table
- Source uses `ON DELETE CASCADE`: When source device deleted, remove its connections
- Destination uses `ON DELETE NO ACTION`: Prevent deletion of devices that are connection targets
- Unique constraint prevents duplicate connections in same direction
- Indexes optimize queries for device connections and cleanup operations

### DatabaseManager Extensions

#### New Methods

```python
class DatabaseManager:
    
    def initialize_neighbor_table(self) -> bool:
        """Create device_neighbors table if it doesn't exist"""
        
    def upsert_device_neighbors(self, device_id: int, neighbors: List[NeighborInfo]) -> int:
        """
        Store or update neighbor connections for a device
        
        Args:
            device_id: Source device ID
            neighbors: List of NeighborInfo objects
            
        Returns:
            Count of neighbors successfully stored
        """
        
    def resolve_hostname_to_device_id(self, hostname: str) -> Optional[int]:
        """
        Resolve neighbor hostname to device_id
        
        Args:
            hostname: Device hostname (may be FQDN)
            
        Returns:
            device_id if found, None otherwise
        """
        
    def check_reverse_connection(self, source_id: int, source_if: str, 
                                 dest_id: int, dest_if: str) -> Optional[int]:
        """
        Check if reverse connection exists (dest→source)
        
        Returns:
            neighbor_id if reverse exists, None otherwise
        """
        
    def get_device_neighbors(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve all neighbors for a device (both directions)
        
        Returns:
            List of neighbor connection dictionaries
        """
        
    def get_unresolved_neighbors(self) -> List[Dict[str, Any]]:
        """
        Get neighbors that couldn't be resolved to device_ids
        
        Returns:
            List of unresolved neighbor information
        """
        
    def cleanup_stale_neighbors(self, days: int) -> int:
        """
        Delete neighbors not seen in specified days
        
        Returns:
            Count of neighbors deleted
        """
```

### ProtocolParser Extensions

#### Interface Normalization

```python
class ProtocolParser:
    
    def normalize_interface_name(self, interface_name: str, platform: str = None) -> str:
        """
        Normalize interface names for consistent storage
        
        Args:
            interface_name: Raw interface name from device
            platform: Device platform (IOS, NX-OS, etc.)
            
        Returns:
            Normalized interface name
            
        Examples:
            "Gi1/0/1" → "GigabitEthernet1/0/1"
            "Eth1/1" → "Ethernet1/1" (NX-OS preserved)
            "Po1" → "Port-channel1"
            "mgmt0" → "Management0"
        """
```

**Normalization Rules**:
1. **IOS Abbreviations**: Expand to full names
   - `Gi` → `GigabitEthernet`
   - `Te` → `TenGigabitEthernet`
   - `Fa` → `FastEthernet`
2. **NX-OS**: Preserve existing format
   - `Ethernet1/1` → `Ethernet1/1` (no change)
3. **Port-channels**: Standardize to `Port-channel`
   - `Po1`, `port-channel1`, `PortChannel1` → `Port-channel1`
4. **Management**: Standardize to `Management`
   - `mgmt0`, `Mgmt0`, `Management0` → `Management0`
5. **Case**: Preserve case for platform-specific formats

### Discovery Integration

#### Modified process_device_discovery

```python
class DatabaseManager:
    
    def process_device_discovery(self, device_info: Dict[str, Any]) -> bool:
        """
        Process complete device discovery including neighbors
        
        Current flow:
        1. Upsert device
        2. Upsert version
        3. Upsert interfaces
        4. Upsert VLANs
        
        New flow adds:
        5. Upsert neighbors (NEW)
        
        Args:
            device_info: Complete device information including neighbors
            
        Returns:
            True if successful, False otherwise
        """
```

## Data Models

### Existing Models (No Changes)

```python
@dataclass
class NeighborInfo:
    """Neighbor information from CDP/LLDP (already exists)"""
    device_id: str  # Neighbor hostname
    local_interface: str
    remote_interface: str
    platform: str
    capabilities: List[str]
    ip_address: Optional[str]
    protocol: str  # "CDP" or "LLDP"
```

### New Models

```python
@dataclass
class DeviceNeighbor:
    """Database model for device_neighbors table"""
    neighbor_id: Optional[int] = None
    source_device_id: int = 0
    source_interface: str = ""
    destination_device_id: int = 0
    destination_interface: str = ""
    protocol: str = ""
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### Data Mapping

```
NeighborInfo → DeviceNeighbor
─────────────────────────────────────────────────────
device_id (hostname)     → destination_device_id (via resolution)
local_interface          → source_interface (normalized)
remote_interface         → destination_interface (normalized)
protocol                 → protocol
(current device_id)      → source_device_id
(current timestamp)      → first_seen, last_seen
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Foreign Key Constraint Enforcement

*For any* neighbor connection with an invalid source_device_id or destination_device_id, attempting to insert it into the device_neighbors table should fail with a foreign key constraint violation.

**Validates: Requirements 1.2**

### Property 2: Unique Connection Constraint

*For any* neighbor connection, attempting to insert a duplicate connection (same source_device_id, source_interface, destination_device_id, destination_interface) should fail with a unique constraint violation.

**Validates: Requirements 1.3**

### Property 3: Neighbor Storage During Discovery

*For any* device with neighbors, when database storage is enabled and the device is successfully processed, all resolvable neighbors should be stored in the device_neighbors table.

**Validates: Requirements 2.1, 5.1**

### Property 4: Hostname Resolution

*For any* neighbor hostname, when resolving to a device_id, the system should strip domain suffixes (FQDN → short name) and query the devices table by device_name, returning the device with the most recent last_seen timestamp if multiple matches exist.

**Validates: Requirements 2.2, 6.1, 6.2, 6.4**

### Property 5: Unresolved Neighbor Handling

*For any* neighbor whose destination hostname cannot be resolved to a device_id, the system should skip storing that connection and log a warning.

**Validates: Requirements 2.3, 6.3**

### Property 6: Neighbor Upsert Behavior

*For any* neighbor connection, if it already exists in the database (matching source, source interface, destination, destination interface), the system should update the last_seen timestamp; otherwise, it should insert a new record with both first_seen and last_seen set to the current time.

**Validates: Requirements 2.4, 2.5**

### Property 7: Interface Name Normalization

*For any* interface name, the normalized version should follow platform-specific rules: IOS abbreviations expanded to full names, NX-OS formats preserved, port-channels standardized to "Port-channel", and management interfaces standardized to "Management".

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

### Property 8: Bidirectional Connection Deduplication

*For any* neighbor connection (A→B), before inserting, the system should check if the reverse connection (B→A) exists; if it does, update the existing record's last_seen instead of creating a duplicate; if it doesn't, create a new connection with consistent direction (lower device_id as source).

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 9: Bidirectional Connection Queries

*For any* device_id, querying for neighbors should return all connections where the device is either the source or the destination.

**Validates: Requirements 4.5, 5.5**

### Property 10: Error Resilience

*For any* neighbor in a list of neighbors, if storing that neighbor fails, the system should continue processing the remaining neighbors in the list.

**Validates: Requirements 5.2, 8.5**

### Property 11: Protocol Storage and Preference

*For any* neighbor connection, the protocol (CDP or LLDP) should be stored; when a connection is discovered by both protocols on a Cisco device, CDP should be preferred; when discovered multiple times, the protocol should reflect the most recent discovery.

**Validates: Requirements 7.1, 7.2, 7.3**

### Property 12: Protocol Query Filtering

*For any* protocol type (CDP or LLDP), the system should provide a method to query connections filtered by that protocol.

**Validates: Requirements 7.4**

### Property 13: Connection Query Results

*For any* connection query, the results should include source device name, source interface, destination device name, destination interface, and protocol.

**Validates: Requirements 9.1, 9.2**

### Property 14: Missing Destination Handling

*For any* connection where the destination device is not included in the current diagram scope, the Visio generator should omit that connection from the diagram.

**Validates: Requirements 9.5**

### Property 15: Stale Connection Cleanup

*For any* configurable time period in days, the system should provide a method to delete connections where last_seen is older than that period.

**Validates: Requirements 10.1, 10.2**

### Property 16: Cascade Deletion

*For any* device, when that device is deleted from the devices table, all neighbor connections where that device is the source should be automatically deleted via CASCADE constraint.

**Validates: Requirements 10.4**

## Error Handling

### Database Errors

**Connection Failures**:
- If database connection fails during neighbor storage, log error and continue discovery
- Neighbor data remains in memory for current session
- Next discovery attempt will retry database storage

**Constraint Violations**:
- Foreign key violations: Log warning with unresolved hostname, skip that neighbor
- Unique constraint violations: Should not occur due to upsert logic, but log if it does
- Transaction rollback on critical errors

**Resolution Failures**:
- Hostname not found: Log warning, add to unresolved neighbors list
- Multiple hostname matches: Use most recent last_seen, log info message
- FQDN vs short name: Strip domain and retry before failing

### Discovery Errors

**Protocol Parsing Failures**:
- CDP parse error: Log error, try LLDP if available
- LLDP parse error: Log error, use CDP if available
- Both fail: Log error, continue with zero neighbors

**Interface Normalization Failures**:
- Unknown interface format: Store as-is, log warning
- Platform detection failure: Use generic normalization rules

### Integration Errors

**Visio Generation**:
- Missing destination device: Skip connection, log info
- Invalid interface names: Use raw names from database
- Query failures: Generate diagram without connections, log error

## Testing Strategy

### Unit Testing

Unit tests will focus on specific examples and edge cases:

**Database Operations**:
- Test table creation with correct schema
- Test foreign key constraint enforcement with invalid device_ids
- Test unique constraint enforcement with duplicate connections
- Test cascade deletion when device is removed

**Hostname Resolution**:
- Test FQDN stripping (e.g., "router.example.com" → "router")
- Test multiple matches returning most recent
- Test unresolved hostname handling

**Interface Normalization**:
- Test IOS abbreviation expansion ("Gi1/0/1" → "GigabitEthernet1/0/1")
- Test NX-OS format preservation ("Ethernet1/1" → "Ethernet1/1")
- Test port-channel standardization ("Po1" → "Port-channel1")
- Test management interface standardization ("mgmt0" → "Management0")

**Deduplication**:
- Test reverse connection detection
- Test consistent direction ordering (lower device_id as source)
- Test update vs insert logic

### Property-Based Testing

Property tests will verify universal properties across randomized inputs (minimum 100 iterations per test):

**Property Test 1: Foreign Key Enforcement**
- Generate random invalid device_ids
- Verify all insertion attempts fail with foreign key violations
- **Tag**: Feature: cdp-lldp-neighbor-discovery, Property 1: Foreign key constraint enforcement

**Property Test 2: Unique Constraint Enforcement**
- Generate random valid connections
- Insert each connection twice
- Verify second insertion fails with unique constraint violation
- **Tag**: Feature: cdp-lldp-neighbor-discovery, Property 2: Unique connection constraint

**Property Test 3: Neighbor Storage Completeness**
- Generate random devices with random neighbor lists
- Process each device
- Verify all resolvable neighbors are in database
- **Tag**: Feature: cdp-lldp-neighbor-discovery, Property 3: Neighbor storage during discovery

**Property Test 4: Hostname Resolution Consistency**
- Generate random hostnames (some FQDN, some short)
- Resolve each hostname
- Verify FQDN and short name resolve to same device_id
- **Tag**: Feature: cdp-lldp-neighbor-discovery, Property 4: Hostname resolution

**Property Test 5: Unresolved Neighbor Handling**
- Generate random neighbors with non-existent hostnames
- Attempt to store each neighbor
- Verify none are stored and warnings are logged
- **Tag**: Feature: cdp-lldp-neighbor-discovery, Property 5: Unresolved neighbor handling

**Property Test 6: Upsert Behavior**
- Generate random connections
- Insert each connection, then insert again
- Verify first creates record, second updates last_seen
- **Tag**: Feature: cdp-lldp-neighbor-discovery, Property 6: Neighbor upsert behavior

**Property Test 7: Interface Normalization**
- Generate random interface names with various formats
- Normalize each interface name
- Verify normalization follows platform-specific rules
- **Tag**: Feature: cdp-lldp-neighbor-discovery, Property 7: Interface name normalization

**Property Test 8: Bidirectional Deduplication**
- Generate random connections
- Insert connection A→B, then attempt B→A
- Verify only one record exists with consistent direction
- **Tag**: Feature: cdp-lldp-neighbor-discovery, Property 8: Bidirectional connection deduplication

**Property Test 9: Bidirectional Queries**
- Generate random devices with connections in both directions
- Query neighbors for each device
- Verify results include connections where device is source or destination
- **Tag**: Feature: cdp-lldp-neighbor-discovery, Property 9: Bidirectional connection queries

**Property Test 10: Error Resilience**
- Generate random neighbor lists with some invalid entries
- Process each list
- Verify valid neighbors are stored despite invalid ones
- **Tag**: Feature: cdp-lldp-neighbor-discovery, Property 10: Error resilience

**Property Test 11: Protocol Storage**
- Generate random connections with various protocols
- Store each connection
- Verify protocol is correctly stored and queryable
- **Tag**: Feature: cdp-lldp-neighbor-discovery, Property 11: Protocol storage and preference

**Property Test 12: Protocol Filtering**
- Generate random connections with mixed protocols
- Query by each protocol type
- Verify results contain only connections with that protocol
- **Tag**: Feature: cdp-lldp-neighbor-discovery, Property 12: Protocol query filtering

**Property Test 13: Query Result Completeness**
- Generate random connections
- Query each connection
- Verify all required fields are present in results
- **Tag**: Feature: cdp-lldp-neighbor-discovery, Property 13: Connection query results

**Property Test 14: Stale Connection Cleanup**
- Generate random connections with various last_seen timestamps
- Run cleanup with random day thresholds
- Verify only connections older than threshold are deleted
- **Tag**: Feature: cdp-lldp-neighbor-discovery, Property 15: Stale connection cleanup

**Property Test 15: Cascade Deletion**
- Generate random devices with connections
- Delete random devices
- Verify their source connections are automatically deleted
- **Tag**: Feature: cdp-lldp-neighbor-discovery, Property 16: Cascade deletion

### Integration Testing

Integration tests will verify end-to-end workflows:

**Discovery Integration**:
- Run full discovery on test network
- Verify neighbors are collected and stored
- Verify database contains expected connections

**Visio Integration**:
- Generate Visio diagram from database
- Verify connections are drawn between devices
- Verify interface labels are correct

**Database Integration**:
- Test with real SQL Server database
- Verify schema creation
- Verify data persistence across sessions

### Test Configuration

All property-based tests will be configured to run a minimum of 100 iterations to ensure comprehensive coverage through randomization. This is critical because property-based testing relies on generating many random inputs to find edge cases that might not be covered by example-based unit tests.

