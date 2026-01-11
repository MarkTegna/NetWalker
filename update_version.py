#!/usr/bin/env python3
"""
Manual Version Update Script for NetWalker

Allows manual setting of version numbers for major releases or specific version requirements.
Validates version format and updates compile date.

Author: Mark Oldham
"""

import sys
import re
from pathlib import Path
from datetime import datetime


def read_version_file():
    """Read the current version file"""
    version_file = Path("netwalker/version.py")
    
    if not version_file.exists():
        raise FileNotFoundError("Version file not found: netwalker/version.py")
    
    with open(version_file, 'r') as f:
        content = f.read()
    
    return content


def validate_version_format(version_str):
    """Validate version format (MAJOR.MINOR.PATCH)"""
    if not re.match(r'^\d+\.\d+\.\d+$', version_str):
        raise ValueError(f"Invalid version format: {version_str}. Expected MAJOR.MINOR.PATCH (e.g., 1.2.3)")
    
    major, minor, patch = map(int, version_str.split('.'))
    
    if major < 0 or minor < 0 or patch < 0:
        raise ValueError("Version numbers cannot be negative")
    
    return major, minor, patch


def get_current_version(content):
    """Get current version from file content"""
    version_match = re.search(r'__version__ = "([^"]+)"', content)
    if not version_match:
        raise ValueError("Could not find version in file")
    
    return version_match.group(1)


def update_version_file(content, old_version, new_version):
    """Update version file with new version and compile date"""
    compile_date = datetime.now().strftime("%Y-%m-%d")
    
    # Update version
    new_content = content.replace(
        f'__version__ = "{old_version}"',
        f'__version__ = "{new_version}"'
    )
    
    # Update compile date
    new_content = re.sub(
        r'__compile_date__ = "[^"]*"',
        f'__compile_date__ = "{compile_date}"',
        new_content
    )
    
    return new_content


def write_version_file(content):
    """Write updated content to version file"""
    version_file = Path("netwalker/version.py")
    
    with open(version_file, 'w') as f:
        f.write(content)


def compare_versions(old_version, new_version):
    """Compare versions and provide guidance"""
    old_major, old_minor, old_patch = map(int, old_version.split('.'))
    new_major, new_minor, new_patch = map(int, new_version.split('.'))
    
    if new_major > old_major:
        return "MAJOR version increment - incompatible API changes"
    elif new_major < old_major:
        return "MAJOR version downgrade - unusual, please confirm"
    elif new_minor > old_minor:
        return "MINOR version increment - new features, backwards compatible"
    elif new_minor < old_minor:
        return "MINOR version downgrade - unusual, please confirm"
    elif new_patch > old_patch:
        return "PATCH version increment - bug fixes, backwards compatible"
    elif new_patch < old_patch:
        return "PATCH version downgrade - unusual, please confirm"
    else:
        return "No version change"


def main():
    """Main version update process"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Manually update NetWalker version number",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_version.py 1.0.0         # Set version to 1.0.0
  python update_version.py 2.1.5         # Set version to 2.1.5
  python update_version.py --show         # Show current version
        """
    )
    
    parser.add_argument('version', nargs='?', help='New version number (MAJOR.MINOR.PATCH)')
    parser.add_argument('--show', action='store_true', help='Show current version and exit')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    parser.add_argument('--force', action='store_true', help='Force version change without confirmation')
    
    args = parser.parse_args()
    
    try:
        # Read current version
        content = read_version_file()
        old_version = get_current_version(content)
        
        if args.show:
            print(f"Current version: {old_version}")
            return 0
        
        if not args.version:
            print(f"Current version: {old_version}")
            print("Please specify a new version number or use --show to display current version")
            return 1
        
        # Validate new version
        new_version = args.version.strip()
        validate_version_format(new_version)
        
        # Compare versions
        change_type = compare_versions(old_version, new_version)
        
        print(f"Current version: {old_version}")
        print(f"New version: {new_version}")
        print(f"Change type: {change_type}")
        
        if old_version == new_version:
            print("No version change needed")
            return 0
        
        # Confirm change if not forced
        if not args.force and not args.dry_run:
            response = input("Proceed with version change? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("Version change cancelled")
                return 0
        
        if args.dry_run:
            print("Dry run - no changes made")
            return 0
        
        # Update version file
        new_content = update_version_file(content, old_version, new_version)
        write_version_file(new_content)
        
        print(f"Version updated successfully: {old_version} -> {new_version}")
        
        # Provide guidance based on change type
        if "MAJOR" in change_type:
            print("\nMAJOR version change detected:")
            print("- Consider updating documentation")
            print("- Update GitHub when ready")
            print("- Create distribution package")
        elif "MINOR" in change_type:
            print("\nMINOR version change detected:")
            print("- Update GitHub when feature is complete")
            print("- Create distribution package")
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())