"""
NetWalker Database Module

Provides persistent storage for network device discovery data.
"""

from .database_manager import DatabaseManager
from .models import Device, DeviceVersion, DeviceInterface, VLAN, DeviceVLAN

__all__ = [
    'DatabaseManager',
    'Device',
    'DeviceVersion',
    'DeviceInterface',
    'VLAN',
    'DeviceVLAN'
]
