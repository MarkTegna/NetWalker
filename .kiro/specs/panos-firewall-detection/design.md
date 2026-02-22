# Design Document: PAN-OS Firewall Detection Enhancement

## Overview

This design enhances NetWalker's network discovery capabilities to properly detect, connect to, and collect data from PAN-OS (Palo Alto Networks) firewalls. The enhancement addresses three key issues:

1. PAN-OS devices are detected as "Unknown" platform instead of "PAN-OS"
2. SSH connections use wrong device_type (cisco_ios) causing command timeouts
3. Device data extraction fails due to platform-specific output format differences

The solution implements early PAN-OS detection in the Connection Manager before establishing SSH connections, uses the correct netmiko device_type ('paloalto_panos'), and executes PAN-OS-specific commands with appropriate extraction patterns.

## Architecture

### Component Interaction Flow

```
User/Seed File
    ↓
NetWalker App
    ↓
Connection Manager (Enhanced)
    ├─→ Detect PAN-OS from hostname/database
    ├─→ Select device_type ('paloalto_panos' or 'cisco_ios')
    └─→ Establish SSH connection with netmiko
         ↓
Device Collector (Enhanced)
    ├─→ Execute "set cli pager off" (PAN-OS only)
    ├─→ Execute "show system info" (PAN-OS) or "show version" (others)
    ├─→ Extract data using platform-specific patterns
    └─→ Return DeviceInfo with platform="PAN-OS"
         ↓
Database Manager
    └─→ Store/update device with correct platform and capabilities
```

### Key Design Decisions

1. **Early Detection**: PAN-OS detection occurs in Connection Manager before SSH connection, not after
   - Rationale: Netmiko requires device_type at connection time; changing it after connection is not supported
   
2. **Multiple Detection Heuristics**: Use hostname patterns, database platform field, and CDP/LLDP neighbor data
   - Rationale: Devices may be discovered through different paths (seed file, neighbors, re-discovery)
   
3. **Fallback to Default**: Non-matching devices use 'cisco_ios' device_type
   - Rationale: Maintains backward compatibility with existing IOS/IOS-XE/NX-OS discovery
   
4. **Extended Timeout**: PAN-OS "show system info" uses 60-second timeout
   - Rationale: PAN-OS output can be lengthy; default 30-second timeout causes failures

## Components and Interfaces

### Connection Manager Enhancements

**New Method: `_detect_panos_from_context(host: str, db_manager: Optional[DatabaseManager]) -> bool`**

Detects if a device is likely PAN-OS based on available context before connection.

```python
def _detect_panos_from_context(self, host: str, db_manager: Optional[DatabaseManager]) -> bool:
    """
    Detect if device is PAN-OS based on hostname or database information
    
    Args:
        host: Device hostname or IP address
        db_manager: Optional database manager for platform lookup
        
    Returns:
        True if device is likely PAN-OS, False otherwise
    """
    # Check hostname pattern
    if "-fw" in host.lower():
        self.logger.info(f"PAN-OS detected for {host}: hostname contains '-fw'")
        return True
    
    # Check database if available
    if db_manager:
        platform = db_manager.get_device_platform(host)
        if platform:
            platform_lower = platform.lower()
            if any(pattern in platform_lower for pattern in ["palo alto", "pa-", "panos", "pan-os"]):
                self.logger.info(f"PAN-OS detected for {host}: database platform='{platform}'")
                return True
    
    return False
```

**Modified Method: `_try_netmiko_ssh_connection()`**

Update to accept device_type parameter and use PAN-OS detection.

```python
def _try_netmiko_ssh_connection(self, host: str, credentials: Credentials, 
                                start_time: float, db_manager: Optional[DatabaseManager] = None) -> Tuple[Optional[Any], ConnectionResult]:
    """
    Attempt SSH connection using netmiko with platform detection
    
    Args:
        host: Device hostname or IP address
        credentials: Authentication credentials
        start_time: Connection attempt start time
        db_manager: Optional database manager for platform lookup
        
    Returns:
        Tuple of (connection object, connection result)
    """
    # Detect if this is a PAN-OS device
    is_panos = self._detect_panos_from_context(host, db_manager)
    
    # Select appropriate device_type
    device_type = 'paloalto_panos' if is_panos else 'cisco_ios'
    
    self.logger.info(f"Using device_type='{device_type}' for {host}")
    
    # Netmiko device parameters
    device_params = {
        'device_type': device_type,  # Platform-specific
        'host': host,
        'username': credentials.username,
        'password': credentials.password,
        # ... rest of parameters
    }
    
    # ... rest of connection logic
```

**Modified Method: `connect_device()`**

Update to pass database manager to SSH connection method.

```python
def connect_device(self, host: str, credentials: Credentials, 
                  db_manager: Optional[DatabaseManager] = None) -> Tuple[Optional[Any], ConnectionResult]:
    """
    Establish connection to device with platform detection
    
    Args:
        host: Device hostname or IP address
        credentials: Authentication credentials
        db_manager: Optional database manager for platform lookup
        
    Returns:
        Tuple of (connection object, connection result)
    """
    # ... validation logic
    
    # Try SSH with platform detection
    connection, result = self._try_netmiko_ssh_connection(host, credentials, start_time, db_manager)
    
    # ... rest of connection logic
```

### Device Collector Enhancements

**Modified Method: `collect_device_information()`**

Update PAN-OS detection logic to rely on connection type rather than post-connection testing.

```python
def collect_device_information(self, connection: Any, host: str, 
                              connection_method: str, discovery_depth: int = 0, 
                              is_seed: bool = False) -> Optional[DeviceInfo]:
    """
    Collect comprehensive device information with PAN-OS support
    
    Args:
        connection: Active netmiko or scrapli connection
        host: Device hostname or IP
        connection_method: SSH or Telnet
        discovery_depth: Current discovery depth level
        is_seed: Whether this is a seed device
        
    Returns:
        DeviceInfo object or None if collection failed
    """
    try:
        self.logger.info(f"Collecting device information from {host}")
        
        # Detect if this is a PAN-OS device from connection type
        is_panos = False
        if hasattr(connection, 'device_type'):
            is_panos = connection.device_type == 'paloalto_panos'
            if is_panos:
                self.logger.info(f"PAN-OS device detected from connection device_type: {host}")
        
        # Execute platform-specific commands
        if is_panos:
            # Disable pager for PAN-OS
            self._execute_command(connection, "set cli pager off")
            
            # Get system info with extended timeout
            version_output = self._execute_command(connection, "show system info", timeout=60)
            
            # Add marker for platform detection
            if version_output:
                version_output = "PAN-OS\n" + version_output
        else:
            # Standard Cisco command
            version_output = self._execute_command(connection, "show version")
        
        if not version_output:
            return self._create_failed_device_info(host, connection_method, 
                                                  discovery_depth, is_seed, 
                                                  "Failed to get version information")
        
        # Extract device information using platform-specific patterns
        hostname = self._extract_hostname(version_output, host)
        primary_ip = self._extract_primary_ip(connection, host)
        platform = self._detect_platform(version_output)
        software_version = self._extract_software_version(version_output)
        serial_number = self._extract_serial_number(version_output)
        hardware_model = self._extract_hardware_model(version_output)
        uptime = self._extract_uptime(version_output)
        
        # Skip VTP for PAN-OS
        vtp_version = None if platform == "PAN-OS" else self._get_vtp_version(connection)
        
        # Determine capabilities
        capabilities = self._determine_capabilities(version_output, platform)
        
        # ... rest of collection logic
```

**Modified Method: `_detect_platform()`**

Already has PAN-OS detection patterns - no changes needed.

```python
def _detect_platform(self, version_output: str) -> str:
    """Detect device platform from version output"""
    version_lower = version_output.lower()
    
    # Check for PAN-OS (Palo Alto) - multiple detection patterns
    if any(pattern in version_lower for pattern in ["panos", "pan-os", "sw-version:", "palo alto", "pa-"]):
        return "PAN-OS"
    elif "nx-os" in version_lower or "nexus" in version_lower:
        return "NX-OS"
    elif "ios-xe" in version_lower:
        return "IOS-XE"
    elif "ios" in version_lower:
        return "IOS"
    else:
        return "Unknown"
```

**Modified Method: `_determine_capabilities()`**

Add PAN-OS capability detection.

```python
def _determine_capabilities(self, version_output: str, platform: str) -> List[str]:
    """Determine device capabilities based on platform and output"""
    capabilities = []
    
    if platform == "PAN-OS":
        # PAN-OS devices are firewalls with routing capability
        capabilities = ["Firewall", "Router"]
    elif "switch" in version_output.lower():
        capabilities.append("Switch")
        if "router" in version_output.lower():
            capabilities.append("Router")
    elif "router" in version_output.lower():
        capabilities.append("Router")
    
    return capabilities if capabilities else ["Unknown"]
```

### Database Manager Enhancements

**New Method: `get_device_platform(host: str) -> Optional[str]`**

Retrieve platform for a device by hostname or IP address.

```python
def get_device_platform(self, host: str) -> Optional[str]:
    """
    Get platform for a device by hostname or IP address
    
    Args:
        host: Device hostname or IP address
        
    Returns:
        Platform string or None if not found
    """
    try:
        cursor = self.conn.cursor()
        
        # Try by hostname first
        cursor.execute("""
            SELECT platform 
            FROM devices 
            WHERE hostname = ? OR primary_ip = ?
            LIMIT 1
        """, (host, host))
        
        row = cursor.fetchone()
        return row[0] if row else None
        
    except Exception as e:
        self.logger.error(f"Failed to get platform for {host}: {e}")
        return None
```

### NetWalker App Integration

**Modified: Discovery initialization**

Pass database manager to connection manager for platform lookup.

```python
# In netwalker_app.py or main discovery loop
connection, result = connection_manager.connect_device(
    host=device_host,
    credentials=credentials,
    db_manager=database_manager  # Pass database manager
)
```

## Data Models

### DeviceInfo

No changes to DeviceInfo structure - existing fields support PAN-OS data:

```python
@dataclass
class DeviceInfo:
    hostname: str              # From "hostname: VALUE"
    primary_ip: str           # From connection or interface data
    platform: str             # Set to "PAN-OS"
    capabilities: List[str]   # Set to ["Firewall", "Router"]
    software_version: str     # From "sw-version: VALUE"
    serial_number: str        # From "serial: VALUE"
    hardware_model: str       # From "model: VALUE"
    # ... other fields unchanged
```

### PAN-OS Output Format

Example "show system info" output:

```
hostname: FW-SITE-01
model: PA-5220
serial: 013201032480
sw-version: 10.2.12-h4
app-version: 8799-8432
threat-version: 8799-8432
wildfire-version: 0
url-filtering-version: 20240101.20001
```

### Extraction Patterns

PAN-OS-specific regex patterns (already implemented):

```python
# Hostname: "hostname: VALUE"
hostname_pattern = r'^hostname:\s*(\S+)'

# Model: "model: VALUE"
model_pattern = r'^model:\s*(\S+)'

# Serial: "serial: VALUE"
serial_pattern = r'^serial:\s*(\S+)'

# Software version: "sw-version: VALUE"
version_pattern = r'sw-version:\s+([^\s,]+)'
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Device Type Selection Based on Detection

*For any* device hostname or database platform value, when the hostname contains "-fw" (case-insensitive) OR the platform contains "palo alto", "pa-", "panos", or "pan-os" (case-insensitive), the Connection Manager should select device_type 'paloalto_panos'; otherwise, it should select 'cisco_ios'.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: Platform-Specific Command Selection

*For any* device connection, when the device_type is 'paloalto_panos', the Device Collector should execute "show system info"; when the device_type is not 'paloalto_panos', the Device Collector should execute "show version".

**Validates: Requirements 2.2, 5.2**

### Property 3: PAN-OS Data Extraction Completeness

*For any* valid PAN-OS "show system info" output containing the patterns "hostname: X", "model: Y", "serial: Z", and "sw-version: W", the Device Collector should extract all four values correctly; for any output missing a pattern, the corresponding field should be set to "Unknown".

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

### Property 4: PAN-OS Platform Detection

*For any* device output containing "panos", "pan-os", "sw-version:", "palo alto", or "pa-" (case-insensitive), the Device Collector should set the platform field to exactly "PAN-OS".

**Validates: Requirements 4.1, 4.3**

### Property 5: PAN-OS Capability Assignment

*For any* device with platform set to "PAN-OS", the Device Collector should set capabilities to include both "Firewall" and "Router".

**Validates: Requirements 4.2**

### Property 6: Backward Compatibility for Non-PAN-OS Devices

*For any* device with platform IOS, IOS-XE, or NX-OS, the enhanced system should produce identical DeviceInfo results (hostname, platform, software_version, serial_number, hardware_model) as the original implementation.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

### Property 7: Database Query Consistency

*For any* set of devices stored in the database with various platform values, querying for platform "PAN-OS" should return all and only those devices where platform equals "PAN-OS".

**Validates: Requirements 4.4**

## Error Handling

### Connection Failures

**PAN-OS Connection Timeout**
- Symptom: SSH connection to PAN-OS device times out
- Cause: Network connectivity issues or incorrect credentials
- Handling: Log error with device_type used, return ConnectionResult with FAILED status
- Recovery: User can retry with correct credentials or check network connectivity

**Wrong Device Type Selected**
- Symptom: Commands fail or timeout after connection established
- Cause: Detection heuristics incorrectly identified device platform
- Handling: Log command failure, mark device collection as failed
- Recovery: Manual correction of device platform in database, re-discovery

### Data Collection Failures

**Command Timeout**
- Symptom: "show system info" command times out (>60 seconds)
- Cause: Device is slow to respond or output is extremely large
- Handling: Log timeout with command and duration, return failed DeviceInfo
- Recovery: Increase timeout in configuration, retry collection

**Extraction Pattern Mismatch**
- Symptom: Regex patterns don't match PAN-OS output format
- Cause: PAN-OS version has different output format
- Handling: Set field to "Unknown", log which field failed with pattern used
- Recovery: Update extraction patterns for new PAN-OS version format

**Missing Required Fields**
- Symptom: PAN-OS output doesn't contain expected fields
- Cause: Incomplete command output or device configuration issue
- Handling: Set missing fields to "Unknown", continue with available data
- Recovery: Investigate device configuration, verify command output manually

### Database Errors

**Platform Lookup Failure**
- Symptom: Cannot retrieve platform from database for detection
- Cause: Database connection issue or device not in database
- Handling: Fall back to hostname-based detection only, log warning
- Recovery: Database connection will be retried on next operation

**Update Failure**
- Symptom: Cannot update device record with new PAN-OS data
- Cause: Database lock or constraint violation
- Handling: Log error with device details, continue discovery
- Recovery: Re-discovery will retry update

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs
- Both approaches are complementary and necessary

### Unit Testing Focus

Unit tests should cover:

1. **Specific Examples**
   - Known PAN-OS hostname patterns ("-fw", "-FW", "-Fw")
   - Known PAN-OS platform strings from database
   - Sample PAN-OS "show system info" output
   - Sample IOS/NX-OS "show version" output

2. **Edge Cases**
   - Empty hostname
   - Hostname with multiple "-fw" occurrences
   - Database returns None for platform
   - PAN-OS output with missing fields
   - PAN-OS output with extra whitespace

3. **Error Conditions**
   - Connection timeout
   - Command execution failure
   - Regex pattern mismatch
   - Database query failure

4. **Integration Points**
   - Connection Manager → Device Collector handoff
   - Device Collector → Database Manager storage
   - NetWalker App → Connection Manager initialization

### Property-Based Testing Configuration

Property tests should be implemented using Python's `hypothesis` library with the following configuration:

- **Minimum iterations**: 100 per property test
- **Test tagging**: Each test must reference its design property
- **Tag format**: `# Feature: panos-firewall-detection, Property N: [property title]`

### Property Test Specifications

**Property 1: Device Type Selection**
```python
# Feature: panos-firewall-detection, Property 1: Device Type Selection Based on Detection
@given(hostname=text(), platform=text())
def test_device_type_selection(hostname, platform):
    # Generate random hostnames and platform values
    # Verify correct device_type is selected based on patterns
```

**Property 2: Platform-Specific Command Selection**
```python
# Feature: panos-firewall-detection, Property 2: Platform-Specific Command Selection
@given(device_type=sampled_from(['paloalto_panos', 'cisco_ios', 'cisco_nxos']))
def test_command_selection(device_type):
    # Verify correct command is selected for each device_type
```

**Property 3: PAN-OS Data Extraction**
```python
# Feature: panos-firewall-detection, Property 3: PAN-OS Data Extraction Completeness
@given(hostname=text(), model=text(), serial=text(), version=text(), 
       include_hostname=booleans(), include_model=booleans(), 
       include_serial=booleans(), include_version=booleans())
def test_panos_extraction(hostname, model, serial, version, 
                         include_hostname, include_model, 
                         include_serial, include_version):
    # Generate PAN-OS output with random field presence
    # Verify extraction returns correct values or "Unknown"
```

**Property 4: PAN-OS Platform Detection**
```python
# Feature: panos-firewall-detection, Property 4: PAN-OS Platform Detection
@given(output=text(), pattern=sampled_from(['panos', 'pan-os', 'sw-version:', 'palo alto', 'pa-']))
def test_platform_detection(output, pattern):
    # Generate output containing PAN-OS patterns
    # Verify platform is set to "PAN-OS"
```

**Property 5: PAN-OS Capability Assignment**
```python
# Feature: panos-firewall-detection, Property 5: PAN-OS Capability Assignment
@given(platform=just("PAN-OS"))
def test_capability_assignment(platform):
    # Verify capabilities include "Firewall" and "Router"
```

**Property 6: Backward Compatibility**
```python
# Feature: panos-firewall-detection, Property 6: Backward Compatibility for Non-PAN-OS Devices
@given(platform=sampled_from(['IOS', 'IOS-XE', 'NX-OS']))
def test_backward_compatibility(platform):
    # Generate device data for non-PAN-OS platforms
    # Compare results with original implementation
```

**Property 7: Database Query Consistency**
```python
# Feature: panos-firewall-detection, Property 7: Database Query Consistency
@given(devices=lists(tuples(text(), sampled_from(['PAN-OS', 'IOS', 'NX-OS', 'Unknown']))))
def test_database_query(devices):
    # Create random devices with various platforms
    # Query for "PAN-OS" and verify only PAN-OS devices returned
```

### Test Execution

Run all tests with:
```bash
# Unit tests
pytest tests/test_panos_detection.py -v

# Property tests (minimum 100 iterations)
pytest tests/test_panos_properties.py -v --hypothesis-seed=random
```

### Coverage Goals

- **Line coverage**: >90% for modified files
- **Branch coverage**: >85% for conditional logic
- **Property coverage**: 100% of correctness properties tested
