"""
Data models for connection management
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class ConnectionMethod(Enum):
    """Connection method enumeration"""
    SSH = "SSH"
    TELNET = "Telnet"


class ConnectionStatus(Enum):
    """Connection status enumeration"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    AUTH_FAILED = "auth_failed"


@dataclass
class ConnectionResult:
    """Result of a connection attempt"""
    host: str
    method: ConnectionMethod
    status: ConnectionStatus
    error_message: Optional[str] = None
    connection_time: Optional[float] = None
    

@dataclass
class DeviceInfo:
    """Complete device information collected during discovery"""
    hostname: str
    primary_ip: str
    platform: str
    capabilities: List[str]
    software_version: str
    vtp_version: Optional[str]
    serial_number: str
    hardware_model: str
    uptime: str
    discovery_timestamp: datetime
    discovery_depth: int
    is_seed: bool
    connection_method: str
    connection_status: str
    error_details: Optional[str]
    neighbors: List['NeighborInfo'] = None
    
    def __post_init__(self):
        if self.neighbors is None:
            self.neighbors = []


@dataclass
class NeighborInfo:
    """Information about a neighboring device"""
    device_id: str
    local_interface: str
    remote_interface: str
    platform: str
    capabilities: List[str]
    ip_address: Optional[str] = None
    protocol: str = "CDP"  # CDP or LLDP