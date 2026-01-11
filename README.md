# NetWalker - Network Topology Discovery Tool

[![Version](https://img.shields.io/badge/version-0.1.1-blue.svg)](https://github.com/MarkTegna/NetWalker/releases)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/MarkTegna/NetWalker)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

NetWalker is a Windows-based Python application that automatically discovers and maps Cisco network topologies using CDP (Cisco Discovery Protocol) and LLDP (Link Layer Discovery Protocol). The system connects to seed devices via SSH/Telnet, recursively discovers neighboring devices, and generates comprehensive documentation in Excel format.

## 🚀 Features

### Core Functionality
- **Automated Discovery**: Breadth-first network traversal starting from seed devices
- **Dual Protocol Support**: CDP and LLDP neighbor discovery
- **Connection Flexibility**: SSH with automatic TELNET fallback for legacy devices
- **Windows Compatible**: Proper TELNET transport for Windows systems
- **Concurrent Processing**: Multi-threaded discovery for large networks

### Reporting & Output
- **Excel Reports**: Comprehensive device inventory and connection details
- **Professional Formatting**: Auto-sized columns, filters, and headers
- **Multiple Sheets**: Consolidated connections, device inventory, per-device details
- **Timestamp Naming**: Automatic file naming with timestamps

### Advanced Features
- **Device Filtering**: Wildcard patterns, CIDR ranges, platform exclusions
- **Credential Security**: Automatic MD5 encryption of passwords
- **Error Recovery**: Continues discovery despite individual device failures
- **Configurable Depth**: Limit discovery depth to control scope
- **Comprehensive Logging**: Detailed logs with configurable output directories

## 📦 Quick Start

### Download & Install
1. Download the latest release: [NetWalker_v0.1.1.zip](https://github.com/MarkTegna/NetWalker/releases)
2. Extract to your desired directory
3. No additional installation required - single executable with all dependencies

### Configuration
1. **Edit Credentials** (`secret_creds.ini`):
   ```ini
   [credentials]
   username = your_username
   password = your_password
   # enable_password = your_enable_password  # Optional
   ```

2. **Add Seed Devices** (`seed_file.csv`):
   ```
   CORE-SWITCH-01
   192.168.1.1
   router.example.com
   ```

3. **Configure Settings** (`netwalker.ini`) - Optional:
   ```ini
   [discovery]
   max_depth = 10
   concurrent_connections = 5
   
   [filtering]
   exclude_hostnames = PHONE*,CAMERA*
   exclude_platforms = linux,windows
   ```

### Run Discovery
```bash
# Basic discovery
netwalker.exe

# Custom configuration
netwalker.exe --config custom.ini

# Specific seed devices
netwalker.exe --seed-devices "router1:192.168.1.1,switch1:192.168.1.2"

# Show help
netwalker.exe --help
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
- **Authentication**: Username/password with optional enable password

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
- `NetWalker_Discovery_20260111-14-30.xlsx` - Main discovery report
- `NetWalker_Inventory_20260111-14-30.xlsx` - Device inventory
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
**Solution**: Verify credentials in `secret_creds.ini` and ensure SSH is enabled on target devices.

**Discovery Stops Early**
```
Warning: Max depth reached, stopping discovery
```
**Solution**: Increase `max_depth` in `netwalker.ini` or use filtering to reduce scope.

### Debug Mode
Enable detailed logging by editing `netwalker.ini`:
```ini
[logging]
level = DEBUG
```

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