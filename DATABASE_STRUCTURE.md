# NetWalker Inventory Database Structure

**Version:** 1.0  
**Last Updated:** January 14, 2026  
**Author:** Mark Oldham

## Overview

The NetWalker Inventory Database provides persistent storage for network device discovery data, tracking device history, software versions, interfaces, and VLAN configurations over time.

## Database Connection

- **Server:** eit-prisqldb01.tgna.tegna.com
- **Port:** 1433
- **Database:** NetWalker (auto-created if not exists)
- **Username:** NetWalker
- **Authentication:** SQL Server Authentication

## Design Principles

1. **Extensibility:** Schema designed to accommodate future data types
2. **Historical Tracking:** All changes tracked with timestamps
3. **Data Integrity:** Foreign key constraints maintain referential integrity
4. **Uniqueness:** Composite keys prevent duplicate entries
5. **Soft Deletes:** Status-based deletion for audit trail

## Database Schema

### Table: devices

Primary table tracking all discovered network devices.

**Purpose:** Store device identity and lifecycle information

**Key:** `device_name` + `serial_number` (composite primary key)

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| device_id | INT | PRIMARY KEY, IDENTITY | Auto-incrementing unique identifier |
| device_name | NVARCHAR(255) | NOT NULL | Device hostname |
| serial_number | NVARCHAR(100) | NOT NULL | Device serial number |
| platform | NVARCHAR(100) | NULL | Device platform (IOS, IOS-XE, NX-OS, etc.) |
| hardware_model | NVARCHAR(100) | NULL | Hardware model number |
| first_seen | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Date device first discovered |
| last_seen | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Date device last seen in discovery |
| status | NVARCHAR(20) | NOT NULL, DEFAULT 'active' | Device status: 'active', 'purge' |
| created_at | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record creation timestamp |
| updated_at | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record last update timestamp |

**Indexes:**
- PRIMARY KEY: `device_id`
- UNIQUE INDEX: `device_name` + `serial_number`
- INDEX: `status` (for purge queries)
- INDEX: `last_seen` (for reporting)

**Business Rules:**
- If `device_name` exists but `serial_number` changes → New device (hardware replacement)
- If `status` = 'purge' → Device marked for deletion by external process
- `last_seen` updated on every discovery where device is found
- `first_seen` never changes after initial creation

---

### Table: device_versions

Tracks software versions seen on each device over time.

**Purpose:** Historical record of software versions and changes

**Key:** `device_id` + `software_version`

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| version_id | INT | PRIMARY KEY, IDENTITY | Auto-incrementing unique identifier |
| device_id | INT | NOT NULL, FOREIGN KEY → devices(device_id) | Reference to parent device |
| software_version | NVARCHAR(100) | NOT NULL | Software version string |
| first_seen | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Date version first seen on device |
| last_seen | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Date version last seen on device |
| created_at | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record creation timestamp |
| updated_at | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record last update timestamp |

**Indexes:**
- PRIMARY KEY: `version_id`
- UNIQUE INDEX: `device_id` + `software_version`
- FOREIGN KEY: `device_id` → `devices(device_id)` ON DELETE CASCADE
- INDEX: `last_seen` (for reporting)

**Business Rules:**
- New version entry created when device reports different version
- `last_seen` updated when version still present on device
- Multiple versions can exist per device (historical record)
- Cascade delete when parent device deleted

---

### Table: device_interfaces

Tracks all interfaces and their IP addresses on each device.

**Purpose:** Monitor interface configurations and IP address assignments

**Key:** `device_id` + `interface_name` + `ip_address`

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| interface_id | INT | PRIMARY KEY, IDENTITY | Auto-incrementing unique identifier |
| device_id | INT | NOT NULL, FOREIGN KEY → devices(device_id) | Reference to parent device |
| interface_name | NVARCHAR(100) | NOT NULL | Interface name (e.g., GigabitEthernet0/1, Loopback0) |
| ip_address | NVARCHAR(50) | NOT NULL | IP address assigned to interface |
| subnet_mask | NVARCHAR(50) | NULL | Subnet mask or prefix length |
| interface_type | NVARCHAR(50) | NULL | Interface type: 'physical', 'loopback', 'vlan', 'tunnel' |
| first_seen | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Date interface first seen |
| last_seen | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Date interface last seen |
| created_at | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record creation timestamp |
| updated_at | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record last update timestamp |

**Indexes:**
- PRIMARY KEY: `interface_id`
- UNIQUE INDEX: `device_id` + `interface_name` + `ip_address`
- FOREIGN KEY: `device_id` → `devices(device_id)` ON DELETE CASCADE
- INDEX: `ip_address` (for IP address lookups)
- INDEX: `interface_type` (for filtering)

**Business Rules:**
- One interface can have multiple IP addresses (secondary IPs)
- Loopback interfaces tracked separately from physical interfaces
- `last_seen` updated when interface still present
- Cascade delete when parent device deleted

---

### Table: vlans

Master table of all VLAN numbers and names across the network.

**Purpose:** Centralized VLAN registry for the entire network

**Key:** `vlan_number` + `vlan_name`

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| vlan_id | INT | PRIMARY KEY, IDENTITY | Auto-incrementing unique identifier |
| vlan_number | INT | NOT NULL | VLAN ID (1-4094) |
| vlan_name | NVARCHAR(255) | NOT NULL | VLAN name |
| first_seen | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Date VLAN first discovered |
| last_seen | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Date VLAN last seen |
| created_at | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record creation timestamp |
| updated_at | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record last update timestamp |

**Indexes:**
- PRIMARY KEY: `vlan_id`
- UNIQUE INDEX: `vlan_number` + `vlan_name`
- INDEX: `vlan_number` (for lookups)
- INDEX: `last_seen` (for reporting)

**Business Rules:**
- Same VLAN number can have different names (different VLANs)
- VLAN 100 named "USERS" is different from VLAN 100 named "GUESTS"
- `last_seen` updated when VLAN found on any device
- Global registry across all devices

---

### Table: device_vlans

Tracks which VLANs are configured on which devices.

**Purpose:** Device-specific VLAN assignments with name consistency enforcement

**Key:** `device_id` + `vlan_id`

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| device_vlan_id | INT | PRIMARY KEY, IDENTITY | Auto-incrementing unique identifier |
| device_id | INT | NOT NULL, FOREIGN KEY → devices(device_id) | Reference to parent device |
| vlan_id | INT | NOT NULL, FOREIGN KEY → vlans(vlan_id) | Reference to VLAN |
| vlan_number | INT | NOT NULL | VLAN number (denormalized for queries) |
| vlan_name | NVARCHAR(255) | NOT NULL | VLAN name (denormalized for queries) |
| port_count | INT | NULL, DEFAULT 0 | Number of ports in VLAN |
| first_seen | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Date VLAN first seen on device |
| last_seen | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Date VLAN last seen on device |
| created_at | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record creation timestamp |
| updated_at | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Record last update timestamp |

**Indexes:**
- PRIMARY KEY: `device_vlan_id`
- UNIQUE INDEX: `device_id` + `vlan_id`
- FOREIGN KEY: `device_id` → `devices(device_id)` ON DELETE CASCADE
- FOREIGN KEY: `vlan_id` → `vlans(vlan_id)` ON DELETE CASCADE
- INDEX: `vlan_number` (for VLAN lookups)

**Business Rules:**
- One device can have multiple VLANs
- One VLAN can be on multiple devices
- If device has VLAN 100 with name "USERS", then later reports VLAN 100 with name "GUESTS":
  - Delete old link to VLAN 100 "USERS"
  - Create new link to VLAN 100 "GUESTS"
  - Keep only latest VLAN name per number per device
- Cascade delete when parent device or VLAN deleted

---

## Data Flow

### Device Discovery Process

```
1. Device Discovered
   ↓
2. Check if device exists (name + serial)
   ↓
   ├─ Exists → Update last_seen
   └─ New → Create device record
   ↓
3. Check software version
   ↓
   ├─ Version exists → Update last_seen
   └─ New version → Create version record
   ↓
4. Process interfaces
   ↓
   For each interface:
   ├─ Interface exists → Update last_seen
   └─ New interface → Create interface record
   ↓
5. Process VLANs
   ↓
   For each VLAN:
   ├─ Check vlans table (number + name)
   │  ├─ Exists → Update last_seen
   │  └─ New → Create VLAN record
   ↓
   ├─ Check device_vlans (device + VLAN number)
   │  ├─ Exists with same name → Update last_seen
   │  ├─ Exists with different name → Delete old, create new
   │  └─ New → Create device_vlan record
```

### Purge Process

```
1. External process marks device status = 'purge'
   ↓
2. NetWalker purge command runs
   ↓
3. Query devices WHERE status = 'purge'
   ↓
4. For each device:
   ├─ Delete device_vlans (CASCADE)
   ├─ Delete device_interfaces (CASCADE)
   ├─ Delete device_versions (CASCADE)
   └─ Delete device
   ↓
5. Clean up orphaned VLANs (optional)
   └─ Delete VLANs not referenced by any device
```

## SQL Server Connection String

```
Server=eit-prisqldb01.tgna.tegna.com,1433;Database=NetWalker;User Id=NetWalker;Password=FluffyBunnyHitbyaBus;TrustServerCertificate=True;
```

## CLI Commands

### Database Initialization
```bash
netwalker --db-init
```
Creates database and all tables if they don't exist.

### Database Purge
```bash
netwalker --db-purge
```
Deletes all data and recreates empty tables. Requires confirmation.

### Purge Marked Devices
```bash
netwalker --db-purge-devices
```
Deletes devices marked with status='purge'.

### Database Status
```bash
netwalker --db-status
```
Shows database connection status and record counts.

## Configuration

### INI File Settings

```ini
[database]
enabled = true
server = eit-prisqldb01.tgna.tegna.com
port = 1433
database = NetWalker
username = NetWalker
password = FluffyBunnyHitbyaBus
trust_server_certificate = true
connection_timeout = 30
command_timeout = 60
```

## Error Handling

### Connection Failures
- Retry logic: 3 attempts with exponential backoff
- Fallback: Continue discovery without database (log warning)
- Error logging: All database errors logged to file

### Data Conflicts
- Duplicate key violations: Update existing record
- Foreign key violations: Log error, skip record
- Transaction rollback on failure

## Performance Considerations

### Batch Operations
- Use bulk insert for multiple records
- Transaction batching (100 records per transaction)
- Commit after each device processed

### Indexing Strategy
- Indexes on all foreign keys
- Indexes on frequently queried columns
- Composite indexes for unique constraints

### Connection Pooling
- Reuse connections across discoveries
- Close connections after discovery complete
- Maximum pool size: 10 connections

## Security

### Credentials
- Password stored in INI file (encrypted in future version)
- SQL Server authentication (Windows auth in future)
- Least privilege: NetWalker user has INSERT, UPDATE, DELETE, SELECT only

### Data Protection
- No sensitive data stored (passwords, SNMP communities)
- Connection string uses TrustServerCertificate for internal network
- Audit trail via created_at/updated_at timestamps

## Future Enhancements

### Planned Features
1. Encrypted password storage in INI file
2. Windows Authentication support
3. Database backup/restore commands
4. Data export to CSV/Excel
5. Historical reporting queries
6. Device change notifications
7. VLAN consistency reports
8. Interface utilization tracking

### Schema Extensions
- Add `device_neighbors` table for CDP/LLDP data
- Add `device_routes` table for routing information
- Add `device_acls` table for access control lists
- Add `audit_log` table for all database changes

## Maintenance

### Regular Tasks
- Weekly: Review devices not seen in 30+ days
- Monthly: Purge devices marked for deletion
- Quarterly: Database performance tuning
- Annually: Archive old historical data

### Monitoring
- Database size growth
- Query performance
- Connection failures
- Data consistency checks

## Change Log

### Version 1.0 (2026-01-14)
- Initial database schema design
- Core tables: devices, device_versions, device_interfaces, vlans, device_vlans
- Basic CLI commands
- SQL Server connection configuration
