#!/usr/bin/env python3
"""
NetWalker Distribution Creator

Creates ZIP distribution package with version numbering from existing build.

Author: Mark Oldham
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# Import version information
sys.path.insert(0, str(Path(__file__).parent))
from netwalker.version import __version__, __author__


def create_distribution_package(version):
    """Create ZIP distribution package with version number"""
    dist_dir = Path('dist/netwalker')
    
    if not dist_dir.exists():
        print("Distribution directory not found! Please run build_executable.py first.")
        return False
    
    # Create distribution package name
    package_name = f"NetWalker_v{version}"
    package_path = Path(f"dist/{package_name}")
    
    # Remove existing package directory if it exists
    if package_path.exists():
        print(f"Removing existing package directory: {package_path}")
        shutil.rmtree(package_path)
    
    # Copy distribution files to versioned directory
    print(f"Creating distribution package: {package_path}")
    shutil.copytree(dist_dir, package_path)
    
    # Copy supporting files to distribution
    supporting_files = [
        'netwalker.ini',
        'secret_creds.ini', 
        'seed_file.csv',
    ]
    
    for file_name in supporting_files:
        if Path(file_name).exists():
            print(f"Adding supporting file: {file_name}")
            shutil.copy2(file_name, package_path)
        else:
            print(f"Warning: Supporting file not found: {file_name}")
    
    # Create README for distribution
    readme_path = package_path / 'README.md'
    readme_content = f"""# NetWalker v{version}

Network Topology Discovery Tool

## Author
{__author__}

## Version Information
- Version: {version}
- Compile Date: {datetime.now().strftime("%Y-%m-%d")}
- Platform: Windows

## Installation
1. Extract all files to a directory
2. Edit netwalker.ini with your network settings
3. Edit secret_creds.ini with your device credentials
4. Edit seed_file.csv with your seed devices
5. Run netwalker.exe

## Usage
```
netwalker.exe --config netwalker.ini
netwalker.exe --seed-devices "router1:192.168.1.1,switch1:192.168.1.2"
netwalker.exe --help
netwalker.exe --version
```

## Command Line Options
- `--config <file>` - Specify configuration file (default: netwalker.ini)
- `--seed-devices <list>` - Comma-separated list of seed devices (hostname:ip)
- `--max-depth <num>` - Maximum discovery depth (default: 10)
- `--concurrent <num>` - Number of concurrent connections (default: 5)
- `--reports-dir <path>` - Output directory for reports (default: ./reports)
- `--logs-dir <path>` - Output directory for logs (default: ./logs)
- `--dry-run` - Test configuration without running discovery
- `--version` - Display version information
- `--help` - Display help information

## Files Included
- **netwalker.exe** - Main executable (no Python installation required)
- **netwalker.ini** - Configuration file with all available options
- **secret_creds.ini** - Credentials file (will be encrypted automatically)
- **seed_file.csv** - Seed devices list for batch processing
- **README.md** - This documentation file
- **_internal/** - Supporting libraries and dependencies (do not modify)

## Configuration Files

### netwalker.ini
Main configuration file with discovery settings, filtering options, and output preferences.

### secret_creds.ini
Device authentication credentials. Plain text passwords will be automatically encrypted with MD5 on first use.

### seed_file.csv
CSV file containing seed devices for batch discovery. Format: hostname,ip_address,status,error_details

## Output Files
- **Reports**: Excel files generated in ./reports directory (or configured location)
  - NetWalker_Discovery_YYYYMMDD-HH-MM.xlsx - Connection details
  - NetWalker_Master_Inventory_YYYYMMDD-HH-MM.xlsx - Device inventory
- **Logs**: Application logs in ./logs directory (or configured location)
  - netwalker_YYYYMMDD-HH-MM.log - Detailed execution logs

## System Requirements
- Windows 10 or later
- No Python installation required
- Network connectivity to target devices
- Sufficient disk space for reports and logs

## Network Discovery Features
- **Protocols**: CDP (Cisco Discovery Protocol) and LLDP (Link Layer Discovery Protocol)
- **Connections**: SSH with Telnet fallback
- **Traversal**: Breadth-first network exploration
- **Filtering**: Wildcard patterns and CIDR ranges
- **Concurrent Processing**: Configurable parallel connections
- **Error Handling**: Robust error isolation and recovery

## Supported Platforms
- Cisco IOS
- Cisco IOS-XE  
- Cisco NX-OS
- Other CDP/LLDP compatible devices

## Troubleshooting

### Common Issues
1. **Connection failures**: Check credentials in secret_creds.ini
2. **Permission errors**: Run as Administrator if needed
3. **Network timeouts**: Adjust connection_timeout in netwalker.ini
4. **Missing reports**: Check reports directory permissions

### Getting Help
- Run `netwalker.exe --help` for command line options
- Check log files in ./logs directory for detailed error information
- Verify network connectivity to seed devices

## Support
For issues or questions, visit: https://github.com/MarkTegna

---
**NetWalker Network Topology Discovery Tool**  
**Author**: {__author__}  
**Version**: {version}  
**Build Date**: {datetime.now().strftime("%Y-%m-%d")}
"""
    
    print(f"Creating README.md with version {version}")
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    # Create ZIP file (remove existing first)
    zip_name = f"dist/{package_name}.zip"
    if Path(zip_name).exists():
        print(f"Removing existing ZIP file: {zip_name}")
        os.remove(zip_name)
    
    print(f"Creating ZIP distribution: {zip_name}")
    shutil.make_archive(f"dist/{package_name}", 'zip', package_path.parent, package_path.name)
    
    # Verify ZIP file was created
    if Path(zip_name).exists():
        zip_size = Path(zip_name).stat().st_size
        print(f"✅ ZIP distribution created successfully!")
        print(f"   File: {zip_name}")
        print(f"   Size: {zip_size:,} bytes ({zip_size / 1024 / 1024:.1f} MB)")
        return True
    else:
        print("❌ Failed to create ZIP distribution!")
        return False


def test_distribution_package(version):
    """Test the distribution package"""
    package_name = f"NetWalker_v{version}"
    zip_path = Path(f"dist/{package_name}.zip")
    
    if not zip_path.exists():
        print("❌ Distribution ZIP file not found!")
        return False
    
    print("🔍 Testing distribution package...")
    
    # Test ZIP file integrity
    try:
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            # Test ZIP file
            test_result = zip_file.testzip()
            if test_result is None:
                print("✅ ZIP file integrity check passed")
            else:
                print(f"❌ ZIP file integrity check failed: {test_result}")
                return False
            
            # Check required files
            required_files = [
                f"{package_name}/netwalker.exe",
                f"{package_name}/README.md",
                f"{package_name}/netwalker.ini",
                f"{package_name}/secret_creds.ini",
                f"{package_name}/seed_file.csv"
            ]
            
            zip_contents = [f.filename for f in zip_file.filelist]
            
            for required_file in required_files:
                if required_file in zip_contents:
                    print(f"✅ Required file found: {required_file}")
                else:
                    print(f"❌ Required file missing: {required_file}")
                    return False
            
            print(f"✅ Distribution package contains {len(zip_contents)} files")
            return True
            
    except Exception as e:
        print(f"❌ Error testing ZIP file: {e}")
        return False


def main():
    """Main distribution creation process"""
    print(f"NetWalker Distribution Creator")
    print(f"Author: {__author__}")
    print(f"Version: {__version__}")
    print("-" * 50)
    
    try:
        # Create distribution package
        if not create_distribution_package(__version__):
            return 1
        
        # Test distribution package
        if not test_distribution_package(__version__):
            print("Warning: Distribution package test failed")
        
        print(f"\n🎉 Distribution creation completed successfully!")
        print(f"📦 Package: NetWalker_v{__version__}.zip")
        print(f"📁 Location: dist/NetWalker_v{__version__}.zip")
        print(f"📋 Contents: Executable, configuration files, documentation")
        
        return 0
    
    except Exception as e:
        print(f"❌ Distribution creation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())