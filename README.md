# NetWalker - Network Topology Discovery Tool

[![Version](https://img.shields.io/badge/version-0.1.1-blue.svg)](https://github.com/MarkTegna/NetWalker/releases)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/MarkTegna/NetWalker)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

NetWalker is a Windows-based Python application that automatically discovers and maps Cisco network topologies using CDP (Cisco Discovery Protocol) and LLDP (Link Layer Discovery Protocol). The system connects to seed devices via SSH/Telnet, recursively discovers neighboring devices, and generates comprehensive documentation in Excel format.

## 🚀 Features

### Core Functionality
- **Automated Discovery**: Breadth-first network traversal starting from seed devices
- **Command Execution**: Execute arbitrary commands on filtered device sets
- **Dual Protocol Support**: CDP and LLDP neighbor discovery
- **Connection Flexibility**: SSH with automatic TELNET fallback for legacy devices
- **Windows Compatible**: Proper TELNET transport for Windows systems
- **Concurrent Processing**: Multi-threaded discovery for large networks

### Reporting & Output
- **Excel Reports**: Comprehensive device inventory and connection details
- **Command Results**: Export command outputs to timestamped Excel files
- **Professional Formatting**: Auto-sized columns, filters, and headers
- **Multiple Workbooks**: Main discovery report plus per-seed device reports
- **Neighbor Details**: Individual sheets for each seed's neighbors
- **Timestamp Naming**: Automatic file naming with timestamps

### Advanced Features
- **Device Filtering**: Wildcard patterns, CIDR ranges, platform exclusions
- **Credential Security**: Multiple credential sources with interactive prompting fallback
- **Error Recovery**: Continues discovery despite individual device failures
- **Configurable Depth**: Limit discovery depth to control scope
- **Comprehensive Logging**: Detailed logs with configurable output directories

## 📦 Quick Start

### Download & Install
1. Download the latest release: [NetWalker_v0.1.1.zip](https://github.com/MarkTegna/NetWalker/releases)
2. Extract to your desired directory
3. No additional installation required - single executable with all dependencies

### Configuration
1. **Add Seed Devices** (`seed_file.csv`):
   ```
   CORE-SWITCH-01
   192.168.1.1
   router.example.com
   ```

2. **Configure Settings** (`netwalker.ini`) - Optional:
   ```ini
   [discovery]
   max_depth = 10
   concurrent_connections = 5
   
   [filtering]
   exclude_hostnames = PHONE*,CAMERA*
   exclude_platforms = linux,windows
   ```

3. **Set Credentials** - Multiple options available:
   ```bash
   # Option 1: CLI parameters (recommended for one-time use)
   netwalker.exe --username admin --password mypass
   
   # Option 2: Environment variables (recommended for automation)
   set NETWALKER_USERNAME=admin
   set NETWALKER_PASSWORD=mypass
   netwalker.exe
   
   # Option 3: Interactive prompting (if no credentials provided)
   netwalker.exe
   # Will prompt: "Username: " and "Password: "
   ```

### Run Discovery
```bash
# Basic discovery with CLI credentials
netwalker.exe --username admin --password mypass

# Using environment variables
set NETWALKER_USERNAME=admin
set NETWALKER_PASSWORD=mypass
netwalker.exe

# Interactive prompting (no credentials provided)
netwalker.exe
# Will prompt for username and password

# Custom configuration with credentials
netwalker.exe --config custom.ini --username admin --password mypass

# Specific seed devices with credentials
netwalker.exe --seed-devices "router1:192.168.1.1,switch1:192.168.1.2" --username admin --password mypass

# Show help
netwalker.exe --help
```

## 🎯 Command Execution

NetWalker can execute arbitrary commands on filtered sets of network devices and export results to Excel. This feature is perfect for collecting operational data, running show commands, or gathering configuration information across multiple devices.

### Quick Start - Execute Commands

```bash
# Execute command on devices matching a pattern
netwalker.exe execute --filter "*-SW-*" --command "show version"

# Execute with custom output directory
netwalker.exe execute --filter "CORE%" --command "show ip route summary" --output ./reports

# Execute with custom config file
netwalker.exe execute --config custom.ini --filter "%" --command "show interfaces status"
```

### Command Execution Options

```bash
netwalker.exe execute [OPTIONS]

Required Arguments:
  --filter, -f PATTERN      Device name filter pattern (SQL wildcards: % = multiple chars, _ = single char)
  --command, -cmd COMMAND   Command to execute on devices

Optional Arguments:
  --config, -c FILE         Configuration file path (default: netwalker.ini)
  --output, -o DIR          Output directory for Excel file (default: current directory)
```

### Filter Pattern Examples

```bash
# Match all devices
netwalker.exe execute --filter "%" --command "show version"

# Match devices with "SW" in the name
netwalker.exe execute --filter "%SW%" --command "show interfaces"

# Match devices starting with "CORE"
netwalker.exe execute --filter "CORE%" --command "show ip route"

# Match devices ending with "-01"
netwalker.exe execute --filter "%-01" --command "show running-config"

# Match specific pattern (e.g., BORO-SW-UW01, BORO-SW-UW02)
netwalker.exe execute --filter "BORO-SW-UW%" --command "show ip eigrp neighbors"
```

### Command Examples

```bash
# Show version information
netwalker.exe execute --filter "%" --command "show version"

# Check interface status
netwalker.exe execute --filter "%SWITCH%" --command "show interfaces status"

# View routing table
netwalker.exe execute --filter "CORE%" --command "show ip route"

# Check EIGRP neighbors
netwalker.exe execute --filter "*-RTR-*" --command "show ip eigrp neighbors"

# View running configuration (be careful with sensitive data!)
netwalker.exe execute --filter "CORE-SW-01" --command "show running-config"

# Check CDP neighbors
netwalker.exe execute --filter "%" --command "show cdp neighbors detail"
```

### Output Format

Command execution generates an Excel file with the following format:

**Filename**: `Command_Results_YYYYMMDD-HH-MM.xlsx`

**Columns**:
- **Device Name**: Hostname of the device
- **Device IP**: IP address used for connection
- **Status**: Success, Failed, Timeout, or Auth Failed
- **Command Output**: Complete command output (preserves line breaks)
- **Execution Time**: Time taken in seconds

**Example Console Output**:
```
Command Execution: show ip eigrp neighbors
================================================================================
Found 15 devices matching filter

Connecting to devices...
  [1/15] Connecting to BORO-SW-UW01 (10.1.1.1)...
    [OK] BORO-SW-UW01: Command executed successfully
  [2/15] Connecting to BORO-SW-UW02 (10.1.1.2)...
    [FAIL] BORO-SW-UW02: Connection timeout
  [3/15] Connecting to BORO-SW-UW03 (10.1.1.3)...
    [OK] BORO-SW-UW03: Command executed successfully

================================================================================
Execution Summary:
  Total devices: 15
  Successful: 13
  Failed: 2
  Total time: 45.3 seconds

Results exported to: Command_Results_20260209-19-15.xlsx
================================================================================
```

### Configuration

Add command executor settings to `netwalker.ini`:

```ini
[command_executor]
# Connection timeout in seconds (default: 30)
connection_timeout = 30

# SSH strict key checking (default: false)
ssh_strict_key = false

# Output directory for Excel files (default: current directory)
output_directory = ./reports
```

### Credentials

Command execution uses the same credential system as discovery:

1. **Credentials File** (`secret_creds.ini`):
   ```ini
   [credentials]
   username = admin
   password = mypassword
   enable_password = myenablepass
   ```

2. **Encrypted Passwords** (recommended):
   ```ini
   [credentials]
   username = admin
   password = ENC:bXlwYXNzd29yZA==
   enable_password = ENC:bXllbmFibGVwYXNz
   ```

3. **Interactive Prompting**: If credentials are not found, NetWalker will prompt for them.

### Use Cases

**Collect Version Information**:
```bash
netwalker.exe execute --filter "%" --command "show version" --output ./audit
```

**Check Interface Status Across Switches**:
```bash
netwalker.exe execute --filter "%SWITCH%" --command "show interfaces status"
```

**Verify EIGRP Neighbors**:
```bash
netwalker.exe execute --filter "%RTR%" --command "show ip eigrp neighbors"
```

**Audit Configuration**:
```bash
netwalker.exe execute --filter "CORE%" --command "show running-config | include logging"
```

**Troubleshoot Connectivity**:
```bash
netwalker.exe execute --filter "%" --command "show ip interface brief"
```

## 🔧 System Requirements

- **Operating System**: Windows 10/11 (64-bit)
- **Network Access**: SSH (port 22) and/or TELNET (port 23) to target devices
- **Permissions**: Network connectivity to discovery targets
- **Disk Space**: ~50MB for application + space for reports/logs

## 📊 Supported Devices

### Tested Platforms
- **Cisco IOS**: All versions
- **Cisco IOS-XE**: All versions  
- **Cisco NX-OS**: All versions
- **Generic Devices**: Any device supporting CDP or LLDP

### Connection Methods
- **SSH**: Primary connection method (port 22)
- **TELNET**: Automatic fallback for legacy devices (port 23)
- **Authentication**: Multiple credential sources (CLI, environment, interactive prompting)

## 🛠 Configuration Reference

### Discovery Settings
```ini
[discovery]
max_depth = 10                    # Maximum discovery depth
concurrent_connections = 5        # Simultaneous connections
connection_timeout = 30          # Connection timeout (seconds)
discovery_protocols = CDP,LLDP   # Protocols to use
```

### Filtering Options
```ini
[filtering]
include_wildcards = *             # Include patterns
exclude_wildcards = PHONE*       # Exclude patterns
exclude_cidrs = 192.168.100.0/24 # Exclude IP ranges

[exclusions]
exclude_platforms = linux,windows,phone
exclude_capabilities = phone,camera,printer
```

### Output Configuration
```ini
[output]
reports_directory = ./reports     # Report output directory
logs_directory = ./logs          # Log output directory
excel_format = xlsx              # Excel file format
```

## 📈 Example Output

### Console Output
```
NetWalker 0.1.1 by Mark Oldham
Loading configuration from netwalker.ini
Loaded 3 seed devices from seed_file.csv
Starting network discovery...

✅ CORE-SWITCH-A (192.168.1.1) - SSH - 5 neighbors found
✅ CORE-SWITCH-B (192.168.1.2) - TELNET - 3 neighbors found  
✅ ACCESS-SW-01 (192.168.1.10) - SSH - 2 neighbors found

Discovery completed: 15 devices discovered, 3 filtered
Reports generated in ./reports/
```

### Generated Files
- `NetWalker_Discovery_20260111-14-30.xlsx` - Main discovery report (summary, inventory, connections)
- `NetWalker_Inventory_20260111-14-30.xlsx` - Device inventory
- `NetWalker_Seed_CORE-SWITCH-A_20260111-14-30.xlsx` - Seed device report with neighbors
- `netwalker_20260111-14-30.log` - Detailed execution log

## 🔍 Troubleshooting

### Common Issues

**TELNET Connection Failures**
```
Error: system transport is not supported on windows devices
```
**Solution**: Update to v0.1.1+ which includes Windows TELNET compatibility fix.

**SSH Authentication Failures**
```
Error: Authentication failed for device X.X.X.X
```
**Solution**: Verify credentials. NetWalker will prompt for credentials if none are provided via CLI or environment variables.

**Discovery Stops Early**
```
Warning: Max depth reached, stopping discovery
```
**Solution**: Increase `max_depth` in `netwalker.ini` or use filtering to reduce scope.

### Command Execution Issues

**No Devices Found**
```
Found 0 devices matching filter
```
**Solution**: 
- Verify your filter pattern uses SQL wildcards (% not *)
- Check that devices exist in the database (run discovery first)
- Try a broader filter pattern like "%" to match all devices

**Database Connection Failed**
```
Failed to connect to database server: localhost
```
**Solution**:
- Verify database configuration in `netwalker.ini`
- Ensure SQL Server is running and accessible
- Check network connectivity to database server
- Verify database credentials are correct

**Connection Timeout**
```
[FAIL] DEVICE-NAME: Connection timeout
```
**Solution**:
- Verify device is reachable (ping test)
- Check firewall rules allow SSH/TELNET
- Increase `connection_timeout` in `netwalker.ini`
- Verify device IP address is correct in database

**Authentication Failed**
```
[FAIL] DEVICE-NAME: Auth Failed
```
**Solution**:
- Verify credentials in `secret_creds.ini`
- Ensure username and password are correct
- Check if enable password is required
- Verify account has appropriate privileges

**Excel Export Failed**
```
[FAIL] Permission denied writing Excel file
```
**Solution**:
- Close any open Excel files with the same name
- Verify write permissions to output directory
- Choose a different output directory with `--output`
- Check available disk space

**Command Returns Error**
```
Status: Success
Output: % Invalid input detected at '^' marker
```
**Note**: This is expected behavior. The connection succeeded, but the command had an error. The status is "Success" because the connection worked, and the error output is captured for analysis.

### Debug Mode
Enable detailed logging by editing `netwalker.ini`:
```ini
[logging]
level = DEBUG
```

Logs are saved to the logs directory with timestamps: `netwalker_YYYYMMDD-HH-MM.log`

## 🧪 Development & Testing

### Property-Based Testing
NetWalker includes comprehensive property-based tests covering:
- Connection management (SSH/TELNET fallback)
- Discovery algorithms (breadth-first traversal)
- Filtering logic (wildcards, CIDR ranges)
- Report generation (Excel formatting)
- Error handling (isolation and recovery)

### Running Tests
```bash
# Install development dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest tests/

# Run property tests only
python -m pytest tests/property/

# Run with coverage
python -m pytest --cov=netwalker tests/
```

## 📝 Version History

### v0.1.1 (2026-01-11)
- 🔧 **Fixed**: Windows TELNET compatibility issue
- 🚀 **Added**: Automatic SSH to TELNET fallback
- 📊 **Improved**: Error handling and logging
- 🧪 **Added**: Comprehensive property-based test suite

### v0.0.26 (Previous)
- 🎯 **Initial**: Core discovery functionality
- 📊 **Added**: Excel report generation
- 🔧 **Added**: Device filtering capabilities

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Clone repository
git clone https://github.com/MarkTegna/NetWalker.git
cd NetWalker

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Build executable
python build_executable.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Mark Oldham**
- GitHub: [@MarkTegna](https://github.com/MarkTegna)
- Email: [Contact via GitHub](https://github.com/MarkTegna)

## 🙏 Acknowledgments

- **scrapli**: Network device connectivity library
- **openpyxl**: Excel file generation
- **hypothesis**: Property-based testing framework
- **Cisco Systems**: CDP and LLDP protocols

---

**⭐ Star this repository if NetWalker helps you map your network topology!**