# Design Document: NX-OS Device Information Extraction Fix

## Overview

This design enhances the `DeviceCollector` class to correctly extract software version and hardware model information from Cisco NX-OS devices while maintaining backward compatibility with IOS and IOS-XE devices.

## Architecture

The solution modifies two extraction methods in `DeviceCollector`:
- `_extract_software_version()`: Add NX-OS-specific version pattern with priority ordering
- `_extract_hardware_model()`: Add NX-OS chassis pattern with priority ordering

Both methods will use a platform-aware pattern matching approach where platform-specific patterns are checked before generic fallback patterns.

## Components and Interfaces

### Modified Component: DeviceCollector

**File**: `netwalker/discovery/device_collector.py`

**Modified Methods**:

1. `_extract_software_version(version_output: str) -> str`
   - **Input**: Raw text from "show version" command
   - **Output**: Software version string (e.g., "9.3(9)", "17.12.06")
   - **Behavior**: Check patterns in priority order, return first match

2. `_extract_hardware_model(version_output: str) -> str`
   - **Input**: Raw text from "show version" command
   - **Output**: Hardware model string (e.g., "C9396PX", "ISR4451-X/K9")
   - **Behavior**: Check patterns in priority order, return first match

## Data Models

No changes to data models. The `DeviceInfo` class already has fields for:
- `software_version: str`
- `hardware_model: str`

## Implementation Details

### Software Version Extraction

**Pattern Priority Order**:

1. **NX-OS Pattern** (highest priority)
   - Regex: `r'NXOS:\s+version\s+([^\s,]+)'`
   - Matches: "NXOS: version 9.3(9)"
   - Captures: "9.3(9)"

2. **System Version Pattern** (NX-OS fallback)
   - Regex: `r'System version:\s+([^\s,]+)'`
   - Matches: "System version: 9.3(9)"
   - Captures: "9.3(9)"

3. **Generic Version Pattern** (IOS/IOS-XE)
   - Regex: `r'Version\s+([^\s,]+)'`
   - Matches: "Version 17.12.06"
   - Captures: "17.12.06"
   - **Note**: This pattern currently matches license text, so NX-OS patterns must be checked first

### Hardware Model Extraction

**Pattern Priority Order**:

1. **Model Number Field** (all platforms)
   - Regex: `r'Model [Nn]umber\s*:\s*([\w-]+)'`
   - Matches: "Model Number: C9396PX"
   - Captures: "C9396PX"

2. **NX-OS Chassis Pattern** (Nexus switches)
   - Regex: `r'cisco\s+Nexus\d+\s+(C\d+[A-Z]*)\s+Chassis'`
   - Matches: "cisco Nexus9000 C9396PX Chassis"
   - Captures: "C9396PX"

3. **Processor Line Pattern** (ISR/ASR routers)
   - Regex: `r'cisco\s+([\w-]+/[\w-]+)\s+\([^)]+\)\s+processor'`
   - Matches: "cisco ISR4451-X/K9 (OVLD-2RU) processor"
   - Captures: "ISR4451-X/K9"

4. **IOS Switch Pattern** (Catalyst switches)
   - Regex: `r'Cisco\s+(\d+[A-Z]*)\s+\('`
   - Matches: "Cisco 2960 (revision 1.0)"
   - Captures: "2960"

5. **Generic Cisco Pattern** (fallback)
   - Regex: `r'cisco\s+([\w-]+)\s+'`
   - Matches: "cisco MODELNAME "
   - Captures: "MODELNAME"
   - Filter: Exclude ['systems', 'nexus', 'catalyst', 'ios']

### Pseudocode

```python
def _extract_software_version(version_output: str) -> str:
    # Pattern 1: NX-OS specific
    nxos_match = re.search(r'NXOS:\s+version\s+([^\s,]+)', version_output, IGNORECASE)
    if nxos_match:
        return nxos_match.group(1).strip()
    
    # Pattern 2: System version (NX-OS fallback)
    system_match = re.search(r'System version:\s+([^\s,]+)', version_output, IGNORECASE)
    if system_match:
        return system_match.group(1).strip()
    
    # Pattern 3: Generic version (IOS/IOS-XE)
    version_match = re.search(r'Version\s+([^\s,]+)', version_output, IGNORECASE)
    if version_match:
        return version_match.group(1).strip()
    
    return "Unknown"

def _extract_hardware_model(version_output: str) -> str:
    # Pattern 1: Model Number field (all platforms)
    model_match = re.search(r'Model [Nn]umber\s*:\s*([\w-]+)', version_output, IGNORECASE)
    if model_match:
        return model_match.group(1).strip()
    
    # Pattern 2: NX-OS Chassis
    nexus_match = re.search(r'cisco\s+Nexus\d+\s+(C\d+[A-Z]*)\s+Chassis', version_output, IGNORECASE)
    if nexus_match:
        return nexus_match.group(1).strip()
    
    # Pattern 3: Processor line (ISR/ASR)
    processor_match = re.search(r'cisco\s+([\w-]+/[\w-]+)\s+\([^)]+\)\s+processor', version_output, IGNORECASE)
    if processor_match:
        return processor_match.group(1).strip()
    
    # Pattern 4: IOS switch
    cisco_model_match = re.search(r'Cisco\s+(\d+[A-Z]*)\s+\(', version_output, IGNORECASE)
    if cisco_model_match:
        return cisco_model_match.group(1).strip()
    
    # Pattern 5: Generic fallback
    hardware_match = re.search(r'cisco\s+([\w-]+)\s+', version_output, IGNORECASE)
    if hardware_match:
        model = hardware_match.group(1).strip()
        if model.lower() not in ['systems', 'nexus', 'catalyst', 'ios']:
            return model
    
    return "Unknown"
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: NX-OS Version Extraction Accuracy
*For any* NX-OS device output containing "NXOS: version X.X(X)", the extracted software version should match the NX-OS version string, not any license text version strings.

**Validates: Requirements 1.1, 1.3**

### Property 2: NX-OS Hardware Model Extraction Accuracy
*For any* NX-OS device output containing "cisco NexusXXXX CXXXXXX Chassis", the extracted hardware model should be the model number (CXXXXXX) without the "Chassis" suffix.

**Validates: Requirements 2.1, 2.2**

### Property 3: IOS/IOS-XE Backward Compatibility
*For any* IOS or IOS-XE device output, the extracted software version and hardware model should match the same values as before the NX-OS enhancement.

**Validates: Requirements 1.4, 2.3, 2.4**

### Property 4: Pattern Priority Enforcement
*For any* device output containing multiple version or model patterns, the extraction should return the result from the highest-priority matching pattern for that platform.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 5: License Text Exclusion
*For any* device output containing GPL license version strings, those version strings should never be returned as the device software version.

**Validates: Requirements 4.1, 4.2**

## Error Handling

- If no patterns match, return "Unknown" (existing behavior)
- Invalid regex patterns will raise exceptions during module load (fail-fast)
- Empty or None input returns "Unknown"

## Testing Strategy

### Unit Tests

Test specific examples for each device type:

1. **NX-OS Version Extraction**
   - Test with sample NX-OS output containing license text
   - Verify "9.3(9)" is extracted, not "2.0" from license
   - Test with various NX-OS version formats: X.X(X), X.X(X)X

2. **NX-OS Hardware Extraction**
   - Test with Nexus 9000 series output
   - Test with Nexus 5000 series output
   - Test with Nexus 7000 series output
   - Verify model number extracted without "Chassis" suffix

3. **IOS/IOS-XE Backward Compatibility**
   - Test with ISR router output (verify ISR4451-X/K9 still works)
   - Test with Catalyst switch output
   - Test with IOS-XE router output

4. **Edge Cases**
   - Empty output
   - Output with no version information
   - Output with multiple Cisco devices mentioned
   - Malformed version strings

### Property-Based Tests

1. **Property Test: NX-OS Version Priority**
   - Generate random NX-OS outputs with license text
   - Verify NX-OS version always extracted over license version
   - **Feature: nxos-extraction-fix, Property 1: NX-OS Version Extraction Accuracy**

2. **Property Test: Hardware Model Format**
   - Generate random device outputs with various model formats
   - Verify extracted model matches expected format for platform
   - **Feature: nxos-extraction-fix, Property 2: NX-OS Hardware Model Extraction Accuracy**

3. **Property Test: Backward Compatibility**
   - Generate random IOS/IOS-XE outputs
   - Verify extraction matches pre-enhancement behavior
   - **Feature: nxos-extraction-fix, Property 3: IOS/IOS-XE Backward Compatibility**

### Integration Tests

- Run discovery against real NX-OS devices (DFW1-CORE-A)
- Run discovery against real IOS-XE devices (BORO-UW01)
- Verify inventory reports show correct versions and models
- Verify database stores correct information

### Testing Configuration

- Minimum 100 iterations per property test
- Each property test references its design document property
- Both unit tests and property tests are required for comprehensive coverage
