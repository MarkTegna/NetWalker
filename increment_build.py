#!/usr/bin/env python3
"""
Version Increment Script for NetWalker

Increments the patch version number before build according to version management standards.
Can also be used to manually increment MAJOR or MINOR versions.

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


def parse_version(content):
    """Parse version from file content"""
    version_match = re.search(r'__version__ = "([^"]+)"', content)
    if not version_match:
        raise ValueError("Could not find version in file")
    
    version_str = version_match.group(1)
    
    # Validate version format (MAJOR.MINOR.PATCH)
    if not re.match(r'^\d+\.\d+\.\d+$', version_str):
        raise ValueError(f"Invalid version format: {version_str}. Expected MAJOR.MINOR.PATCH")
    
    major, minor, patch = map(int, version_str.split('.'))
    return major, minor, patch


def increment_version(major, minor, patch, increment_type='patch'):
    """Increment version based on type"""
    if increment_type == 'major':
        return major + 1, 0, 0
    elif increment_type == 'minor':
        return major, minor + 1, 0
    elif increment_type == 'patch':
        return major, minor, patch + 1
    else:
        raise ValueError(f"Invalid increment type: {increment_type}")


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


def main():
    """Main version increment process"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Increment NetWalker version number",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python increment_build.py              # Increment patch version (default)
  python increment_build.py --major      # Increment major version
  python increment_build.py --minor      # Increment minor version
  python increment_build.py --patch      # Increment patch version
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--major', action='store_true', help='Increment major version')
    group.add_argument('--minor', action='store_true', help='Increment minor version')
    group.add_argument('--patch', action='store_true', help='Increment patch version (default)')
    
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    
    args = parser.parse_args()
    
    # Determine increment type
    if args.major:
        increment_type = 'major'
    elif args.minor:
        increment_type = 'minor'
    else:
        increment_type = 'patch'  # Default
    
    try:
        # Read current version
        content = read_version_file()
        major, minor, patch = parse_version(content)
        old_version = f"{major}.{minor}.{patch}"
        
        # Calculate new version
        new_major, new_minor, new_patch = increment_version(major, minor, patch, increment_type)
        new_version = f"{new_major}.{new_minor}.{new_patch}"
        
        print(f"Current version: {old_version}")
        print(f"New version: {new_version}")
        print(f"Increment type: {increment_type.upper()}")
        
        if args.dry_run:
            print("Dry run - no changes made")
            return 0
        
        # Update version file
        new_content = update_version_file(content, old_version, new_version)
        write_version_file(new_content)
        
        print(f"Version updated successfully: {old_version} -> {new_version}")
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())