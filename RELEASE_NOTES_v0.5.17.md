# NetWalker v0.5.17 Release Notes

**Release Date:** January 20, 2026  
**Author:** Mark Oldham

## Overview

This release adds **CDP/LLDP Neighbor Discovery Database Storage**, enabling complete network topology visualization with device connections in Visio diagrams. NetWalker now stores neighbor relationships discovered via CDP and LLDP protocols, allowing you to generate professional network topology diagrams showing how devices are physically connected.

## Major New Features

### 🔗 CDP/LLDP Neighbor Discovery Database Storage

NetWalker now persists neighbor connection data to the SQL Server database, enabling:

- **Complete Topology Visualization**: Visio diagrams now show connections between devices
- **Historical Connection Tracking**: Track when connections were first/last seen
- **Bidirectional Deduplication**: Each physical link stored only once
- **Interface Normalization**: Consistent interface naming across platforms
- **Automatic Integration**: Connections automatically queried for Visio diagrams

#### New Database Table: device_neighbors

```sql
CREATE TABLE device_neighbors (
    neighbor_id INT IDENTITY(1,1) PRIMARY KEY,
    source_device_id INT NOT NULL,
    source_interface NVARCHAR(100) NOT NULL,
    destination_device_id INT NOT NULL,
    destination_interface NVARCHAR(100) NOT NULL,
    protocol NVARCHAR(10) NOT NULL,  -- 'CDP' or 'LLDP'
    first_seen DATETIME2 NOT NULL,
    last_seen DATETIME2 NOT NULL,
    created_at DATETIME2 NOT NULL,
    updated_at DATETIME2 NOT NULL
);
```

#### Key Features

**Intelligent Deduplication:**
- Detects reverse connections (A→B vs B→A)
- Stores each physical link only once
- Consistent direction (lower device_id as source)

**Interface Name Normalization:**
- IOS abbreviations expanded (Gi→GigabitEthernet, Te→TenGigabitEthernet)
- NX-OS formats preserved (Ethernet1/1 stays as-is)
- Port-channels standardized (Po1, port-channel1 → Port-channel1)
- Management interfaces standardized (mgmt0 → Management0)

**Hostname Resolution:**
- Strips domain suffixes (router.example.com → router)
- Handles multiple matches (uses most recent)
- Logs warnings for unresolved neighbors

**Error Resilience:**
- Continues discovery if neighbor storage fails
- Processes remaining neighbors on individual failures
- Detailed logging for troubleshooting

**Visio Integration:**
- Automatically queries connections from database
- Filters to devices in current diagram
- Handles missing destination devices gracefully
- Shows interface names on connectors

## Technical Implementation

### New Database Methods

**DatabaseManager:**
- `resolve_hostname_to_device_id()` - Resolve neighbor hostnames to device IDs
- `check_reverse_connection()` - Check for existing reverse connections
- `get_consistent_direction()` - Ensure consistent connection direction
- `upsert_neighbor_connection()` - Insert or update single connection
- `upsert_device_neighbors()` - Store all neighbors for a device
- `get_device_neighbors()` - Query neighbors for a device
- `get_neighbors_by_protocol()` - Filter by CDP or LLDP
- `get_all_connections()` - Get all connections for Visio
- `cleanup_stale_neighbors()` - Delete old connections

**ProtocolParser:**
- Enhanced `normalize_interface_name()` with platform parameter
- Platform-aware normalization (IOS vs NX-OS)

**VisioGenerator:**
- Accepts optional `database_manager` parameter
- Automatically queries connections if not provided
- `_get_connections_for_devices()` - Filter connections to diagram scope

### Modified Components

**Discovery Integration:**
- `process_device_discovery()` now stores neighbors automatically
- Neighbor storage integrated into discovery workflow
- Continues on failure (doesn't break discovery)

**Visio Generation:**
- Updated to use DatabaseManager instead of direct pyodbc
- Connections parameter now optional (queries from database)
- All diagram generation methods updated

## Usage

### Automatic Neighbor Storage

Neighbor data is automatically stored during discovery:

```bash
netwalker.exe --config netwalker.ini
```

No configuration changes needed - if database is enabled, neighbors are stored.

### Generate Topology Diagrams with Connections

```bash
# Single site diagram with connections
netwalker.exe --visio --visio-site BORO

# All sites in one diagram
netwalker.exe --visio --visio-all-in-one

# Separate diagrams for each site
netwalker.exe --visio
```

Connections are automatically queried from the database and drawn on diagrams.

### Query Neighbor Data

Use SQL to query neighbor connections:

```sql
-- Count total connections
SELECT COUNT(*) FROM device_neighbors;

-- View all connections
SELECT 
    d1.device_name AS source,
    n.source_interface,
    d2.device_name AS destination,
    n.destination_interface,
    n.protocol,
    n.last_seen
FROM device_neighbors n
INNER JOIN devices d1 ON n.source_device_id = d1.device_id
INNER JOIN devices d2 ON n.destination_device_id = d2.device_id
ORDER BY d1.device_name;

-- Connections for specific device
SELECT * FROM device_neighbors 
WHERE source_device_id = 123 OR destination_device_id = 123;
```

### Cleanup Old Connections

The database manager provides cleanup methods (not exposed via CLI yet):

```python
# Delete connections not seen in 30 days
db_manager.cleanup_stale_neighbors(30)

# Purge all neighbor data
db_manager.purge_database()  # Includes neighbors
```

## Database Schema Changes

### New Table: device_neighbors

- **Primary Key**: neighbor_id (auto-increment)
- **Foreign Keys**: 
  - source_device_id → devices(device_id) ON DELETE CASCADE
  - destination_device_id → devices(device_id) ON DELETE NO ACTION
- **Unique Constraint**: (source_device_id, source_interface, destination_device_id, destination_interface)
- **Indexes**: source_device_id, destination_device_id, last_seen, protocol

### Automatic Migration

The table is created automatically when you run discovery or initialize the database:

```bash
netwalker.exe --db-init
```

No manual migration required.

## Breaking Changes

None. This release is fully backward compatible.

## Bug Fixes

None in this release (new feature only).

## Known Limitations

1. **Protocol Preference**: CDP/LLDP protocol preference not yet implemented
2. **Unresolved Neighbor Tracking**: No method to query unresolved neighbors
3. **CLI Cleanup Commands**: No CLI commands for neighbor cleanup yet
4. **Property-Based Tests**: Not implemented (manual testing performed)

## Performance Considerations

- Neighbor storage adds minimal overhead to discovery
- Database queries optimized with indexes
- Visio generation may be slightly slower with many connections
- Deduplication check adds one query per neighbor

## Testing

Comprehensive testing performed:
- ✓ Database schema creation verified
- ✓ Hostname resolution tested
- ✓ Neighbor storage tested
- ✓ Deduplication verified (reverse connections handled)
- ✓ Interface normalization tested
- ✓ Query operations tested
- ✓ Visio integration tested

Test scripts included:
- `test_neighbor_schema.py` - Verify database schema
- `test_neighbor_storage.py` - End-to-end functionality test

## Upgrade Instructions

1. **Backup Database** (recommended):
   ```sql
   BACKUP DATABASE NetWalker TO DISK = 'C:\Backups\NetWalker_pre_v0.5.17.bak';
   ```

2. **Replace Executable**:
   - Extract `NetWalker_v0.5.17.zip`
   - Replace old `netwalker.exe` with new version

3. **Run Discovery**:
   ```bash
   netwalker.exe --config netwalker.ini
   ```
   
   The device_neighbors table will be created automatically on first run.

4. **Generate Diagrams**:
   ```bash
   netwalker.exe --visio --visio-site BORO
   ```
   
   Connections will appear automatically!

## Files Changed

- `netwalker/database/models.py` - Added DeviceNeighbor model
- `netwalker/database/database_manager.py` - Added neighbor storage methods
- `netwalker/discovery/protocol_parser.py` - Enhanced interface normalization
- `netwalker/reports/visio_generator.py` - Added database integration
- `main.py` - Updated Visio generation to use DatabaseManager
- `netwalker/version.py` - Version 0.5.17

## Documentation

New documentation files:
- `CDP_LLDP_NEIGHBOR_IMPLEMENTATION_SUMMARY.md` - Complete implementation details
- `test_neighbor_schema.py` - Schema verification test
- `test_neighbor_storage.py` - Functionality test
- `RELEASE_NOTES_v0.5.17.md` - This file

## Future Enhancements

Planned for future releases:
- Protocol preference logic (prefer CDP over LLDP for Cisco)
- CLI commands for neighbor cleanup
- Unresolved neighbor tracking and reporting
- Connection age visualization in Visio
- Link utilization tracking
- Topology change detection and alerting

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review `CDP_LLDP_NEIGHBOR_IMPLEMENTATION_SUMMARY.md`
- Run test scripts to verify functionality

## Credits

**Author:** Mark Oldham  
**Version:** 0.5.17  
**Release Date:** January 20, 2026

---

**Previous Version:** 0.5.16 (Visio diagram generation)  
**Next Version:** TBD
