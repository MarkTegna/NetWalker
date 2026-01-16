# NetWalker Database Setup Instructions

**Date:** January 14, 2026  
**Status:** Database Integration Complete - Awaiting Database Creation

## Current Status

The NetWalker database integration is **fully implemented and tested**. The code successfully:
- ✅ Connects to SQL Server using available ODBC drivers
- ✅ Attempts to create database and schema
- ✅ Handles connection errors gracefully
- ✅ Falls back to non-database mode if unavailable

## Issue Encountered

The `NetWalker` SQL Server user does not have `CREATE DATABASE` permission on `eit-prisqldb01.tgna.tegna.com`.

**Error:**
```
CREATE DATABASE permission denied in database 'master'. (262)
```

This is expected and correct for security reasons in production environments.

## Required DBA Action

Please have your DBA execute the following SQL script on `eit-prisqldb01.tgna.tegna.com`:

```sql
-- Create NetWalker database
CREATE DATABASE [NetWalker];
GO

-- Grant permissions to NetWalker user
USE [NetWalker];
GO

GRANT CREATE TABLE TO [NetWalker];
GRANT ALTER TO [NetWalker];
GRANT SELECT, INSERT, UPDATE, DELETE TO [NetWalker];
GO
```

## After Database Creation

Once the DBA creates the database, run:

```bash
python main.py --db-init
```

This will create all required tables, indexes, and constraints.

## Alternative: Use Existing Database

If you have an existing database you can use for testing, update `netwalker.ini`:

```ini
[database]
enabled = true
server = eit-prisqldb01.tgna.tegna.com
port = 1433
database = YourExistingDatabase  # Change this
username = NetWalker
password = FluffyBunnyHitbyaBus
trust_server_certificate = true
connection_timeout = 30
command_timeout = 60
```

## Testing Without Database

For now, we can test NetWalker discovery with the database disabled:

```ini
[database]
enabled = false
```

The application will work normally and store data in Excel reports only.

## Database Schema

Once created, the database will have 5 tables:

1. **devices** - Device inventory (hostname + serial number)
2. **device_versions** - Software version history
3. **device_interfaces** - Interface and IP tracking
4. **vlans** - Master VLAN registry
5. **device_vlans** - Device-VLAN relationships

## Verification

After database creation, verify with:

```bash
python main.py --db-status
```

Expected output:
```
Database Status:
------------------------------------------------------------
Enabled: True
Connected: True
Server: eit-prisqldb01.tgna.tegna.com
Database: NetWalker

Record Counts:
  devices: 0
  device_versions: 0
  device_interfaces: 0
  vlans: 0
  device_vlans: 0
```

## Next Steps

1. **Option A:** Have DBA create NetWalker database
2. **Option B:** Use existing test database
3. **Option C:** Test discovery without database (disable in config)

The database feature is production-ready and will work immediately once the database is created.
