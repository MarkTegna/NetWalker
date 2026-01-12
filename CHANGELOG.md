# NetWalker Changelog

All notable changes to NetWalker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-01-12

### Added
- **Version Management Standards**: Implemented comprehensive versioning system with automatic/user build distinction
- **Enhanced Property-Based Testing**: 11+ universal properties with 100+ iterations each for comprehensive coverage
- **Comprehensive Documentation Suite**: NetWalker Comprehensive Guide, Quick Start Guide, and multiple technical summaries
- **DNS Validation Framework**: Enhanced DNS resolution and validation capabilities
- **Local Version Steering**: Project-specific version management rules and standards

### Fixed
- **Site Boundary Detection Critical Fix**: Resolved bug where devices matching `*-CORE-*` pattern weren't generating separate workbooks
  - Fixed condition from `len(site_boundaries) > 1` to `len(site_boundaries) >= 1`
  - Now correctly creates separate workbooks for single-site discoveries
  - Verified with LUMT-CORE-A and BORO-CORE-A test scenarios
- **Configuration Optimization**: Updated default `max_depth` from various values (2, 5, 9, 10) to consistent value of 1
  - Updated in netwalker.ini, config_manager.py, data_models.py, and discovery_engine.py
  - Optimizes discovery performance for typical network scenarios

### Enhanced
- **Hostname Cleaning Integration**: Improved pattern matching with cleaned hostnames for better site detection
- **Device Association Logic**: Multiple association methods (pattern match, seed device, parent device, hostname prefix, neighbor)
- **Error Handling**: Comprehensive error handling and graceful degradation mechanisms
- **Build Process**: Enhanced build scripts with proper version management and distribution creation

### Testing
- **Site Boundary Detection Tests**: Comprehensive property-based tests covering all scenarios
- **Integration Tests**: Multi-site discovery scenarios and edge case handling
- **DNS Property Tests**: Validation of DNS resolution and filtering functionality
- **Configuration Tests**: Validation of configuration loading and CLI overrides

### Documentation
- Added SITE_BOUNDARY_DETECTION_CRITICAL_FIX_SUMMARY.md
- Added NETWALKER_COMPREHENSIVE_GUIDE.md
- Added QUICK_START_GUIDE.md
- Added multiple technical fix summaries and release notes
- Enhanced README.md with current version information

### Version Management
- MINOR increment: 0.2.56 → 0.3.1 (following new version management standards)
- User-requested build (no letter suffix)
- Automatic PATCH increment during build process
- Created GitHub release with distribution ZIP file
- Archived distribution in /Archive directory

## [0.2.53] - 2026-01-12

### Fixed
- **Queue Progress Tracking**: Resolved configuration access issue in discovery engine
  - Fixed `self.config` attribute error in DiscoveryEngine initialization
  - Progress tracking now works correctly with dictionary-based configuration
  - Verified real-time progress display functionality

### Verified
- Progress tracking displays correctly: "Processing device X of Y (Z% complete) - Queue: N remaining"
- Dynamic total updates work as new neighbors are discovered
- Console and log output both show progress information
- Feature is fully functional and tested

## [0.2.52] - 2026-01-12

### Added
- **Queue Progress Tracking**: Real-time progress display during network discovery
  - Shows "Processing device X of Y (Z% complete) - Queue: N remaining"
  - Displays progress in both console and log output
  - Dynamic total updates as new neighbors are discovered
  - Configurable via `enable_progress_tracking` option in netwalker.ini
  - Provides visibility into discovery process without performance impact

### Configuration
- Added `enable_progress_tracking = true` option in `[discovery]` section
- Progress tracking enabled by default, can be disabled if not needed

## [0.2.51] - 2026-01-12

### Build
- Version increment for distribution update

## [0.2.50] - 2026-01-12

### Fixed
- **Discovery Depth**: Fixed critical issue preventing discovery beyond seed device
  - **Root Cause**: CDP parsing regex patterns not matching actual NEXUS CDP output format
  - **Solution**: Added new regex patterns for `IPv4 Address:` format found in real CDP data
  - **Impact**: Discovery now properly continues to configured max_depth instead of stopping at depth 0
  - Updated `protocol_parser.py` with enhanced IP extraction logic for NEXUS devices
  - Added `cdp_ipv4_pattern` and `cdp_interface_address_pattern` for comprehensive IP extraction
  - **Test Results**: Discovery now reaches depth 3, processes 277+ devices vs. previous 1 device limit

## [0.2.49] - 2026-01-12

### Added
- Neighbor-only device collection in Device Inventory sheet
- `_collect_neighbor_only_devices()` method to extract neighbor information
- Special "neighbor_only" status for devices discovered as neighbors but not directly connected
- Complete network topology visibility including unreachable devices

### Fixed
- Missing neighbor devices in Device Inventory workbook
- Devices appearing in Neighbor Details but not in main inventory
- Incomplete network documentation due to connection failures/timeouts/filtering

### Changed
- Enhanced `_create_device_inventory_sheet()` to include neighbor-only devices
- Device Inventory now shows ALL discovered devices regardless of connection status
- Added comprehensive logging for neighbor-only device collection

## [0.2.48] - 2026-01-12

### Fixed
- Hostname parsing issues with serial numbers in parentheses (e.g., "LUMT-CORE-A(FOX1849GQKY)")
- Centralized hostname cleaning across all Excel report locations
- Consistent application of `_clean_hostname()` method in Excel generator

### Changed
- Enhanced hostname cleaning with regex pattern `r'\([^)]*\)'` to remove serial numbers
- Updated all 15+ locations in Excel generator where hostnames are displayed

## [0.2.47] - 2026-01-12

### Changed
- Automatic PATCH version increment for build process
- Updated distribution package with latest fixes

### Build
- Successful build with PyInstaller
- Created distribution ZIP: `NetWalker_v0.2.47.zip`
- Copied to Archive directory for version history

## [0.2.46] - 2026-01-12

### Added
- Enhanced site boundary identification with comprehensive logging
- Visual indicators for site boundary pattern matching (✅/❌)
- Multiple methods for device-to-site association
- Comprehensive status reporting for site boundary detection

### Fixed
- Site boundary pattern not creating separate workbooks for `*-CORE-*` devices
- Filtered devices getting individual neighbor detail tabs in Excel reports
- Status-based filtering for tab creation prevention
- Filter reason detection and inventory-wide validation

### Changed
- Improved site boundary device grouping logic
- Enhanced logging for tab creation decisions
- Better handling of filtered device status checking

## [0.2.45] - 2026-01-12

### Added
- Discovery timeout reset functionality for large networks
- Dynamic timeout management with safety limits (max 10 resets)
- Enhanced NEXUS/NX-OS device support with specialized parsing
- Improved hostname extraction for NEXUS devices with multiple patterns
- NEXUS-specific CDP/LLDP parsing patterns
- Specialized debugging for NEXUS device processing

### Changed
- Discovery timeout now resets when new devices are added
- Enhanced interface normalization for NEXUS devices
- Improved management address handling for NEXUS CDP output

### Fixed
- Large networks being cut off prematurely due to timeout
- NEXUS devices not being properly discovered (e.g., LUMT-CORE-A)
- Hostname extraction issues for NX-OS devices

## [0.2.44] - 2026-01-12

### Fixed
- Discovery timeout being incorrectly set to connection timeout (30s instead of 300s)
- Configuration loading for discovery timeout settings
- Timeout mapping in NetWalkerApp initialization

### Changed
- Separated discovery timeout from connection timeout in configuration
- Updated configuration data models for proper timeout handling
- Enhanced timeout configuration validation

### Added
- Proper discovery timeout field in configuration
- Better timeout logging and monitoring

## [0.2.43] - 2026-01-12

### Added
- Comprehensive discovery logging with detailed decision tracking
- Enhanced FilterManager logging for device filtering decisions
- Detailed queue processing and inventory operation logging

### Fixed
- Unicode encoding issues in log files on Windows systems
- Logs not writing to files due to Unicode characters
- Enhanced discovery logging implementation

### Changed
- Replaced Unicode emoji characters with ASCII text markers
- Improved logging format for better readability
- Enhanced debugging capabilities for discovery decisions

## [0.2.42] - 2026-01-12

### Fixed
- LUMT-CORE-A discovery depth issue with max_depth = 2 configuration
- FilterManager configuration loading for both structured and flat config formats
- Hostname exclusion patterns preventing LUMT* devices from being discovered
- IP range exclusion processing for 10.70.0.0/16 ranges

### Changed
- Removed problematic LUMT* hostname exclusions from default configuration
- Updated FilterManager to handle different configuration formats
- Set default max_depth = 2 in distributed configuration files

### Added
- Better configuration validation and error handling
- Enhanced filtering logic for complex network environments

## [0.2.41] - 2026-01-12

### Fixed
- NX-OS devices showing hostname as "kernel" instead of actual device name
- Hostname extraction logic incorrectly parsing "kernel uptime is..." from show version
- Hardware model extraction for various Cisco platforms

### Added
- Multiple platform-specific hostname extraction patterns
- Enhanced NX-OS "Device name:" format support
- Prompt pattern matching for hostname detection
- System word filtering to exclude non-hostname terms
- Improved hardware model extraction with multiple patterns

### Changed
- Enhanced hostname extraction with fallback mechanisms
- Better validation for extracted hostnames
- Improved hardware model detection for Cisco devices

## [0.2.40] - 2026-01-12

### Changed
- Removed standalone "phone" from exclude_platforms configuration
- Updated default configuration template to allow IP phone discovery
- Maintained "host phone" exclusion for end-user devices

### Fixed
- Phone devices being incorrectly filtered from discovery
- VoIP device discovery issues

### Added
- Better distinction between network phones and end-user devices
- Enhanced platform filtering logic

## [0.2.39] - 2026-01-12

### Added
- Automated build process with PyInstaller
- Version increment functionality (PATCH auto-increment)
- Archive management for distribution files
- Build validation and testing

### Changed
- Removed pause commands from build.bat for unattended execution
- Enhanced build script with comprehensive error handling
- Improved distribution packaging

### Fixed
- Build process reliability and automation
- Version management consistency

## [0.2.38] - 2026-01-12

### Added
- Initial release with core network discovery functionality
- Breadth-first network topology discovery
- CDP and LLDP protocol support
- Excel report generation with multiple sheets
- Device filtering and boundary management
- Configuration file support
- Credential management
- Seed device functionality

### Features
- Multi-protocol neighbor discovery (CDP/LLDP)
- Professional Excel reporting with tables and formatting
- Configurable device filtering (platform, capability, hostname, IP)
- Resume capability for interrupted discoveries
- Comprehensive logging and error handling
- Windows executable distribution

---

## Version Format

NetWalker uses semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Incompatible API changes or major feature overhauls
- **MINOR**: New features in a backwards compatible manner
- **PATCH**: Backwards compatible bug fixes and small improvements

## Build Process

- **PATCH versions** are automatically incremented on every successful build
- **MINOR versions** are incremented manually for new features
- **MAJOR versions** are incremented manually for breaking changes

Each build creates:
- Windows executable: `dist/netwalker.exe`
- Distribution ZIP: `dist/NetWalker_vX.Y.Z.zip`
- Archive copy: `Archive/NetWalker_vX.Y.Z.zip`

## Links

- **Repository**: [https://github.com/MarkTegna](https://github.com/MarkTegna)
- **Documentation**: See included guide files
- **Issues**: GitHub Issues for bug reports and feature requests