# NetWalker Database Schema Documentation

## Overview

NetWalker uses a Microsoft SQL Server database to store network discovery data, device inventory, topology connections, and IPv4 prefix information. The database schema is designed to track devices over time, maintain historical data, and support complex network topology queries.

**Database Name**: `NetWalker` (configurable)  
**Database Type**: Microsoft SQL Server  
**Schema Version**: 1.1.1  
**Last Updated**: 2026-02-24

---

## Connection Information

### Configuration
Database connection settings are stored in `netwalker.ini`:

```ini
[database]
enabled = true
server = your-sql-server.domain.com
port = 1433
database = NetWalker
username = NetWalker
password = ENC:base64encodedpassword
trust_server_certificate = true
connection_timeout = 30
command_timeout = 60
```

### Credentials
- Passwords can be stored encrypted with `ENC:` prefix
- Base64 encoding is used for password encryption
- Use `ConfigurationManager` class to decrypt passwords

---

## Database Tables

### Core Tables
1. [devices](#1-devices-table) - Main device inventory
2. [device_versions](#2-device_versions-table) - Software versions
3. [device_interfaces](#3-device_interfaces-table) - Network interfaces and IP addresses
4. [device_stack_members](#4-device_stack_members-table) - Switch stack member details
5. [device_neighbors](#5-device_neighbors-table) - Network topology connections
6. [vlans](#6-vlans-table) - VLAN definitions
7. [device_vlans](#7-device_vlans-table) - Device-to-VLAN mappings

### IPv4 Prefix Inventory Tables
8. [ipv4_prefixes](#8-ipv4_prefixes-table) - IPv4 routing prefixes
9. [ipv4_prefix_summarization](#9-ipv4_prefix_summarization-table) - Route summarization relationships

---

## Table Definitions

### 1. devices Table

**Purpose**: Main device inventory table storing discovered network devices.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `device_id` | INT | PRIMARY KEY, IDENTITY(1,1) | Unique device identifier |
| `device_name` | NVARCHAR(255) | NOT NULL | Device hostname |
| `serial_number` | NVARCHAR(100) | NOT NULL | Device serial number |
| `platform` | NVARCHAR(100) | NULL | Device platform (e.g., "Cisco IOS-XE", "SG300", "Aruba AP") |
| `hardware_model` | NVARCHAR(100) | NULL | Hardware model (e.g., "C9300-48P", "SG300-20 SRW2016-K9") |
| `capabilities` | NVARCHAR(500) | NULL | Comma-separated capabilities (e.g., "Router,Switch,IGMP") |
| `connection_failures` | INT | NOT NULL, DEFAULT 0 | Count of consecutive connection failures |
| `first_seen` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | First discovery timestamp |
| `last_seen` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Last seen timestamp |
| `status` | NVARCHAR(20) | NOT NULL, DEFAULT 'active' | Device status ('active', 'inactive', 'purge') |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record creation timestamp |
| `updated_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record last update timestamp |

**Constraints**:
- `UQ_device_name_serial`: UNIQUE constraint on (device_name, serial_number)

**Indexes**:
- `IX_devices_status`: Index on status column
- `IX_devices_last_seen`: Index on last_seen column

**Notes**:
- Devices discovered via CDP/LLDP but not walked are created as "Unwalked Neighbors"
- `serial_number` may be 'unknown' for unwalked devices
- `status='purge'` marks devices for deletion
- Platform values are normalized (e.g., "SG300" not "Cisco SG300")

---

### 2. device_versions Table

**Purpose**: Tracks software versions for devices over time.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `version_id` | INT | PRIMARY KEY, IDENTITY(1,1) | Unique version record identifier |
| `device_id` | INT | NOT NULL, FOREIGN KEY | Reference to devices table |
| `software_version` | NVARCHAR(100) | NOT NULL | Software version string |
| `first_seen` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | First time this version was seen |
| `last_seen` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Last time this version was seen |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record creation timestamp |
| `updated_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record last update timestamp |

**Constraints**:
- `FK_device_versions_device`: FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
- `UQ_device_version`: UNIQUE constraint on (device_id, software_version)

**Indexes**:
- `IX_device_versions_last_seen`: Index on last_seen column

**Notes**:
- Supports tracking version changes over time
- Multiple versions can exist per device (historical tracking)
- Most recent version determined by `last_seen` timestamp

---

### 3. device_interfaces Table

**Purpose**: Stores network interface information and IP addresses.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `interface_id` | INT | PRIMARY KEY, IDENTITY(1,1) | Unique interface identifier |
| `device_id` | INT | NOT NULL, FOREIGN KEY | Reference to devices table |
| `interface_name` | NVARCHAR(100) | NOT NULL | Interface name (e.g., "GigabitEthernet1/0/1") |
| `ip_address` | NVARCHAR(50) | NOT NULL | IP address assigned to interface |
| `subnet_mask` | NVARCHAR(50) | NULL | Subnet mask or prefix length |
| `interface_type` | NVARCHAR(50) | NULL | Interface type (e.g., "Management", "Loopback") |
| `first_seen` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | First discovery timestamp |
| `last_seen` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Last seen timestamp |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record creation timestamp |
| `updated_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record last update timestamp |

**Constraints**:
- `FK_device_interfaces_device`: FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
- `UQ_device_interface_ip`: UNIQUE constraint on (device_id, interface_name, ip_address)

**Indexes**:
- `IX_device_interfaces_ip`: Index on ip_address column
- `IX_device_interfaces_type`: Index on interface_type column

**Notes**:
- Multiple interfaces per device supported
- IP addresses stored as strings (supports IPv4 and IPv6)
- Interface names normalized (e.g., "Gi1/0/1" → "GigabitEthernet1/0/1")

---

### 4. device_stack_members Table

**Purpose**: Stores individual switch stack member details for StackWise and VSS configurations.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `stack_member_id` | INT | PRIMARY KEY, IDENTITY(1,1) | Unique stack member identifier |
| `device_id` | INT | NOT NULL, FOREIGN KEY | Reference to parent stack device |
| `switch_number` | INT | NOT NULL | Switch number in stack (1, 2, 3, etc.) |
| `role` | NVARCHAR(20) | NULL | Stack role ("Active", "Standby", "Member", "Master") |
| `priority` | INT | NULL | Stack priority value (StackWise only) |
| `hardware_model` | NVARCHAR(100) | NULL | Hardware model of this member |
| `serial_number` | NVARCHAR(100) | NOT NULL | Serial number of this member |
| `mac_address` | NVARCHAR(20) | NULL | Base MAC address |
| `software_version` | NVARCHAR(100) | NULL | Software version (if different from stack) |
| `state` | NVARCHAR(20) | NULL | Operational state ("Ready", "Provisioned", etc.) |
| `first_seen` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | First discovery timestamp |
| `last_seen` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Last seen timestamp |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record creation timestamp |
| `updated_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record last update timestamp |

**Constraints**:
- `FK_stack_members_device`: FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
- `UQ_device_switch_serial`: UNIQUE constraint on (device_id, switch_number, serial_number)

**Indexes**:
- `IX_stack_members_device`: Index on device_id column
- `IX_stack_members_serial`: Index on serial_number column
- `IX_stack_members_role`: Index on role column

**Notes**:
- Supports Cisco StackWise (Catalyst 9000, 3850, 3650 series)
- Supports Cisco VSS (Catalyst 4500-X, 6500 series)
- Network modules (models containing "-NM-") are filtered out
- Each stack member has unique serial number

---

### 5. device_neighbors Table

**Purpose**: Stores network topology connections discovered via CDP and LLDP.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `neighbor_id` | INT | PRIMARY KEY, IDENTITY(1,1) | Unique neighbor connection identifier |
| `source_device_id` | INT | NOT NULL, FOREIGN KEY | Source device (discovered from) |
| `source_interface` | NVARCHAR(100) | NOT NULL | Source interface name |
| `destination_device_id` | INT | NOT NULL, FOREIGN KEY | Destination device (neighbor) |
| `destination_interface` | NVARCHAR(100) | NOT NULL | Destination interface name |
| `protocol` | NVARCHAR(10) | NOT NULL | Discovery protocol ("CDP" or "LLDP") |
| `first_seen` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | First discovery timestamp |
| `last_seen` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Last seen timestamp |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record creation timestamp |
| `updated_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record last update timestamp |

**Constraints**:
- `FK_neighbor_source`: FOREIGN KEY (source_device_id) REFERENCES devices(device_id) ON DELETE CASCADE
- `FK_neighbor_destination`: FOREIGN KEY (destination_device_id) REFERENCES devices(device_id) ON DELETE NO ACTION
- `UQ_neighbor_connection`: UNIQUE constraint on (source_device_id, source_interface, destination_device_id, destination_interface)

**Indexes**:
- `IX_neighbors_source`: Index on source_device_id column
- `IX_neighbors_destination`: Index on destination_device_id column
- `IX_neighbors_last_seen`: Index on last_seen column
- `IX_neighbors_protocol`: Index on protocol column

**Notes**:
- Represents directed connections (A → B)
- Bidirectional connections stored as two records (A → B and B → A)
- Interface names normalized for consistency
- Used for topology diagram generation

---

### 6. vlans Table

**Purpose**: Global VLAN definitions discovered across the network.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `vlan_id` | INT | PRIMARY KEY, IDENTITY(1,1) | Unique VLAN identifier |
| `vlan_number` | INT | NOT NULL | VLAN number (1-4094) |
| `vlan_name` | NVARCHAR(255) | NOT NULL | VLAN name |
| `first_seen` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | First discovery timestamp |
| `last_seen` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Last seen timestamp |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record creation timestamp |
| `updated_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record last update timestamp |

**Constraints**:
- `UQ_vlan_number_name`: UNIQUE constraint on (vlan_number, vlan_name)
- `CHK_vlan_number`: CHECK constraint (vlan_number BETWEEN 1 AND 4094)

**Indexes**:
- `IX_vlans_number`: Index on vlan_number column
- `IX_vlans_last_seen`: Index on last_seen column

**Notes**:
- Global VLAN registry (not device-specific)
- Same VLAN number can have different names (tracked separately)
- Standard VLAN range enforced (1-4094)

---

### 7. device_vlans Table

**Purpose**: Maps VLANs to specific devices with port count information.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `device_vlan_id` | INT | PRIMARY KEY, IDENTITY(1,1) | Unique device-VLAN mapping identifier |
| `device_id` | INT | NOT NULL, FOREIGN KEY | Reference to devices table |
| `vlan_id` | INT | NOT NULL, FOREIGN KEY | Reference to vlans table |
| `vlan_number` | INT | NOT NULL | VLAN number (denormalized for performance) |
| `vlan_name` | NVARCHAR(255) | NOT NULL | VLAN name (denormalized for performance) |
| `port_count` | INT | NULL, DEFAULT 0 | Number of ports in this VLAN |
| `first_seen` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | First discovery timestamp |
| `last_seen` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Last seen timestamp |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record creation timestamp |
| `updated_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record last update timestamp |

**Constraints**:
- `FK_device_vlans_device`: FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
- `FK_device_vlans_vlan`: FOREIGN KEY (vlan_id) REFERENCES vlans(vlan_id) ON DELETE CASCADE
- `UQ_device_vlan`: UNIQUE constraint on (device_id, vlan_id)

**Indexes**:
- `IX_device_vlans_number`: Index on vlan_number column

**Notes**:
- Links devices to VLANs they participate in
- Port count indicates number of interfaces in VLAN
- Denormalized vlan_number and vlan_name for query performance

---

### 8. ipv4_prefixes Table

**Purpose**: Stores IPv4 routing prefixes collected from device routing tables.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `prefix_id` | INT | PRIMARY KEY, IDENTITY(1,1) | Unique prefix identifier |
| `device_id` | INT | NOT NULL, FOREIGN KEY | Reference to devices table |
| `vrf` | NVARCHAR(100) | NOT NULL | VRF name ("global" for default routing table) |
| `prefix` | NVARCHAR(50) | NOT NULL | IPv4 prefix in CIDR notation (e.g., "10.1.0.0/16") |
| `source` | NVARCHAR(20) | NOT NULL | Prefix source ("routing_table", "bgp", "connected") |
| `protocol` | NVARCHAR(10) | NULL | Routing protocol (e.g., "EIGRP", "OSPF", "BGP", "static") |
| `vlan` | INT | NULL | Associated VLAN number (for connected routes) |
| `interface` | NVARCHAR(100) | NULL | Associated interface (for connected routes) |
| `first_seen` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | First discovery timestamp |
| `last_seen` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Last seen timestamp |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record creation timestamp |
| `updated_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record last update timestamp |

**Constraints**:
- `FK_ipv4_prefixes_device`: FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
- `UQ_device_vrf_prefix_source`: UNIQUE constraint on (device_id, vrf, prefix, source)

**Indexes**:
- `IX_ipv4_prefixes_vrf`: Index on vrf column
- `IX_ipv4_prefixes_prefix`: Index on prefix column
- `IX_ipv4_prefixes_source`: Index on source column
- `IX_ipv4_prefixes_last_seen`: Index on last_seen column

**Notes**:
- Supports multi-VRF environments
- Prefixes normalized to CIDR notation
- Source indicates where prefix was discovered
- Protocol indicates routing protocol (if applicable)

---

### 9. ipv4_prefix_summarization Table

**Purpose**: Tracks route summarization relationships between summary and component prefixes.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `summarization_id` | INT | PRIMARY KEY, IDENTITY(1,1) | Unique summarization relationship identifier |
| `summary_prefix_id` | INT | NOT NULL, FOREIGN KEY | Reference to summary prefix in ipv4_prefixes |
| `component_prefix_id` | INT | NOT NULL, FOREIGN KEY | Reference to component prefix in ipv4_prefixes |
| `device_id` | INT | NOT NULL, FOREIGN KEY | Reference to devices table |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record creation timestamp |

**Constraints**:
- `FK_summarization_summary`: FOREIGN KEY (summary_prefix_id) REFERENCES ipv4_prefixes(prefix_id) ON DELETE CASCADE
- `FK_summarization_component`: FOREIGN KEY (component_prefix_id) REFERENCES ipv4_prefixes(prefix_id) ON DELETE NO ACTION
- `FK_summarization_device`: FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE NO ACTION
- `UQ_summarization_relationship`: UNIQUE constraint on (summary_prefix_id, component_prefix_id, device_id)

**Indexes**:
- `IX_summarization_summary`: Index on summary_prefix_id column
- `IX_summarization_component`: Index on component_prefix_id column
- `IX_summarization_device`: Index on device_id column

**Notes**:
- Tracks which prefixes are summarized by which summary routes
- Example: 10.1.0.0/24 and 10.1.1.0/24 summarized by 10.1.0.0/16
- Used for route optimization analysis

---

## Entity Relationships

```
devices (1) ──< (M) device_versions
devices (1) ──< (M) device_interfaces
devices (1) ──< (M) device_stack_members
devices (1) ──< (M) device_vlans ──> (1) vlans
devices (1) ──< (M) device_neighbors >── (1) devices
devices (1) ──< (M) ipv4_prefixes
ipv4_prefixes (1) ──< (M) ipv4_prefix_summarization >── (1) ipv4_prefixes
```

**Key Relationships**:
- One device can have multiple versions (historical tracking)
- One device can have multiple interfaces
- One device can have multiple stack members (for stacks)
- One device can participate in multiple VLANs
- One device can have multiple neighbor connections
- One device can have multiple IPv4 prefixes
- One prefix can summarize multiple component prefixes

---

## Common Queries

### Get All Active Devices with Latest Version
```sql
SELECT 
    d.device_name,
    d.platform,
    d.hardware_model,
    d.serial_number,
    dv.software_version,
    di.ip_address
FROM devices d
LEFT JOIN (
    SELECT device_id, software_version,
           ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY last_seen DESC) as rn
    FROM device_versions
) dv ON d.device_id = dv.device_id AND dv.rn = 1
LEFT JOIN (
    SELECT device_id, ip_address,
           ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY last_seen DESC) as rn
    FROM device_interfaces
) di ON d.device_id = di.device_id AND di.rn = 1
WHERE d.status = 'active'
ORDER BY d.device_name;
```

### Get Device Topology Connections
```sql
SELECT 
    sd.device_name as source_device,
    dn.source_interface,
    dd.device_name as destination_device,
    dn.destination_interface,
    dn.protocol
FROM device_neighbors dn
INNER JOIN devices sd ON dn.source_device_id = sd.device_id
INNER JOIN devices dd ON dn.destination_device_id = dd.device_id
WHERE sd.device_name = 'YOUR-DEVICE-NAME'
ORDER BY dn.source_interface;
```

### Get Stack Member Details
```sql
SELECT 
    d.device_name,
    sm.switch_number,
    sm.role,
    sm.hardware_model,
    sm.serial_number,
    sm.state
FROM device_stack_members sm
INNER JOIN devices d ON sm.device_id = d.device_id
WHERE d.device_name = 'YOUR-STACK-NAME'
ORDER BY sm.switch_number;
```

### Get Devices Not Walked in X Days
```sql
SELECT 
    device_name,
    last_seen,
    DATEDIFF(day, last_seen, GETDATE()) as days_since_seen
FROM devices
WHERE status = 'active'
  AND DATEDIFF(day, last_seen, GETDATE()) > 30
ORDER BY last_seen;
```

### Get Unwalked Neighbors
```sql
SELECT 
    d.device_name,
    d.platform,
    d.hardware_model,
    d.serial_number
FROM devices d
WHERE d.serial_number = 'unknown'
  AND d.status = 'active'
ORDER BY d.device_name;
```

### Get IPv4 Prefixes by VRF
```sql
SELECT 
    d.device_name,
    p.vrf,
    p.prefix,
    p.source,
    p.protocol
FROM ipv4_prefixes p
INNER JOIN devices d ON p.device_id = d.device_id
WHERE p.vrf = 'global'
ORDER BY d.device_name, p.prefix;
```

---

## Database Initialization

### Using NetWalker Executable
```powershell
# Initialize database schema
.\netwalker.exe --db-init

# Check database status
.\netwalker.exe --db-status

# Purge all data (requires confirmation)
.\netwalker.exe --db-purge

# Delete devices marked for purge
.\netwalker.exe --db-purge-devices
```

### Using Python
```python
from netwalker.config.config_manager import ConfigurationManager
from netwalker.database import DatabaseManager

# Load configuration
config_manager = ConfigurationManager('netwalker.ini')
config = config_manager.load_configuration()

# Initialize database manager
db_manager = DatabaseManager(config['database'])

# Initialize schema
if db_manager.initialize_database():
    print("Database initialized successfully")

# Initialize IPv4 prefix schema
if db_manager.initialize_ipv4_prefix_schema():
    print("IPv4 prefix schema initialized successfully")
```

---

## Data Retention and Cleanup

### Automatic Cleanup
- No automatic cleanup is performed
- Historical data is retained indefinitely
- Use `status='purge'` to mark devices for deletion

### Manual Cleanup
```sql
-- Mark old devices for purge (not seen in 90 days)
UPDATE devices
SET status = 'purge'
WHERE DATEDIFF(day, last_seen, GETDATE()) > 90;

-- Delete marked devices
DELETE FROM devices WHERE status = 'purge';
```

### Purge Using NetWalker
```powershell
# Mark devices for purge in database, then run:
.\netwalker.exe --db-purge-devices
```

---

## Performance Considerations

### Indexes
- All foreign keys have indexes for join performance
- `last_seen` columns indexed for temporal queries
- `status` column indexed for filtering active devices
- `ip_address` indexed for IP-based lookups

### Query Optimization
- Use `ROW_NUMBER()` for latest version/interface queries
- Filter by `status='active'` to exclude purged devices
- Use indexed columns in WHERE clauses
- Consider denormalized columns (vlan_number, vlan_name) for performance

### Maintenance
```sql
-- Update statistics
UPDATE STATISTICS devices;
UPDATE STATISTICS device_neighbors;

-- Rebuild indexes
ALTER INDEX ALL ON devices REBUILD;
ALTER INDEX ALL ON device_neighbors REBUILD;
```

---

## Security Considerations

### Database Access
- Use dedicated SQL Server login for NetWalker
- Grant minimum required permissions (SELECT, INSERT, UPDATE, DELETE)
- Encrypt passwords in configuration files
- Use TrustServerCertificate for self-signed certificates

### Sensitive Data
- Device credentials are NOT stored in database
- Configuration files may contain encrypted passwords
- Serial numbers and hardware details are stored (consider compliance requirements)

### Recommended Permissions
```sql
-- Create login
CREATE LOGIN NetWalker WITH PASSWORD = 'StrongPassword123!';

-- Create user in NetWalker database
USE NetWalker;
CREATE USER NetWalker FOR LOGIN NetWalker;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO NetWalker;
```

---

## Backup and Recovery

### Backup Strategy
```sql
-- Full backup
BACKUP DATABASE NetWalker
TO DISK = 'C:\Backups\NetWalker_Full.bak'
WITH FORMAT, COMPRESSION;

-- Differential backup
BACKUP DATABASE NetWalker
TO DISK = 'C:\Backups\NetWalker_Diff.bak'
WITH DIFFERENTIAL, COMPRESSION;
```

### Recovery
```sql
-- Restore full backup
RESTORE DATABASE NetWalker
FROM DISK = 'C:\Backups\NetWalker_Full.bak'
WITH REPLACE, RECOVERY;
```

---

## Migration and Upgrades

### Schema Version Tracking
- Schema version tracked in README and this document
- No automated migration scripts currently
- Manual schema updates via `ALTER TABLE` statements

### Adding New Columns
```sql
-- Example: Add new column to devices table
IF NOT EXISTS (SELECT * FROM sys.columns
              WHERE object_id = OBJECT_ID('devices')
              AND name = 'new_column')
BEGIN
    ALTER TABLE devices ADD new_column NVARCHAR(100) NULL;
END
```

---

## Troubleshooting

### Connection Issues
```
Error: Database connection failed
```
**Solutions**:
- Verify SQL Server is running
- Check server name and port in configuration
- Verify credentials are correct
- Check firewall rules allow port 1433
- Verify TrustServerCertificate setting

### Schema Issues
```
Error: Invalid object name 'devices'
```
**Solutions**:
- Run `netwalker.exe --db-init` to create schema
- Verify connected to correct database
- Check user has permissions to create tables

### Performance Issues
```
Queries running slowly
```
**Solutions**:
- Update statistics: `UPDATE STATISTICS devices;`
- Rebuild indexes: `ALTER INDEX ALL ON devices REBUILD;`
- Check for missing indexes in execution plans
- Consider archiving old data

---

## Future Enhancements

### Planned Features
- Automated schema migration scripts
- Data archiving and retention policies
- Additional indexes for common query patterns
- Audit logging for data changes
- Support for additional database platforms (PostgreSQL, MySQL)

### Web UI Integration
- RESTful API for database access
- Real-time topology visualization
- Historical trend analysis
- Custom report generation
- Device search and filtering

---

## Contact and Support

**Author**: Mark Oldham  
**GitHub**: [https://github.com/MarkTegna/NetWalker](https://github.com/MarkTegna/NetWalker)  
**Version**: 1.1.1  
**Last Updated**: 2026-02-24
