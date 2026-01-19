---
inclusion: manual
---

# NetWalker Database Integration Guide

**Version:** 1.0  
**Last Updated:** January 17, 2026  
**Author:** Mark Oldham

## Overview

This guide provides complete information for building Python programs that interact with the NetWalker inventory database. It includes database schema, connection details, data models, API examples, and best practices.

## Quick Start

### Connection Information

- **Server:** eit-prisqldb01.tgna.tegna.com
- **Port:** 1433
- **Database:** NetWalker
- **Username:** NetWalker
- **Password:** FluffyBunnyHitbyaBus (encrypted: ENC:Rmx1ZmZ5QnVubnlIaXRieWFCdXM=)
- **Driver:** ODBC Driver 17/18 for SQL Server (or SQL Server driver)

### Connection String

```python
connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=eit-prisqldb01.tgna.tegna.com,1433;"
    "DATABASE=NetWalker;"
    "UID=NetWalker;"
    "PWD=FluffyBunnyHitbyaBus;"
    "TrustServerCertificate=yes;"
    "Connection Timeout=30;"
)
```

### Basic Connection Example

```python
import pyodbc

conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

# Query devices
cursor.execute("SELECT device_name, serial_number, platform FROM devices WHERE status = 'active'")
for row in cursor.fetchall():
    print(f"Device: {row.device_name}, Serial: {row.serial_number}, Platform: {row.platform}")

cursor.close()
conn.close()
```


## Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐
│    devices      │
│─────────────────│
│ device_id (PK)  │◄─────┐
│ device_name     │      │
│ serial_number   │      │
│ platform        │      │
│ hardware_model  │      │
│ first_seen      │      │
│ last_seen       │      │
│ status          │      │
└─────────────────┘      │
                         │
         ┌───────────────┼───────────────┬───────────────┐
         │               │               │               │
         │               │               │               │
┌────────▼────────┐ ┌────▼──────────┐ ┌─▼──────────────┐ ┌─▼──────────────┐
│device_versions  │ │device_interfaces│ │  device_vlans  │ │  (future)      │
│─────────────────│ │─────────────────│ │────────────────│ │  device_       │
│ version_id (PK) │ │ interface_id(PK)│ │device_vlan_id  │ │  neighbors     │
│ device_id (FK)  │ │ device_id (FK)  │ │device_id (FK)  │ │                │
│ software_version│ │ interface_name  │ │vlan_id (FK)    │ │                │
│ first_seen      │ │ ip_address      │ │vlan_number     │ │                │
│ last_seen       │ │ subnet_mask     │ │vlan_name       │ │                │
└─────────────────┘ │ interface_type  │ │port_count      │ └────────────────┘
                    │ first_seen      │ │first_seen      │
                    │ last_seen       │ │last_seen       │
                    └─────────────────┘ └────────────────┘
                                                │
                                                │
                                        ┌───────▼────────┐
                                        │     vlans      │
                                        │────────────────│
                                        │ vlan_id (PK)   │
                                        │ vlan_number    │
                                        │ vlan_name      │
                                        │ first_seen     │
                                        │ last_seen      │
                                        └────────────────┘
```


### Table: devices

**Purpose:** Primary table tracking all discovered network devices

**Primary Key:** `device_id` (INT, IDENTITY)  
**Unique Constraint:** `device_name` + `serial_number`

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| device_id | INT | NO | IDENTITY | Auto-incrementing unique identifier |
| device_name | NVARCHAR(255) | NO | - | Device hostname |
| serial_number | NVARCHAR(100) | NO | - | Device serial number |
| platform | NVARCHAR(100) | YES | NULL | Platform (IOS, IOS-XE, NX-OS, etc.) |
| hardware_model | NVARCHAR(100) | YES | NULL | Hardware model number |
| first_seen | DATETIME2 | NO | GETDATE() | Date device first discovered |
| last_seen | DATETIME2 | NO | GETDATE() | Date device last seen |
| status | NVARCHAR(20) | NO | 'active' | Status: 'active' or 'purge' |
| created_at | DATETIME2 | NO | GETDATE() | Record creation timestamp |
| updated_at | DATETIME2 | NO | GETDATE() | Record last update timestamp |

**Indexes:**
- PRIMARY KEY on `device_id`
- UNIQUE INDEX on (`device_name`, `serial_number`)
- INDEX on `status`
- INDEX on `last_seen`

**Business Rules:**
- If `device_name` exists but `serial_number` changes → New device (hardware replacement)
- If `status` = 'purge' → Device marked for deletion
- `last_seen` updated on every discovery
- `first_seen` never changes after creation


### Table: device_versions

**Purpose:** Track software versions seen on each device over time

**Primary Key:** `version_id` (INT, IDENTITY)  
**Unique Constraint:** `device_id` + `software_version`  
**Foreign Key:** `device_id` → `devices(device_id)` ON DELETE CASCADE

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| version_id | INT | NO | IDENTITY | Auto-incrementing unique identifier |
| device_id | INT | NO | - | Reference to parent device |
| software_version | NVARCHAR(100) | NO | - | Software version string |
| first_seen | DATETIME2 | NO | GETDATE() | Date version first seen on device |
| last_seen | DATETIME2 | NO | GETDATE() | Date version last seen on device |
| created_at | DATETIME2 | NO | GETDATE() | Record creation timestamp |
| updated_at | DATETIME2 | NO | GETDATE() | Record last update timestamp |

**Indexes:**
- PRIMARY KEY on `version_id`
- UNIQUE INDEX on (`device_id`, `software_version`)
- FOREIGN KEY on `device_id`
- INDEX on `last_seen`

**Business Rules:**
- New version entry created when device reports different version
- Multiple versions can exist per device (historical record)
- Cascade delete when parent device deleted


### Table: device_interfaces

**Purpose:** Track all interfaces and IP addresses on each device

**Primary Key:** `interface_id` (INT, IDENTITY)  
**Unique Constraint:** `device_id` + `interface_name` + `ip_address`  
**Foreign Key:** `device_id` → `devices(device_id)` ON DELETE CASCADE

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| interface_id | INT | NO | IDENTITY | Auto-incrementing unique identifier |
| device_id | INT | NO | - | Reference to parent device |
| interface_name | NVARCHAR(100) | NO | - | Interface name (e.g., GigabitEthernet0/1) |
| ip_address | NVARCHAR(50) | NO | - | IP address assigned to interface |
| subnet_mask | NVARCHAR(50) | YES | NULL | Subnet mask or prefix length |
| interface_type | NVARCHAR(50) | YES | NULL | Type: 'physical', 'loopback', 'vlan', 'tunnel' |
| first_seen | DATETIME2 | NO | GETDATE() | Date interface first seen |
| last_seen | DATETIME2 | NO | GETDATE() | Date interface last seen |
| created_at | DATETIME2 | NO | GETDATE() | Record creation timestamp |
| updated_at | DATETIME2 | NO | GETDATE() | Record last update timestamp |

**Indexes:**
- PRIMARY KEY on `interface_id`
- UNIQUE INDEX on (`device_id`, `interface_name`, `ip_address`)
- FOREIGN KEY on `device_id`
- INDEX on `ip_address`
- INDEX on `interface_type`

**Business Rules:**
- One interface can have multiple IP addresses (secondary IPs)
- Loopback interfaces tracked separately
- Cascade delete when parent device deleted


### Table: vlans

**Purpose:** Master table of all VLAN numbers and names across the network

**Primary Key:** `vlan_id` (INT, IDENTITY)  
**Unique Constraint:** `vlan_number` + `vlan_name`

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| vlan_id | INT | NO | IDENTITY | Auto-incrementing unique identifier |
| vlan_number | INT | NO | - | VLAN ID (1-4094) |
| vlan_name | NVARCHAR(255) | NO | - | VLAN name |
| first_seen | DATETIME2 | NO | GETDATE() | Date VLAN first discovered |
| last_seen | DATETIME2 | NO | GETDATE() | Date VLAN last seen |
| created_at | DATETIME2 | NO | GETDATE() | Record creation timestamp |
| updated_at | DATETIME2 | NO | GETDATE() | Record last update timestamp |

**Indexes:**
- PRIMARY KEY on `vlan_id`
- UNIQUE INDEX on (`vlan_number`, `vlan_name`)
- INDEX on `vlan_number`
- INDEX on `last_seen`

**Business Rules:**
- Same VLAN number can have different names (different VLANs)
- VLAN 100 "USERS" is different from VLAN 100 "GUESTS"
- Global registry across all devices


### Table: device_vlans

**Purpose:** Track which VLANs are configured on which devices

**Primary Key:** `device_vlan_id` (INT, IDENTITY)  
**Unique Constraint:** `device_id` + `vlan_id`  
**Foreign Keys:**
- `device_id` → `devices(device_id)` ON DELETE CASCADE
- `vlan_id` → `vlans(vlan_id)` ON DELETE CASCADE

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| device_vlan_id | INT | NO | IDENTITY | Auto-incrementing unique identifier |
| device_id | INT | NO | - | Reference to parent device |
| vlan_id | INT | NO | - | Reference to VLAN |
| vlan_number | INT | NO | - | VLAN number (denormalized) |
| vlan_name | NVARCHAR(255) | NO | - | VLAN name (denormalized) |
| port_count | INT | YES | 0 | Number of ports in VLAN |
| first_seen | DATETIME2 | NO | GETDATE() | Date VLAN first seen on device |
| last_seen | DATETIME2 | NO | GETDATE() | Date VLAN last seen on device |
| created_at | DATETIME2 | NO | GETDATE() | Record creation timestamp |
| updated_at | DATETIME2 | NO | GETDATE() | Record last update timestamp |

**Indexes:**
- PRIMARY KEY on `device_vlan_id`
- UNIQUE INDEX on (`device_id`, `vlan_id`)
- FOREIGN KEY on `device_id`
- FOREIGN KEY on `vlan_id`
- INDEX on `vlan_number`

**Business Rules:**
- One device can have multiple VLANs
- One VLAN can be on multiple devices
- If device reports VLAN with different name: delete old link, create new
- Cascade delete when parent device or VLAN deleted


## Python Data Models

NetWalker uses Python dataclasses to represent database tables. Import from `netwalker.database.models`:

```python
from netwalker.database.models import Device, DeviceVersion, DeviceInterface, VLAN, DeviceVLAN
from datetime import datetime

# Create a device
device = Device(
    device_name="CORE-SW01",
    serial_number="FOX1234ABCD",
    platform="IOS-XE",
    hardware_model="C9300-48P",
    status="active"
)

# Create a device version
version = DeviceVersion(
    device_id=1,
    software_version="17.9.4a"
)

# Create an interface
interface = DeviceInterface(
    device_id=1,
    interface_name="GigabitEthernet1/0/1",
    ip_address="10.1.1.1",
    subnet_mask="255.255.255.0",
    interface_type="physical"
)

# Create a VLAN
vlan = VLAN(
    vlan_number=100,
    vlan_name="USERS"
)

# Create a device-VLAN association
device_vlan = DeviceVLAN(
    device_id=1,
    vlan_id=1,
    vlan_number=100,
    vlan_name="USERS",
    port_count=24
)
```


## Common Query Examples

### Get All Active Devices

```python
cursor.execute("""
    SELECT device_id, device_name, serial_number, platform, hardware_model, last_seen
    FROM devices
    WHERE status = 'active'
    ORDER BY device_name
""")

for row in cursor.fetchall():
    print(f"{row.device_name} ({row.platform}) - Last seen: {row.last_seen}")
```

### Get Device with Current Software Version

```python
cursor.execute("""
    SELECT d.device_name, d.platform, dv.software_version, dv.last_seen
    FROM devices d
    INNER JOIN device_versions dv ON d.device_id = dv.device_id
    WHERE d.device_name = ?
    AND dv.last_seen = (
        SELECT MAX(last_seen) 
        FROM device_versions 
        WHERE device_id = d.device_id
    )
""", ('CORE-SW01',))

row = cursor.fetchone()
if row:
    print(f"{row.device_name} running {row.software_version}")
```

### Get All Interfaces for a Device

```python
cursor.execute("""
    SELECT interface_name, ip_address, subnet_mask, interface_type
    FROM device_interfaces
    WHERE device_id = ?
    ORDER BY interface_name
""", (device_id,))

for row in cursor.fetchall():
    print(f"{row.interface_name}: {row.ip_address}/{row.subnet_mask}")
```

### Get All VLANs on a Device

```python
cursor.execute("""
    SELECT dv.vlan_number, dv.vlan_name, dv.port_count
    FROM device_vlans dv
    INNER JOIN devices d ON dv.device_id = d.device_id
    WHERE d.device_name = ?
    ORDER BY dv.vlan_number
""", ('CORE-SW01',))

for row in cursor.fetchall():
    print(f"VLAN {row.vlan_number}: {row.vlan_name} ({row.port_count} ports)")
```

### Find Devices with Specific VLAN

```python
cursor.execute("""
    SELECT d.device_name, d.platform, dv.port_count
    FROM devices d
    INNER JOIN device_vlans dv ON d.device_id = dv.device_id
    WHERE dv.vlan_number = ? AND dv.vlan_name = ?
    ORDER BY d.device_name
""", (100, 'USERS'))

for row in cursor.fetchall():
    print(f"{row.device_name}: {row.port_count} ports in VLAN")
```


### Get VLAN Consistency Report

```python
# Find VLANs with same number but different names
cursor.execute("""
    SELECT vlan_number, COUNT(DISTINCT vlan_name) as name_count, 
           STRING_AGG(vlan_name, ', ') as names
    FROM vlans
    GROUP BY vlan_number
    HAVING COUNT(DISTINCT vlan_name) > 1
    ORDER BY vlan_number
""")

for row in cursor.fetchall():
    print(f"VLAN {row.vlan_number} has {row.name_count} different names: {row.names}")
```

### Get Devices Not Seen Recently

```python
cursor.execute("""
    SELECT device_name, platform, last_seen, 
           DATEDIFF(day, last_seen, GETDATE()) as days_ago
    FROM devices
    WHERE status = 'active'
    AND last_seen < DATEADD(day, -30, GETDATE())
    ORDER BY last_seen
""")

for row in cursor.fetchall():
    print(f"{row.device_name}: Last seen {row.days_ago} days ago")
```

### Get Software Version Distribution

```python
cursor.execute("""
    SELECT dv.software_version, COUNT(DISTINCT d.device_id) as device_count
    FROM device_versions dv
    INNER JOIN devices d ON dv.device_id = d.device_id
    WHERE d.status = 'active'
    AND dv.last_seen = (
        SELECT MAX(last_seen) 
        FROM device_versions 
        WHERE device_id = d.device_id
    )
    GROUP BY dv.software_version
    ORDER BY device_count DESC
""")

for row in cursor.fetchall():
    print(f"{row.software_version}: {row.device_count} devices")
```

### Get Device Count by Platform

```python
cursor.execute("""
    SELECT platform, COUNT(*) as device_count
    FROM devices
    WHERE status = 'active'
    GROUP BY platform
    ORDER BY device_count DESC
""")

for row in cursor.fetchall():
    print(f"{row.platform}: {row.device_count} devices")
```


## Using DatabaseManager Class

NetWalker provides a `DatabaseManager` class for database operations. Import from `netwalker.database.database_manager`:

```python
from netwalker.database.database_manager import DatabaseManager

# Configuration
config = {
    'enabled': True,
    'server': 'eit-prisqldb01.tgna.tegna.com',
    'port': 1433,
    'database': 'NetWalker',
    'username': 'NetWalker',
    'password': 'FluffyBunnyHitbyaBus',
    'trust_server_certificate': True,
    'connection_timeout': 30,
    'command_timeout': 60
}

# Initialize and connect
db = DatabaseManager(config)
if db.connect():
    print("Connected to database")
    
    # Use the connection
    cursor = db.connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'active'")
    count = cursor.fetchone()[0]
    print(f"Active devices: {count}")
    cursor.close()
    
    # Disconnect
    db.disconnect()
else:
    print("Failed to connect to database")
```

### DatabaseManager Methods

```python
# Initialize database schema (create tables)
db.initialize_database()

# Get database status
status = db.get_database_status()
print(f"Devices: {status['device_count']}")
print(f"VLANs: {status['vlan_count']}")

# Upsert device (insert or update)
from netwalker.database.models import Device
device = Device(
    device_name="CORE-SW01",
    serial_number="FOX1234ABCD",
    platform="IOS-XE",
    hardware_model="C9300-48P"
)
device_id = db.upsert_device(device)

# Upsert device version
from netwalker.database.models import DeviceVersion
version = DeviceVersion(
    device_id=device_id,
    software_version="17.9.4a"
)
db.upsert_device_version(version)

# Purge devices marked for deletion
deleted_count = db.purge_marked_devices()
print(f"Deleted {deleted_count} devices")

# Purge all data
db.purge_database()
```


## Data Flow and Business Logic

### Device Discovery Flow

```
1. Device Discovered
   ↓
2. Check if device exists (device_name + serial_number)
   ├─ Exists → Update last_seen
   └─ New → Create device record
   ↓
3. Check software version
   ├─ Version exists → Update last_seen
   └─ New version → Create version record
   ↓
4. Process interfaces
   For each interface:
   ├─ Interface exists → Update last_seen
   └─ New interface → Create interface record
   ↓
5. Process VLANs
   For each VLAN:
   ├─ Check vlans table (vlan_number + vlan_name)
   │  ├─ Exists → Update last_seen, get vlan_id
   │  └─ New → Create VLAN record, get vlan_id
   ↓
   ├─ Check device_vlans (device_id + vlan_number)
   │  ├─ Exists with same name → Update last_seen
   │  ├─ Exists with different name → Delete old, create new
   │  └─ New → Create device_vlan record
```

### VLAN Name Change Handling

When a device reports a VLAN with a different name:

```python
# Example: Device has VLAN 100 "USERS", now reports VLAN 100 "GUESTS"

# 1. Find or create new VLAN in vlans table
cursor.execute("""
    SELECT vlan_id FROM vlans 
    WHERE vlan_number = ? AND vlan_name = ?
""", (100, 'GUESTS'))

new_vlan_id = cursor.fetchone()
if not new_vlan_id:
    # Create new VLAN entry
    cursor.execute("""
        INSERT INTO vlans (vlan_number, vlan_name)
        VALUES (?, ?)
    """, (100, 'GUESTS'))
    new_vlan_id = cursor.execute("SELECT @@IDENTITY").fetchone()[0]

# 2. Delete old device_vlan link
cursor.execute("""
    DELETE FROM device_vlans
    WHERE device_id = ? AND vlan_number = ?
""", (device_id, 100))

# 3. Create new device_vlan link
cursor.execute("""
    INSERT INTO device_vlans (device_id, vlan_id, vlan_number, vlan_name, port_count)
    VALUES (?, ?, ?, ?, ?)
""", (device_id, new_vlan_id, 100, 'GUESTS', port_count))

conn.commit()
```


## Best Practices

### Connection Management

```python
# Always use try-finally for connection cleanup
conn = None
try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # Your database operations here
    cursor.execute("SELECT * FROM devices")
    
    conn.commit()
finally:
    if conn:
        conn.close()
```

### Transaction Management

```python
# Use transactions for multiple related operations
try:
    cursor.execute("INSERT INTO devices (...) VALUES (...)")
    device_id = cursor.execute("SELECT @@IDENTITY").fetchone()[0]
    
    cursor.execute("INSERT INTO device_versions (...) VALUES (...)", (device_id, ...))
    cursor.execute("INSERT INTO device_interfaces (...) VALUES (...)", (device_id, ...))
    
    conn.commit()  # Commit all or nothing
except Exception as e:
    conn.rollback()  # Rollback on error
    raise
```

### Parameterized Queries

```python
# ALWAYS use parameterized queries to prevent SQL injection
# GOOD:
cursor.execute("SELECT * FROM devices WHERE device_name = ?", (device_name,))

# BAD (SQL injection risk):
cursor.execute(f"SELECT * FROM devices WHERE device_name = '{device_name}'")
```

### Batch Operations

```python
# Use executemany for bulk inserts
interfaces = [
    (device_id, 'Gi1/0/1', '10.1.1.1', '255.255.255.0'),
    (device_id, 'Gi1/0/2', '10.1.1.2', '255.255.255.0'),
    (device_id, 'Gi1/0/3', '10.1.1.3', '255.255.255.0'),
]

cursor.executemany("""
    INSERT INTO device_interfaces (device_id, interface_name, ip_address, subnet_mask)
    VALUES (?, ?, ?, ?)
""", interfaces)

conn.commit()
```

### Error Handling

```python
import pyodbc

try:
    cursor.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,))
    row = cursor.fetchone()
    if not row:
        print("Device not found")
except pyodbc.IntegrityError as e:
    print(f"Constraint violation: {e}")
except pyodbc.OperationalError as e:
    print(f"Connection error: {e}")
except pyodbc.ProgrammingError as e:
    print(f"SQL syntax error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```


## Configuration File Format

NetWalker uses INI files for database configuration. Example `netwalker.ini`:

```ini
[database]
# Enable/disable database integration
enabled = true

# SQL Server connection details
server = eit-prisqldb01.tgna.tegna.com
port = 1433
database = NetWalker
username = NetWalker

# Password can be plain text or encrypted with ENC: prefix
password = FluffyBunnyHitbyaBus
# password = ENC:Rmx1ZmZ5QnVubnlIaXRieWFCdXM=

# Connection settings
trust_server_certificate = true
connection_timeout = 30
command_timeout = 60
```

### Reading Configuration

```python
import configparser

config = configparser.ConfigParser()
config.read('netwalker.ini')

db_config = {
    'enabled': config.getboolean('database', 'enabled', fallback=False),
    'server': config.get('database', 'server', fallback=''),
    'port': config.getint('database', 'port', fallback=1433),
    'database': config.get('database', 'database', fallback='NetWalker'),
    'username': config.get('database', 'username', fallback=''),
    'password': config.get('database', 'password', fallback=''),
    'trust_server_certificate': config.getboolean('database', 'trust_server_certificate', fallback=True),
    'connection_timeout': config.getint('database', 'connection_timeout', fallback=30),
    'command_timeout': config.getint('database', 'command_timeout', fallback=60)
}
```


## Common Use Cases

### 1. Device Inventory Report

```python
# Generate CSV report of all active devices
import csv

cursor.execute("""
    SELECT d.device_name, d.serial_number, d.platform, d.hardware_model,
           dv.software_version, d.last_seen
    FROM devices d
    LEFT JOIN device_versions dv ON d.device_id = dv.device_id
    WHERE d.status = 'active'
    AND (dv.last_seen IS NULL OR dv.last_seen = (
        SELECT MAX(last_seen) FROM device_versions WHERE device_id = d.device_id
    ))
    ORDER BY d.device_name
""")

with open('device_inventory.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Device Name', 'Serial Number', 'Platform', 'Hardware Model', 'Software Version', 'Last Seen'])
    writer.writerows(cursor.fetchall())
```

### 2. VLAN Audit Report

```python
# Find all devices with a specific VLAN
vlan_number = 100

cursor.execute("""
    SELECT d.device_name, dv.vlan_name, dv.port_count, dv.last_seen
    FROM device_vlans dv
    INNER JOIN devices d ON dv.device_id = d.device_id
    WHERE dv.vlan_number = ?
    AND d.status = 'active'
    ORDER BY d.device_name
""", (vlan_number,))

print(f"Devices with VLAN {vlan_number}:")
for row in cursor.fetchall():
    print(f"  {row.device_name}: {row.vlan_name} ({row.port_count} ports)")
```

### 3. Software Version Compliance Check

```python
# Find devices not running approved software version
approved_versions = ['17.9.4a', '17.9.5']

cursor.execute("""
    SELECT d.device_name, d.platform, dv.software_version
    FROM devices d
    INNER JOIN device_versions dv ON d.device_id = dv.device_id
    WHERE d.status = 'active'
    AND dv.last_seen = (
        SELECT MAX(last_seen) FROM device_versions WHERE device_id = d.device_id
    )
    AND dv.software_version NOT IN ({})
    ORDER BY d.device_name
""".format(','.join('?' * len(approved_versions))), approved_versions)

print("Devices with non-compliant software versions:")
for row in cursor.fetchall():
    print(f"  {row.device_name} ({row.platform}): {row.software_version}")
```

### 4. Interface IP Address Lookup

```python
# Find which device has a specific IP address
ip_address = '10.1.1.1'

cursor.execute("""
    SELECT d.device_name, di.interface_name, di.ip_address, di.subnet_mask
    FROM device_interfaces di
    INNER JOIN devices d ON di.device_id = d.device_id
    WHERE di.ip_address = ?
    AND d.status = 'active'
""", (ip_address,))

row = cursor.fetchone()
if row:
    print(f"IP {ip_address} found on {row.device_name} interface {row.interface_name}")
else:
    print(f"IP {ip_address} not found in database")
```


### 5. Device Change History

```python
# Track software version changes for a device
device_name = 'CORE-SW01'

cursor.execute("""
    SELECT dv.software_version, dv.first_seen, dv.last_seen,
           DATEDIFF(day, dv.first_seen, dv.last_seen) as days_active
    FROM device_versions dv
    INNER JOIN devices d ON dv.device_id = d.device_id
    WHERE d.device_name = ?
    ORDER BY dv.first_seen DESC
""", (device_name,))

print(f"Software version history for {device_name}:")
for row in cursor.fetchall():
    print(f"  {row.software_version}: {row.first_seen} to {row.last_seen} ({row.days_active} days)")
```

### 6. Stale Device Cleanup

```python
# Mark devices not seen in 90 days for purge
cursor.execute("""
    UPDATE devices
    SET status = 'purge', updated_at = GETDATE()
    WHERE status = 'active'
    AND last_seen < DATEADD(day, -90, GETDATE())
""")

marked_count = cursor.rowcount
conn.commit()
print(f"Marked {marked_count} devices for purge")

# Later, purge marked devices
cursor.execute("DELETE FROM devices WHERE status = 'purge'")
deleted_count = cursor.rowcount
conn.commit()
print(f"Deleted {deleted_count} devices")
```

### 7. VLAN Consistency Check

```python
# Find VLANs with inconsistent names across devices
cursor.execute("""
    SELECT vlan_number, 
           COUNT(DISTINCT vlan_name) as name_count,
           STRING_AGG(DISTINCT vlan_name, ', ') as names,
           COUNT(DISTINCT device_id) as device_count
    FROM device_vlans
    GROUP BY vlan_number
    HAVING COUNT(DISTINCT vlan_name) > 1
    ORDER BY vlan_number
""")

print("VLANs with inconsistent names:")
for row in cursor.fetchall():
    print(f"  VLAN {row.vlan_number}: {row.name_count} different names across {row.device_count} devices")
    print(f"    Names: {row.names}")
```


## Advanced Queries

### Devices by Site (using hostname prefix)

```python
# Assuming site code is first 4 characters of hostname (e.g., KENS-CORE-A)
cursor.execute("""
    SELECT LEFT(device_name, 4) as site_code,
           COUNT(*) as device_count,
           COUNT(DISTINCT platform) as platform_count
    FROM devices
    WHERE status = 'active'
    GROUP BY LEFT(device_name, 4)
    ORDER BY device_count DESC
""")

print("Devices by site:")
for row in cursor.fetchall():
    print(f"  {row.site_code}: {row.device_count} devices, {row.platform_count} platforms")
```

### Interface Utilization Summary

```python
# Count interfaces by type per device
cursor.execute("""
    SELECT d.device_name, di.interface_type, COUNT(*) as interface_count
    FROM device_interfaces di
    INNER JOIN devices d ON di.device_id = d.device_id
    WHERE d.status = 'active'
    GROUP BY d.device_name, di.interface_type
    ORDER BY d.device_name, di.interface_type
""")

current_device = None
for row in cursor.fetchall():
    if row.device_name != current_device:
        print(f"\n{row.device_name}:")
        current_device = row.device_name
    print(f"  {row.interface_type}: {row.interface_count} interfaces")
```

### VLAN Port Distribution

```python
# Show VLAN port count distribution
cursor.execute("""
    SELECT vlan_number, vlan_name,
           SUM(port_count) as total_ports,
           COUNT(DISTINCT device_id) as device_count,
           AVG(port_count) as avg_ports_per_device
    FROM device_vlans
    GROUP BY vlan_number, vlan_name
    HAVING SUM(port_count) > 0
    ORDER BY total_ports DESC
""")

print("VLAN port distribution:")
for row in cursor.fetchall():
    print(f"  VLAN {row.vlan_number} ({row.vlan_name}): {row.total_ports} total ports across {row.device_count} devices")
```

### Device Discovery Timeline

```python
# Show when devices were first discovered
cursor.execute("""
    SELECT CAST(first_seen AS DATE) as discovery_date,
           COUNT(*) as devices_discovered
    FROM devices
    GROUP BY CAST(first_seen AS DATE)
    ORDER BY discovery_date DESC
""")

print("Device discovery timeline:")
for row in cursor.fetchall():
    print(f"  {row.discovery_date}: {row.devices_discovered} devices")
```


## Performance Tips

### Use Indexes Effectively

```python
# Good: Uses index on device_name
cursor.execute("SELECT * FROM devices WHERE device_name = ?", (name,))

# Bad: Full table scan (function on indexed column)
cursor.execute("SELECT * FROM devices WHERE UPPER(device_name) = ?", (name.upper(),))
```

### Limit Result Sets

```python
# Use TOP to limit results
cursor.execute("SELECT TOP 100 * FROM devices ORDER BY last_seen DESC")

# Or use WHERE clauses to filter
cursor.execute("""
    SELECT * FROM devices 
    WHERE last_seen > DATEADD(day, -7, GETDATE())
""")
```

### Use Appropriate Data Types

```python
# Good: Use proper types for parameters
cursor.execute("SELECT * FROM devices WHERE device_id = ?", (123,))  # int

# Bad: String when int expected (forces type conversion)
cursor.execute("SELECT * FROM devices WHERE device_id = ?", ('123',))  # string
```

### Batch Commits

```python
# Commit in batches for large operations
batch_size = 100
for i, device in enumerate(devices):
    cursor.execute("INSERT INTO devices (...) VALUES (...)", device)
    
    if (i + 1) % batch_size == 0:
        conn.commit()

conn.commit()  # Final commit
```

## Troubleshooting

### Connection Issues

```python
# Test connection with detailed error info
import pyodbc

try:
    conn = pyodbc.connect(connection_string, timeout=10)
    print("Connection successful")
    conn.close()
except pyodbc.Error as e:
    print(f"Connection failed: {e}")
    print(f"SQL State: {e.args[0] if e.args else 'Unknown'}")
    print(f"Error Message: {e.args[1] if len(e.args) > 1 else 'Unknown'}")
```

### Check Available Drivers

```python
import pyodbc

print("Available ODBC drivers:")
for driver in pyodbc.drivers():
    print(f"  - {driver}")
```

### Verify Database Exists

```python
# Connect to master database to check if NetWalker exists
conn_str_master = connection_string.replace("DATABASE=NetWalker", "DATABASE=master")
conn = pyodbc.connect(conn_str_master)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sys.databases WHERE name = 'NetWalker'")
if cursor.fetchone():
    print("NetWalker database exists")
else:
    print("NetWalker database does not exist")

cursor.close()
conn.close()
```


## Security Considerations

### Password Encryption

```python
# NetWalker supports encrypted passwords with ENC: prefix
import base64

def encrypt_password(password: str) -> str:
    """Encrypt password using base64 encoding"""
    encoded = base64.b64encode(password.encode()).decode()
    return f"ENC:{encoded}"

def decrypt_password(encrypted_password: str) -> str:
    """Decrypt password from base64 encoding"""
    if encrypted_password.startswith("ENC:"):
        encoded_part = encrypted_password[4:]
        return base64.b64decode(encoded_part.encode()).decode()
    return encrypted_password

# Usage
encrypted = encrypt_password("FluffyBunnyHitbyaBus")
print(f"Encrypted: {encrypted}")
# Output: ENC:Rmx1ZmZ5QnVubnlIaXRieWFCdXM=

decrypted = decrypt_password(encrypted)
print(f"Decrypted: {decrypted}")
```

### Least Privilege Access

The NetWalker database user should have minimal permissions:

```sql
-- Required permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO [NetWalker];
GRANT CREATE TABLE TO [NetWalker];
GRANT ALTER TO [NetWalker];

-- NOT required (security best practice)
-- DENY CREATE DATABASE TO [NetWalker];
-- DENY DROP TO [NetWalker];
```

### Connection String Security

```python
# Don't hardcode credentials in source code
# BAD:
connection_string = "SERVER=...;UID=NetWalker;PWD=FluffyBunnyHitbyaBus;..."

# GOOD: Read from config file
import configparser
config = configparser.ConfigParser()
config.read('netwalker.ini')
password = config.get('database', 'password')

# BETTER: Use environment variables
import os
password = os.getenv('NETWALKER_DB_PASSWORD', '')
```

## Reference Links

- **NetWalker Repository:** https://github.com/MarkTegna/NetWalker
- **Database Structure:** `DATABASE_STRUCTURE.md`
- **Database Setup:** `DATABASE_SETUP_INSTRUCTIONS.md`
- **pyodbc Documentation:** https://github.com/mkleehammer/pyodbc/wiki
- **SQL Server Documentation:** https://docs.microsoft.com/en-us/sql/

## Version History

- **v1.0 (2026-01-17):** Initial steering document created
  - Complete database schema documentation
  - Python examples and best practices
  - Common query patterns
  - DatabaseManager API reference

---

**For questions or issues, contact Mark Oldham.**
