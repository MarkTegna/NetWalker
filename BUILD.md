# NetWalker Build Instructions

This document describes how to build NetWalker into a Windows executable using PyInstaller.

## Author
Mark Oldham

## Prerequisites

1. **Python 3.8+** installed and available in PATH
2. **All dependencies** installed: `pip install -r requirements.txt`
3. **Windows environment** (tested on Windows 10/11)

## Build Scripts

### Quick Build Options

#### Option 1: PowerShell Script (Recommended)
```powershell
.\build.ps1
```

#### Option 2: Batch Script
```cmd
build.bat
```

#### Option 3: Python Script (Direct)
```cmd
python build_executable.py
```

### Manual Build Process

If you prefer to run the build steps manually:

1. **Install PyInstaller**:
   ```cmd
   pip install pyinstaller
   ```

2. **Increment Version** (automatic in build scripts):
   ```cmd
   python increment_build.py
   ```

3. **Create Executable**:
   ```cmd
   pyinstaller --clean --noconfirm netwalker.spec
   ```

## Version Management

### Automatic Version Increment
- **PATCH version** is automatically incremented with every build
- Version format: `MAJOR.MINOR.PATCH` (e.g., `1.2.15`)

### Manual Version Updates

#### Increment Patch Version
```cmd
python increment_build.py --patch
```

#### Increment Minor Version
```cmd
python increment_build.py --minor
```

#### Increment Major Version
```cmd
python increment_build.py --major
```

#### Set Specific Version
```cmd
python update_version.py 1.0.0
```

#### Show Current Version
```cmd
python update_version.py --show
```

## Build Output

### Generated Files

After a successful build, you'll find:

```
dist/
├── netwalker/                    # Executable directory
│   ├── netwalker.exe            # Main executable
│   └── _internal/               # Supporting libraries
├── NetWalker_v{version}/        # Distribution package
│   ├── netwalker.exe            # Main executable
│   ├── _internal/               # Supporting libraries
│   ├── netwalker.ini            # Sample configuration
│   ├── secret_creds.ini         # Sample credentials
│   ├── seed_file.csv            # Sample seed devices
│   └── README.md                # Distribution README
└── NetWalker_v{version}.zip     # ZIP distribution
```

### File Naming Convention

- **Executable**: `netwalker.exe` (no version in filename)
- **ZIP Distribution**: `NetWalker_v{version}.zip` (includes version)
- **Timestamps**: Use `YYYYMMDD-HH-MM` format for logs and reports

## Testing the Executable

### Basic Tests
```cmd
# Test version display
.\dist\netwalker\netwalker.exe --version

# Test help display
.\dist\netwalker\netwalker.exe --help

# Test configuration loading
.\dist\netwalker\netwalker.exe --config netwalker.ini --dry-run
```

### Clean System Testing

To test on a clean Windows system:

1. Copy the entire `NetWalker_v{version}` directory to the target system
2. Ensure no Python installation is required
3. Run `netwalker.exe --version` to verify functionality
4. Test with sample configuration files

## Build Configuration

### PyInstaller Spec File

The build process uses `netwalker.spec` with the following key settings:

- **Console Application**: `console=True`
- **Single Directory**: Executable with supporting files in `_internal/`
- **UPX Compression**: Enabled for smaller file size
- **Hidden Imports**: All required modules explicitly listed
- **Data Files**: Configuration samples included

### Included Dependencies

The executable includes:
- **scrapli**: SSH/Telnet connectivity
- **openpyxl**: Excel report generation
- **configparser**: Configuration file handling
- **ipaddress**: IP address validation
- **All Python standard library modules**

### Excluded from Build

- **pytest**: Testing framework
- **hypothesis**: Property-based testing
- **Test files**: All test directories
- **Development tools**: Linting, formatting tools

## Troubleshooting

### Common Build Issues

#### PyInstaller Not Found
```cmd
pip install --upgrade pyinstaller
```

#### Missing Dependencies
```cmd
pip install -r requirements.txt
```

#### Permission Errors
- Run command prompt as Administrator
- Check antivirus software isn't blocking the build

#### Import Errors in Executable
- Check `hiddenimports` in `netwalker.spec`
- Add missing modules to the hidden imports list

### Build Validation

The build script automatically validates:
- ✅ Version increment successful
- ✅ PyInstaller completed without errors
- ✅ Executable runs and displays version
- ✅ Distribution package created
- ✅ ZIP file generated with correct naming

### Clean Build

To perform a completely clean build:

```cmd
# Remove previous build artifacts
rmdir /s /q build
rmdir /s /q dist

# Run build
python build_executable.py
```

## Distribution

### Local Distribution
- Use the generated ZIP file: `NetWalker_v{version}.zip`
- Contains executable and all supporting files
- No Python installation required on target system

### GitHub Distribution
- Push to GitHub only when instructed
- Tag releases with version numbers: `v{version}`
- Include ZIP file in GitHub releases
- Update CHANGELOG.md with version history

## Version History

Version increments follow these rules:

- **MAJOR**: Incompatible API changes, major new features
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, small improvements (auto-incremented on build)

### Example Version Progression
```
0.0.1  -> Initial version
0.0.2  -> First build (patch increment)
0.1.0  -> Added new feature (minor increment)
1.0.0  -> Major release (major increment)
1.0.1  -> Bug fix (patch increment)
```

## Support

For build issues or questions:
- Check this documentation first
- Review error messages in build output
- Ensure all prerequisites are met
- Test on a clean Windows system if possible

---

**Author**: Mark Oldham  
**Last Updated**: 2026-01-11  
**Build System**: PyInstaller 5.13.0+