"""
Database Manager for NetWalker Inventory

Handles all database operations including connection management,
schema creation, and CRUD operations.
"""

import ipaddress
import logging
import pyodbc
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from .models import Device, DeviceVersion, DeviceInterface, VLAN, DeviceVLAN


class DatabaseManager:
    """Manages database connections and operations for NetWalker inventory"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database manager

        Args:
            config: Database configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.connection = None
        self.enabled = config.get('enabled', False)

        if self.enabled:
            self.server = config.get('server', '')
            self.port = config.get('port', 1433)
            self.database = config.get('database', 'NetWalker')
            self.username = config.get('username', '')
            self.password = config.get('password', '')
            self.trust_cert = config.get('trust_server_certificate', True)
            self.conn_timeout = config.get('connection_timeout', 30)
            self.cmd_timeout = config.get('command_timeout', 60)

            self.logger.info(f"DatabaseManager initialized: server={self.server}, database={self.database}")
        else:
            self.logger.info("DatabaseManager disabled in configuration")

    def connect(self) -> bool:
        """
        Establish database connection

        Returns:
            True if connection successful, False otherwise
        """
        if not self.enabled:
            self.logger.debug("Database disabled, skipping connection")
            return False

        try:
            # Try to find an available SQL Server driver
            available_drivers = pyodbc.drivers()
            sql_drivers = [d for d in available_drivers if 'SQL Server' in d]

            if not sql_drivers:
                self.logger.error("No SQL Server ODBC driver found. Available drivers: " + ", ".join(available_drivers))
                self.connection = None
                return False

            # Prefer ODBC Driver 17/18, fall back to older drivers
            driver = None
            for preferred in ['ODBC Driver 18 for SQL Server', 'ODBC Driver 17 for SQL Server', 'SQL Server']:
                if preferred in sql_drivers:
                    driver = preferred
                    break

            if not driver:
                driver = sql_drivers[0]  # Use first available

            self.logger.info(f"Using ODBC driver: {driver}")

            # Build connection string (older drivers don't support TrustServerCertificate)
            # If database is empty or 'default', don't specify DATABASE parameter (use login's default)
            if self.database and self.database.lower() not in ['', 'default']:
                if 'ODBC Driver 1' in driver:  # ODBC Driver 17 or 18
                    conn_str = (
                        f"DRIVER={{{driver}}};"
                        f"SERVER={self.server},{self.port};"
                        f"DATABASE={self.database};"
                        f"UID={self.username};"
                        f"PWD={self.password};"
                        f"TrustServerCertificate={'yes' if self.trust_cert else 'no'};"
                        f"Connection Timeout={self.conn_timeout};"
                    )
                else:  # Older SQL Server driver
                    conn_str = (
                        f"DRIVER={{{driver}}};"
                        f"SERVER={self.server},{self.port};"
                        f"DATABASE={self.database};"
                        f"UID={self.username};"
                        f"PWD={self.password};"
                        f"Connection Timeout={self.conn_timeout};"
                    )
            else:
                # Use default database for login (don't specify DATABASE)
                if 'ODBC Driver 1' in driver:  # ODBC Driver 17 or 18
                    conn_str = (
                        f"DRIVER={{{driver}}};"
                        f"SERVER={self.server},{self.port};"
                        f"UID={self.username};"
                        f"PWD={self.password};"
                        f"TrustServerCertificate={'yes' if self.trust_cert else 'no'};"
                        f"Connection Timeout={self.conn_timeout};"
                    )
                else:  # Older SQL Server driver
                    conn_str = (
                        f"DRIVER={{{driver}}};"
                        f"SERVER={self.server},{self.port};"
                        f"UID={self.username};"
                        f"PWD={self.password};"
                        f"Connection Timeout={self.conn_timeout};"
                    )

            self.connection = pyodbc.connect(conn_str, timeout=self.conn_timeout)
            self.connection.timeout = self.cmd_timeout

            # Get the actual database we're connected to
            cursor = self.connection.cursor()
            cursor.execute("SELECT DB_NAME()")
            actual_db = cursor.fetchone()[0]
            cursor.close()

            self.logger.info(f"Connected to database: {self.server}/{actual_db}")

            # Update self.database to reflect actual connected database
            if not self.database or self.database.lower() in ['', 'default']:
                self.database = actual_db
                self.logger.info(f"Using default database for login: {actual_db}")

            return True

        except pyodbc.Error as e:
            self.logger.error(f"Database connection failed: {e}")
            self.connection = None
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error connecting to database: {e}")
            self.connection = None
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            try:
                self.connection.close()
                self.logger.info("Database connection closed")
            except Exception as e:
                self.logger.error(f"Error closing database connection: {e}")
            finally:
                self.connection = None

    def is_connected(self) -> bool:
        """Check if database connection is active"""
        if not self.connection:
            return False

        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except:
            return False

    def initialize_database(self) -> bool:
        """
        Create database and tables if they don't exist

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            self.logger.warning("Database disabled, cannot initialize")
            return False

        # First, try to connect to the target database
        if not self.connect():
            # If connection failed, try connecting to master to create the database
            self.logger.info("Target database doesn't exist, attempting to create it...")
            original_database = self.database
            self.database = 'master'

            if not self.connect():
                self.logger.error("Failed to connect to master database")
                self.database = original_database
                return False

            try:
                cursor = self.connection.cursor()

                # Check if database exists
                cursor.execute(f"SELECT database_id FROM sys.databases WHERE name = '{original_database}'")
                if not cursor.fetchone():
                    # Create database (must be outside transaction)
                    self.logger.info(f"Creating database: {original_database}")
                    self.connection.autocommit = True
                    cursor.execute(f"CREATE DATABASE [{original_database}]")
                    self.connection.autocommit = False
                    self.logger.info(f"Database {original_database} created successfully")
                else:
                    self.logger.info(f"Database {original_database} already exists")

                cursor.close()
                self.disconnect()

                # Reconnect to the target database
                self.database = original_database
                if not self.connect():
                    self.logger.error(f"Failed to connect to {original_database} after creation")
                    return False

            except pyodbc.Error as e:
                self.logger.error(f"Error creating database: {e}")
                self.database = original_database
                return False

        try:
            cursor = self.connection.cursor()

            # Create devices table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'devices')
                BEGIN
                    CREATE TABLE devices (
                        device_id INT IDENTITY(1,1) PRIMARY KEY,
                        device_name NVARCHAR(255) NOT NULL,
                        serial_number NVARCHAR(100) NOT NULL,
                        platform NVARCHAR(100) NULL,
                        hardware_model NVARCHAR(100) NULL,
                        capabilities NVARCHAR(500) NULL,
                        first_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
                        last_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
                        status NVARCHAR(20) NOT NULL DEFAULT 'active',
                        created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
                        updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
                        CONSTRAINT UQ_device_name_serial UNIQUE (device_name, serial_number)
                    );
                    CREATE INDEX IX_devices_status ON devices(status);
                    CREATE INDEX IX_devices_last_seen ON devices(last_seen);
                END
            """)

            # Add capabilities column to existing devices table if it doesn't exist
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.columns
                              WHERE object_id = OBJECT_ID('devices')
                              AND name = 'capabilities')
                BEGIN
                    ALTER TABLE devices ADD capabilities NVARCHAR(500) NULL;
                END
            """)

            # Create device_versions table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'device_versions')
                BEGIN
                    CREATE TABLE device_versions (
                        version_id INT IDENTITY(1,1) PRIMARY KEY,
                        device_id INT NOT NULL,
                        software_version NVARCHAR(100) NOT NULL,
                        first_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
                        last_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
                        created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
                        updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
                        CONSTRAINT FK_device_versions_device FOREIGN KEY (device_id)
                            REFERENCES devices(device_id) ON DELETE CASCADE,
                        CONSTRAINT UQ_device_version UNIQUE (device_id, software_version)
                    );
                    CREATE INDEX IX_device_versions_last_seen ON device_versions(last_seen);
                END
            """)

            # Create device_interfaces table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'device_interfaces')
                BEGIN
                    CREATE TABLE device_interfaces (
                        interface_id INT IDENTITY(1,1) PRIMARY KEY,
                        device_id INT NOT NULL,
                        interface_name NVARCHAR(100) NOT NULL,
                        ip_address NVARCHAR(50) NOT NULL,
                        subnet_mask NVARCHAR(50) NULL,
                        interface_type NVARCHAR(50) NULL,
                        first_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
                        last_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
                        created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
                        updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
                        CONSTRAINT FK_device_interfaces_device FOREIGN KEY (device_id)
                            REFERENCES devices(device_id) ON DELETE CASCADE,
                        CONSTRAINT UQ_device_interface_ip UNIQUE (device_id, interface_name, ip_address)
                    );
                    CREATE INDEX IX_device_interfaces_ip ON device_interfaces(ip_address);
                    CREATE INDEX IX_device_interfaces_type ON device_interfaces(interface_type);
                END
            """)

            # Create vlans table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'vlans')
                BEGIN
                    CREATE TABLE vlans (
                        vlan_id INT IDENTITY(1,1) PRIMARY KEY,
                        vlan_number INT NOT NULL,
                        vlan_name NVARCHAR(255) NOT NULL,
                        first_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
                        last_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
                        created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
                        updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
                        CONSTRAINT UQ_vlan_number_name UNIQUE (vlan_number, vlan_name),
                        CONSTRAINT CHK_vlan_number CHECK (vlan_number BETWEEN 1 AND 4094)
                    );
                    CREATE INDEX IX_vlans_number ON vlans(vlan_number);
                    CREATE INDEX IX_vlans_last_seen ON vlans(last_seen);
                END
            """)

            # Create device_vlans table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'device_vlans')
                BEGIN
                    CREATE TABLE device_vlans (
                        device_vlan_id INT IDENTITY(1,1) PRIMARY KEY,
                        device_id INT NOT NULL,
                        vlan_id INT NOT NULL,
                        vlan_number INT NOT NULL,
                        vlan_name NVARCHAR(255) NOT NULL,
                        port_count INT NULL DEFAULT 0,
                        first_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
                        last_seen DATETIME2 NOT NULL DEFAULT GETDATE(),
                        created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
                        updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
                        CONSTRAINT FK_device_vlans_device FOREIGN KEY (device_id)
                            REFERENCES devices(device_id) ON DELETE CASCADE,
                        CONSTRAINT FK_device_vlans_vlan FOREIGN KEY (vlan_id)
                            REFERENCES vlans(vlan_id) ON DELETE CASCADE,
                        CONSTRAINT UQ_device_vlan UNIQUE (device_id, vlan_id)
                    );
                    CREATE INDEX IX_device_vlans_number ON device_vlans(vlan_number);
                END
            """)

            # Create device_neighbors table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'device_neighbors')
                BEGIN
                    CREATE TABLE device_neighbors (
                        neighbor_id INT IDENTITY(1,1) PRIMARY KEY,
                        source_device_id INT NOT NULL,
                        source_interface NVARCHAR(100) NOT NULL,
                        destination_device_id INT NOT NULL,
                        destination_interface NVARCHAR(100) NOT NULL,
                        protocol NVARCHAR(10) NOT NULL,
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
                END
            """)

            self.connection.commit()
            self.logger.info("Database schema initialized successfully")
            return True

        except pyodbc.Error as e:
            self.logger.error(f"Error initializing database schema: {e}")
            if self.connection:
                self.connection.rollback()
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error initializing database: {e}")
            if self.connection:
                self.connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def purge_database(self) -> bool:
        """
        Delete all data from database (keep schema)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            self.logger.warning("Database disabled, cannot purge")
            return False

        if not self.is_connected() and not self.connect():
            return False

        try:
            cursor = self.connection.cursor()

            # Delete in order to respect foreign key constraints
            # Delete neighbors first (references devices)
            cursor.execute("DELETE FROM device_neighbors")
            cursor.execute("DELETE FROM device_vlans")
            cursor.execute("DELETE FROM device_interfaces")
            cursor.execute("DELETE FROM device_versions")
            cursor.execute("DELETE FROM vlans")
            cursor.execute("DELETE FROM devices")

            self.connection.commit()
            self.logger.info("Database purged successfully")
            return True

        except pyodbc.Error as e:
            self.logger.error(f"Error purging database: {e}")
            if self.connection:
                self.connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def purge_marked_devices(self) -> int:
        """
        Delete devices marked with status='purge'

        Returns:
            Number of devices deleted, -1 on error
        """
        if not self.enabled:
            self.logger.warning("Database disabled, cannot purge devices")
            return -1

        if not self.is_connected() and not self.connect():
            return -1

        try:
            cursor = self.connection.cursor()

            # Get count of devices to purge
            cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'purge'")
            count = cursor.fetchone()[0]

            if count == 0:
                self.logger.info("No devices marked for purge")
                return 0

            # Delete devices (CASCADE will handle related records)
            cursor.execute("DELETE FROM devices WHERE status = 'purge'")

            self.connection.commit()
            self.logger.info(f"Purged {count} devices marked for deletion")
            return count

        except pyodbc.Error as e:
            self.logger.error(f"Error purging marked devices: {e}")
            if self.connection:
                self.connection.rollback()
            return -1
        finally:
            if cursor:
                cursor.close()

    def get_database_status(self) -> Dict[str, Any]:
        """
        Get database connection status and record counts

        Returns:
            Dictionary with status information
        """
        status = {
            'enabled': self.enabled,
            'connected': False,
            'server': self.server if self.enabled else None,
            'database': self.database if self.enabled else None,
            'record_counts': {}
        }

        if not self.enabled:
            return status

        if not self.is_connected() and not self.connect():
            return status

        status['connected'] = True

        try:
            cursor = self.connection.cursor()

            # Get record counts
            tables = ['devices', 'device_versions', 'device_interfaces', 'vlans', 'device_vlans']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                status['record_counts'][table] = count

            cursor.close()

        except Exception as e:
            self.logger.error(f"Error getting database status: {e}")

        return status

    def upsert_device(self, device_info: Dict[str, Any]) -> Optional[int]:
        """
        Insert or update device record

        Args:
            device_info: Dictionary with device information

        Returns:
            device_id if successful, None otherwise
        """
        if not self.enabled or not self.is_connected():
            return None

        device_name = device_info.get('hostname', '')
        serial_number = device_info.get('serial_number', 'unknown')
        platform = device_info.get('platform', '')
        hardware_model = device_info.get('hardware_model', '')
        capabilities = device_info.get('capabilities', [])

        # Convert capabilities list to comma-separated string
        capabilities_str = ','.join(capabilities) if capabilities else None

        if not device_name or not serial_number:
            self.logger.warning("Missing device_name or serial_number, skipping upsert")
            return None

        try:
            cursor = self.connection.cursor()

            # First, check if device exists with same name and serial number
            cursor.execute("""
                SELECT device_id FROM devices
                WHERE device_name = ? AND serial_number = ?
            """, (device_name, serial_number))

            row = cursor.fetchone()

            if row:
                # Update existing device with same name and serial
                device_id = row[0]
                cursor.execute("""
                    UPDATE devices
                    SET last_seen = GETDATE(),
                        platform = ?,
                        hardware_model = ?,
                        capabilities = ?,
                        updated_at = GETDATE()
                    WHERE device_id = ?
                """, (platform, hardware_model, capabilities_str, device_id))

                self.logger.debug(f"Updated device: {device_name} (ID: {device_id})")
            else:
                # Check if device exists with same name but serial='unknown' (unwalked neighbor)
                # If we now have a real serial number, update the existing record instead of creating a duplicate
                if serial_number != 'unknown':
                    cursor.execute("""
                        SELECT device_id FROM devices
                        WHERE device_name = ? AND serial_number = 'unknown'
                    """, (device_name,))
                    
                    unwalked_row = cursor.fetchone()
                    
                    if unwalked_row:
                        # Update the unwalked neighbor record with real data
                        device_id = unwalked_row[0]
                        cursor.execute("""
                            UPDATE devices
                            SET serial_number = ?,
                                last_seen = GETDATE(),
                                platform = ?,
                                hardware_model = ?,
                                capabilities = ?,
                                updated_at = GETDATE()
                            WHERE device_id = ?
                        """, (serial_number, platform, hardware_model, capabilities_str, device_id))
                        
                        self.logger.info(f"Updated unwalked neighbor to walked device: {device_name} (ID: {device_id})")
                    else:
                        # No unwalked neighbor found, insert new device
                        cursor.execute("""
                            INSERT INTO devices (device_name, serial_number, platform, hardware_model, capabilities)
                            VALUES (?, ?, ?, ?, ?)
                        """, (device_name, serial_number, platform, hardware_model, capabilities_str))

                        cursor.execute("SELECT @@IDENTITY")
                        device_id = cursor.fetchone()[0]

                        self.logger.info(f"Created new device: {device_name} (ID: {device_id})")
                else:
                    # serial_number is 'unknown', just insert as unwalked neighbor
                    cursor.execute("""
                        INSERT INTO devices (device_name, serial_number, platform, hardware_model, capabilities)
                        VALUES (?, ?, ?, ?, ?)
                    """, (device_name, serial_number, platform, hardware_model, capabilities_str))

                    cursor.execute("SELECT @@IDENTITY")
                    device_id = cursor.fetchone()[0]

                    self.logger.info(f"Created new unwalked neighbor: {device_name} (ID: {device_id})")

            self.connection.commit()
            cursor.close()
            return device_id

        except pyodbc.Error as e:
            self.logger.error(f"Error upserting device {device_name}: {e}")
            if self.connection:
                self.connection.rollback()
            return None

    def upsert_device_version(self, device_id: int, software_version: str) -> bool:
        """
        Insert or update device version record

        Args:
            device_id: Device ID
            software_version: Software version string

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.is_connected() or not software_version:
            return False

        try:
            cursor = self.connection.cursor()

            # Check if version exists
            cursor.execute("""
                SELECT version_id FROM device_versions
                WHERE device_id = ? AND software_version = ?
            """, (device_id, software_version))

            row = cursor.fetchone()

            if row:
                # Update last_seen
                cursor.execute("""
                    UPDATE device_versions
                    SET last_seen = GETDATE(), updated_at = GETDATE()
                    WHERE version_id = ?
                """, (row[0],))
            else:
                # Insert new version
                cursor.execute("""
                    INSERT INTO device_versions (device_id, software_version)
                    VALUES (?, ?)
                """, (device_id, software_version))

            self.connection.commit()
            cursor.close()
            return True

        except pyodbc.Error as e:
            self.logger.error(f"Error upserting device version: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def upsert_device_interface(self, device_id: int, interface_info: Dict[str, Any]) -> bool:
        """
        Insert or update device interface record

        Args:
            device_id: Device ID
            interface_info: Dictionary with interface information

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.is_connected():
            return False

        interface_name = interface_info.get('interface_name', '')
        ip_address = interface_info.get('ip_address', '')
        subnet_mask = interface_info.get('subnet_mask', '')
        interface_type = interface_info.get('interface_type', '')

        if not interface_name or not ip_address:
            return False

        try:
            cursor = self.connection.cursor()

            # Check if interface exists
            cursor.execute("""
                SELECT interface_id FROM device_interfaces
                WHERE device_id = ? AND interface_name = ? AND ip_address = ?
            """, (device_id, interface_name, ip_address))

            row = cursor.fetchone()

            if row:
                # Update last_seen
                cursor.execute("""
                    UPDATE device_interfaces
                    SET last_seen = GETDATE(),
                        subnet_mask = ?,
                        interface_type = ?,
                        updated_at = GETDATE()
                    WHERE interface_id = ?
                """, (subnet_mask, interface_type, row[0]))
            else:
                # Insert new interface
                cursor.execute("""
                    INSERT INTO device_interfaces
                    (device_id, interface_name, ip_address, subnet_mask, interface_type)
                    VALUES (?, ?, ?, ?, ?)
                """, (device_id, interface_name, ip_address, subnet_mask, interface_type))

            self.connection.commit()
            cursor.close()
            return True

        except pyodbc.Error as e:
            self.logger.error(f"Error upserting device interface: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def upsert_vlan(self, vlan_number: int, vlan_name: str) -> Optional[int]:
        """
        Insert or update VLAN record

        Args:
            vlan_number: VLAN number (1-4094)
            vlan_name: VLAN name

        Returns:
            vlan_id if successful, None otherwise
        """
        if not self.enabled or not self.is_connected():
            return None

        if not (1 <= vlan_number <= 4094) or not vlan_name:
            return None

        try:
            cursor = self.connection.cursor()

            # Check if VLAN exists
            cursor.execute("""
                SELECT vlan_id FROM vlans
                WHERE vlan_number = ? AND vlan_name = ?
            """, (vlan_number, vlan_name))

            row = cursor.fetchone()

            if row:
                # Update last_seen
                vlan_id = row[0]
                cursor.execute("""
                    UPDATE vlans
                    SET last_seen = GETDATE(), updated_at = GETDATE()
                    WHERE vlan_id = ?
                """, (vlan_id,))
            else:
                # Insert new VLAN
                cursor.execute("""
                    INSERT INTO vlans (vlan_number, vlan_name)
                    VALUES (?, ?)
                """, (vlan_number, vlan_name))

                cursor.execute("SELECT @@IDENTITY")
                vlan_id = cursor.fetchone()[0]

            self.connection.commit()
            cursor.close()
            return vlan_id

        except pyodbc.Error as e:
            self.logger.error(f"Error upserting VLAN {vlan_number}: {e}")
            if self.connection:
                self.connection.rollback()
            return None

    def upsert_device_vlan(self, device_id: int, vlan_number: int, vlan_name: str, port_count: int = 0) -> bool:
        """
        Insert or update device VLAN record
        Handles VLAN name changes by deleting old link and creating new one

        Args:
            device_id: Device ID
            vlan_number: VLAN number
            vlan_name: VLAN name
            port_count: Number of ports in VLAN

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.is_connected():
            return False

        try:
            cursor = self.connection.cursor()

            # Get or create VLAN
            vlan_id = self.upsert_vlan(vlan_number, vlan_name)
            if not vlan_id:
                return False

            # Check if device has this VLAN number with different name
            cursor.execute("""
                SELECT device_vlan_id, vlan_name FROM device_vlans
                WHERE device_id = ? AND vlan_number = ?
            """, (device_id, vlan_number))

            row = cursor.fetchone()

            if row:
                existing_vlan_name = row[1]
                if existing_vlan_name != vlan_name:
                    # VLAN name changed - delete old link
                    self.logger.info(f"VLAN {vlan_number} name changed from '{existing_vlan_name}' to '{vlan_name}' on device {device_id}")
                    cursor.execute("""
                        DELETE FROM device_vlans WHERE device_vlan_id = ?
                    """, (row[0],))

                    # Insert new link
                    cursor.execute("""
                        INSERT INTO device_vlans
                        (device_id, vlan_id, vlan_number, vlan_name, port_count)
                        VALUES (?, ?, ?, ?, ?)
                    """, (device_id, vlan_id, vlan_number, vlan_name, port_count))
                else:
                    # Same name - update last_seen and port_count
                    cursor.execute("""
                        UPDATE device_vlans
                        SET last_seen = GETDATE(),
                            port_count = ?,
                            updated_at = GETDATE()
                        WHERE device_vlan_id = ?
                    """, (port_count, row[0]))
            else:
                # New device-VLAN link
                cursor.execute("""
                    INSERT INTO device_vlans
                    (device_id, vlan_id, vlan_number, vlan_name, port_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (device_id, vlan_id, vlan_number, vlan_name, port_count))

            self.connection.commit()
            cursor.close()
            return True

        except pyodbc.Error as e:
            self.logger.error(f"Error upserting device VLAN: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def process_device_discovery(self, device_info: Dict[str, Any]) -> bool:
        """
        Process complete device discovery and update database

        Args:
            device_info: Complete device information dictionary

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.is_connected():
            return False

        try:
            # Upsert device
            device_id = self.upsert_device(device_info)
            if not device_id:
                return False

            # Upsert software version
            software_version = device_info.get('software_version', '')
            if software_version and software_version != 'unknown':
                self.upsert_device_version(device_id, software_version)

            # Store primary_ip as management interface (before processing other interfaces)
            primary_ip = device_info.get('primary_ip')
            if primary_ip:
                self.logger.debug(
                    "Extracted primary_ip: %s for device_id %s", primary_ip, device_id
                )

                # Validate IP address format
                try:
                    ipaddress.ip_address(primary_ip)
                    # Valid IP address - proceed with storage
                    primary_interface = {
                        'interface_name': 'Primary Management',
                        'ip_address': primary_ip,
                        'subnet_mask': '',
                        'interface_type': 'management'
                    }
                    if self.upsert_device_interface(device_id, primary_interface):
                        self.logger.debug(
                            "Stored primary_ip %s as management interface for device_id %s",
                            primary_ip, device_id
                        )
                    else:
                        self.logger.warning(
                            "Failed to store primary_ip %s for device_id %s",
                            primary_ip, device_id
                        )
                except (ValueError, AttributeError) as e:
                    # Invalid IP address format - log warning and skip storage
                    self.logger.warning(
                        "Invalid IP address format for primary_ip '%s' on device_id %s: %s",
                        primary_ip, device_id, e
                    )
            else:
                self.logger.debug(
                    "No primary_ip found in device_info for device_id %s", device_id
                )

            # Upsert interfaces (if available)
            interfaces = device_info.get('interfaces', [])
            for interface in interfaces:
                self.upsert_device_interface(device_id, interface)

            # Upsert VLANs (if available)
            vlans = device_info.get('vlans', [])
            for vlan in vlans:
                vlan_number = vlan.get('vlan_id') if hasattr(vlan, 'get') else getattr(vlan, 'vlan_id', 0)
                vlan_name = vlan.get('vlan_name') if hasattr(vlan, 'get') else getattr(vlan, 'vlan_name', '')
                port_count = vlan.get('port_count', 0) if hasattr(vlan, 'get') else getattr(vlan, 'port_count', 0)

                if vlan_number and vlan_name:
                    self.upsert_device_vlan(device_id, vlan_number, vlan_name, port_count)

            # Upsert neighbors (if available)
            neighbors = device_info.get('neighbors', [])
            if neighbors:
                try:
                    neighbor_count = self.upsert_device_neighbors(device_id, neighbors)
                    if neighbor_count > 0:
                        self.logger.info(f"Stored {neighbor_count} neighbors for device {device_id}")
                except Exception as e:
                    # Log error but continue - don't fail entire discovery
                    self.logger.error(f"Error storing neighbors for device {device_id}: {e}")

            return True

        except Exception as e:
            self.logger.error(f"Error processing device discovery: {e}")
            return False

    def resolve_hostname_to_device_id(self, hostname: str, create_if_missing: bool = False,
                                      capabilities: List[str] = None, platform: str = None) -> Optional[int]:
        """
        Resolve neighbor hostname to device_id

        Args:
            hostname: Device hostname (may be FQDN)
            create_if_missing: If True, create placeholder device record for unwalked neighbors
            capabilities: Device capabilities (for placeholder creation)
            platform: Device platform (for placeholder creation)

        Returns:
            device_id if found or created, None otherwise
        """
        if not self.enabled or not self.is_connected():
            return None

        if not hostname:
            return None

        try:
            cursor = self.connection.cursor()

            # Strip domain suffix from FQDN (e.g., "router.example.com" → "router")
            short_hostname = hostname.split('.')[0] if '.' in hostname else hostname

            # Query devices table by device_name
            # If multiple matches, return device with most recent last_seen
            cursor.execute("""
                SELECT TOP 1 device_id
                FROM devices
                WHERE device_name = ?
                ORDER BY last_seen DESC
            """, (short_hostname,))

            row = cursor.fetchone()

            if row:
                device_id = row[0]
                cursor.close()
                self.logger.debug(f"Resolved hostname '{hostname}' to device_id {device_id}")
                return device_id
            else:
                # Device not found
                if create_if_missing:
                    # Create placeholder device record for unwalked neighbor
                    self.logger.info(f"Creating placeholder device for unwalked neighbor: {short_hostname}")

                    # Convert capabilities list to comma-separated string
                    capabilities_str = ','.join(capabilities) if capabilities else None
                    platform_str = platform if platform else 'Unknown'

                    cursor.execute("""
                        INSERT INTO devices (device_name, serial_number, platform, hardware_model, capabilities, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (short_hostname, 'unknown', platform_str, 'Unwalked Neighbor', capabilities_str, 'active'))

                    cursor.execute("SELECT @@IDENTITY")
                    device_id = cursor.fetchone()[0]

                    self.connection.commit()
                    cursor.close()

                    self.logger.info(f"Created placeholder device '{short_hostname}' with device_id {device_id}, capabilities: {capabilities_str}")
                    return device_id
                else:
                    cursor.close()
                    self.logger.debug(f"Could not resolve hostname '{hostname}' to device_id")
                    return None

        except pyodbc.Error as e:
            self.logger.error(f"Error resolving hostname '{hostname}': {e}")
            return None

    def check_reverse_connection(self, source_id: int, source_if: str,
                                 dest_id: int, dest_if: str) -> Optional[int]:
        """
        Check if reverse connection exists (dest→source)

        Args:
            source_id: Source device ID
            source_if: Source interface name
            dest_id: Destination device ID
            dest_if: Destination interface name

        Returns:
            neighbor_id if reverse exists, None otherwise
        """
        if not self.enabled or not self.is_connected():
            return None

        try:
            cursor = self.connection.cursor()

            # Check for reverse connection (dest→source with swapped interfaces)
            cursor.execute("""
                SELECT neighbor_id
                FROM device_neighbors
                WHERE source_device_id = ?
                  AND source_interface = ?
                  AND destination_device_id = ?
                  AND destination_interface = ?
            """, (dest_id, dest_if, source_id, source_if))

            row = cursor.fetchone()
            cursor.close()

            if row:
                neighbor_id = row[0]
                self.logger.debug(f"Found reverse connection: neighbor_id {neighbor_id}")
                return neighbor_id
            else:
                return None

        except pyodbc.Error as e:
            self.logger.error(f"Error checking reverse connection: {e}")
            return None

    def get_consistent_direction(self, source_id: int, source_if: str,
                                 dest_id: int, dest_if: str) -> Tuple[int, str, int, str]:
        """
        Return connection with consistent direction (lower device_id as source)

        Args:
            source_id: Source device ID
            source_if: Source interface name
            dest_id: Destination device ID
            dest_if: Destination interface name

        Returns:
            Tuple of (source_id, source_if, dest_id, dest_if) in consistent direction
        """
        if source_id <= dest_id:
            # Already in correct direction
            return (source_id, source_if, dest_id, dest_if)
        else:
            # Swap to put lower device_id as source
            return (dest_id, dest_if, source_id, source_if)

    def upsert_neighbor_connection(self, source_id: int, source_if: str,
                                   dest_id: int, dest_if: str, protocol: str) -> bool:
        """
        Insert or update a neighbor connection

        Args:
            source_id: Source device ID
            source_if: Source interface name
            dest_id: Destination device ID
            dest_if: Destination interface name
            protocol: Protocol used (CDP or LLDP)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.is_connected():
            return False

        try:
            cursor = self.connection.cursor()

            # Check if connection exists (exact match)
            cursor.execute("""
                SELECT neighbor_id FROM device_neighbors
                WHERE source_device_id = ?
                  AND source_interface = ?
                  AND destination_device_id = ?
                  AND destination_interface = ?
            """, (source_id, source_if, dest_id, dest_if))

            row = cursor.fetchone()

            if row:
                # Update existing connection
                neighbor_id = row[0]
                cursor.execute("""
                    UPDATE device_neighbors
                    SET last_seen = GETDATE(),
                        protocol = ?,
                        updated_at = GETDATE()
                    WHERE neighbor_id = ?
                """, (protocol, neighbor_id))

                self.logger.debug(f"Updated neighbor connection: {neighbor_id}")
            else:
                # Insert new connection
                cursor.execute("""
                    INSERT INTO device_neighbors
                    (source_device_id, source_interface, destination_device_id,
                     destination_interface, protocol)
                    VALUES (?, ?, ?, ?, ?)
                """, (source_id, source_if, dest_id, dest_if, protocol))

                self.logger.debug(f"Created new neighbor connection: {source_id} -> {dest_id}")

            self.connection.commit()
            cursor.close()
            return True

        except pyodbc.Error as e:
            self.logger.error(f"Error upserting neighbor connection: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def upsert_device_neighbors(self, device_id: int, neighbors: List[Any]) -> int:
        """
        Store or update neighbor connections for a device

        Args:
            device_id: Source device ID
            neighbors: List of NeighborInfo objects

        Returns:
            Count of neighbors successfully stored
        """
        if not self.enabled or not self.is_connected():
            return 0

        if not neighbors:
            return 0

        stored_count = 0

        for neighbor in neighbors:
            try:
                # Extract neighbor information
                neighbor_hostname = neighbor.device_id if hasattr(neighbor, 'device_id') else str(neighbor)
                neighbor_capabilities = neighbor.capabilities if hasattr(neighbor, 'capabilities') else []
                neighbor_platform = neighbor.platform if hasattr(neighbor, 'platform') else None

                # Resolve hostname to destination_device_id
                # Create placeholder device if neighbor doesn't exist (unwalked leaf node)
                # Pass capabilities and platform for placeholder creation
                dest_device_id = self.resolve_hostname_to_device_id(
                    neighbor_hostname,
                    create_if_missing=True,
                    capabilities=neighbor_capabilities,
                    platform=neighbor_platform
                )

                if not dest_device_id:
                    # Skip if resolution fails
                    self.logger.warning(f"Could not resolve neighbor hostname: {neighbor_hostname}")
                    continue

                # Get interface names
                local_interface = neighbor.local_interface if hasattr(neighbor, 'local_interface') else 'Unknown'
                remote_interface = neighbor.remote_interface if hasattr(neighbor, 'remote_interface') else 'Unknown'
                protocol = neighbor.protocol if hasattr(neighbor, 'protocol') else 'CDP'

                # Normalize interface names (import ProtocolParser if needed)
                from netwalker.discovery.protocol_parser import ProtocolParser
                parser = ProtocolParser()
                local_interface = parser.normalize_interface_name(local_interface)
                remote_interface = parser.normalize_interface_name(remote_interface)

                # Check for reverse connection
                reverse_id = self.check_reverse_connection(
                    device_id, local_interface,
                    dest_device_id, remote_interface
                )

                if reverse_id:
                    # Reverse connection exists, update it
                    cursor = self.connection.cursor()
                    cursor.execute("""
                        UPDATE device_neighbors
                        SET last_seen = GETDATE(),
                            protocol = ?,
                            updated_at = GETDATE()
                        WHERE neighbor_id = ?
                    """, (protocol, reverse_id))
                    self.connection.commit()
                    cursor.close()

                    self.logger.debug(f"Updated reverse connection: {reverse_id}")
                    stored_count += 1
                else:
                    # No reverse connection, insert with consistent direction
                    src_id, src_if, dst_id, dst_if = self.get_consistent_direction(
                        device_id, local_interface,
                        dest_device_id, remote_interface
                    )

                    if self.upsert_neighbor_connection(src_id, src_if, dst_id, dst_if, protocol):
                        stored_count += 1

            except Exception as e:
                # Continue processing remaining neighbors on individual failures
                self.logger.error(f"Error storing neighbor {neighbor}: {e}")
                continue

        if stored_count > 0:
            self.logger.info(f"Stored {stored_count} neighbor connections for device {device_id}")

        return stored_count

    def get_device_neighbors(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve all neighbors for a device (both directions)

        Args:
            device_id: Device ID to query neighbors for

        Returns:
            List of neighbor connection dictionaries
        """
        if not self.enabled or not self.is_connected():
            return []

        try:
            cursor = self.connection.cursor()

            # Query device_neighbors where device is source OR destination
            cursor.execute("""
                SELECT
                    n.neighbor_id,
                    n.source_device_id,
                    d1.device_name AS source_name,
                    n.source_interface,
                    n.destination_device_id,
                    d2.device_name AS dest_name,
                    n.destination_interface,
                    n.protocol,
                    n.first_seen,
                    n.last_seen
                FROM device_neighbors n
                INNER JOIN devices d1 ON n.source_device_id = d1.device_id
                INNER JOIN devices d2 ON n.destination_device_id = d2.device_id
                WHERE n.source_device_id = ? OR n.destination_device_id = ?
                ORDER BY n.last_seen DESC
            """, (device_id, device_id))

            neighbors = []
            for row in cursor.fetchall():
                neighbors.append({
                    'neighbor_id': row[0],
                    'source_device_id': row[1],
                    'source_name': row[2],
                    'source_interface': row[3],
                    'destination_device_id': row[4],
                    'dest_name': row[5],
                    'destination_interface': row[6],
                    'protocol': row[7],
                    'first_seen': row[8],
                    'last_seen': row[9]
                })

            cursor.close()
            return neighbors

        except pyodbc.Error as e:
            self.logger.error(f"Error querying device neighbors: {e}")
            return []

    def get_neighbors_by_protocol(self, protocol: str) -> List[Dict[str, Any]]:
        """
        Query connections filtered by protocol (CDP or LLDP)

        Args:
            protocol: Protocol type ('CDP' or 'LLDP')

        Returns:
            List of connections with all fields
        """
        if not self.enabled or not self.is_connected():
            return []

        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT
                    n.neighbor_id,
                    n.source_device_id,
                    d1.device_name AS source_name,
                    n.source_interface,
                    n.destination_device_id,
                    d2.device_name AS dest_name,
                    n.destination_interface,
                    n.protocol,
                    n.first_seen,
                    n.last_seen
                FROM device_neighbors n
                INNER JOIN devices d1 ON n.source_device_id = d1.device_id
                INNER JOIN devices d2 ON n.destination_device_id = d2.device_id
                WHERE n.protocol = ?
                ORDER BY n.last_seen DESC
            """, (protocol,))

            neighbors = []
            for row in cursor.fetchall():
                neighbors.append({
                    'neighbor_id': row[0],
                    'source_device_id': row[1],
                    'source_name': row[2],
                    'source_interface': row[3],
                    'destination_device_id': row[4],
                    'dest_name': row[5],
                    'destination_interface': row[6],
                    'protocol': row[7],
                    'first_seen': row[8],
                    'last_seen': row[9]
                })

            cursor.close()
            return neighbors

        except pyodbc.Error as e:
            self.logger.error(f"Error querying neighbors by protocol: {e}")
            return []

    def get_all_connections(self) -> List[Dict[str, Any]]:
        """
        Retrieve all neighbor connections from database

        Returns:
            List of all connection dictionaries
        """
        if not self.enabled or not self.is_connected():
            return []

        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT
                    n.neighbor_id,
                    n.source_device_id,
                    d1.device_name AS source_name,
                    n.source_interface,
                    n.destination_device_id,
                    d2.device_name AS dest_name,
                    n.destination_interface,
                    n.protocol,
                    n.first_seen,
                    n.last_seen
                FROM device_neighbors n
                INNER JOIN devices d1 ON n.source_device_id = d1.device_id
                INNER JOIN devices d2 ON n.destination_device_id = d2.device_id
                ORDER BY d1.device_name, d2.device_name
            """)

            connections = []
            for row in cursor.fetchall():
                connections.append({
                    'neighbor_id': row[0],
                    'source_device_id': row[1],
                    'source_name': row[2],
                    'source_interface': row[3],
                    'destination_device_id': row[4],
                    'dest_name': row[5],
                    'destination_interface': row[6],
                    'protocol': row[7],
                    'first_seen': row[8],
                    'last_seen': row[9]
                })

            cursor.close()
            return connections

        except pyodbc.Error as e:
            self.logger.error(f"Error querying all connections: {e}")
            return []

    def cleanup_stale_neighbors(self, days: int) -> int:
        """
        Delete neighbors not seen in specified days

        Args:
            days: Number of days - delete neighbors older than this

        Returns:
            Count of neighbors deleted
        """
        if not self.enabled or not self.is_connected():
            return 0

        try:
            cursor = self.connection.cursor()

            # Get count before deletion
            cursor.execute("""
                SELECT COUNT(*) FROM device_neighbors
                WHERE last_seen < DATEADD(day, -?, GETDATE())
            """, (days,))

            count = cursor.fetchone()[0]

            if count == 0:
                self.logger.info("No stale neighbors to clean up")
                return 0

            # Delete stale neighbors
            cursor.execute("""
                DELETE FROM device_neighbors
                WHERE last_seen < DATEADD(day, -?, GETDATE())
            """, (days,))

            self.connection.commit()
            cursor.close()

            self.logger.info(f"Cleaned up {count} stale neighbor connections")
            return count

        except pyodbc.Error as e:
            self.logger.error(f"Error cleaning up stale neighbors: {e}")
            if self.connection:
                self.connection.rollback()
            return 0

    def get_stale_devices(self, days: int) -> List[Dict[str, Any]]:
        """
        Get devices that haven't been walked in X days
        Excludes devices with hardware_model='Unwalked Neighbor'

        Args:
            days: Number of days - return devices not seen in this many days

        Returns:
            List of device dictionaries with device_name, ip_address, and last_seen
        """
        if not self.enabled or not self.is_connected():
            return []

        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT
                    d.device_name,
                    d.last_seen,
                    d.platform,
                    d.hardware_model,
                    COALESCE(
                        (SELECT TOP 1 ip_address
                         FROM device_interfaces
                         WHERE device_id = d.device_id
                         ORDER BY
                            CASE
                                WHEN interface_name LIKE '%Management%' THEN 1
                                WHEN interface_name LIKE '%Loopback%' THEN 2
                                WHEN interface_name LIKE '%Vlan%' THEN 3
                                ELSE 4
                            END,
                            interface_name
                        ),
                        ''
                    ) AS ip_address
                FROM devices d
                WHERE d.status = 'active'
                  AND d.hardware_model != 'Unwalked Neighbor'
                  AND d.last_seen < DATEADD(day, -?, GETDATE())
                ORDER BY d.last_seen ASC
            """, (days,))

            devices = []
            for row in cursor.fetchall():
                devices.append({
                    'device_name': row[0],
                    'last_seen': row[1],
                    'platform': row[2],
                    'hardware_model': row[3],
                    'ip_address': row[4]
                })

            cursor.close()
            self.logger.info(f"Found {len(devices)} stale devices (not walked in {days} days)")
            return devices

        except pyodbc.Error as e:
            self.logger.error(f"Error querying stale devices: {e}")
            return []

    def get_unwalked_devices(self) -> List[Dict[str, Any]]:
        """
        Get devices that have been discovered but never walked
        These are devices with hardware_model='Unwalked Neighbor'

        Returns:
            List of device dictionaries with device_name, ip_address, platform, and capabilities
        """
        if not self.enabled or not self.is_connected():
            return []

        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT
                    d.device_name,
                    d.platform,
                    d.capabilities,
                    d.first_seen,
                    d.last_seen,
                    COALESCE(
                        (SELECT TOP 1 ip_address
                         FROM device_interfaces
                         WHERE device_id = d.device_id
                         ORDER BY
                            CASE
                                WHEN interface_name LIKE '%Management%' THEN 1
                                WHEN interface_name LIKE '%Loopback%' THEN 2
                                WHEN interface_name LIKE '%Vlan%' THEN 3
                                ELSE 4
                            END,
                            interface_name
                        ),
                        ''
                    ) AS ip_address
                FROM devices d
                WHERE d.status = 'active'
                  AND d.hardware_model = 'Unwalked Neighbor'
                ORDER BY d.device_name
            """)

            devices = []
            for row in cursor.fetchall():
                devices.append({
                    'device_name': row[0],
                    'platform': row[1] or 'Unknown',
                    'capabilities': row[2] or '',
                    'first_seen': row[3],
                    'last_seen': row[4],
                    'ip_address': row[5]
                })

            cursor.close()
            self.logger.info(f"Found {len(devices)} unwalked devices (discovered but never walked)")
            return devices

        except pyodbc.Error as e:
            self.logger.error(f"Error querying unwalked devices: {e}")
            return []

    def get_primary_ip_by_hostname(self, hostname: str) -> Optional[str]:
        """
        Query database for a device's primary IP address by hostname.
        
        The primary IP is stored in the device_interfaces table with 
        interface_name = 'Primary Management' and interface_type = 'management'.
        
        Args:
            hostname: Device hostname to look up
            
        Returns:
            Primary IP address if found, None otherwise
            
        Note:
            This method never raises exceptions - returns None on any error
        """
        if not self.enabled or not self.is_connected():
            return None
            
        if not hostname:
            return None
        
        try:
            cursor = self.connection.cursor()
            
            # Query for primary IP by joining devices and device_interfaces tables
            # Prioritize 'Primary Management' interface, then any management interface
            cursor.execute("""
                SELECT TOP 1 di.ip_address
                FROM devices d
                INNER JOIN device_interfaces di ON d.device_id = di.device_id
                WHERE d.device_name = ?
                  AND di.ip_address IS NOT NULL
                  AND di.ip_address != ''
                ORDER BY
                    CASE
                        WHEN di.interface_name = 'Primary Management' THEN 1
                        WHEN di.interface_type = 'management' THEN 2
                        WHEN di.interface_name LIKE '%Management%' THEN 3
                        WHEN di.interface_name LIKE '%Loopback%' THEN 4
                        WHEN di.interface_name LIKE '%Vlan%' THEN 5
                        ELSE 6
                    END,
                    di.interface_name
            """, (hostname,))
            
            row = cursor.fetchone()
            cursor.close()
            
            if row and row[0]:
                ip_address = row[0]
                self.logger.debug(f"Found primary IP {ip_address} for hostname '{hostname}'")
                return ip_address
            else:
                self.logger.debug(f"No primary IP found for hostname '{hostname}'")
                return None
                
        except pyodbc.Error as e:
            self.logger.error(f"Database error looking up IP for hostname '{hostname}': {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error looking up IP for hostname '{hostname}': {e}")
            return None
