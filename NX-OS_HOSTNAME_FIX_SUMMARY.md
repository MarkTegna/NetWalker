# NX-OS Hostname Extraction Fix

## Problem Description

NX-OS devices were showing with a hostname of "kernel" instead of their actual device names. This was caused by the hostname extraction logic incorrectly parsing the `show version` output.

## Root Cause

The original hostname extraction used a single regex pattern:
```python
self.hostname_pattern = re.compile(r'^(\S+)\s+uptime is', re.MULTILINE | re.IGNORECASE)
```

In NX-OS `show version` output, there's a line like:
```
kernel uptime is 0 day(s), 2 hour(s), 15 minute(s), 23 second(s)
```

This pattern matched "kernel" as the hostname because it was the first word on a line containing "uptime is".

## Solution Implemented

Enhanced the `_extract_hostname` method in `netwalker/discovery/device_collector.py` with multiple extraction patterns:

### 1. NX-OS Device Name Pattern
```python
nxos_hostname_match = re.search(r'Device name:\s*(\S+)', version_output, re.IGNORECASE)
```
Looks for "Device name: hostname" format specific to NX-OS.

### 2. Prompt Pattern
```python
prompt_match = re.search(r'^(\S+)[#>]\s*$', version_output, re.MULTILINE)
```
Extracts hostname from command prompts (hostname# or hostname>).

### 3. Enhanced Original Pattern with Filtering
```python
if potential_hostname.lower() not in ['kernel', 'system', 'device', 'switch', 'router']:
    hostname = potential_hostname
```
Uses the original pattern but excludes system words that aren't actual hostnames.

### 4. IOS-Specific Pattern
```python
ios_hostname_match = re.search(r'^([A-Za-z][A-Za-z0-9_-]*)\s+uptime is', version_output, re.MULTILINE | re.IGNORECASE)
```
More restrictive pattern for IOS devices that requires hostnames to start with a letter.

## Hardware Model Extraction Enhancement

Also fixed hardware model extraction to handle different formats:

### 1. Model Number Field (NX-OS)
```python
r'Model [Nn]umber\s*:\s*([\w-]+)'
```

### 2. Cisco Platform Line (IOS)
```python
r'Cisco\s+(\d+[A-Z]*)\s+\('
```
Extracts model from "Cisco 2911 (revision 1.0)" format.

### 3. Hardware Description
```python
r'cisco\s+([\w-]+)\s+'
```
Fallback pattern with filtering for non-model words.

## Testing

- Created comprehensive test cases for both NX-OS and IOS hostname extraction
- Verified the fix correctly extracts "NEXUS-SWITCH-01" from NX-OS output
- Confirmed it still works correctly for IOS devices
- Ensured "kernel" is properly rejected as a hostname
- All existing property-based tests pass

## Files Modified

1. `netwalker/discovery/device_collector.py`
   - Enhanced `_extract_hostname()` method with multiple patterns
   - Enhanced `_extract_hardware_model()` method with multiple patterns
   - Enhanced `_execute_command()` method for better mock compatibility

2. `tests/property/test_device_collection_properties.py`
   - Fixed mock setup to properly simulate scrapli connections

## Impact

- NX-OS devices will now show their correct hostnames instead of "kernel"
- IOS devices continue to work as before
- Hardware model extraction is more robust across platforms
- Better debugging with added logging for hostname extraction patterns

## Validation

The fix has been validated with:
- Unit tests for hostname extraction patterns
- Property-based tests for device collection
- Mock testing for both connection types
- Real-world NX-OS and IOS show version outputs

This fix ensures accurate device identification across all supported Cisco platforms.