"""
Data models for connection management
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from enum import Enum

# Forward references will be resolved at runtime


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
    vlans: List['VLANInfo'] = None
    vlan_collection_status: str = "not_attempted"  # not_attempted, success, failed, skipped
    vlan_collection_error: Optional[str] = None
    
    def __post_init__(self):
        if self.neighbors is None:
            self.neighbors = []
        if self.vlans is None:
            self.vlans = []


@dataclass
class VLANInfo:
    """VLAN information collected from a device"""
    vlan_id: int
    vlan_name: str
    port_count: int
    portchannel_count: int
    device_hostname: str
    device_ip: str
    collection_timestamp: Optional[datetime] = None
    collection_error: Optional[str] = None


@dataclass
class VLANCollectionResult:
    """Result of VLAN collection operation"""
    device_hostname: str
    device_ip: str
    vlans: List[VLANInfo]
    collection_success: bool
    collection_timestamp: datetime
    error_details: Optional[str] = None


@dataclass
class VLANCollectionConfig:
    """Configuration for VLAN collection"""
    enabled: bool = True
    command_timeout: int = 30
    max_retries: int = 2
    include_inactive_vlans: bool = True
    platforms_to_skip: List[str] = None
    
    def __post_init__(self):
        if self.platforms_to_skip is None:
            self.platforms_to_skip = []


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