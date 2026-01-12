# NetWalker Comprehensive User Guide

**Author:** Mark Oldham  
**Version:** 0.2.47  
**Compile Date:** 2026-01-12  

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Features](#features)
5. [Usage](#usage)
6. [Excel Reports](#excel-reports)
7. [Troubleshooting](#troubleshooting)
8. [Version History](#version-history)

## Overview

NetWalker is a comprehensive network discovery tool designed for Windows environments. It performs breadth-first network topology discovery using CDP and LLDP protocols, generating detailed Excel reports with device inventory, connection details, and neighbor information.

### Key Features

- **Automated Network Discovery**: Breadth-first traversal with configurable depth limits
- **Multi-Protocol Support**: CDP and LLDP neighbor discovery
- **Site Boundary Detection**: Automatic creation of separate workbooks for different sites
- **Advanced Filtering**: Platform, capability, and hostname-based device filtering
- **Dynamic Timeout Management**: Prevents large networks from being cut off prematurely
- **Enhanced NEXUS Support**: Specialized handling for Cisco NEXUS/NX-OS devices
- **Comprehensive Reporting**: Professional Excel reports with multiple sheets and tables
- **Resume Capability**: Continue discovery from previous sessions
- **Detailed Logging**: Comprehensive debugging and decision tracking

## Installation

### Prerequisites

- Windows 10/11 or Windows Server 2016+
- Network access to target devices
- Valid credentials for network devices

### Installation Steps

1. Download the latest NetWalker distribution ZIP file
2. Extract to your desired directory (e.g., `C:\NetWalker\`)
3. The distribution includes:
   - `netwalker.exe` - Main executable
   - `netwalker.ini` - Configuration file
   - `seed_file.csv` - Seed device template
   - `secret_creds.ini` - Credentials template

## Configuration

### Main Configuration File (netwalker.ini)

```ini
[discovery]
# Maximum depth for recursive discovery
max_depth = 2
# Number of concurrent device connections
concurrent_connections = 5
# Connection timeout in seconds
connection_timeout = 30
# Total discovery process timeout in seconds
discovery_timeout = 300
# Discovery protocols to use (comma-separated)
discovery_protocols = CDP,LLDP

[filtering]
# Include devices matching these wildcards (comma-separated)
include_wildcards = *
# Exclude devices matching these wildcards (comma-separated)
exclude_wildcards = 
# Include devices in these CIDR ranges (comma-separated)
include_cidrs = 
# Exclude devices in these CIDR ranges (comma-separated)
exclude_cidrs = 

[exclusions]
# Exclude devices with these hostname patterns (comma-separated)
exclude_hostnames = 
# Exclude devices in these IP ranges (comma-separated)
exclude_ip_ranges = 
# Exclude devices with these platforms (comma-separated)
exclude_platforms = linux,windows,unix,freebsd,openbsd,netbsd,solaris,aix,hp-ux,vmware,docker,kubernetes,host phone,camera,printer,access point,wireless,server
# Exclude devices with these capabilities (comma-separated)
exclude_capabilities = host phone,camera,printer,server

[output]
# Directory for report files
reports_directory = ./reports
# Directory for log files
logs_directory = ./logs
# Excel file format
excel_format = xlsx
# Enable Visio diagram generation (true/false)
visio_enabled = true
# Site boundary pattern for creating separate workbooks (wildcard pattern)
site_boundary_pattern = *-CORE-*

[connection]
# SSH port number
ssh_port = 22
# Telnet port number
telnet_port = 23
# Preferred connection method (ssh/telnet)
preferred_method = ssh
```

### Credentials Configuration (secret_creds.ini)

```ini
[credentials]
username = your_username
password = your_password
enable_password = your_enable_password
```

### Seed Devices File (seed_file.csv)

```csv
hostname,ip_address,status
CORE-SWITCH-01,192.168.1.1,
CORE-SWITCH-02,192.168.1.2,
DISTRIBUTION-01,192.168.2.1,
```

## Features

### 1. Site Boundary Detection

NetWalker automatically detects site boundaries based on configurable patterns and creates separate Excel workbooks for each site.

**Configuration:**
```ini
[output]
site_boundary_pattern = *-CORE-*
```

**Behavior:**
- Devices matching the pattern (e.g., `LUMT-CORE-A`, `BORO-CORE-A`) create separate workbooks
- Each site workbook contains only devices associated with that site
- Workbook naming: `Discovery_SITENAME_YYYYMMDD-HH-MM.xlsx`

### 2. Advanced Device Filtering

Multiple layers of filtering prevent unwanted devices from cluttering reports:

**Platform Filtering:**
- Excludes non-network devices (servers, phones, printers)
- Configurable platform exclusion list

**Capability Filtering:**
- Filters based on CDP/LLDP capabilities
- Prevents end-user devices from being discovered

**Hostname/IP Filtering:**
- Wildcard pattern matching for hostnames
- CIDR range exclusions for IP addresses

### 3. Dynamic Timeout Management

Prevents large networks from being cut off prematurely:

- **Automatic Timeout Reset**: Extends discovery time when new devices are found
- **Safety Limits**: Maximum 10 resets to prevent infinite loops
- **Configurable Timeouts**: Separate connection and discovery timeouts

### 4. Enhanced NEXUS Support

Specialized handling for Cisco NEXUS/NX-OS devices:

- **Improved Hostname Extraction**: Multiple patterns for NX-OS hostname detection
- **Enhanced CDP/LLDP Parsing**: NEXUS-specific parsing patterns
- **Debug Logging**: Special debugging for NEXUS device processing

### 5. Comprehensive Excel Reporting

Professional Excel reports with multiple sheets:

**Main Discovery Report:**
- Discovery Summary
- Device Inventory
- Network Connections

**Site-Specific Reports:**
- Separate workbooks for each site boundary
- Site-specific device inventory and connections

**Per-Seed Reports:**
- Individual reports for each seed device
- Seed device information and neighbors
- Neighbor detail sheets (excluding filtered devices)

## Usage

### Command Line Interface

```powershell
# Basic discovery
.\netwalker.exe

# Discovery with specific seed file
.\netwalker.exe --seed-file custom_seeds.csv

# Discovery with custom configuration
.\netwalker.exe --config custom_config.ini

# Resume previous discovery
.\netwalker.exe --resume

# Generate inventory report only
.\netwalker.exe --inventory-only

# DNS validation
.\netwalker.exe --dns-validation

# Help and version information
.\netwalker.exe --help
.\netwalker.exe --version
```

### Discovery Process

1. **Initialization**: Load configuration and credentials
2. **Seed Loading**: Read seed devices from CSV file
3. **Discovery Loop**: Breadth-first traversal of network
4. **Filtering**: Apply device filters at multiple stages
5. **Report Generation**: Create Excel reports and summaries
6. **Cleanup**: Close connections and save state

### Best Practices

1. **Start Small**: Begin with a few seed devices to test configuration
2. **Monitor Logs**: Check log files for discovery decisions and errors
3. **Adjust Timeouts**: Increase timeouts for large networks
4. **Review Filters**: Ensure filtering rules match your environment
5. **Regular Updates**: Keep credentials and seed files current

## Excel Reports

### Report Types

#### 1. Main Discovery Report
**Filename:** `Discovery_YYYYMMDD-HH-MM.xlsx`

**Sheets:**
- **Discovery Summary**: Overview of discovery results
- **Device Inventory**: Complete device information
- **Network Connections**: All discovered connections

#### 2. Site-Specific Reports
**Filename:** `Discovery_SITENAME_YYYYMMDD-HH-MM.xlsx`

**Sheets:**
- **Discovery Summary**: Site-specific summary
- **Device Inventory**: Site devices only
- **Network Connections**: Site connections only

#### 3. Per-Seed Reports
**Filename:** `Seed_HOSTNAME_YYYYMMDD-HH-MM.xlsx`

**Sheets:**
- **Seed Device Info**: Detailed seed device information
- **Neighbors Overview**: Summary of seed's neighbors
- **Neighbors_HOSTNAME**: Individual neighbor details (non-filtered only)

### Report Features

- **Professional Formatting**: Headers, borders, and color coding
- **Excel Tables**: Sortable and filterable data tables
- **Auto-Sizing**: Automatically sized columns for readability
- **Comprehensive Data**: All discovered device and connection information

## Troubleshooting

### Common Issues

#### 1. Discovery Timeout
**Symptoms:** Discovery stops before completing all devices
**Solutions:**
- Increase `discovery_timeout` in configuration
- Reduce `max_depth` to limit scope
- Check network connectivity to devices

#### 2. Authentication Failures
**Symptoms:** Many "Connection failed" messages
**Solutions:**
- Verify credentials in `secret_creds.ini`
- Check SSH/Telnet connectivity
- Ensure enable passwords are correct

#### 3. No Site Boundaries Detected
**Symptoms:** Single workbook created despite site boundary pattern
**Solutions:**
- Verify `site_boundary_pattern` matches device hostnames
- Check seed device naming conventions
- Review site boundary logs for pattern matching

#### 4. Filtered Devices Getting Tabs
**Symptoms:** Unwanted devices appear in Excel reports
**Solutions:**
- Review filtering configuration
- Check platform and capability exclusions
- Verify device filtering logs

### Log Analysis

**Log Locations:**
- Discovery logs: `logs/netwalker_YYYYMMDD-HH-MM.log`
- Error logs: `logs/error_YYYYMMDD-HH-MM.log`

**Key Log Messages:**
- `[DISCOVERY DECISION]`: Device processing decisions
- `[NEIGHBOR FILTERED]`: Neighbor filtering results
- `[SITE BOUNDARY]`: Site boundary detection
- `[TIMEOUT RESET]`: Dynamic timeout management

### Performance Optimization

1. **Concurrent Connections**: Adjust based on network capacity
2. **Discovery Depth**: Limit depth for large networks
3. **Filtering Rules**: Use aggressive filtering to reduce scope
4. **Timeout Settings**: Balance thoroughness with performance

## Version History

### Version 0.2.47 (2026-01-12)
- **Build**: Automatic PATCH increment
- **Status**: Current production version
- **Features**: All major enhancements included

### Version 0.2.46 (2026-01-12)
- **Site Boundary Fixes**: Enhanced site boundary identification
- **Filtered Device Tab Prevention**: Eliminated unwanted Excel tabs
- **Comprehensive Logging**: Improved debugging capabilities

### Version 0.2.45 (2026-01-12)
- **Discovery Timeout Reset**: Dynamic timeout management for large networks
- **NEXUS Enhancement**: Improved NEXUS/NX-OS device support
- **Timeout Safety**: Maximum reset limits to prevent infinite loops

### Version 0.2.44 (2026-01-12)
- **Discovery Timeout Fix**: Separate discovery and connection timeouts
- **Configuration Updates**: Enhanced timeout configuration
- **Testing Validation**: Confirmed timeout functionality

### Previous Versions
- **0.2.43**: Enhanced discovery logging and Unicode fixes
- **0.2.42**: LUMT filtering and configuration fixes
- **0.2.41**: NX-OS hostname extraction improvements
- **0.2.40**: Phone filter removal and platform updates

## Support and Contact

**Author:** Mark Oldham  
**Repository:** [https://github.com/MarkTegna](https://github.com/MarkTegna)  
**Documentation:** This guide and included summary files  

For issues and feature requests, refer to the GitHub repository or contact the author directly.

---

*This guide covers NetWalker version 0.2.47. For the latest updates and features, check the version history and release notes.*