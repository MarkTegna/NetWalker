#!/usr/bin/env python3
"""
NetWalker Build Script

Creates Windows executable using PyInstaller with all necessary dependencies
and supporting files included.

Author: Mark Oldham
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import tempfile
from datetime import datetime

# Import version information
sys.path.insert(0, str(Path(__file__).parent))
from netwalker.version import __version__, __author__


def increment_patch_version():
    """Increment the patch version number before build"""
    version_file = Path("netwalker/version.py")
    
    # Read current version file
    with open(version_file, 'r') as f:
        content = f.read()
    
    # Parse current version
    current_version = __version__
    major, minor, patch = map(int, current_version.split('.'))
    
    # Increment patch version
    new_patch = patch + 1
    new_version = f"{major}.{minor}.{new_patch}"
    
    # Update compile date
    compile_date = datetime.now().strftime("%Y-%m-%d")
    
    # Update version file
    new_content = content.replace(
        f'__version__ = "{current_version}"',
        f'__version__ = "{new_version}"'
    ).replace(
        f'__compile_date__ = "{datetime.now().strftime("%Y-%m-%d")}"',
        f'__compile_date__ = "{compile_date}"'
    )
    
    # Handle case where compile_date might have different format
    import re
    new_content = re.sub(
        r'__compile_date__ = "[^"]*"',
        f'__compile_date__ = "{compile_date}"',
        new_content
    )
    
    with open(version_file, 'w') as f:
        f.write(new_content)
    
    print(f"Version incremented: {current_version} -> {new_version}")
    return new_version


def create_spec_file():
    """Create PyInstaller spec file with all necessary configurations"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Add project root to path
project_root = Path.cwd()
sys.path.insert(0, str(project_root))

block_cipher = None

# Define data files to include
datas = [
    # Include sample configuration files
    ('netwalker.ini', '.'),
    ('secret_creds.ini', '.'),
    ('seed_file.csv', '.'),
    
    # Include any additional data files
    ('netwalker', 'netwalker'),
]

# Add transport plugin packages as data files
import pkg_resources
try:
    # Try to include transport plugin packages
    for package in ['paramiko', 'ssh2', 'asyncssh']:
        try:
            pkg_path = pkg_resources.get_distribution(package).location
            if pkg_path:
                datas.append((f'{pkg_path}/{package}', package))
        except:
            pass
except:
    pass

# Define hidden imports for dynamic imports
hiddenimports = [
    # Core scrapli modules
    'scrapli',
    'scrapli.driver',
    'scrapli.driver.core',
    'scrapli.driver.core.cisco_iosxe',
    'scrapli.driver.core.cisco_iosxr',
    'scrapli.driver.core.cisco_nxos',
    'scrapli.driver.core.arista_eos',
    'scrapli.driver.core.juniper_junos',
    'scrapli.transport',
    'scrapli.transport.base',
    'scrapli.transport.plugins',
    'scrapli.transport.plugins.ssh2',
    'scrapli.transport.plugins.ssh2.transport',
    'scrapli.transport.plugins.paramiko',
    'scrapli.transport.plugins.paramiko.transport',
    'scrapli.transport.plugins.asyncssh',
    'scrapli.transport.plugins.asyncssh.transport',
    'scrapli.transport.plugins.telnet',
    'scrapli.transport.plugins.telnet.transport',
    'scrapli.transport.plugins.system',
    'scrapli.transport.plugins.system.transport',
    'scrapli.factory',
    'scrapli.exceptions',
    'scrapli.response',
    'scrapli.channel',
    'scrapli.logging',
    'scrapli_community',
    
    # Transport plugin dependencies
    'ssh2',
    'ssh2.session',
    'ssh2.channel',
    'ssh2.sftp',
    'ssh2.exceptions',
    'paramiko',
    'paramiko.client',
    'paramiko.ssh_exception',
    'paramiko.transport',
    'paramiko.channel',
    'paramiko.auth_handler',
    'paramiko.rsa',
    'paramiko.dss',
    'paramiko.ecdsa',
    'paramiko.ed25519',
    'paramiko.hostkeys',
    'paramiko.config',
    'asyncssh',
    'asyncssh.connection',
    'asyncssh.channel',
    'asyncssh.client',
    'asyncssh.auth',
    'asyncssh.crypto',
    
    # Other dependencies
    'openpyxl',
    'openpyxl.workbook',
    'openpyxl.worksheet',
    'openpyxl.styles',
    'configparser',
    'ipaddress',
    'hashlib',
    'threading',
    'concurrent.futures',
    'queue',
    'logging',
    'logging.handlers',
    'pathlib',
    'fnmatch',
    'socket',
    'datetime',
    'csv',
    'json',
    're',
    'base64',
    'binascii',
    'struct',
    'time',
    'os',
    'sys',
    'platform',
    'subprocess',
    'tempfile',
    'shutil',
    'glob',
    'collections',
    'itertools',
    'functools',
    'weakref',
    'copy',
    'pickle',
    'warnings',
    'traceback',
    'inspect',
    'types',
    'importlib',
    'importlib.util',
    'pkg_resources',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['.'],  # Use current directory for custom hooks
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'hypothesis',
        'test',
        'tests',
        '_pytest',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='netwalker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
    
    with open('netwalker.spec', 'w') as f:
        f.write(spec_content)
    
    print("Created PyInstaller spec file: netwalker.spec")


def prepare_supporting_files():
    """Prepare supporting files for distribution"""
    
    # Create sample configuration files if they don't exist
    if not Path('netwalker.ini').exists():
        print("Creating sample netwalker.ini...")
        # Import and create default config
        from netwalker.config.config_manager import ConfigurationManager
        config_manager = ConfigurationManager()
        config_manager.create_default_config('netwalker.ini')
    
    if not Path('secret_creds.ini').exists():
        print("Creating sample secret_creds.ini...")
        sample_creds = """# NetWalker Credentials Configuration
# This file contains device authentication credentials
# Credentials will be automatically encrypted when first used

[credentials]
# Primary credentials for device access
username = admin
password = password123

# Alternative credentials (optional)
# alt_username = backup_admin
# alt_password = backup_pass

# Enable password (optional)
# enable_password = enable123
"""
        with open('secret_creds.ini', 'w') as f:
            f.write(sample_creds)
    
    if not Path('seed_file.csv').exists():
        print("Creating sample seed_file.csv...")
        sample_seeds = """hostname,ip_address,status,error_details
router1,192.168.1.1,,
switch1,192.168.1.10,,
core-switch,10.0.0.1,,
"""
        with open('seed_file.csv', 'w') as f:
            f.write(sample_seeds)


def run_pyinstaller():
    """Run PyInstaller to create the executable"""
    print("Running PyInstaller...")
    
    # Clean previous builds
    if Path('dist').exists():
        shutil.rmtree('dist')
    if Path('build').exists():
        shutil.rmtree('build')
    
    # Run PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        'netwalker.spec'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("PyInstaller failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
    
    print("PyInstaller completed successfully!")
    return True


def create_distribution_package(version):
    """Create ZIP distribution package with version number"""
    exe_file = Path('dist/netwalker.exe')
    
    if not exe_file.exists():
        print("Executable file not found!")
        return False
    
    # Create distribution package name
    package_name = f"NetWalker_v{version}"
    package_path = Path(f"dist/{package_name}")
    
    # Create distribution directory
    if package_path.exists():
        shutil.rmtree(package_path)
    package_path.mkdir(parents=True)
    
    # Copy executable to distribution directory
    shutil.copy2(exe_file, package_path / 'netwalker.exe')
    
    # Copy supporting files to distribution
    supporting_files = [
        'netwalker.ini',
        'secret_creds.ini', 
        'seed_file.csv',
        'README.md'
    ]
    
    for file_name in supporting_files:
        if Path(file_name).exists():
            shutil.copy2(file_name, package_path)
    
    # Create README for distribution if it doesn't exist
    readme_path = package_path / 'README.md'
    if not readme_path.exists():
        readme_content = f"""# NetWalker v{version}

Network Topology Discovery Tool

## Author
{__author__}

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
```

## Files Included
- netwalker.exe - Single executable file with all libraries included
- netwalker.ini - Configuration file
- secret_creds.ini - Credentials file (will be encrypted automatically)
- seed_file.csv - Seed devices list

## Output
- Reports will be generated in ./reports directory
- Logs will be written to ./logs directory

## Notes
- This is a single executable file with all dependencies included
- No additional installation or Python environment required
- All libraries are packaged inside the executable

For more information, visit: https://github.com/MarkTegna
"""
        with open(readme_path, 'w') as f:
            f.write(readme_content)
    
    # Create ZIP file
    zip_name = f"dist/{package_name}.zip"
    shutil.make_archive(f"dist/{package_name}", 'zip', package_path.parent, package_path.name)
    
    print(f"Created distribution package: {zip_name}")
    return True


def test_executable():
    """Test the created executable"""
    exe_path = Path('dist/netwalker.exe')
    
    if not exe_path.exists():
        print("Executable not found!")
        return False
    
    print("Testing executable...")
    
    # Test version display
    result = subprocess.run([str(exe_path), '--version'], 
                          capture_output=True, text=True, timeout=30)
    
    if result.returncode == 0:
        print("Executable test passed!")
        print("Version output:", result.stdout.strip())
        return True
    else:
        print("Executable test failed!")
        print("STDERR:", result.stderr)
        return False


def main():
    """Main build process"""
    print(f"NetWalker Build Script")
    print(f"Author: {__author__}")
    print("-" * 50)
    
    try:
        # Step 1: Increment version
        new_version = increment_patch_version()
        
        # Step 2: Prepare supporting files
        prepare_supporting_files()
        
        # Step 3: Create PyInstaller spec file
        create_spec_file()
        
        # Step 4: Run PyInstaller
        if not run_pyinstaller():
            return 1
        
        # Step 5: Test executable
        if not test_executable():
            print("Warning: Executable test failed, but build completed")
        
        # Step 6: Create distribution package
        if not create_distribution_package(new_version):
            return 1
        
        print(f"\nBuild completed successfully!")
        print(f"Version: {new_version}")
        print(f"Executable: dist/netwalker.exe")
        print(f"Distribution: dist/NetWalker_v{new_version}.zip")
        
        return 0
    
    except Exception as e:
        print(f"Build failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())