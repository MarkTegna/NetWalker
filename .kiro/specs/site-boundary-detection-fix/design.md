# Design Document

## Overview

This design addresses the critical failure in NetWalker's site boundary detection system. The current implementation fails to create separate workbooks for devices matching the `*-CORE-*` pattern, resulting in all devices being placed in a single main workbook regardless of site boundaries. This design provides a comprehensive solution to fix pattern matching, site extraction, device association, and workbook generation.

## Architecture

### Current Architecture Issues
The existing site boundary detection has several critical flaws:
1. **Pattern Matching Failure**: The fnmatch pattern matching is not working correctly
2. **Hostname Processing**: Site boundary detection may not be using cleaned hostnames
3. **Site Extraction Logic**: The logic to extract site names from hostnames is broken
4. **Device Association**: Devices are not being properly associated with their sites
5. **Workbook Generation**: The logic to create separate workbooks is not executing

### Proposed Architecture
```
Configuration → Site Boundary Detector → Site Extractor → Device Associator → Workbook Generator
     ↓                    ↓                   ↓              ↓                ↓
site_boundary_pattern → Pattern Matching → Site Names → Device Groups → Separate Workbooks
```

## Components and Interfaces

### 1. Site Boundary Configuration Handler
**Purpose**: Load and validate site boundary configuration
**Interface**:
```python
class SiteBoundaryConfig:
    def __init__(self, config: Dict[str, Any])
    def get_pattern(self) -> str
    def is_enabled(self) -> bool
    def validate_pattern(self) -> bool
```

### 2. Hostname Cleaner Integration
**Purpose**: Ensure consistent hostname cleaning for pattern matching
**Interface**:
```python
def clean_hostname_for_site_detection(hostname: str) -> str:
    """Clean hostname specifically for site boundary detection"""
    # Remove serial numbers: LUMT-CORE-A(FOX123) → LUMT-CORE-A
    # Handle FQDN: device.domain.com → device
    # Preserve hyphens for pattern matching
```

### 3. Site Boundary Detector
**Purpose**: Identify devices that match the site boundary pattern
**Interface**:
```python
class SiteBoundaryDetector:
    def __init__(self, pattern: str)
    def matches_pattern(self, hostname: str) -> bool
    def extract_site_name(self, hostname: str) -> str
    def find_boundary_devices(self, inventory: Dict) -> Dict[str, List[str]]
```

### 4. Device Site Associator
**Purpose**: Associate all devices with their respective sites
**Interface**:
```python
class DeviceSiteAssociator:
    def __init__(self, boundary_devices: Dict[str, List[str]])
    def associate_device(self, device_info: Dict) -> str
    def get_site_inventories(self, full_inventory: Dict) -> Dict[str, Dict]
```

### 5. Site Workbook Generator
**Purpose**: Create separate workbooks for each site
**Interface**:
```python
class SiteWorkbookGenerator:
    def __init__(self, base_generator: ExcelGenerator)
    def create_site_workbooks(self, site_inventories: Dict[str, Dict]) -> List[str]
    def generate_workbook_name(self, site_name: str, timestamp: str) -> str
```

## Data Models

### Site Boundary Information
```python
@dataclass
class SiteBoundaryInfo:
    site_name: str
    boundary_devices: List[str]
    associated_devices: List[str]
    device_count: int
    workbook_path: str
```

### Device Site Association
```python
@dataclass
class DeviceSiteAssociation:
    device_hostname: str
    site_name: str
    association_method: str  # "boundary_match", "neighbor_of_boundary", "default"
    boundary_device: str     # The boundary device that caused this association
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

<function_calls>
<invoke name="prework">
<parameter name="featureName">site-boundary-detection-fix

### Property 1: Pattern Matching Consistency
*For any* valid hostname and site boundary pattern, the pattern matching function should return consistent results when called multiple times with the same inputs
**Validates: Requirements 1.1, 4.3**

### Property 2: Site Name Extraction Determinism
*For any* hostname that matches the site boundary pattern, extracting the site name should always produce the same result
**Validates: Requirements 1.4, 6.2**

### Property 3: Unique Site Identification
*For any* set of devices matching the site boundary pattern, the system should identify each unique site prefix exactly once
**Validates: Requirements 1.3**

### Property 4: Hostname Cleaning Integration
*For any* hostname with serial numbers in parentheses, pattern matching should work correctly with cleaned hostnames
**Validates: Requirements 1.5, 6.1**

### Property 5: Workbook Creation Completeness
*For any* set of identified sites, the system should create exactly one workbook per site
**Validates: Requirements 2.1**

### Property 6: Filename Format Consistency
*For any* site name and timestamp, the generated workbook filename should follow the format "Discovery_SITENAME_YYYYMMDD-HH-MM.xlsx"
**Validates: Requirements 2.2**

### Property 7: Device Association Completeness
*For any* device in the inventory, it should be associated with exactly one site or the main workbook
**Validates: Requirements 2.3, 3.1**

### Property 8: Neighbor Inclusion Consistency
*For any* device associated with a site boundary, all its neighbors should be included in the same site workbook
**Validates: Requirements 2.4, 3.2**

### Property 9: Configuration Loading Reliability
*For any* valid site boundary pattern in configuration, the system should load and use it correctly
**Validates: Requirements 4.1**

### Property 10: Error Handling Graceful Degradation
*For any* error during site boundary detection, the system should continue and generate the main workbook
**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

### Property 11: Logging Completeness
*For any* site boundary detection operation, all major steps should be logged with appropriate detail
**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

## Error Handling

### Configuration Errors
- **Invalid Pattern**: Log error and disable site boundary detection
- **Missing Pattern**: Disable site boundary detection silently
- **Pattern Compilation Error**: Log error and fall back to no site boundaries

### Runtime Errors
- **Hostname Cleaning Failure**: Fall back to original hostname
- **Site Name Extraction Failure**: Use default site name or main workbook
- **Workbook Creation Failure**: Log error and include devices in main workbook
- **Device Association Failure**: Include device in main workbook

### Recovery Strategies
- **Graceful Degradation**: Always ensure main workbook is created
- **Partial Success**: Create workbooks for successful sites, main workbook for failures
- **Comprehensive Logging**: Log all errors with sufficient detail for debugging

## Testing Strategy

### Unit Testing
- **Pattern Matching**: Test various hostname and pattern combinations
- **Site Name Extraction**: Test extraction logic with different hostname formats
- **Configuration Loading**: Test valid and invalid configuration scenarios
- **Error Handling**: Test all error conditions and recovery paths

### Property-Based Testing
- **Pattern Consistency**: Verify pattern matching is deterministic
- **Site Extraction**: Verify site name extraction is consistent
- **Device Association**: Verify all devices are properly associated
- **Workbook Generation**: Verify correct number of workbooks are created
- **Filename Format**: Verify all generated filenames follow the correct format

### Integration Testing
- **End-to-End**: Test complete site boundary detection with real device data
- **Configuration Integration**: Test with various configuration scenarios
- **Excel Generation**: Verify actual workbook creation and content
- **Logging Integration**: Verify all logging works correctly

### Test Configuration
- Use pytest for unit and integration tests
- Use Hypothesis for property-based testing with minimum 100 iterations per property
- Each property test must reference its design document property
- Tag format: **Feature: site-boundary-detection-fix, Property {number}: {property_text}**