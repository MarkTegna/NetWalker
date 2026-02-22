# Requirements Document

## Introduction

This document specifies requirements for improving PAN-OS (Palo Alto Networks) firewall detection and data collection in the NetWalker network discovery tool. Currently, PAN-OS devices are incorrectly detected as "Unknown" platform and connection attempts fail due to using the wrong netmiko device_type. This enhancement will enable proper detection, connection, and data extraction for PAN-OS firewalls.

## Glossary

- **NetWalker**: Network discovery tool that connects to network devices via SSH/Telnet and collects device information
- **Connection_Manager**: Component responsible for establishing SSH/Telnet connections to network devices
- **Device_Collector**: Component responsible for collecting device information after connection is established
- **PAN-OS**: Palo Alto Networks operating system running on PA-series firewalls
- **Netmiko**: Python library used for SSH connections to network devices
- **Device_Type**: Netmiko parameter that specifies the platform-specific command set and behavior
- **Platform**: The operating system or device type (e.g., IOS, NX-OS, PAN-OS)
- **CDP/LLDP**: Cisco Discovery Protocol / Link Layer Discovery Protocol used to discover neighbor devices
- **Seed_Device**: Initial device specified by user to start network discovery

## Requirements

### Requirement 1: Early PAN-OS Detection

**User Story:** As a network administrator, I want PAN-OS devices to be detected before establishing the SSH connection, so that the correct device_type is used from the start.

#### Acceptance Criteria

1. WHEN a device hostname contains "-fw" (case-insensitive), THEN THE Connection_Manager SHALL attempt connection using device_type 'paloalto_panos'
2. WHEN a device platform field in the database contains "palo alto" or "pa-" (case-insensitive), THEN THE Connection_Manager SHALL attempt connection using device_type 'paloalto_panos'
3. WHEN a device is discovered via CDP/LLDP with platform containing "Palo Alto Networks", THEN THE Connection_Manager SHALL attempt connection using device_type 'paloalto_panos'
4. WHEN PAN-OS detection patterns do not match, THEN THE Connection_Manager SHALL use device_type 'cisco_ios' as default
5. WHEN device_type is set to 'paloalto_panos', THEN THE Connection_Manager SHALL log the detection reason

### Requirement 2: PAN-OS Command Execution

**User Story:** As a network administrator, I want PAN-OS-specific commands to execute successfully, so that device information can be collected without timeouts.

#### Acceptance Criteria

1. WHEN connected to a PAN-OS device, THEN THE Device_Collector SHALL execute "set cli pager off" before collecting information
2. WHEN connected to a PAN-OS device, THEN THE Device_Collector SHALL execute "show system info" instead of "show version"
3. WHEN executing "show system info" on PAN-OS, THEN THE Device_Collector SHALL use a timeout of at least 60 seconds
4. WHEN "show system info" completes successfully, THEN THE Device_Collector SHALL return the complete output
5. IF "show system info" times out or fails, THEN THE Device_Collector SHALL log the error and mark collection as failed

### Requirement 3: PAN-OS Data Extraction

**User Story:** As a network administrator, I want device information extracted correctly from PAN-OS output, so that accurate data is stored in the database.

#### Acceptance Criteria

1. WHEN parsing PAN-OS output, THEN THE Device_Collector SHALL extract hostname from "hostname: VALUE" pattern
2. WHEN parsing PAN-OS output, THEN THE Device_Collector SHALL extract model from "model: VALUE" pattern
3. WHEN parsing PAN-OS output, THEN THE Device_Collector SHALL extract serial number from "serial: VALUE" pattern
4. WHEN parsing PAN-OS output, THEN THE Device_Collector SHALL extract software version from "sw-version: VALUE" pattern
5. WHEN any extraction pattern fails to match, THEN THE Device_Collector SHALL set that field to "Unknown"

### Requirement 4: PAN-OS Platform Classification

**User Story:** As a network administrator, I want PAN-OS devices to be correctly classified in the database, so that I can identify and filter firewall devices.

#### Acceptance Criteria

1. WHEN device output contains "panos", "pan-os", "sw-version:", "palo alto", or "pa-" (case-insensitive), THEN THE Device_Collector SHALL set platform to "PAN-OS"
2. WHEN platform is set to "PAN-OS", THEN THE Device_Collector SHALL set capabilities to include "Firewall" and "Router"
3. WHEN a device is stored in the database with platform "PAN-OS", THEN THE platform field SHALL contain exactly "PAN-OS"
4. WHEN querying devices by platform, THEN THE System SHALL return all devices with platform "PAN-OS"

### Requirement 5: Backward Compatibility

**User Story:** As a network administrator, I want existing non-PAN-OS device discovery to continue working unchanged, so that the enhancement does not break current functionality.

#### Acceptance Criteria

1. WHEN a device does not match PAN-OS detection patterns, THEN THE Connection_Manager SHALL use device_type 'cisco_ios'
2. WHEN connected to a non-PAN-OS device, THEN THE Device_Collector SHALL execute "show version" command
3. WHEN connected to a non-PAN-OS device, THEN THE Device_Collector SHALL use existing extraction patterns
4. WHEN connected to a non-PAN-OS device, THEN THE Device_Collector SHALL set platform using existing detection logic
5. WHEN processing IOS, IOS-XE, or NX-OS devices, THEN THE System SHALL produce identical results to current implementation

### Requirement 6: Error Handling and Logging

**User Story:** As a network administrator, I want clear error messages and logging for PAN-OS connection issues, so that I can troubleshoot problems effectively.

#### Acceptance Criteria

1. WHEN PAN-OS detection occurs, THEN THE Connection_Manager SHALL log the detection method and reason
2. WHEN connection to PAN-OS device fails, THEN THE Connection_Manager SHALL log the failure with device_type used
3. WHEN "show system info" times out, THEN THE Device_Collector SHALL log the timeout with command and duration
4. WHEN data extraction fails for any field, THEN THE Device_Collector SHALL log which field failed and the pattern used
5. WHEN device collection completes, THEN THE Device_Collector SHALL log success with platform and key fields extracted

### Requirement 7: Database Update for Existing Devices

**User Story:** As a network administrator, I want existing PAN-OS devices in the database to be re-discovered with correct information, so that historical data is corrected.

#### Acceptance Criteria

1. WHEN a device with platform containing "Palo Alto Networks" is re-discovered, THEN THE System SHALL update platform to "PAN-OS"
2. WHEN a device with platform "Unknown" is re-discovered and detected as PAN-OS, THEN THE System SHALL update platform to "PAN-OS"
3. WHEN a PAN-OS device is re-discovered, THEN THE System SHALL update all fields (hostname, model, serial, software version)
4. WHEN a PAN-OS device is re-discovered, THEN THE System SHALL update capabilities to include "Firewall" and "Router"
5. WHEN database update completes, THEN THE System SHALL log the number of devices updated
