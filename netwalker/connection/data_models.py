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
    stack_members: List['StackMemberInfo'] = None
    is_stack: bool = False
    is_physical_device: Optional[bool] = None  # True for physical, False for cloud/virtual, None if unknown
    ha_role: Optional[str] = None  # For PAN-OS: Active, Passive, or None if HA not enabled
    
    def __post_init__(self):
        if self.neighbors is None:
            self.neighbors = []
        if self.vlans is None:
            self.vlans = []
        if self.stack_members is None:
            self.stack_members = []


@dataclass
class VLANInfo:
    """VLAN information collected from a device"""
    vlan_id: int
    vlan_name: str
    port_count: int
    portchannel_count: int
    connected_port_count: int  # Number of ports in "connected" status
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


@dataclass
class StackMemberInfo:
    """Information about a switch stack member"""
    switch_number: int
    role: Optional[str]  # Master, Member, Standby
    priority: Optional[int]
    hardware_model: str
    serial_number: str
    mac_address: Optional[str]
    software_version: Optional[str]
    state: Optional[str]  # Ready, Provisioned, etc.
    uptime: Optional[str] = None  # Uptime for this specific stack member


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