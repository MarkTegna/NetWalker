# NetWalker v0.5.1 Release Notes

**Release Date:** January 15, 2026  
**Author:** Mark Oldham

## Overview

Version 0.5.1 is a minor release focusing on hardware detection improvements and VLAN parsing fixes for Cisco Nexus devices. This release also includes credential management enhancements and inventory reporting improvements.

## What's New

### Hardware Detection Improvements

1. **Nexus Hardware Model with Hyphens**
   - Fixed extraction for Nexus models containing hyphens (e.g., C9336C-FX2)
   - Updated regex pattern to handle `cisco Nexus9000 C9336C-FX2 Chassis` format
   - Pattern now correctly skips Nexus series number and captures actual model

2. **Catalyst 4500X Support**
   - Added detection for WS-C4500X series switches
   - New pattern handles format: `cisco WS-C4500X-16 (MPC8572) processor`
   - Tested on WS-C4500X-16 devices

### VLAN Parsing Fix

1. **NX-OS Type Section Handling**
   - Fixed duplicate VLAN warnings on Nexus devices
   - Parser now stops at "VLAN Type" section to avoid confusion
   - Prevents treating VLAN type (e.g., "enet") as VLAN name
   - Example fix: VLAN 1 no longer appears twice as "default" and "enet"

### Credential Management

1. **Extended Credential Search**
   - Now checks grandparent directory for `secret_creds.ini`
   - Search order: current dir → parent dir → grandparent dir
   - Paths: `.\`, `..\`, `..\..\`

2. **Optional Enable Password**
   - Added `prompt_for_enable_password` configuration option
   - Default: false (no prompt)
   - CLI flag: `--enable-password` (boolean)
   - INI setting: `[credentials]` section

3. **Database Password Encryption**
   - Automatic encryption of plaintext database passwords
   - Uses base64 encoding with `ENC:` prefix
   - Rewrites INI file with encrypted password

### Inventory Reporting

1. **Skipped Device Filtering**
   - Devices with status "skipped" excluded from inventory sheets
   - Still included in discovery sheets for troubleshooting
   - Prevents inaccurate/incomplete information in inventory

## Bug Fixes

- Fixed credential manager logger initialization order
- Fixed hardware model extraction for various Cisco platforms
- Resolved NX-OS VLAN duplicate detection false positives

## Technical Details

### Modified Files

**Core Components:**
- `netwalker/discovery/device_collector.py` - Hardware model extraction patterns
- `netwalker/vlan/vlan_parser.py` - NX-OS VLAN parsing logic
- `netwalker/config/credentials.py` - Credential file search and enable password
- `netwalker/config/config_manager.py` - Database password encryption
- `netwalker/reports/excel_generator.py` - Inventory sheet filtering

**Configuration:**
- `netwalker.ini` - Added `[credentials]` section with `prompt_for_enable_password`
- `main.py` - Updated `--enable-password` CLI argument

### Hardware Model Patterns

**Pattern 1:** Model Number field (highest priority)
```regex
Model [Nn]umber\s*:\s*([\w-]+)
```

**Pattern 2:** NX-OS Chassis
```regex
cisco\s+Nexus\d*\s+([\w-]+)\s+Chassis
```

**Pattern 3:** Catalyst 4500X
```regex
cisco\s+(WS-[\w-]+)\s+\([^)]+\)\s+processor
```

**Pattern 4:** ISR/ASR with slash
```regex
cisco\s+([\w-]+/[\w-]+)\s+\([^)]+\)\s+processor
```

### VLAN Parsing Logic

NX-OS `show vlan` output has two sections:
1. **VLAN Name section** (lines 1-435): VLAN ID, Name, Status, Ports
2. **VLAN Type section** (lines 436+): VLAN ID, Type, Vlan-mode

Parser now stops at "VLAN Type" header to avoid parsing type as name.

## Testing

### Devices Tested

**Nexus Devices:**
- DFW1-CORE-A (C9336C-FX2) - Hardware model extraction ✓
- iad2-tegna-56128p-2 (56128P) - Hardware model extraction ✓

**Catalyst Devices:**
- KIDY-CORE-A (WS-C4500X-16) - Hardware model extraction ✓
- KIII-CORE-A (WS-C4500X-16) - Hardware model extraction ✓
- WMAZ-CORE-A (WS-C4500X-16) - Hardware model extraction ✓

**IOS-XE Devices:**
- KENS-CORE-A (C9500-48Y4C) - Regression test ✓
- KSDK-CORE-A (C9500-48Y4C) - Regression test ✓
- BORO-UW01 (ISR4451-X/K9) - Regression test ✓

### Test Results

- All hardware models correctly detected
- No duplicate VLAN warnings on Nexus devices
- Credential file search working in all three directories
- Inventory sheets correctly exclude skipped devices

## Installation

### New Installation

1. Download `NetWalker_v0.5.1.zip` from GitHub releases
2. Extract to a directory
3. Edit `netwalker.ini` with your network settings
4. Edit `seed_file.csv` with your seed devices
5. Run `netwalker.exe`

### Upgrade from Previous Version

1. Backup your current `netwalker.ini` and `seed_file.csv`
2. Extract new version to a new directory
3. Copy your backed-up configuration files to new directory
4. Run `netwalker.exe`

## Configuration Changes

### New INI Settings

```ini
[credentials]
# Prompt for enable password (default: false)
prompt_for_enable_password = false
```

### Database Password Encryption

If you have a plaintext database password in your INI file:
```ini
[database]
password = MyPassword123
```

It will be automatically encrypted on first run:
```ini
[database]
password = ENC:TXlQYXNzd29yZDEyMw==
```

## Known Issues

None reported in this release.

## Upgrade Notes

- No breaking changes
- Configuration files from v0.4.x are compatible
- Database passwords will be automatically encrypted on first run

## Future Enhancements

- Additional hardware platform support
- Enhanced VLAN reporting features
- Database integration improvements

## Support

For issues or questions:
- GitHub: https://github.com/MarkTegna/NetWalker
- Create an issue on GitHub for bug reports

## Version History

- **v0.5.1** (2026-01-15) - Hardware detection and VLAN parsing improvements
- **v0.4.18** (2026-01-15) - NX-OS VLAN Type section fix
- **v0.4.17** (2026-01-15) - Catalyst 4500X detection
- **v0.4.16** (2026-01-15) - Credential search improvements
- **v0.4.15** (2026-01-15) - Nexus hardware model fix

## Credits

**Author:** Mark Oldham  
**Platform:** Windows  
**Python Version:** 3.11+  
**Build Tool:** PyInstaller

---

*NetWalker - Network Topology Discovery Tool*
