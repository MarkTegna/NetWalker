"""
Device Filter Module for Command Executor

This module provides functionality to filter devices from the NetWalker database
based on SQL wildcard patterns and retrieve their primary IP addresses.

Author: Mark Oldham
"""

import logging
from typing import List
from netwalker.database.database_manager import DatabaseManager
from netwalker.executor.data_models import DeviceInfo


class DeviceFilter:
    """
    Filters devices from the database based on name patterns.
    
    This class provides methods to query the NetWalker database for devices
    matching SQL wildcard patterns (% for multiple characters, _ for single
    character) and retrieve their primary IP addresses.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the device filter.
        
        Args:
            db_manager: DatabaseManager instance for database operations
        """
        self.logger = logging.getLogger(__name__)
        self.db_manager = db_manager
    
    def filter_devices(self, pattern: str) -> List[DeviceInfo]:
        """
        Filter devices by name pattern and retrieve their primary IP addresses.
        
        This method queries the devices table using SQL LIKE pattern matching
        and joins with device_interfaces to get the most recently seen IP address
        for each device.
        
        Args:
            pattern: SQL wildcard pattern for device name matching
                    (% for multiple characters, _ for single character)
        
        Returns:
            List of DeviceInfo objects containing device name and primary IP address.
            Returns empty list if no devices match or if database is not connected.
        
        Examples:
            >>> filter = DeviceFilter(db_manager)
            >>> devices = filter.filter_devices("*-uw*")  # Matches any device with '-uw' in name
            >>> devices = filter.filter_devices("BORO%")  # Matches devices starting with 'BORO'
        """
        if not self.db_manager.enabled:
            self.logger.warning("Database is disabled, cannot filter devices")
            return []
        
        if not self.db_manager.is_connected():
            self.logger.warning("Database is not connected, attempting to connect...")
            if not self.db_manager.connect():
                self.logger.error("Failed to connect to database")
                return []
        
        try:
            cursor = self.db_manager.connection.cursor()
            
            # Query to get devices matching the pattern with their most recent IP address
            # We join with device_interfaces and use ROW_NUMBER to get the most recent IP
            # for each device based on last_seen timestamp
            query = """
                SELECT 
                    d.device_name,
                    di.ip_address
                FROM devices d
                INNER JOIN (
                    SELECT 
                        device_id,
                        ip_address,
                        ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY last_seen DESC) as rn
                    FROM device_interfaces
                ) di ON d.device_id = di.device_id AND di.rn = 1
                WHERE d.device_name LIKE ?
                ORDER BY d.device_name
            """
            
            self.logger.debug("Filtering devices with pattern: %s", pattern)
            cursor.execute(query, (pattern,))
            
            devices = []
            for row in cursor.fetchall():
                device_name = row[0]
                ip_address = row[1]
                devices.append(DeviceInfo(device_name=device_name, ip_address=ip_address))
            
            cursor.close()
            
            self.logger.info("Found %d devices matching pattern: %s", len(devices), pattern)
            return devices
        
        except Exception as e:
            self.logger.error("Error filtering devices with pattern '%s': %s", pattern, e)
            return []
