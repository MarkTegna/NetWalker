# NetWalker Quick Start Guide

**Author:** Mark Oldham  
**Version:** 0.2.47  
**Platform:** Windows  

## 🚀 Quick Setup (5 Minutes)

### 1. Download and Extract
```
1. Download NetWalker_v0.2.47.zip
2. Extract to C:\NetWalker\ (or your preferred location)
3. Open PowerShell as Administrator
4. Navigate to NetWalker directory: cd C:\NetWalker
```

### 2. Configure Credentials
Edit `secret_creds.ini`:
```ini
[credentials]
username = your_network_username
password = your_network_password
enable_password = your_enable_password
```

### 3. Add Seed Devices
Edit `seed_file.csv`:
```csv
hostname,ip_address,status
CORE-SWITCH-01,192.168.1.1,
CORE-SWITCH-02,192.168.1.2,
```

### 4. Run Discovery
```powershell
.\netwalker.exe
```

## 📋 Essential Configuration

### Basic Settings (netwalker.ini)
```ini
[discovery]
max_depth = 2                    # How deep to discover (1-5)
discovery_timeout = 300          # 5 minutes total timeout
connection_timeout = 30          # 30 seconds per device

[output]
site_boundary_pattern = *-CORE-* # Creates separate site workbooks
reports_directory = ./reports    # Where Excel files go
logs_directory = ./logs         # Where log files go
```

### Device Filtering
```ini
[exclusions]
# Exclude these device types (already configured)
exclude_platforms = linux,windows,unix,server,printer,phone
exclude_capabilities = host phone,camera,printer,server
```

## 🎯 Common Use Cases

### Small Network (< 50 devices)
```ini
[discovery]
max_depth = 3
concurrent_connections = 3
discovery_timeout = 180
```

### Large Network (> 500 devices)
```ini
[discovery]
max_depth = 2
concurrent_connections = 5
discovery_timeout = 600
```

### Multi-Site Network
```ini
[output]
site_boundary_pattern = *-CORE-*  # Matches SITE-CORE-A, SITE-CORE-B
```
**Result:** Separate Excel workbooks for each site

## 📊 Understanding Reports

### Generated Files
- `Discovery_YYYYMMDD-HH-MM.xlsx` - Main discovery report
- `Discovery_SITENAME_YYYYMMDD-HH-MM.xlsx` - Site-specific reports
- `Seed_HOSTNAME_YYYYMMDD-HH-MM.xlsx` - Per-seed device reports

### Excel Sheets
- **Discovery Summary** - Overview and statistics
- **Device Inventory** - All discovered devices
- **Network Connections** - Device-to-device connections
- **Neighbors_HOSTNAME** - Individual device neighbors

## 🔧 Troubleshooting

### Discovery Stops Early
```ini
# Increase timeout for large networks
[discovery]
discovery_timeout = 900  # 15 minutes
```

### Authentication Failures
```
1. Verify credentials in secret_creds.ini
2. Test SSH/Telnet manually to a device
3. Check enable password if using Cisco devices
```

### No Site Boundaries
```
1. Check seed device hostnames match pattern
2. Review logs for site boundary detection
3. Adjust site_boundary_pattern if needed
```

### Too Many Devices
```ini
# Add more aggressive filtering
[exclusions]
exclude_hostnames = PC-*,LAPTOP-*,PHONE-*
exclude_ip_ranges = 192.168.100.0/24,10.0.50.0/24
```

## 📝 Command Line Options

```powershell
# Basic discovery
.\netwalker.exe

# Custom seed file
.\netwalker.exe --seed-file my_seeds.csv

# Resume previous discovery
.\netwalker.exe --resume

# Inventory only (no neighbor discovery)
.\netwalker.exe --inventory-only

# DNS validation
.\netwalker.exe --dns-validation

# Help
.\netwalker.exe --help
```

## 🎯 Best Practices

### 1. Start Small
- Begin with 2-3 seed devices
- Test configuration before full deployment
- Review first reports to adjust filtering

### 2. Monitor Progress
- Watch log files during discovery
- Check for authentication failures
- Monitor timeout resets for large networks

### 3. Optimize Performance
- Use appropriate max_depth (2-3 for most networks)
- Adjust concurrent_connections based on network capacity
- Enable aggressive filtering for large environments

### 4. Regular Maintenance
- Update credentials when they change
- Review and update seed devices quarterly
- Archive old reports to save disk space

## 🚨 Important Notes

### Security
- Store `secret_creds.ini` securely
- Use read-only accounts when possible
- Limit network access to discovery workstation

### Performance
- Discovery speed: ~5-10 devices per minute
- Memory usage: ~50-100MB typical
- Disk space: ~10-50MB per discovery session

### Compatibility
- **Supported**: Cisco IOS/IOS-XE/NX-OS, generic LLDP devices
- **Enhanced**: Cisco NEXUS with specialized parsing
- **Platform**: Windows 10/11, Windows Server 2016+

## 📞 Getting Help

### Log Files
Check `logs/netwalker_YYYYMMDD-HH-MM.log` for:
- Discovery decisions
- Authentication issues
- Filtering results
- Site boundary detection

### Key Log Messages
- `[DISCOVERY DECISION]` - Device processing
- `[NEIGHBOR FILTERED]` - Why devices were excluded
- `[TIMEOUT RESET]` - Dynamic timeout management
- `[SITE BOUNDARY]` - Site detection results

### Support Resources
- **Documentation**: `NETWALKER_COMPREHENSIVE_GUIDE.md`
- **Release Notes**: `RELEASE_NOTES_v0.2.47.md`
- **GitHub**: [https://github.com/MarkTegna](https://github.com/MarkTegna)

---

**Ready to discover your network? Run `.\netwalker.exe` and watch the magic happen!** ✨

*For detailed configuration and advanced features, see the Comprehensive Guide.*