# Requirements Document

## Introduction

NetWalker's site boundary detection feature is not working correctly. Devices matching the configured site boundary pattern `*-CORE-*` should generate separate workbooks but are only appearing in the main discovery workbook. This affects network organization and usability for large enterprise networks with multiple sites.

## Glossary

- **Site_Boundary_Pattern**: A wildcard pattern used to identify devices that represent site boundaries (e.g., `*-CORE-*`)
- **Site_Workbook**: A separate Excel workbook created for devices and their neighbors within a specific site boundary
- **Main_Workbook**: The primary discovery workbook containing all devices when no site boundaries are detected
- **Excel_Generator**: The component responsible for creating Excel reports and workbooks
- **Device_Inventory**: The collection of all discovered network devices

## Requirements

### Requirement 1: Site Boundary Pattern Matching

**User Story:** As a network administrator, I want devices matching the site boundary pattern to be correctly identified, so that separate workbooks are created for each site.

#### Acceptance Criteria

1. WHEN a device hostname matches the configured site boundary pattern, THE Excel_Generator SHALL identify it as a site boundary device
2. WHEN the site boundary pattern is `*-CORE-*`, THE Excel_Generator SHALL match devices like "LUMT-CORE-A", "BORO-CORE-B", "SITE-CORE-01"
3. WHEN multiple devices match the site boundary pattern, THE Excel_Generator SHALL identify each unique site prefix
4. WHEN a device matches the site boundary pattern, THE Excel_Generator SHALL extract the site name from the hostname
5. WHEN hostname cleaning is applied, THE Excel_Generator SHALL use cleaned hostnames for pattern matching

### Requirement 2: Site Workbook Generation

**User Story:** As a network administrator, I want separate workbooks created for each identified site, so that I can analyze site-specific network topology.

#### Acceptance Criteria

1. WHEN site boundary devices are identified, THE Excel_Generator SHALL create separate workbooks for each site
2. WHEN creating site workbooks, THE Excel_Generator SHALL use the format "Discovery_SITENAME_YYYYMMDD-HH-MM.xlsx"
3. WHEN a site workbook is created, THE Excel_Generator SHALL include all devices associated with that site boundary
4. WHEN a device is associated with a site boundary, THE Excel_Generator SHALL include its neighbors in the same site workbook
5. WHEN no site boundaries are detected, THE Excel_Generator SHALL create only the main discovery workbook

### Requirement 3: Device Association Logic

**User Story:** As a network administrator, I want devices to be correctly associated with their respective sites, so that site workbooks contain complete topology information.

#### Acceptance Criteria

1. WHEN a device matches the site boundary pattern, THE Excel_Generator SHALL associate it with the extracted site name
2. WHEN a device is discovered as a neighbor of a site boundary device, THE Excel_Generator SHALL associate it with the same site
3. WHEN a device has multiple site associations, THE Excel_Generator SHALL use the primary site boundary device association
4. WHEN associating devices with sites, THE Excel_Generator SHALL handle both connected and neighbor-only devices
5. WHEN devices cannot be associated with any site, THE Excel_Generator SHALL include them in the main workbook

### Requirement 4: Configuration Processing

**User Story:** As a network administrator, I want the site boundary pattern to be correctly loaded from configuration, so that the feature works with my network naming conventions.

#### Acceptance Criteria

1. WHEN the configuration contains a site_boundary_pattern, THE Excel_Generator SHALL load and use the pattern for matching
2. WHEN the site_boundary_pattern is empty or missing, THE Excel_Generator SHALL disable site boundary detection
3. WHEN the site_boundary_pattern contains wildcards, THE Excel_Generator SHALL support standard glob pattern matching
4. WHEN the configuration is reloaded, THE Excel_Generator SHALL use the updated site boundary pattern
5. WHEN the site_boundary_pattern is invalid, THE Excel_Generator SHALL log an error and disable site boundary detection

### Requirement 5: Logging and Debugging

**User Story:** As a network administrator, I want detailed logging of site boundary detection, so that I can troubleshoot configuration issues.

#### Acceptance Criteria

1. WHEN site boundary detection runs, THE Excel_Generator SHALL log the configured pattern and number of devices being processed
2. WHEN a device is tested against the pattern, THE Excel_Generator SHALL log whether it matches or not
3. WHEN site boundaries are identified, THE Excel_Generator SHALL log the site names and device counts
4. WHEN workbooks are created, THE Excel_Generator SHALL log the workbook names and associated devices
5. WHEN site boundary detection fails, THE Excel_Generator SHALL log detailed error information

### Requirement 6: Hostname Cleaning Integration

**User Story:** As a network administrator, I want site boundary detection to work with cleaned hostnames, so that devices with serial numbers are properly matched.

#### Acceptance Criteria

1. WHEN devices have serial numbers in parentheses, THE Excel_Generator SHALL use cleaned hostnames for pattern matching
2. WHEN extracting site names, THE Excel_Generator SHALL use cleaned hostnames to avoid serial number contamination
3. WHEN creating workbook names, THE Excel_Generator SHALL use cleaned site names without special characters
4. WHEN logging site boundary information, THE Excel_Generator SHALL display both original and cleaned hostnames
5. WHEN hostname cleaning fails, THE Excel_Generator SHALL fall back to original hostnames for pattern matching

### Requirement 7: Error Handling and Fallback

**User Story:** As a network administrator, I want the system to handle site boundary detection errors gracefully, so that report generation continues even if site detection fails.

#### Acceptance Criteria

1. WHEN site boundary detection encounters an error, THE Excel_Generator SHALL log the error and continue with main workbook generation
2. WHEN pattern matching fails for a device, THE Excel_Generator SHALL include the device in the main workbook
3. WHEN site name extraction fails, THE Excel_Generator SHALL use a default site name or include the device in the main workbook
4. WHEN workbook creation fails for a site, THE Excel_Generator SHALL log the error and include affected devices in the main workbook
5. WHEN configuration is invalid, THE Excel_Generator SHALL disable site boundary detection and generate only the main workbook