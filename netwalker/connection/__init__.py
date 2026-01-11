"""
Connection management for NetWalker
"""

from .connection_manager import ConnectionManager
from .data_models import ConnectionResult, DeviceInfo

__all__ = ['ConnectionManager', 'ConnectionResult', 'DeviceInfo']