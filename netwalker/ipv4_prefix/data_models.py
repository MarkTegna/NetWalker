"""
Data Models for IPv4 Prefix Inventory Module

This module defines all data structures used throughout the IPv4 prefix inventory
workflow, from raw prefix extraction through normalization, deduplication, and
summarization analysis.

Author: Mark Oldham
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class IPv4PrefixConfig:
    """
    Configuration for IPv4 prefix inventory operations.
    
    Attributes:
        collect_global_table: Enable collection from global routing table
        collect_per_vrf: Enable collection from per-VRF routing tables
        collect_bgp: Enable collection of BGP prefixes
        output_directory: Directory path for CSV and Excel exports
        create_summary_file: Enable creation of summary.txt statistics file
        enable_database_storage: Enable storage of results in NetWalker database
        track_summarization: Enable tracking of route summarization relationships
        concurrent_devices: Number of devices to process concurrently
        command_timeout: Timeout in seconds for command execution
    """
    collect_global_table: bool
    collect_per_vrf: bool
    collect_bgp: bool
    output_directory: str
    create_summary_file: bool
    enable_database_storage: bool
    track_summarization: bool
    concurrent_devices: int
    command_timeout: int


@dataclass
class RawPrefix:
    """
    Raw prefix extracted from command output before normalization.
    
    Attributes:
        prefix_str: The prefix string as extracted (may be CIDR, mask format, or ambiguous)
        raw_line: The complete output line from which the prefix was extracted
        is_ambiguous: True if prefix lacks explicit length (e.g., "10.0.0.0" without /len)
    """
    prefix_str: str
    raw_line: str
    is_ambiguous: bool


@dataclass
class ParsedPrefix:
    """
    Parsed prefix with metadata from command output.
    
    Attributes:
        device: Device hostname where prefix was collected
        platform: Device platform (ios, iosxe, nxos)
        vrf: VRF name ("global" for global routing table)
        prefix_str: The prefix string (not yet normalized)
        source: Source of prefix ("rib", "connected", or "bgp")
        protocol: Routing protocol code ("B", "D", "C", "L", "S", or empty string)
        raw_line: The complete output line from which the prefix was extracted
        is_ambiguous: True if prefix lacks explicit length
        timestamp: When the prefix was collected
        vlan: VLAN number if prefix is associated with a VLAN interface (None otherwise)
        interface: Interface name if available (None otherwise)
    """
    device: str
    platform: str
    vrf: str
    prefix_str: str
    source: str
    protocol: str
    raw_line: str
    is_ambiguous: bool
    timestamp: datetime
    vlan: Optional[int] = None
    interface: Optional[str] = None


@dataclass
class NormalizedPrefix:
    """
    Normalized prefix in CIDR notation with complete metadata.
    
    Attributes:
        device: Device hostname where prefix was collected
        platform: Device platform (ios, iosxe, nxos)
        vrf: VRF name ("global" for global routing table)
        prefix: The prefix in CIDR notation (e.g., "192.168.1.0/24")
        source: Source of prefix ("rib", "connected", or "bgp")
        protocol: Routing protocol code ("B", "D", "C", "L", "S", or empty string)
        raw_line: The complete output line from which the prefix was extracted
        timestamp: When the prefix was collected
        vlan: VLAN number if prefix is associated with a VLAN interface (None otherwise)
        interface: Interface name if available (None otherwise)
    """
    device: str
    platform: str
    vrf: str
    prefix: str
    source: str
    protocol: str
    raw_line: str
    timestamp: datetime
    vlan: Optional[int] = None
    interface: Optional[str] = None


@dataclass
class DeduplicatedPrefix:
    """
    Deduplicated prefix view aggregated across devices.
    
    Attributes:
        vrf: VRF name ("global" for global routing table)
        prefix: The prefix in CIDR notation
        device_count: Number of devices where this prefix appears
        device_list: List of device hostnames where this prefix appears
    """
    vrf: str
    prefix: str
    device_count: int
    device_list: List[str]


@dataclass
class SummarizationRelationship:
    """
    Route summarization relationship between summary and component prefixes.
    
    Attributes:
        summary_prefix: The summary prefix in CIDR notation (e.g., "192.168.0.0/16")
        component_prefix: The component prefix in CIDR notation (e.g., "192.168.1.0/24")
        device: Device hostname where the summarization occurs
        vrf: VRF name where the summarization occurs
    """
    summary_prefix: str
    component_prefix: str
    device: str
    vrf: str


@dataclass
class CollectionException:
    """
    Exception or error encountered during collection or parsing.
    
    Attributes:
        device: Device hostname where the exception occurred
        command: Command that was being executed (or empty if not command-specific)
        error_type: Type of error ("command_failure", "parse_error", "unresolved_prefix", etc.)
        raw_token: The problematic token or prefix string (if applicable)
        error_message: Detailed error message
        timestamp: When the exception occurred
    """
    device: str
    command: str
    error_type: str
    raw_token: Optional[str]
    error_message: str
    timestamp: datetime


@dataclass
class DeviceCollectionResult:
    """
    Result of collecting prefix data from a single device.
    
    Attributes:
        device: Device hostname
        platform: Device platform (ios, iosxe, nxos)
        success: True if collection completed successfully
        vrfs: List of VRF names discovered on the device
        raw_outputs: Dictionary mapping command strings to their output
        error: Error message if collection failed (None if successful)
    """
    device: str
    platform: str
    success: bool
    vrfs: List[str]
    raw_outputs: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class InventoryResult:
    """
    Final result of complete IPv4 prefix inventory operation.
    
    Attributes:
        total_devices: Total number of devices processed
        successful_devices: Number of devices successfully processed
        failed_devices: Number of devices that failed processing
        total_prefixes: Total number of prefixes collected (before deduplication)
        unique_prefixes: Number of unique prefixes (after deduplication)
        host_routes_count: Number of /32 host routes collected
        unresolved_count: Number of ambiguous prefixes that could not be resolved
        summarization_relationships: Number of summarization relationships identified
        execution_time: Total execution time in seconds
        output_files: List of output file paths created
    """
    total_devices: int
    successful_devices: int
    failed_devices: int
    total_prefixes: int
    unique_prefixes: int
    host_routes_count: int
    unresolved_count: int
    summarization_relationships: int
    execution_time: float
    output_files: List[str]
