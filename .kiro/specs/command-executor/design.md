# Design Document: Command Executor

## Overview

The Command Executor feature extends NetWalker's capabilities by adding a command-line interface for executing arbitrary commands on filtered sets of network devices. This feature transforms NetWalker from a pure discovery tool into a network automation platform capable of collecting operational data on demand.

The design leverages NetWalker's existing infrastructure including database management, credential handling, connection management, and Excel reporting. The feature is implemented as a new CLI subcommand that integrates seamlessly with the existing architecture.

### Key Design Principles

1. **Reuse Existing Components**: Leverage DatabaseManager, CredentialManager, ConnectionManager, and Excel formatting patterns
2. **Fail-Safe Operation**: Individual device failures should not stop the entire operation
3. **Progress Transparency**: Provide real-time feedback during execution
4. **Consistent Patterns**: Follow existing NetWalker conventions for configuration, logging, and output

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Interface                          │
│                    (netwalker/cli.py)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Command Executor                           │
│            (netwalker/executor/command_executor.py)         │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Device     │  │   Command    │  │   Result     │    │
│  │   Filter     │  │   Executor   │  │   Collector  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└──────┬────────────────┬────────────────┬───────────────────┘
       │                │                │
       ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Database   │  │ Connection  │  │   Excel     │
│  Manager    │  │  Manager    │  │  Exporter   │
└─────────────┘  └─────────────┘  └─────────────┘
```

### Data Flow

1. **CLI Parsing**: User invokes `netwalker execute --filter "*-uw*" --command "show ip eigrp vrf WAN neigh"`
2. **Initialization**: Load configuration and credentials
3. **Device Filtering**: Query database for devices matching filter pattern
4. **Sequential Execution**: For each device:
   - Connect using ConnectionManager
   - Execute command
   - Capture output and status
   - Close connection
   - Report progress
5. **Result Export**: Generate Excel file with timestamped filename
6. **Summary Display**: Show execution statistics

## Components and Interfaces

### 1. CLI Integration (netwalker/cli.py)

**Purpose**: Add "execute" subcommand to NetWalker CLI

**Interface**:
```python
# New subcommand in create_parser()
execute_parser = subparsers.add_parser('execute', help='Execute commands on filtered devices')

execute_parser.add_argument('--config', '-c', default='netwalker.ini',
                           help='Configuration file path')
execute_parser.add_argument('--filter', '-f', required=True,
                           help='Device name filter pattern (SQL wildcard: % for multiple chars, _ for single char)')
execute_parser.add_argument('--command', '-cmd', required=True,
                           help='Command to execute on devices')
execute_parser.add_argument('--output', '-o', default='.',
                           help='Output directory for Excel file')
```

### 2. Command Executor (netwalker/executor/command_executor.py)

**Purpose**: Core logic for command execution workflow

**Class Structure**:
```python
class CommandExecutor:
    def __init__(self, config_file: str, device_filter: str, command: str, output_dir: str)
    def execute(self) -> ExecutionSummary
    def _load_configuration(self) -> Dict[str, Any]
    def _get_credentials(self) -> Credentials
    def _filter_devices(self) -> List[DeviceInfo]
    def _execute_on_device(self, device: DeviceInfo) -> CommandResult
    def _export_results(self, results: List[CommandResult]) -> str
    def _display_summary(self, summary: ExecutionSummary)
```

**Key Methods**:

- `execute()`: Main orchestration method
  - Loads configuration
  - Gets credentials
  - Filters devices from database
  - Executes commands sequentially
  - Exports results to Excel
  - Returns execution summary

- `_filter_devices()`: Query database for matching devices
  - Uses DatabaseManager to query devices table
  - Applies SQL LIKE pattern matching
  - Retrieves device_name and primary IP address
  - Returns list of DeviceInfo objects

- `_execute_on_device()`: Execute command on single device
  - Uses ConnectionManager to establish connection
  - Executes command via connection
  - Captures output or error message
  - Closes connection
  - Returns CommandResult with status

### 3. Data Models (netwalker/executor/data_models.py)

**Purpose**: Define data structures for command execution

**Models**:
```python
@dataclass
class DeviceInfo:
    device_name: str
    ip_address: str

@dataclass
class CommandResult:
    device_name: str
    ip_address: str
    status: str  # "Success", "Failed", "Timeout", "Auth Failed"
    output: str  # Command output or error message
    execution_time: float

@dataclass
class ExecutionSummary:
    total_devices: int
    successful: int
    failed: int
    total_time: float
    output_file: str
```

### 4. Excel Exporter (netwalker/executor/excel_exporter.py)

**Purpose**: Export command results to Excel with consistent formatting

**Class Structure**:
```python
class CommandResultExporter:
    def __init__(self, output_dir: str)
    def export(self, results: List[CommandResult], command: str) -> str
    def _create_workbook(self) -> Workbook
    def _add_results_sheet(self, wb: Workbook, results: List[CommandResult], command: str)
    def _format_headers(self, ws: Worksheet)
    def _auto_adjust_columns(self, ws: Worksheet)
```

**Excel Format**:
- Filename: `Command_Results_YYYYMMDD-HH-MM.xlsx`
- Sheet Name: "Command Results"
- Columns:
  - Device Name
  - Device IP
  - Status
  - Command Output
  - Execution Time (seconds)
- Header Formatting: Bold white text on blue background (#366092)
- Column Widths: Auto-adjusted (max 100 characters)
- Output Preservation: Wrap text to preserve line breaks

### 5. Progress Reporter (netwalker/executor/progress_reporter.py)

**Purpose**: Provide real-time progress feedback

**Class Structure**:
```python
class ProgressReporter:
    def __init__(self, total_devices: int)
    def report_start(self, device_name: str, ip_address: str)
    def report_success(self, device_name: str)
    def report_failure(self, device_name: str, error_type: str)
    def report_summary(self, summary: ExecutionSummary)
```

**Output Format**:
```
Command Execution: show ip eigrp vrf WAN neigh
================================================================================
Found 15 devices matching filter: *-uw*

Connecting to devices...
  [1/15] Connecting to BORO-SW-UW01 (10.1.1.1)...
    [OK] BORO-SW-UW01: Command executed successfully
  [2/15] Connecting to BORO-SW-UW02 (10.1.1.2)...
    [FAIL] BORO-SW-UW02: Connection timeout
  ...

================================================================================
Execution Summary:
  Total devices: 15
  Successful: 13
  Failed: 2
  Total time: 45.3 seconds

Results exported to: Command_Results_20260209-19-15.xlsx
```

## Data Models

### Device Information
```python
DeviceInfo:
  - device_name: str (from devices table)
  - ip_address: str (from device_interfaces table, most recent)
```

### Command Result
```python
CommandResult:
  - device_name: str
  - ip_address: str
  - status: str ("Success", "Failed", "Timeout", "Auth Failed")
  - output: str (command output or error message)
  - execution_time: float (seconds)
```

### Execution Summary
```python
ExecutionSummary:
  - total_devices: int
  - successful: int
  - failed: int
  - total_time: float
  - output_file: str (path to Excel file)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: SQL Wildcard Pattern Matching

*For any* device filter pattern containing SQL wildcards (% or _), the database query should return only devices whose names match the pattern according to SQL LIKE semantics.

**Validates: Requirements 2.1, 2.2**

### Property 2: Device Information Retrieval

*For any* device matching the filter pattern, the system should retrieve both the device name and the primary IP address (most recently seen).

**Validates: Requirements 2.4, 2.5**

### Property 3: Password Decryption

*For any* encrypted password (prefixed with "ENC:"), decrypting then encrypting should produce an equivalent encrypted value.

**Validates: Requirements 3.5**

### Property 4: Successful Command Execution

*For any* device where connection succeeds, executing a command should capture the complete output and return a success status.

**Validates: Requirements 4.4, 4.5**

### Property 5: Error Handling and Continuation

*For any* device where connection or command execution fails, the system should record the error and continue processing the next device without stopping.

**Validates: Requirements 4.6, 4.7, 7.2, 7.3**

### Property 6: Connection Cleanup

*For any* device connection (successful or failed), the connection should be closed after command execution or error.

**Validates: Requirements 4.8**

### Property 7: Progress Reporting Completeness

*For any* device being processed, the system should display progress information including device name, IP address, and status (success or failure).

**Validates: Requirements 5.2, 5.3, 5.4**

### Property 8: Excel Export Generation

*For any* command execution (regardless of individual device success/failure), an Excel file should be created with the correct filename format (Command_Results_YYYYMMDD-HH-MM.xlsx).

**Validates: Requirements 6.1, 6.2**

### Property 9: Status Recording Accuracy

*For any* command result, the Excel export should record "Success" for successful executions and "Failed" for failed executions, with error messages included for failures.

**Validates: Requirements 6.6, 6.7**

### Property 10: Output Preservation

*For any* command output containing line breaks, the Excel export should preserve the formatting including all line breaks.

**Validates: Requirements 6.8**

### Property 11: Column Width Adjustment

*For any* Excel export, column widths should be auto-adjusted based on content with a maximum width of 100 characters.

**Validates: Requirements 6.5**

### Property 12: Command Error Capture

*For any* command that returns an error (but connection succeeds), the system should capture the error output and mark status as "Success" with the error content included.

**Validates: Requirements 7.4**

## Error Handling

### Database Errors

**Connection Failure**:
- Display clear error message: "Failed to connect to database: {error_details}"
- Exit gracefully with non-zero exit code
- Log full error details for troubleshooting

**Query Errors**:
- Log error details
- Display user-friendly message
- Exit gracefully

### Device Connection Errors

**Timeout**:
- Record status as "Timeout"
- Include timeout duration in error message
- Continue to next device
- Log connection attempt details

**Authentication Failure**:
- Record status as "Auth Failed"
- Include authentication error details
- Continue to next device
- Do not log credentials

**General Connection Errors**:
- Record status as "Failed"
- Include error message
- Continue to next device
- Log error for troubleshooting

### Command Execution Errors

**Command Errors**:
- Capture error output
- Record status as "Success" (connection succeeded)
- Include error output in results
- Continue to next device

**Timeout During Execution**:
- Record status as "Timeout"
- Include partial output if available
- Continue to next device

### Excel Export Errors

**File Write Errors**:
- Display error message with file path
- Log full error details
- Exit with non-zero exit code

**Formatting Errors**:
- Log warning
- Continue with basic formatting
- Ensure data is still exported

### Configuration Errors

**Missing Configuration File**:
- Display error message with expected file path
- Exit gracefully

**Invalid Configuration**:
- Display specific validation error
- Exit gracefully

**Missing Credentials**:
- Fall back to interactive prompting
- If prompting fails, exit gracefully

## Testing Strategy

### Dual Testing Approach

The Command Executor feature will be validated using both unit tests and property-based tests:

**Unit Tests**: Focus on specific examples, edge cases, and integration points
- CLI argument parsing with various input combinations
- Configuration file loading with different formats
- Database connection with mock database
- Excel file creation and formatting
- Error message formatting
- Edge cases: empty device list, database connection failure, export failure

**Property-Based Tests**: Verify universal properties across all inputs
- SQL wildcard pattern matching with random patterns
- Device information retrieval with random device sets
- Password encryption/decryption round-trip
- Command execution with random commands
- Error handling with random failure scenarios
- Excel export with random result sets
- Progress reporting with random device counts

### Property-Based Testing Configuration

- **Library**: Use `hypothesis` for Python property-based testing
- **Iterations**: Minimum 100 iterations per property test
- **Tagging**: Each property test must reference its design document property

**Tag Format**:
```python
# Feature: command-executor, Property 1: SQL Wildcard Pattern Matching
@given(device_filter=st.text(alphabet=string.ascii_letters + '%_', min_size=1))
def test_sql_wildcard_matching(device_filter):
    ...
```

### Test Coverage Requirements

**Unit Test Coverage**:
- CLI integration: Test all argument combinations
- Configuration loading: Test valid and invalid configs
- Credential loading: Test file, environment, and interactive modes
- Device filtering: Test various SQL patterns
- Connection management: Test success and failure paths
- Excel export: Test formatting and data accuracy
- Progress reporting: Test console output
- Error handling: Test all error scenarios

**Property Test Coverage**:
- Property 1: SQL wildcard pattern matching (100+ random patterns)
- Property 2: Device information retrieval (100+ random device sets)
- Property 3: Password decryption round-trip (100+ random passwords)
- Property 4: Successful command execution (100+ random commands)
- Property 5: Error handling continuation (100+ random failure scenarios)
- Property 6: Connection cleanup (100+ random connection scenarios)
- Property 7: Progress reporting (100+ random device lists)
- Property 8: Excel export generation (100+ random executions)
- Property 9: Status recording accuracy (100+ random results)
- Property 10: Output preservation (100+ random outputs with line breaks)
- Property 11: Column width adjustment (100+ random content lengths)
- Property 12: Command error capture (100+ random error commands)

### Integration Testing

**End-to-End Tests**:
- Execute command on real test devices (using secret_creds.ini)
- Verify Excel file is created with correct data
- Verify progress reporting is accurate
- Verify error handling for unreachable devices
- Verify database queries return correct devices

**Mock Testing**:
- Mock database for device filtering tests
- Mock connection manager for command execution tests
- Mock Excel library for export tests

### Test Data

**Test Devices**:
- Use devices from NetWalker database with "-uw" pattern
- Create mock devices for unit tests
- Generate random device data for property tests

**Test Commands**:
- "show version" (basic command)
- "show ip eigrp vrf WAN neigh" (complex command)
- "show invalid command" (error command)
- Multi-line output commands

**Test Credentials**:
- Load from secret_creds.ini for integration tests
- Use mock credentials for unit tests
- Generate random credentials for property tests

## Implementation Notes

### Windows Platform Considerations

- Use ASCII characters for progress indicators ([OK], [FAIL]) instead of Unicode (✓, ✗)
- Handle Windows path separators correctly
- Ensure Excel files can be opened by Windows Excel
- Test with PowerShell execution (use .\ prefix for executables)

### Performance Considerations

- Sequential execution (no parallelization) for simplicity and reliability
- Connection timeout of 30 seconds prevents hanging
- Close connections immediately after use to free resources
- Use efficient database queries with proper indexing

### Security Considerations

- Never log passwords or credentials
- Support encrypted passwords in configuration files
- Use existing NetWalker credential encryption mechanism
- Validate user input to prevent SQL injection (use parameterized queries)

### Logging

- Log all database queries (without sensitive data)
- Log connection attempts and results
- Log command execution (without sensitive output)
- Log errors with full stack traces
- Use existing NetWalker logging configuration

### Configuration

Extend netwalker.ini with command executor settings:

```ini
[command_executor]
# Connection timeout in seconds
connection_timeout = 30

# SSH parameters
ssh_strict_key = false

# Output directory for Excel files
output_directory = ./reports
```

## Future Enhancements

1. **Parallel Execution**: Add option for concurrent command execution
2. **Command Templates**: Support predefined command templates
3. **Output Parsing**: Add parsers for common command outputs (EIGRP, BGP, etc.)
4. **Scheduling**: Add ability to schedule recurring command execution
5. **Result Comparison**: Compare results across multiple executions
6. **Custom Filters**: Support more complex device filtering (by platform, site, etc.)
7. **Multiple Commands**: Execute multiple commands per device in single session
8. **Result Caching**: Cache results for offline analysis
