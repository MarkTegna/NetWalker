# Design Document

## Overview

This design addresses critical issues in NetWalker's site-specific device collection and reporting functionality. Currently, the system has two major problems:

1. **Network Device summaries show totals for the entire discovery sweep instead of per-site totals** - Site workbooks display global statistics rather than site-specific counts
2. **Discovered devices at each site are not being properly walked or collected** - Devices identified within site boundaries are not being recursively processed for neighbor discovery

The current site boundary detection system can identify devices matching patterns like `*-CORE-*` and create separate workbooks, but the device collection within those sites is incomplete, and the summary statistics are incorrect. This design provides a comprehensive solution to fix both the collection process and the reporting accuracy.

## Architecture

### Current Architecture Issues

The existing NetWalker architecture has several critical gaps in site-specific functionality:

1. **Incomplete Site Collection**: Site boundary detection identifies devices but doesn't ensure they are fully walked for neighbors
2. **Global Statistics in Site Reports**: Site workbooks show global totals instead of site-specific counts
3. **Missing Site Queue Management**: No dedicated queuing system for site-specific device collection
4. **Inconsistent Device Association**: Devices discovered as neighbors may not be properly associated with their sites

### Proposed Architecture Enhancement

```
Discovery Engine
├── Global Discovery Queue (existing)
├── Site-Specific Collection Manager (new)
│   ├── Site Queue Manager
│   ├── Site Device Walker
│   └── Site Association Validator
└── Site-Aware Excel Generator (enhanced)
    ├── Site Statistics Calculator
    ├── Site Summary Generator
    └── Site Workbook Creator
```

## Components and Interfaces

### 1. Site-Specific Collection Manager
**Purpose**: Orchestrate site-specific device collection and walking
**Interface**:
```python
class SiteSpecificCollectionManager:
    def __init__(self, discovery_engine: DiscoveryEngine, site_boundaries: Dict[str, List[str]])
    def initialize_site_queues(self, site_boundaries: Dict[str, List[str]]) -> Dict[str, deque]
    def collect_site_devices(self, site_name: str) -> Dict[str, Any]
    def get_site_collection_stats(self, site_name: str) -> Dict[str, int]
```

### 2. Site Queue Manager
**Purpose**: Manage separate device queues for each site boundary
**Interface**:
```python
class SiteQueueManager:
    def __init__(self)
    def create_site_queue(self, site_name: str) -> deque[DiscoveryNode]
    def add_device_to_site(self, site_name: str, device_node: DiscoveryNode) -> bool
    def get_next_device(self, site_name: str) -> Optional[DiscoveryNode]
    def is_site_queue_empty(self, site_name: str) -> bool
    def get_site_queue_size(self, site_name: str) -> int
```

### 3. Site Device Walker
**Purpose**: Walk devices within site boundaries to discover neighbors
**Interface**:
```python
class SiteDeviceWalker:
    def __init__(self, connection_manager: ConnectionManager, device_collector: DeviceCollector)
    def walk_site_device(self, device_node: DiscoveryNode, site_name: str) -> SiteWalkResult
    def process_site_neighbors(self, neighbors: List[Any], parent_site: str) -> List[DiscoveryNode]
    def validate_neighbor_site_association(self, neighbor: Any, parent_site: str) -> str
```

### 4. Site Association Validator
**Purpose**: Determine correct site associations for discovered devices
**Interface**:
```python
class SiteAssociationValidator:
    def __init__(self, site_boundary_pattern: str)
    def determine_device_site(self, device_hostname: str, device_ip: str, parent_site: Optional[str]) -> str
    def validate_site_membership(self, device_info: Dict[str, Any], site_name: str) -> bool
    def resolve_multi_site_conflicts(self, device_info: Dict[str, Any], candidate_sites: List[str]) -> str
```

### 5. Site Statistics Calculator
**Purpose**: Calculate accurate statistics for site-specific reporting
**Interface**:
```python
class SiteStatisticsCalculator:
    def __init__(self)
    def calculate_site_device_counts(self, site_inventory: Dict[str, Dict[str, Any]]) -> Dict[str, int]
    def calculate_site_connection_counts(self, site_inventory: Dict[str, Dict[str, Any]]) -> Dict[str, int]
    def calculate_site_discovery_stats(self, site_collection_results: Dict[str, Any]) -> Dict[str, Any]
    def generate_site_summary(self, site_name: str, site_stats: Dict[str, Any]) -> Dict[str, Any]
```

### 6. Enhanced Excel Generator
**Purpose**: Generate accurate site-specific reports with correct statistics
**Interface**:
```python
class EnhancedExcelGenerator(ExcelReportGenerator):
    def generate_site_specific_report(self, site_inventory: Dict[str, Dict[str, Any]], 
                                    site_stats: Dict[str, Any], site_name: str) -> str
    def create_site_summary_sheet(self, workbook: Workbook, site_stats: Dict[str, Any], site_name: str)
    def create_site_device_inventory_sheet(self, workbook: Workbook, site_inventory: Dict[str, Dict[str, Any]])
    def create_site_connections_sheet(self, workbook: Workbook, site_inventory: Dict[str, Dict[str, Any]])
```

## Data Models

### Site Collection Result
```python
@dataclass
class SiteCollectionResult:
    site_name: str
    devices_queued: int
    devices_processed: int
    devices_failed: int
    devices_skipped: int
    collection_start_time: datetime
    collection_end_time: datetime
    collection_duration: float
    site_inventory: Dict[str, Dict[str, Any]]
    error_details: List[str]
```

### Site Walk Result
```python
@dataclass
class SiteWalkResult:
    device_key: str
    site_name: str
    walk_success: bool
    device_info: Optional[Dict[str, Any]]
    neighbors_found: List[Any]
    neighbors_added_to_queue: int
    error_message: Optional[str]
    walk_timestamp: datetime
```

### Site Statistics
```python
@dataclass
class SiteStatistics:
    site_name: str
    total_devices: int
    connected_devices: int
    failed_devices: int
    filtered_devices: int
    total_connections: int
    intra_site_connections: int
    external_connections: int
    collection_success_rate: float
    average_discovery_depth: float
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Site Queue Isolation
*For any* two different sites, devices added to one site's queue should never appear in another site's queue
**Validates: Requirements 5.2**

### Property 2: Site Device Collection Completeness
*For any* site with devices in its queue, all reachable devices should be either successfully processed or marked as failed
**Validates: Requirements 1.5**

### Property 3: Site-Specific Statistics Accuracy
*For any* site workbook, the device counts and statistics should match only the devices associated with that site
**Validates: Requirements 3.1, 3.2**

### Property 4: Site Device Walking Consistency
*For any* device added to a site queue, the system should attempt to walk it using the same connection methods as global discovery
**Validates: Requirements 2.1, 2.2**

### Property 5: Neighbor Site Association Propagation
*For any* device discovered as a neighbor within a site, it should be associated with the same site as its parent device unless it matches a different site boundary pattern
**Validates: Requirements 1.3, 2.4**

### Property 6: Site Summary Isolation
*For any* site-specific workbook, the summary statistics should not include devices or connections from other sites
**Validates: Requirements 3.5, 4.2**

### Property 7: Global vs Site Statistics Consistency
*For any* discovery operation with multiple sites, the sum of all site statistics should equal the global statistics
**Validates: Requirements 4.1, 4.4**

### Property 8: Site Collection Error Resilience
*For any* site collection operation, errors in processing one device should not prevent processing of remaining devices in the same site
**Validates: Requirements 1.4, 9.1**

### Property 9: Site Queue Deduplication
*For any* site queue, the same device should not appear multiple times in the queue
**Validates: Requirements 5.1**

### Property 10: Site Boundary Pattern Consistency
*For any* configured site boundary pattern, devices matching the pattern should be consistently identified and associated with the correct site
**Validates: Requirements 6.1, 10.1**

### Property 11: Site Collection Progress Tracking
*For any* site collection operation, the reported progress should accurately reflect the number of devices processed versus queued
**Validates: Requirements 5.4, 7.2**

### Property 12: Site Workbook Content Completeness
*For any* site workbook, all devices associated with the site should appear in the device inventory sheet
**Validates: Requirements 8.1, 8.2**

### Property 13: Site Connection Accuracy
*For any* site connections sheet, only connections between devices within the same site should be displayed
**Validates: Requirements 3.3, 8.3**

### Property 14: Site Collection Configuration Integration
*For any* configured discovery settings (depth limits, timeouts, filters), they should apply consistently to both global and site-specific collection
**Validates: Requirements 10.2, 10.3, 10.4**

### Property 15: Site Collection Fallback Behavior
*For any* site collection that encounters critical errors, affected devices should be included in global discovery to ensure they are not lost
**Validates: Requirements 9.4, 10.5**

## Error Handling

### Site Collection Errors
- **Device Walking Failure**: Log error, mark device as failed, continue with remaining devices in site queue
- **Site Queue Corruption**: Reinitialize site queue, log warning, continue with available devices
- **Site Association Conflict**: Use primary site boundary device for association, log conflict details

### Site Statistics Errors
- **Missing Device Information**: Use available data, mark incomplete statistics, continue processing
- **Statistics Calculation Failure**: Use fallback calculations, log error, ensure basic counts are available
- **Workbook Generation Failure**: Create simplified workbook with available data, log detailed error

### Recovery Strategies
- **Graceful Degradation**: Always ensure site workbooks are created even with incomplete data
- **Fallback to Global**: If site collection fails completely, include devices in global discovery
- **Partial Success Handling**: Create workbooks for successful sites, report failures for others

## Testing Strategy

### Unit Testing
- **Site Queue Management**: Test queue creation, device addition, deduplication
- **Site Statistics Calculation**: Test accuracy of counts and percentages for various scenarios
- **Site Association Logic**: Test device assignment to correct sites with various hostname patterns
- **Error Handling**: Test all error conditions and recovery paths

### Property-Based Testing
- **Site Isolation**: Verify devices don't leak between site queues or statistics
- **Collection Completeness**: Verify all queued devices are processed or marked as failed
- **Statistics Accuracy**: Verify site statistics match actual device counts and connections
- **Configuration Consistency**: Verify settings apply uniformly across global and site collection

### Integration Testing
- **End-to-End Site Collection**: Test complete site collection with real device data
- **Multi-Site Scenarios**: Test discovery with multiple sites and overlapping devices
- **Excel Generation**: Verify actual workbook creation with correct site-specific content
- **Error Recovery**: Test system behavior under various failure conditions

### Test Configuration
- Use pytest for unit and integration tests
- Use Hypothesis for property-based testing with minimum 100 iterations per property
- Each property test must reference its design document property
- Tag format: **Feature: site-specific-device-collection-reporting, Property {number}: {property_text}**