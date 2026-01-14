# Requirements Document

## Introduction

NetWalker's site-specific device collection and reporting functionality has critical issues that prevent proper network topology mapping and accurate reporting. Currently, the Network Device summary shows totals for the entire discovery sweep rather than per-site totals, and discovered devices at each site are not being properly walked or collected for further discovery. This affects the accuracy of network topology mapping and the usefulness of site-specific reports for network administrators managing multi-site enterprise networks.

## Glossary

- **Site_Specific_Collection**: The process of collecting and walking devices that belong to a specific site boundary
- **Device_Walking**: The recursive process of connecting to discovered devices to extract their neighbor information
- **Site_Summary**: Statistical summary information specific to devices within a single site boundary
- **Global_Summary**: Statistical summary information for the entire discovery operation across all sites
- **Device_Collection_Queue**: The queue of devices waiting to be processed for neighbor discovery
- **Site_Workbook**: Excel workbook containing devices and topology information for a specific site
- **Discovery_Engine**: The component responsible for device discovery and neighbor walking
- **Excel_Generator**: The component responsible for creating Excel reports and summaries

## Requirements

### Requirement 1: Site-Specific Device Collection

**User Story:** As a network administrator, I want devices discovered within each site boundary to be properly collected and queued for neighbor discovery, so that I can map complete site topologies.

#### Acceptance Criteria

1. WHEN a device is associated with a site boundary, THE Discovery_Engine SHALL add it to the site-specific collection queue
2. WHEN processing site-specific devices, THE Discovery_Engine SHALL walk each device to discover its neighbors
3. WHEN neighbors are discovered within a site, THE Discovery_Engine SHALL add them to the same site's collection queue
4. WHEN a device fails to be walked, THE Discovery_Engine SHALL log the failure and continue with remaining devices in the site queue
5. WHEN site-specific collection completes, THE Discovery_Engine SHALL ensure all reachable devices within the site have been processed

### Requirement 2: Site-Specific Device Walking

**User Story:** As a network administrator, I want discovered devices at each site to be recursively walked for neighbor discovery, so that I can identify the complete network topology within each site.

#### Acceptance Criteria

1. WHEN a device is added to a site collection queue, THE Discovery_Engine SHALL attempt to connect and extract neighbor information
2. WHEN walking site devices, THE Discovery_Engine SHALL use the same connection methods as global discovery (SSH with Telnet fallback)
3. WHEN extracting neighbors from site devices, THE Discovery_Engine SHALL parse both CDP and LLDP information
4. WHEN neighbors are found, THE Discovery_Engine SHALL determine if they belong to the same site or should be processed globally
5. WHEN device walking fails, THE Discovery_Engine SHALL record the device as unreachable but include it in site inventory

### Requirement 3: Site-Specific Summary Generation

**User Story:** As a network administrator, I want accurate device counts and statistics for each site, so that I can understand the scope and composition of each site's network infrastructure.

#### Acceptance Criteria

1. WHEN generating site workbooks, THE Excel_Generator SHALL calculate device counts specific to that site only
2. WHEN creating Network Device summary sheets, THE Excel_Generator SHALL show totals for devices within the site boundary
3. WHEN displaying connection statistics, THE Excel_Generator SHALL count only connections between devices within the site
4. WHEN showing discovery statistics, THE Excel_Generator SHALL report success/failure rates specific to the site
5. WHEN multiple sites exist, THE Excel_Generator SHALL ensure each site workbook contains only site-specific totals

### Requirement 4: Global vs Site Summary Separation

**User Story:** As a network administrator, I want clear separation between global discovery totals and site-specific totals, so that I can analyze both overall network scope and individual site details.

#### Acceptance Criteria

1. WHEN creating the main discovery workbook, THE Excel_Generator SHALL show global totals across all sites
2. WHEN creating site-specific workbooks, THE Excel_Generator SHALL show only site-specific totals
3. WHEN displaying device counts, THE Excel_Generator SHALL clearly distinguish between global and site-specific numbers
4. WHEN generating summary statistics, THE Excel_Generator SHALL maintain separate counters for global and per-site metrics
5. WHEN sites overlap or share devices, THE Excel_Generator SHALL handle device counting appropriately to avoid double-counting

### Requirement 5: Site Collection Queue Management

**User Story:** As a network administrator, I want proper queue management for site-specific device collection, so that devices are processed efficiently and completely within each site.

#### Acceptance Criteria

1. WHEN devices are added to site collection queues, THE Discovery_Engine SHALL prevent duplicate entries within the same site
2. WHEN processing site queues, THE Discovery_Engine SHALL maintain separate queues for each identified site
3. WHEN site collection is active, THE Discovery_Engine SHALL process devices in breadth-first order within each site
4. WHEN site collection completes, THE Discovery_Engine SHALL report the number of devices processed vs queued for each site
5. WHEN errors occur during site collection, THE Discovery_Engine SHALL continue processing remaining devices in the site queue

### Requirement 6: Site Device Association Validation

**User Story:** As a network administrator, I want to ensure that devices are correctly associated with their respective sites during collection, so that site boundaries are properly maintained.

#### Acceptance Criteria

1. WHEN a device is discovered as a neighbor, THE Discovery_Engine SHALL determine its correct site association
2. WHEN devices span multiple sites, THE Discovery_Engine SHALL use primary site boundary device for association
3. WHEN site association is unclear, THE Discovery_Engine SHALL include the device in the global collection
4. WHEN validating site associations, THE Discovery_Engine SHALL use cleaned hostnames for consistent matching
5. WHEN site boundaries change during discovery, THE Discovery_Engine SHALL update device associations accordingly

### Requirement 7: Site Collection Progress Tracking

**User Story:** As a network administrator, I want to track the progress of device collection within each site, so that I can monitor discovery completion and identify potential issues.

#### Acceptance Criteria

1. WHEN site collection begins, THE Discovery_Engine SHALL log the number of devices queued for each site
2. WHEN processing site devices, THE Discovery_Engine SHALL report progress as devices are completed
3. WHEN site collection encounters errors, THE Discovery_Engine SHALL log detailed error information with site context
4. WHEN site collection completes, THE Discovery_Engine SHALL report final statistics for devices processed, failed, and skipped
5. WHEN multiple sites are being processed, THE Discovery_Engine SHALL provide progress updates for each site independently

### Requirement 8: Site Workbook Content Accuracy

**User Story:** As a network administrator, I want site workbooks to contain accurate and complete information for devices within each site, so that I can rely on the reports for network management decisions.

#### Acceptance Criteria

1. WHEN creating site workbooks, THE Excel_Generator SHALL include all devices associated with the site boundary
2. WHEN populating device inventory sheets, THE Excel_Generator SHALL include complete information for all site devices
3. WHEN generating connection sheets, THE Excel_Generator SHALL show connections between devices within the site
4. WHEN creating neighbor detail sheets, THE Excel_Generator SHALL include neighbor information discovered during site collection
5. WHEN site devices have external connections, THE Excel_Generator SHALL indicate connections to devices outside the site

### Requirement 9: Error Handling and Recovery

**User Story:** As a network administrator, I want robust error handling during site-specific collection, so that failures in one site don't prevent discovery of other sites.

#### Acceptance Criteria

1. WHEN site collection fails for a device, THE Discovery_Engine SHALL continue processing remaining devices in the site
2. WHEN an entire site collection fails, THE Discovery_Engine SHALL continue processing other sites
3. WHEN connection errors occur during site walking, THE Discovery_Engine SHALL retry according to configured retry policies
4. WHEN site collection encounters critical errors, THE Discovery_Engine SHALL fall back to including affected devices in global discovery
5. WHEN recovery actions are taken, THE Discovery_Engine SHALL log the recovery method and continue processing

### Requirement 10: Configuration Integration

**User Story:** As a network administrator, I want site-specific collection to integrate with existing NetWalker configuration options, so that I can control collection behavior through standard configuration files.

#### Acceptance Criteria

1. WHEN site boundary patterns are configured, THE Discovery_Engine SHALL use them for site-specific collection
2. WHEN discovery depth limits are set, THE Discovery_Engine SHALL apply them to site-specific collection
3. WHEN connection timeouts are configured, THE Discovery_Engine SHALL use them for site device walking
4. WHEN filtering rules are active, THE Discovery_Engine SHALL apply them during site-specific collection
5. WHEN site collection is disabled, THE Discovery_Engine SHALL fall back to global discovery only