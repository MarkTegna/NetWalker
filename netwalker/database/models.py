"""
Database Models for NetWalker Inventory

Data classes representing database tables.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Device:
    """Represents a network device in the inventory"""
    device_id: Optional[int] = None
    device_name: str = ""
    serial_number: str = ""
    platform: Optional[str] = None
    hardware_model: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class DeviceVersion:
    """Represents a software version seen on a device"""
    version_id: Optional[int] = None
    device_id: int = 0
    software_version: str = ""
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class DeviceInterface:
    """Represents an interface on a device"""
    interface_id: Optional[int] = None
    device_id: int = 0
    interface_name: str = ""
    ip_address: str = ""
    subnet_mask: Optional[str] = None
    interface_type: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class VLAN:
    """Represents a VLAN in the network"""
    vlan_id: Optional[int] = None
    vlan_number: int = 0
    vlan_name: str = ""
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class DeviceVLAN:
    """Represents a VLAN configured on a device"""
    device_vlan_id: Optional[int] = None
    device_id: int = 0
    vlan_id: int = 0
    vlan_number: int = 0
    vlan_name: str = ""
    port_count: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
