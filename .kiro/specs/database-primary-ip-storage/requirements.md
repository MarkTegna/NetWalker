# Requirements Document

## Introduction

NetWalker's database-driven discovery features (--rewalk-stale and --walk-unwalked) currently fail when attempting to reconnect to devices that were discovered via hostname-only entries in seed files. This occurs because the primary management IP address used during initial discovery is not stored in the database, leaving no valid IP address for subsequent reconnection attempts. This feature will ensure that the primary management IP address is captured and stored during initial discovery, enabling reliable database-driven reconnection.

## Glossary

- **NetWalker**: The network discovery application that walks network devices and stores topology information
- **Primary_IP**: The IP address used to initially connect to and discover a device
- **Device_Interfaces**: Database table storing network interface information for discovered devices
- **Database_Manager**: Component responsible for storing and retrieving device information from the database
- **Connection_Manager**: Component responsible for establishing connections to network devices
- **Seed_File**: Input file containing initial devices to discover (can contain hostnames or IP addresses)
- **Database_Driven_Discovery**: Discovery mode where devices to walk are queried from the database rather than a seed file

## Requirements

### Requirement 1: Store Primary Management IP

**User Story:** As a network administrator, I want the primary management IP address stored during initial discovery, so that database-driven reconnection attempts have a valid IP address to use.

#### Acceptance Criteria

1. WHEN a device is successfully discovered, THE Database_Manager SHALL extract the primary_ip from the device_info
2. WHEN storing device information, THE Database_Manager SHALL store the primary_ip as a management interface in the device_interfaces table
3. WHEN the primary_ip is stored, THE Database_Manager SHALL mark it as a management interface type
4. IF the primary_ip already exists in device_interfaces, THEN THE Database_Manager SHALL update the existing record rather than create a duplicate

### Requirement 2: Retrieve Primary IP for Reconnection

**User Story:** As a network administrator, I want database queries to return valid IP addresses for devices, so that reconnection attempts succeed.

#### Acceptance Criteria

1. WHEN querying stale devices, THE Database_Manager SHALL return the primary_ip if no other interface IPs exist
2. WHEN querying unwalked devices, THE Database_Manager SHALL return the primary_ip if no other interface IPs exist
3. WHEN a device has multiple interface IPs, THE Database_Manager SHALL prioritize the primary_ip for management connections
4. THE Database_Manager SHALL ensure every device returned from database queries has at least one valid IP address

### Requirement 3: Connection Manager Compatibility

**User Story:** As a developer, I want the stored primary_ip to be compatible with the Connection_Manager requirements, so that reconnection attempts succeed without errors.

#### Acceptance Criteria

1. WHEN the Connection_Manager receives a device from database queries, THE device SHALL have either an IP address or a resolvable hostname
2. WHEN the primary_ip is provided to Connection_Manager, THE Connection_Manager SHALL successfully establish connections
3. IF a device has no primary_ip stored, THEN THE Database_Manager SHALL log a warning and exclude the device from reconnection queries

### Requirement 4: Data Integrity and Validation

**User Story:** As a developer, I want primary_ip storage to maintain data integrity, so that the database remains consistent and reliable.

#### Acceptance Criteria

1. WHEN storing primary_ip, THE Database_Manager SHALL validate that the IP address is in valid format
2. WHEN storing primary_ip, THE Database_Manager SHALL associate it with the correct device_id
3. WHEN a device is rediscovered, THE Database_Manager SHALL update the primary_ip if it has changed
4. THE Database_Manager SHALL ensure primary_ip storage does not interfere with existing interface storage logic

### Requirement 5: Backward Compatibility

**User Story:** As a network administrator, I want existing database records to work with the new feature, so that previously discovered devices can still be reconnected.

#### Acceptance Criteria

1. WHEN querying devices discovered before this feature, THE Database_Manager SHALL handle missing primary_ip gracefully
2. WHEN a device without primary_ip is encountered, THE Database_Manager SHALL attempt to use any available interface IP
3. IF no IP addresses exist for a device, THEN THE Database_Manager SHALL log a warning and skip the device
4. THE Database_Manager SHALL not require database schema changes beyond using existing device_interfaces table
