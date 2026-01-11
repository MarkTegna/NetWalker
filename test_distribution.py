#!/usr/bin/env python3
"""
NetWalker Distribution Test

Tests the ZIP distribution package to ensure it meets all requirements.

Author: Mark Oldham
"""

import os
import sys
import zipfile
import subprocess
from pathlib import Path

# Import version information
sys.path.insert(0, str(Path(__file__).parent))
from netwalker.version import __version__, __author__


def test_zip_structure():
    """Test ZIP file structure and contents"""
    print("🔍 Testing ZIP file structure...")
    
    zip_path = Path(f"dist/NetWalker_v{__version__}.zip")
    if not zip_path.exists():
        print(f"❌ ZIP file not found: {zip_path}")
        return False
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            # Test ZIP integrity
            test_result = zip_file.testzip()
            if test_result is not None:
                print(f"❌ ZIP file integrity check failed: {test_result}")
                return False
            print("✅ ZIP file integrity check passed")
            
            # Get all files in ZIP
            zip_contents = [f.filename for f in zip_file.filelist]
            
            # Required files
            required_files = [
                f"NetWalker_v{__version__}/netwalker.exe",
                f"NetWalker_v{__version__}/README.md",
                f"NetWalker_v{__version__}/netwalker.ini",
                f"NetWalker_v{__version__}/secret_creds.ini",
                f"NetWalker_v{__version__}/seed_file.csv",
                f"NetWalker_v{__version__}/_internal/",
            ]
            
            # Check required files
            for required_file in required_files:
                found = any(f.startswith(required_file) for f in zip_contents)
                if found:
                    print(f"✅ Required file/directory found: {required_file}")
                else:
                    print(f"❌ Required file/directory missing: {required_file}")
                    return False
            
            # Check for executable
            exe_files = [f for f in zip_contents if f.endswith('.exe')]
            if exe_files:
                print(f"✅ Executable found: {exe_files[0]}")
            else:
                print("❌ No executable found in ZIP")
                return False
            
            print(f"✅ ZIP contains {len(zip_contents)} total files")
            return True
            
    except Exception as e:
        print(f"❌ Error testing ZIP file: {e}")
        return False


def test_version_numbering():
    """Test version numbering in filename"""
    print("🔍 Testing version numbering...")
    
    zip_path = Path(f"dist/NetWalker_v{__version__}.zip")
    
    # Check filename format
    expected_pattern = f"NetWalker_v{__version__}.zip"
    if zip_path.name == expected_pattern:
        print(f"✅ ZIP filename follows version format: {expected_pattern}")
    else:
        print(f"❌ ZIP filename incorrect. Expected: {expected_pattern}, Got: {zip_path.name}")
        return False
    
    # Check version format (MAJOR.MINOR.PATCH)
    version_parts = __version__.split('.')
    if len(version_parts) == 3 and all(part.isdigit() for part in version_parts):
        print(f"✅ Version format is correct: {__version__}")
    else:
        print(f"❌ Version format incorrect. Expected MAJOR.MINOR.PATCH, Got: {__version__}")
        return False
    
    return True


def test_executable_functionality():
    """Test that the executable works"""
    print("🔍 Testing executable functionality...")
    
    exe_path = Path(f"dist/NetWalker_v{__version__}/netwalker.exe")
    
    if not exe_path.exists():
        print(f"❌ Executable not found: {exe_path}")
        return False
    
    try:
        # Test version command
        result = subprocess.run([str(exe_path), '--version'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            version_output = result.stdout.strip()
            if __version__ in version_output and __author__ in version_output:
                print(f"✅ Executable version test passed: {version_output}")
            else:
                print(f"❌ Version output incorrect: {version_output}")
                return False
        else:
            print(f"❌ Executable version test failed: {result.stderr}")
            return False
        
        # Test help command
        result = subprocess.run([str(exe_path), '--help'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            help_output = result.stdout
            if 'NetWalker' in help_output and 'usage' in help_output.lower():
                print("✅ Executable help test passed")
            else:
                print("❌ Help output doesn't contain expected content")
                return False
        else:
            print(f"❌ Executable help test failed: {result.stderr}")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Executable test timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing executable: {e}")
        return False


def test_configuration_files():
    """Test configuration files are properly included"""
    print("🔍 Testing configuration files...")
    
    base_path = Path(f"dist/NetWalker_v{__version__}")
    
    # Test netwalker.ini
    ini_path = base_path / "netwalker.ini"
    if ini_path.exists():
        with open(ini_path, 'r') as f:
            ini_content = f.read()
            if '[discovery]' in ini_content and '[output]' in ini_content:
                print("✅ netwalker.ini contains required sections")
            else:
                print("❌ netwalker.ini missing required sections")
                return False
    else:
        print("❌ netwalker.ini not found")
        return False
    
    # Test secret_creds.ini
    creds_path = base_path / "secret_creds.ini"
    if creds_path.exists():
        with open(creds_path, 'r') as f:
            creds_content = f.read()
            if '[credentials]' in creds_content:
                print("✅ secret_creds.ini contains credentials section")
            else:
                print("❌ secret_creds.ini missing credentials section")
                return False
    else:
        print("❌ secret_creds.ini not found")
        return False
    
    # Test seed_file.csv
    seed_path = base_path / "seed_file.csv"
    if seed_path.exists():
        with open(seed_path, 'r') as f:
            seed_content = f.read()
            if 'hostname,ip_address' in seed_content:
                print("✅ seed_file.csv contains proper CSV header")
            else:
                print("❌ seed_file.csv missing proper CSV header")
                return False
    else:
        print("❌ seed_file.csv not found")
        return False
    
    return True


def test_documentation():
    """Test documentation files"""
    print("🔍 Testing documentation...")
    
    readme_path = Path(f"dist/NetWalker_v{__version__}/README.md")
    
    if not readme_path.exists():
        print("❌ README.md not found")
        return False
    
    with open(readme_path, 'r') as f:
        readme_content = f.read()
    
    # Check required content
    required_content = [
        f"NetWalker v{__version__}",
        __author__,
        "Installation",
        "Usage",
        "Command Line Options",
        "Files Included",
        "Configuration Files",
        "System Requirements",
        "Network Discovery Features",
        "Troubleshooting"
    ]
    
    for content in required_content:
        if content in readme_content:
            print(f"✅ README contains: {content}")
        else:
            print(f"❌ README missing: {content}")
            return False
    
    return True


def test_file_sizes():
    """Test file sizes are reasonable"""
    print("🔍 Testing file sizes...")
    
    zip_path = Path(f"dist/NetWalker_v{__version__}.zip")
    zip_size = zip_path.stat().st_size
    
    # ZIP should be between 10MB and 50MB (reasonable for a Python executable)
    if 10 * 1024 * 1024 <= zip_size <= 50 * 1024 * 1024:
        print(f"✅ ZIP file size is reasonable: {zip_size:,} bytes ({zip_size / 1024 / 1024:.1f} MB)")
    else:
        print(f"⚠️  ZIP file size may be unusual: {zip_size:,} bytes ({zip_size / 1024 / 1024:.1f} MB)")
    
    return True


def main():
    """Main test process"""
    print(f"NetWalker Distribution Test")
    print(f"Author: {__author__}")
    print(f"Version: {__version__}")
    print("=" * 60)
    
    tests = [
        ("ZIP Structure", test_zip_structure),
        ("Version Numbering", test_version_numbering),
        ("Executable Functionality", test_executable_functionality),
        ("Configuration Files", test_configuration_files),
        ("Documentation", test_documentation),
        ("File Sizes", test_file_sizes),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running test: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📦 Distribution: NetWalker_v{__version__}.zip")
    
    if failed == 0:
        print(f"\n🎉 All tests passed! Distribution is ready for use.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review and fix issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())