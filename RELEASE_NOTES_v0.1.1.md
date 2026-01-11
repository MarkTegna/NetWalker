# NetWalker v0.1.1 Release Notes

## 🎉 Major Release: TELNET Fix and Windows Compatibility

### 🔧 Key Features
- **Windows TELNET Compatibility**: Fixed critical issue where TELNET connections failed on Windows systems
- **SSH/TELNET Fallback**: Robust connection handling with automatic fallback from SSH to TELNET
- **Network Discovery**: Automated Cisco network topology discovery using CDP and LLDP protocols
- **Excel Reporting**: Comprehensive Excel reports with device inventory and connection details
- **Concurrent Processing**: Multi-threaded discovery for efficient large network scanning
- **Device Filtering**: Advanced filtering by hostname patterns, IP ranges, and device capabilities

### 🐛 Bug Fixes
- **TELNET Transport**: Resolved "system transport is not supported on windows devices" error
- **Connection Fallback**: Fixed SSH to TELNET fallback mechanism for devices like CBS01711
- **Windows Compatibility**: Proper transport selection for Windows platform

### 🚀 Improvements
- **Property-Based Testing**: Comprehensive test suite with 34+ correctness properties
- **Error Handling**: Improved error isolation and recovery during discovery
- **Logging**: Enhanced logging with configurable output directories
- **Configuration**: Flexible INI-based configuration with CLI overrides

### 📦 Distribution
- **Single Executable**: All dependencies packaged in `netwalker.exe`
- **Sample Configuration**: Generic configuration files with examples
- **Documentation**: Complete setup and usage instructions

### 🔒 Security
- **Credential Security**: Secure credential handling via CLI parameters and environment variables
- **Clean Distribution**: No production credentials or sensitive data included

### 📋 System Requirements
- **Platform**: Windows (tested on Windows 10/11)
- **Network Access**: SSH (port 22) and/or TELNET (port 23) to network devices
- **Permissions**: Network connectivity to target devices

### 🛠 Installation
1. Download `NetWalker_v0.1.1.zip`
2. Extract to desired directory
3. Edit `seed_file.csv` with your seed devices
4. Run `netwalker.exe` with credentials via CLI parameters

### 📖 Usage Examples
```bash
# Basic discovery with credentials
netwalker.exe --username admin --password mypass

# Custom configuration
netwalker.exe --config custom.ini --username admin --password mypass

# Specific seed devices
netwalker.exe --seed-devices "router1:192.168.1.1,switch1:192.168.1.2" --username admin --password mypass

# Show help
netwalker.exe --help
```

### 🔍 Tested Scenarios
- ✅ SSH connections to modern Cisco devices
- ✅ TELNET fallback for legacy devices (like CBS01711)
- ✅ Mixed SSH/TELNET environments
- ✅ Large network topologies (100+ devices)
- ✅ Concurrent discovery operations
- ✅ Error recovery and continuation

### 📊 Technical Details
- **Version**: 0.1.1
- **Build Date**: 2026-01-11
- **Author**: Mark Oldham
- **License**: See repository for details

### 🔗 Links
- **Repository**: https://github.com/MarkTegna/NetWalker
- **Issues**: https://github.com/MarkTegna/NetWalker/issues
- **Documentation**: See README.md in distribution

---

**Note**: This release resolves the critical TELNET compatibility issue reported for device CBS01711 (10.167.1.210) and similar devices that require TELNET fallback on Windows systems.