# Requirements Document

## Introduction

The NetWalker Tool is a Windows-based Python application that automatically discovers and maps Cisco network topologies using the Cisco Discovery Protocol (CDP) and the Link Layer Discovery Protocol (LLDP). The system connects to seed devices via SSH/Telnet, recursively discovers neighboring devices, and generates comprehensive documentation in Excel and Microsoft Visio formats.

## Glossary

- **NetWalker**: The network topology discovery application
- **Seed_Device**: Initial network device used as starting point for discovery
- **CDP**: Cisco Discovery Protocol for device neighbor discovery
- **LLDP**: Link Layer Discovery Protocol for device neighbor discovery
- **Discovery_Engine**: Component responsible for breadth-first network traversal
- **Device_Inventory**: Complete collection of discovered device information
- **Topology_Map**: Visual representation of network connections and relationships
- **Connection_Manager**: Component handling SSH/Telnet connections to devices
- **Report_Generator**: Component creating Excel and Visio output files
- **Configuration_Manager**: Component managing INI file settings and CLI options

## Requirements

### Requirement 1: Network Device Discovery

**User Story:** As a network administrator, I want to automatically discover network devices starting from seed devices, so that I can map my entire network topology without manual intervention.

#### Acceptance Criteria

1. WHEN the Discovery_Engine connects to a Seed_Device, THE NetWalker SHALL extract CDP and LLDP neighbor information
2. WHEN neighbor devices are discovered, THE Discovery_Engine SHALL recursively connect to each neighbor for further discovery
3. WHEN discovering devices, THE NetWalker SHALL use breadth-first traversal to systematically explore the network
4. WHEN a device connection fails, THE NetWalker SHALL log the failure and continue with remaining devices
5. WHEN discovery depth limits are configured, THE NetWalker SHALL respect those boundaries during traversal

### Requirement 2: Device Connection Management

**User Story:** As a network administrator, I want the system to connect to devices using SSH with Telnet fallback, so that I can discover devices regardless of their connection capabilities.

#### Acceptance Criteria

1. WHEN connecting to a device, THE Connection_Manager SHALL attempt SSH connection first
2. IF SSH connection fails, THEN THE Connection_Manager SHALL attempt Telnet connection
3. WHEN a connection is established, THE Connection_Manager SHALL record the connection method used
4. WHEN terminating connections, THE Connection_Manager SHALL properly close sessions by sending exit commands
5. WHEN authentication is required, THE Connection_Manager SHALL use credentials from configuration files
6. WHEN running on Windows platform, THE Connection_Manager SHALL use Windows-compatible transport for Telnet connections

### Requirement 3: Device Information Collection

**User Story:** As a network administrator, I want comprehensive device information collected during discovery, so that I have complete inventory data for network management.

#### Acceptance Criteria

1. WHEN connected to a device, THE NetWalker SHALL collect device hostname or IP address
2. WHEN collecting device data, THE NetWalker SHALL extract primary IP address information
3. WHEN analyzing device capabilities, THE NetWalker SHALL determine platform type (IOS/IOS-XE/NX-OS)
4. WHEN gathering system information, THE NetWalker SHALL collect software version, VTP Verion, serial number, hardware model, and uptime
5. WHEN processing discovery data, THE NetWalker SHALL record discovery timestamp and depth level
6. WHEN discovery completes for a device, THE NetWalker SHALL record success/failure status and error details
7. WHEN device is part of a stack, number of members and Serial numbers SHALL be collected and logged in device inventory
### Requirement 4: Network Filtering and Boundaries

**User Story:** As a network administrator, I want to filter devices based on wildcard names and CIDR ranges, so that I can control the scope of network discovery.

#### Acceptance Criteria

1. WHEN filter rules are configured, THE NetWalker SHALL apply wildcard name matching to discovered devices
2. WHEN CIDR filters are specified, THE NetWalker SHALL evaluate device IP addresses against those ranges
3. WHEN a device matches filter criteria, THE NetWalker SHALL add it to inventory but exclude it from further discovery
4. WHEN filtered devices are processed, THE NetWalker SHALL include them in spreadsheet outputs
5. WHEN discovery boundaries are set, THE NetWalker SHALL prevent traversal beyond filtered devices

### Requirement 5: Excel Report Generation

**User Story:** As a network administrator, I want comprehensive Excel reports generated from discovery data, so that I can analyze and document my network topology.

#### Acceptance Criteria

1. WHEN generating reports, THE Report_Generator SHALL create consolidated sheets showing all network connections
2. WHEN creating device inventory, THE Report_Generator SHALL include complete device information in dedicated sheets
3. WHEN processing individual devices, THE Report_Generator SHALL create per-device CDP neighbor detail sheets
4. WHEN formatting Excel output, THE Report_Generator SHALL apply professional formatting with headers, filters, and auto-sizing
5. WHEN multiple seeds are discovered, THE Report_Generator SHALL create a master inventory workbook with consolidated device listings
6. WHEN saving Excel files, THE Report_Generator SHALL use timestamp-based naming convention
7. WHEN displaying device IP addresses in inventory sheets, THE Report_Generator SHALL extract IP addresses from both 'ip_address' and 'primary_ip' fields with proper fallback logic

### Requirement 6: Microsoft Visio Integration

**User Story:** As a network administrator, I want network topology diagrams generated in Microsoft Visio format, so that I can create visual documentation of my network infrastructure.

#### Acceptance Criteria

1. WHEN Visio output is requested, THE Report_Generator SHALL use the vsdx Python library to generate .vsdx files
2. THE NetWalker SHALL NOT require Microsoft Visio to be installed on the system
3. WHEN creating Visio documents, THE Report_Generator SHALL build documents programmatically without external templates
4. WHEN generating topology diagrams, THE Report_Generator SHALL create visual representations of device connections with proper shapes and connectors
5. WHEN generating topology diagrams, THE Report_Generator SHALL organize devices hierarchically (core, distribution, access layers)
6. WHEN generating topology diagrams, THE Report_Generator SHALL use color coding to distinguish device types
7. WHEN generating topology diagrams, THE Report_Generator SHALL include connection labels showing port information

### Requirement 7: Configuration Management

**User Story:** As a network administrator, I want flexible configuration options through INI files and CLI parameters, so that I can customize the tool's behavior for different environments.

#### Acceptance Criteria

1. WHEN the NetWalker starts, THE Configuration_Manager SHALL load settings from netwalker.ini file
2. WHEN CLI options are provided, THE Configuration_Manager SHALL override INI file settings
3. WHEN no configuration exists, THE Configuration_Manager SHALL prompt for seed device and necessary options
4. WHEN creating default configuration, THE Configuration_Manager SHALL populate netwalker.ini with all available options and descriptions
5. WHEN credentials are configured, THE Configuration_Manager SHALL support both encrypted and plain text formats
6. IF secret_creds.ini exists, THEN THE Configuration_Manager SHALL use those credentials for authentication

### Requirement 8: Security and Credential Management

**User Story:** As a network administrator, I want secure credential handling with encryption support, so that I can protect authentication information.

#### Acceptance Criteria

1. WHEN secret_creds.ini exists, THE Configuration_Manager SHALL use it for device authentication
2. IF credentials are stored in plain text, THEN THE Configuration_Manager SHALL encrypt them using MD5 and remove plain text versions, overwriting the secret_creds.ini file
3. WHEN processing credentials, THE Configuration_Manager SHALL not expose them in documentation or CLI output
4. WHEN authentication fails, THE NetWalker SHALL log the failure without exposing credential details
5. WHEN credentials are encrypted, THE Configuration_Manager SHALL decrypt them for connection attempts
6. WHEN log files are written, passwords MUST be excluded

### Requirement 9: DNS Validation and Address Resolution

**User Story:** As a network administrator, I want DNS validation and RFC1918 address conflict detection, so that I can ensure proper network addressing and name resolution.

#### Acceptance Criteria

1. WHEN a device uses a public IP address, THE NetWalker SHALL ping the device by name to obtain private address
2. WHEN performing DNS validation, THE NetWalker SHALL test forward and reverse DNS entries for each device
3. WHEN DNS testing completes, THE NetWalker SHALL create a DNS Excel file reporting success, failure, and discovery details
4. WHEN RFC1918 conflicts are detected, THE NetWalker SHALL attempt to resolve using DNS lookups
5. WHEN address resolution succeeds, THE NetWalker SHALL use the resolved private address for further operations

### Requirement 10: Concurrent Processing and Performance

**User Story:** As a network administrator, I want concurrent device processing capabilities, so that I can efficiently discover large network topologies.

#### Acceptance Criteria

1. WHEN discovering multiple devices, THE NetWalker SHALL support concurrent connection processing
2. WHEN managing concurrent operations, THE NetWalker SHALL limit the number of simultaneous connections
3. WHEN processing devices concurrently, THE NetWalker SHALL maintain thread safety for shared data structures
4. WHEN concurrent operations complete, THE NetWalker SHALL properly synchronize results
5. WHEN errors occur in concurrent processing, THE NetWalker SHALL isolate failures to individual threads

### Requirement 11: Platform Detection and Protocol Support

**User Story:** As a network administrator, I want automatic platform detection and multi-protocol support, so that I can discover diverse Cisco network environments.

#### Acceptance Criteria

1. WHEN connecting to devices, THE NetWalker SHALL execute "show version" command for platform detection
2. WHEN analyzing device output, THE NetWalker SHALL identify platform type (IOS/IOS-XE/NX-OS)
3. WHEN extracting neighbor information, THE NetWalker SHALL parse both CDP and LLDP protocol outputs
4. WHEN processing protocol data, THE NetWalker SHALL extract hostname information from neighbor entries
5. WHEN platform-specific commands are needed, THE NetWalker SHALL adapt command syntax accordingly

### Requirement 12: Output Directory Management

**User Story:** As a network administrator, I want configurable output directories for reports and logs, so that I can organize generated files according to my preferences.

#### Acceptance Criteria

1. WHEN generating Visio and Excel files, THE NetWalker SHALL write them to a configurable reports directory
2. WHEN creating log files, THE NetWalker SHALL write them to a configurable logs directory
3. WHEN no output directories are specified, THE NetWalker SHALL default to .\reports and .\logs respectively
4. WHEN output directories do not exist, THE NetWalker SHALL create them automatically
5. WHEN file naming is required, THE NetWalker SHALL use YYYYMMDD-HH-MM format for timestamps

### Requirement 13: Discovery Timeout and Queue Management

**User Story:** As a network administrator, I want configurable discovery timeouts separate from connection timeouts, so that large network discoveries can complete without premature termination.

#### Acceptance Criteria

1. WHEN discovery timeout is configured, THE NetWalker SHALL use separate timeout values for discovery operations vs individual connections
2. WHEN discovery is running, THE NetWalker SHALL process all queued devices within the discovery timeout window
3. WHEN discovery timeout is reached, THE NetWalker SHALL complete processing of currently active connections before terminating
4. WHEN discovery queue has remaining devices, THE NetWalker SHALL continue processing until timeout or queue empty
5. WHEN discovery completes, THE NetWalker SHALL log summary of processed vs queued devices
6. WHEN new devices are added to the discovery queue after duplicate checking, THE NetWalker SHALL reset the discovery timeout to ensure large networks are not prematurely terminated

### Requirement 14: Enhanced Discovery Logging and Decision Tracking

**User Story:** As a network administrator, I want detailed logging of discovery decisions and filtering logic, so that I can troubleshoot why devices are included or excluded from discovery.

#### Acceptance Criteria

1. WHEN filtering decisions are made, THE NetWalker SHALL log detailed reasoning for inclusion/exclusion
2. WHEN devices are added to discovery queue, THE NetWalker SHALL log queue operations and depth assignments
3. WHEN discovery processing occurs, THE NetWalker SHALL log device processing status and neighbor extraction
4. WHEN Unicode characters cause logging issues, THE NetWalker SHALL use plain text alternatives for file compatibility
5. WHEN log files are written, THE NetWalker SHALL ensure cross-platform compatibility for special characters

### Requirement 15: NEXUS Device Discovery Enhancement

**User Story:** As a network administrator, I want reliable discovery of NEXUS devices and proper neighbor extraction, so that I can map complete network topologies including data center infrastructure.

#### Acceptance Criteria

1. WHEN connecting to NEXUS devices, THE NetWalker SHALL properly extract device hostnames using NX-OS specific patterns
2. WHEN processing NEXUS device neighbors, THE NetWalker SHALL correctly parse both CDP and LLDP neighbor information
3. WHEN NEXUS devices are discovered, THE NetWalker SHALL ensure they are not incorrectly filtered by platform or capability checks
4. WHEN neighbor processing occurs, THE NetWalker SHALL validate that discovered neighbors are properly added to the discovery queue
5. WHEN NEXUS devices have complex interface names, THE NetWalker SHALL correctly parse and normalize interface information