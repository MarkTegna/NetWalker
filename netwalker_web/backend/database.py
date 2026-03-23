"""
Database connection and query functions for NetWalker Web UI

Author: Mark Oldham
"""

import pyodbc
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages database connections for NetWalker Web UI"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database connection
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config
        self.server = config.get('server', '')
        self.port = config.get('port', 1433)
        self.database = config.get('database', 'NetWalker')
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.trust_cert = config.get('trust_server_certificate', True)
        self.conn_timeout = config.get('connection_timeout', 30)
        
        logger.info(f"Database connection initialized: {self.server}/{self.database}")
    
    def get_connection(self) -> pyodbc.Connection:
        """
        Create and return a database connection
        
        Returns:
            pyodbc.Connection object
        """
        # Find available SQL Server driver
        available_drivers = pyodbc.drivers()
        sql_drivers = [d for d in available_drivers if 'SQL Server' in d]
        
        if not sql_drivers:
            raise Exception("No SQL Server ODBC driver found")
        
        # Prefer ODBC Driver 17/18
        driver = None
        for preferred in ['ODBC Driver 18 for SQL Server', 'ODBC Driver 17 for SQL Server', 'SQL Server']:
            if preferred in sql_drivers:
                driver = preferred
                break
        
        if not driver:
            driver = sql_drivers[0]
        
        # Build connection string
        if 'ODBC Driver 1' in driver:
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={self.server},{self.port};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
                f"TrustServerCertificate={'yes' if self.trust_cert else 'no'};"
                f"Connection Timeout={self.conn_timeout};"
            )
        else:
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={self.server},{self.port};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
                f"Connection Timeout={self.conn_timeout};"
            )
        
        connection = pyodbc.connect(conn_str, timeout=self.conn_timeout)
        logger.debug(f"Database connection established")
        return connection
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager for database cursor
        
        Yields:
            pyodbc.Cursor object
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()
            conn.close()


class DeviceQueries:
    """Device-related database queries"""
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    def get_all_devices(self, limit: int = 1000, offset: int = 0, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get all active devices with pagination and filtering"""
        with self.db.get_cursor() as cursor:
            # Build WHERE clause based on filters
            where_clauses = ["d.status = 'active'"]
            params = []
            
            if filters:
                if filters.get('device_name'):
                    where_clauses.append("d.device_name LIKE ?")
                    params.append(f"%{filters['device_name']}%")
                
                if filters.get('platform'):
                    where_clauses.append("d.platform LIKE ?")
                    params.append(f"%{filters['platform']}%")
                
                if filters.get('hardware_model'):
                    where_clauses.append("d.hardware_model LIKE ?")
                    params.append(f"%{filters['hardware_model']}%")
                
                if filters.get('serial_number'):
                    where_clauses.append("d.serial_number LIKE ?")
                    params.append(f"%{filters['serial_number']}%")
                
                if filters.get('capabilities'):
                    where_clauses.append("d.capabilities LIKE ?")
                    params.append(f"%{filters['capabilities']}%")
                
                if filters.get('ip_address'):
                    where_clauses.append("EXISTS (SELECT 1 FROM device_interfaces di WHERE di.device_id = d.device_id AND di.ip_address LIKE ?)")
                    params.append(f"%{filters['ip_address']}%")
                
                if filters.get('software_version'):
                    where_clauses.append("EXISTS (SELECT 1 FROM device_versions dv WHERE dv.device_id = d.device_id AND dv.software_version LIKE ?)")
                    params.append(f"%{filters['software_version']}%")
            
            where_clause = " AND ".join(where_clauses)
            
            query = f"""
                SELECT 
                    d.device_id,
                    d.device_name,
                    d.platform,
                    d.hardware_model,
                    d.serial_number,
                    d.capabilities,
                    d.status,
                    d.first_seen,
                    d.last_seen,
                    (SELECT TOP 1 software_version 
                     FROM device_versions 
                     WHERE device_id = d.device_id 
                     ORDER BY last_seen DESC) as software_version,
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
                        interface_name) as ip_address
                FROM devices d
                WHERE {where_clause}
                ORDER BY d.device_name
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            
            params.extend([offset, limit])
            cursor.execute(query, tuple(params))
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    
    def get_device_by_id(self, device_id: int) -> Optional[Dict[str, Any]]:
        """Get device details by ID"""
        with self.db.get_cursor() as cursor:
            query = """
                SELECT 
                    d.device_id,
                    d.device_name,
                    d.platform,
                    d.hardware_model,
                    d.serial_number,
                    d.capabilities,
                    d.status,
                    d.connection_failures,
                    d.first_seen,
                    d.last_seen,
                    d.created_at,
                    d.updated_at
                FROM devices d
                WHERE d.device_id = ?
            """
            cursor.execute(query, (device_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
    
    def search_devices(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search devices by name, IP, or serial number"""
        with self.db.get_cursor() as cursor:
            sql = """
                SELECT DISTINCT
                    d.device_id,
                    d.device_name,
                    d.platform,
                    d.hardware_model,
                    d.serial_number,
                    di.ip_address
                FROM devices d
                LEFT JOIN device_interfaces di ON d.device_id = di.device_id
                WHERE d.status = 'active'
                  AND (
                    d.device_name LIKE ?
                    OR d.serial_number LIKE ?
                    OR di.ip_address LIKE ?
                  )
                ORDER BY d.device_name
                OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
            """
            search_pattern = f"%{query}%"
            cursor.execute(sql, (search_pattern, search_pattern, search_pattern, limit))
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    
    def get_device_count(self, filters: Dict[str, Any] = None) -> int:
        """Get total count of active devices with optional filters"""
        with self.db.get_cursor() as cursor:
            # Build WHERE clause based on filters
            where_clauses = ["status = 'active'"]
            params = []
            
            if filters:
                if filters.get('device_name'):
                    where_clauses.append("device_name LIKE ?")
                    params.append(f"%{filters['device_name']}%")
                
                if filters.get('platform'):
                    where_clauses.append("platform LIKE ?")
                    params.append(f"%{filters['platform']}%")
                
                if filters.get('hardware_model'):
                    where_clauses.append("hardware_model LIKE ?")
                    params.append(f"%{filters['hardware_model']}%")
                
                if filters.get('serial_number'):
                    where_clauses.append("serial_number LIKE ?")
                    params.append(f"%{filters['serial_number']}%")
                
                if filters.get('capabilities'):
                    where_clauses.append("capabilities LIKE ?")
                    params.append(f"%{filters['capabilities']}%")
                
                if filters.get('ip_address'):
                    where_clauses.append("EXISTS (SELECT 1 FROM device_interfaces di WHERE di.device_id = devices.device_id AND di.ip_address LIKE ?)")
                    params.append(f"%{filters['ip_address']}%")
                
                if filters.get('software_version'):
                    where_clauses.append("EXISTS (SELECT 1 FROM device_versions dv WHERE dv.device_id = devices.device_id AND dv.software_version LIKE ?)")
                    params.append(f"%{filters['software_version']}%")
            
            where_clause = " AND ".join(where_clauses)
            query = f"SELECT COUNT(*) FROM devices WHERE {where_clause}"
            
            cursor.execute(query, tuple(params))
            return cursor.fetchone()[0]


class TopologyQueries:
    """Topology-related database queries"""
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    def get_device_neighbors(self, device_id: int) -> List[Dict[str, Any]]:
        """Get neighbors for a specific device"""
        with self.db.get_cursor() as cursor:
            query = """
                SELECT 
                    dn.neighbor_id,
                    sd.device_name as source_device,
                    dn.source_interface,
                    dd.device_name as destination_device,
                    dd.device_id as destination_device_id,
                    dn.destination_interface,
                    dn.protocol,
                    dn.last_seen
                FROM device_neighbors dn
                INNER JOIN devices sd ON dn.source_device_id = sd.device_id
                INNER JOIN devices dd ON dn.destination_device_id = dd.device_id
                WHERE dn.source_device_id = ?
                ORDER BY dn.source_interface
            """
            cursor.execute(query, (device_id,))
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    
    def get_all_connections(self) -> List[Dict[str, Any]]:
        """Get all network connections"""
        with self.db.get_cursor() as cursor:
            query = """
                SELECT 
                    dn.neighbor_id,
                    dn.source_device_id,
                    sd.device_name as source_device,
                    dn.source_interface,
                    dn.destination_device_id,
                    dd.device_name as destination_device,
                    dn.destination_interface,
                    dn.protocol
                FROM device_neighbors dn
                INNER JOIN devices sd ON dn.source_device_id = sd.device_id
                INNER JOIN devices dd ON dn.destination_device_id = dd.device_id
                WHERE sd.status = 'active' AND dd.status = 'active'
            """
            cursor.execute(query)
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results


class StackQueries:
    """Stack member-related database queries"""
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    def get_all_stacks(self) -> List[Dict[str, Any]]:
        """Get all devices with stack members"""
        with self.db.get_cursor() as cursor:
            query = """
                SELECT DISTINCT
                    d.device_id,
                    d.device_name,
                    d.platform,
                    COUNT(sm.stack_member_id) as member_count
                FROM devices d
                INNER JOIN device_stack_members sm ON d.device_id = sm.device_id
                WHERE d.status = 'active'
                GROUP BY d.device_id, d.device_name, d.platform
                ORDER BY d.device_name
            """
            cursor.execute(query)
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    
    def get_stack_members(self, device_id: int) -> List[Dict[str, Any]]:
        """Get stack members for a specific device"""
        with self.db.get_cursor() as cursor:
            query = """
                SELECT 
                    sm.stack_member_id,
                    sm.switch_number,
                    sm.role,
                    sm.priority,
                    sm.hardware_model,
                    sm.serial_number,
                    sm.mac_address,
                    sm.software_version,
                    sm.state,
                    sm.first_seen,
                    sm.last_seen
                FROM device_stack_members sm
                WHERE sm.device_id = ?
                ORDER BY sm.switch_number
            """
            cursor.execute(query, (device_id,))
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results


class StatsQueries:
    """Statistics-related database queries"""
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    def get_summary_stats(self) -> Dict[str, int]:
        """Get summary statistics"""
        with self.db.get_cursor() as cursor:
            stats = {}
            
            # Device count
            cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'active'")
            stats['total_devices'] = cursor.fetchone()[0]
            
            # Stack count
            cursor.execute("SELECT COUNT(DISTINCT device_id) FROM device_stack_members")
            stats['stack_devices'] = cursor.fetchone()[0]
            
            # Connection count
            cursor.execute("SELECT COUNT(*) FROM device_neighbors")
            stats['total_connections'] = cursor.fetchone()[0]
            
            # VLAN count
            cursor.execute("SELECT COUNT(*) FROM vlans")
            stats['total_vlans'] = cursor.fetchone()[0]
            
            return stats
    
    def get_platform_stats(self) -> List[Dict[str, Any]]:
        """Get device count by platform"""
        with self.db.get_cursor() as cursor:
            query = """
                SELECT 
                    platform,
                    COUNT(*) as count
                FROM devices
                WHERE status = 'active' AND platform IS NOT NULL
                GROUP BY platform
                ORDER BY count DESC
            """
            cursor.execute(query)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'platform': row[0],
                    'count': row[1]
                })
            
            return results
