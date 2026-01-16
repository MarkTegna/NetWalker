# Requirements Document: NX-OS Device Information Extraction Fix

## Introduction

NetWalker currently fails to correctly extract software version and hardware model information from Cisco NX-OS (Nexus) devices. The generic extraction patterns match incorrect data from license text and don't recognize NX-OS-specific output formats.

## Glossary

- **NX-OS**: Cisco Nexus Operating System, used on Nexus switches
- **IOS**: Cisco Internetwork Operating System, used on routers and switches
- **IOS-XE**: Modern Cisco IOS with Linux kernel
- **Device_Collector**: NetWalker component that extracts device information
- **Version_Output**: Text output from "show version" command
- **Hardware_Model**: Device model number (e.g., C9396PX, ISR4451-X/K9)
- **Software_Version**: Operating system version (e.g., 9.3(9), 17.12.06)

## Requirements

### Requirement 1: Extract NX-OS Software Version

**User Story:** As a network administrator, I want NetWalker to correctly identify NX-OS software versions, so that I can accurately track device firmware in my inventory.

#### Acceptance Criteria

1. WHEN a device is running NX-OS, THE Device_Collector SHALL extract the version from the "NXOS: version X.X(X)" line
2. WHEN the Version_Output contains multiple version strings, THE Device_Collector SHALL prioritize platform-specific patterns over generic patterns
3. WHEN extracting NX-OS version, THE Device_Collector SHALL ignore version strings in license text
4. THE Device_Collector SHALL maintain backward compatibility with IOS and IOS-XE version extraction

### Requirement 2: Extract NX-OS Hardware Model

**User Story:** As a network administrator, I want NetWalker to correctly identify Nexus hardware models, so that I can maintain accurate hardware inventory.

#### Acceptance Criteria

1. WHEN a device is a Nexus switch, THE Device_Collector SHALL extract the model from the "cisco NexusXXXX CXXXXXX Chassis" line
2. WHEN extracting hardware model, THE Device_Collector SHALL return only the model number (e.g., "C9396PX") without "Chassis" suffix
3. THE Device_Collector SHALL maintain backward compatibility with IOS router hardware extraction (e.g., ISR4451-X/K9)
4. THE Device_Collector SHALL maintain backward compatibility with IOS switch hardware extraction (e.g., 2960)

### Requirement 3: Platform-Aware Extraction Order

**User Story:** As a developer, I want the extraction logic to check platform-specific patterns first, so that the most accurate data is captured for each device type.

#### Acceptance Criteria

1. WHEN extracting software version, THE Device_Collector SHALL check NX-OS patterns before generic patterns
2. WHEN extracting hardware model, THE Device_Collector SHALL check platform-specific patterns before generic patterns
3. WHEN a platform-specific pattern matches, THE Device_Collector SHALL use that result and skip remaining patterns
4. WHEN no platform-specific pattern matches, THE Device_Collector SHALL fall back to generic patterns

### Requirement 4: Prevent False Matches

**User Story:** As a network administrator, I want version extraction to ignore license text, so that I don't get incorrect version numbers in my inventory.

#### Acceptance Criteria

1. WHEN parsing Version_Output, THE Device_Collector SHALL not match version strings from GPL license text
2. WHEN parsing Version_Output, THE Device_Collector SHALL not match version strings from copyright notices
3. WHEN multiple version patterns match, THE Device_Collector SHALL select the most specific match for the detected platform
4. THE Device_Collector SHALL validate extracted versions match expected format for the platform (e.g., X.X(X) for NX-OS)
