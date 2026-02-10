# Requirements Document: Command Executor

## Introduction

The Command Executor feature extends NetWalker's capabilities by enabling users to execute arbitrary commands on filtered sets of network devices and export the results to Excel. This feature transforms NetWalker from a pure discovery tool into a network automation platform that can collect operational data from devices on demand.

The feature integrates with NetWalker's existing database, connection management, and credential handling systems to provide a seamless command execution experience with comprehensive result reporting.

## Glossary

- **Command_Executor**: The system component that executes commands on network devices
- **Device_Filter**: A pattern-based mechanism for selecting devices from the database
- **Command_Result**: The output returned from executing a command on a device
- **Excel_Exporter**: The component that formats and exports results to Excel files
- **Connection_Manager**: Existing NetWalker component that handles device connections
- **Database_Manager**: Existing NetWalker component that manages device data
- **Scrapli**: The SSH/Telnet library used for device connections (IOSXEDriver for Cisco IOS-XE)

## Requirements

### Requirement 1: Command-Line Interface

**User Story:** As a network engineer, I want to invoke the command executor from the command line, so that I can integrate it into scripts and workflows.

#### Acceptance Criteria

1. WHEN a user runs NetWalker with the "execute" command, THE Command_Executor SHALL activate
2. THE Command_Executor SHALL accept a device filter pattern as a required parameter
3. THE Command_Executor SHALL accept a command string as a required parameter
4. THE Command_Executor SHALL accept an optional output directory parameter
5. WHERE an output directory is not specified, THE Command_Executor SHALL use the current directory

### Requirement 2: Device Filtering

**User Story:** As a network engineer, I want to filter devices by name pattern, so that I can target specific device groups for command execution.

#### Acceptance Criteria

1. WHEN a device filter pattern is provided, THE Command_Executor SHALL query the database for matching devices
2. THE Command_Executor SHALL support SQL wildcard patterns (% for multiple characters, _ for single character)
3. WHEN no devices match the filter pattern, THE Command_Executor SHALL report zero matches and exit gracefully
4. WHEN devices match the filter pattern, THE Command_Executor SHALL retrieve the device name and primary IP address
5. THE Command_Executor SHALL select the most recently seen IP address when multiple IPs exist for a device

### Requirement 3: Credential Management

**User Story:** As a network engineer, I want credentials to be loaded from the configuration file, so that I don't have to enter them repeatedly.

#### Acceptance Criteria

1. THE Command_Executor SHALL load credentials from the specified configuration file (default: netwalker.ini)
2. WHEN credentials are not found in the configuration file, THE Command_Executor SHALL prompt the user for credentials
3. THE Command_Executor SHALL support username, password, and enable password credentials
4. THE Command_Executor SHALL use the same credential format as the existing NetWalker discovery feature
5. THE Command_Executor SHALL decode encrypted passwords using the existing password decoding mechanism
6. WHERE testing is performed, THE Command_Executor SHALL support loading credentials from secret_creds.ini

### Requirement 4: Device Connection and Command Execution

**User Story:** As a network engineer, I want to execute commands on multiple devices sequentially, so that I can collect operational data efficiently.

#### Acceptance Criteria

1. WHEN connecting to a device, THE Command_Executor SHALL use Scrapli IOSXEDriver with the loaded credentials
2. THE Command_Executor SHALL set connection timeout to 30 seconds for socket and transport
3. THE Command_Executor SHALL disable strict SSH key checking
4. WHEN a connection succeeds, THE Command_Executor SHALL execute the specified command
5. WHEN a command executes successfully, THE Command_Executor SHALL capture the complete output
6. WHEN a connection fails, THE Command_Executor SHALL record the failure reason and continue to the next device
7. WHEN a command execution fails, THE Command_Executor SHALL record the error message and continue to the next device
8. THE Command_Executor SHALL close each connection after command execution or failure

### Requirement 5: Progress Reporting

**User Story:** As a network engineer, I want to see real-time progress as commands execute, so that I can monitor the operation and estimate completion time.

#### Acceptance Criteria

1. WHEN command execution begins, THE Command_Executor SHALL display the total number of devices to process
2. WHEN connecting to each device, THE Command_Executor SHALL display the device name and IP address
3. WHEN a command succeeds, THE Command_Executor SHALL display a success indicator with the device name
4. WHEN a command fails, THE Command_Executor SHALL display a failure indicator with the device name and error type
5. WHEN all devices are processed, THE Command_Executor SHALL display a summary with total, successful, and failed counts

### Requirement 6: Excel Export

**User Story:** As a network engineer, I want results exported to Excel with a timestamped filename, so that I can analyze data and maintain historical records.

#### Acceptance Criteria

1. WHEN command execution completes, THE Command_Executor SHALL export results to an Excel file
2. THE Excel_Exporter SHALL use the filename format: `Command_Results_YYYYMMDD-HH-MM.xlsx`
3. THE Excel_Exporter SHALL create a worksheet with columns: Device Name, Device IP, Status, Command Output
4. THE Excel_Exporter SHALL format headers with bold white text on blue background (color: 366092)
5. THE Excel_Exporter SHALL auto-adjust column widths based on content (maximum 100 characters)
6. WHEN a device connection succeeds, THE Excel_Exporter SHALL record status as "Success"
7. WHEN a device connection fails, THE Excel_Exporter SHALL record status as "Failed" and include the error message
8. THE Excel_Exporter SHALL preserve command output formatting including line breaks
9. THE Excel_Exporter SHALL display the output file path after successful export

### Requirement 7: Error Handling

**User Story:** As a network engineer, I want robust error handling, so that failures on individual devices don't stop the entire operation.

#### Acceptance Criteria

1. WHEN a database connection fails, THE Command_Executor SHALL display an error message and exit
2. WHEN a device connection times out, THE Command_Executor SHALL record the timeout and continue to the next device
3. WHEN a device authentication fails, THE Command_Executor SHALL record the authentication failure and continue
4. WHEN a command returns an error, THE Command_Executor SHALL capture the error output and mark the status as "Success" with error content
5. IF Excel export fails, THEN THE Command_Executor SHALL display an error message with the failure reason

### Requirement 8: Integration with Existing NetWalker Components

**User Story:** As a developer, I want the command executor to reuse existing NetWalker components, so that the codebase remains maintainable and consistent.

#### Acceptance Criteria

1. THE Command_Executor SHALL use the existing Database_Manager for database queries
2. THE Command_Executor SHALL use the existing credential loading mechanism from config/credentials.py
3. THE Command_Executor SHALL use the existing Excel formatting patterns from reports/excel_generator.py
4. THE Command_Executor SHALL follow the existing logging configuration from logging_config.py
5. THE Command_Executor SHALL integrate with the CLI parser in cli.py as a new subcommand

### Requirement 9: Configuration Options

**User Story:** As a network engineer, I want to configure connection parameters, so that I can optimize for different network environments.

#### Acceptance Criteria

1. WHERE a config file parameter is specified, THE Command_Executor SHALL load configuration from that file
2. THE Command_Executor SHALL support configuration of connection timeout values
3. THE Command_Executor SHALL support configuration of SSH parameters (auth_strict_key)
4. THE Command_Executor SHALL use default values when configuration parameters are not specified
5. THE Command_Executor SHALL validate that required configuration sections exist before execution
