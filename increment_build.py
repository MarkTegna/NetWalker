#!/usr/bin/env python3
"""
Version Increment Script for NetWalker

Increments version numbers according to the new version management standards:
- Automatic builds: Add/increment letter suffix (0.3.1 -> 0.3.1a -> 0.3.1b)
- User builds: Remove letter suffix and increment PATCH (0.3.1b -> 0.3.2)

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
    
    # Parse version with optional letter suffix (MAJOR.MINOR.PATCH[LETTER])
    version_pattern = r'^(\d+)\.(\d+)\.(\d+)([a-z]?)$'
    match = re.match(version_pattern, version_str)
    
    if not match:
        raise ValueError(f"Invalid version format: {version_str}. Expected MAJOR.MINOR.PATCH[LETTER]")
    
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3))
    letter = match.group(4) or ''
    
    return major, minor, patch, letter


def increment_version_automatic(major, minor, patch, letter):
    """Increment version for automatic build (add/increment letter suffix)"""
    if not letter:
        # No letter suffix, add 'a'
        return major, minor, patch, 'a'
    else:
        # Increment letter suffix
        if letter == 'z':
            # Letter overflow: increment patch and reset to 'a'
            return major, minor, patch + 1, 'a'
        else:
            # Increment letter
            next_letter = chr(ord(letter) + 1)
            return major, minor, patch, next_letter


def increment_version_user(major, minor, patch, letter):
    """Increment version for user build (remove letter suffix and increment PATCH)"""
    if letter:
        # Remove letter suffix and increment patch
        return major, minor, patch + 1, ''
    else:
        # No letter suffix, just increment patch
        return major, minor, patch + 1, ''


def increment_version_manual(major, minor, patch, letter, increment_type):
    """Increment version manually (MAJOR or MINOR)"""
    if increment_type == 'major':
        return major + 1, 0, 0, ''
    elif increment_type == 'minor':
        return major, minor + 1, 0, ''
    else:
        raise ValueError(f"Invalid manual increment type: {increment_type}")


def format_version(major, minor, patch, letter):
    """Format version string"""
    version = f"{major}.{minor}.{patch}"
    if letter:
        version += letter
    return version


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
        description="Increment NetWalker version number according to version management standards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Build Types:
  --auto      Automatic build (add/increment letter suffix) - DEFAULT
  --user      User-requested build (remove letter, increment PATCH)
  --major     Manual MAJOR version increment
  --minor     Manual MINOR version increment

Examples:
  python increment_build.py              # Automatic build: 0.3.1 -> 0.3.1a
  python increment_build.py --auto       # Automatic build: 0.3.1a -> 0.3.1b
  python increment_build.py --user       # User build: 0.3.1b -> 0.3.2
  python increment_build.py --major      # Manual: 0.3.1b -> 1.0.0
  python increment_build.py --minor      # Manual: 0.3.1b -> 0.4.0

Version Management Standards:
- Automatic builds get letter suffixes for development/troubleshooting
- User builds remove letters and increment PATCH for official releases
- Manual increments are for MAJOR/MINOR version changes
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--auto', action='store_true', help='Automatic build (add/increment letter suffix) - DEFAULT')
    group.add_argument('--user', action='store_true', help='User-requested build (remove letter, increment PATCH)')
    group.add_argument('--major', action='store_true', help='Manual MAJOR version increment')
    group.add_argument('--minor', action='store_true', help='Manual MINOR version increment')
    
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    
    args = parser.parse_args()
    
    # Determine build type (default to automatic)
    if args.user:
        build_type = 'user'
    elif args.major:
        build_type = 'major'
    elif args.minor:
        build_type = 'minor'
    else:
        build_type = 'auto'  # Default
    
    try:
        # Read current version
        content = read_version_file()
        major, minor, patch, letter = parse_version(content)
        old_version = format_version(major, minor, patch, letter)
        
        # Calculate new version based on build type
        if build_type == 'auto':
            new_major, new_minor, new_patch, new_letter = increment_version_automatic(major, minor, patch, letter)
            description = "Automatic build (development/troubleshooting)"
        elif build_type == 'user':
            new_major, new_minor, new_patch, new_letter = increment_version_user(major, minor, patch, letter)
            description = "User-requested build (official release)"
        else:
            new_major, new_minor, new_patch, new_letter = increment_version_manual(major, minor, patch, letter, build_type)
            description = f"Manual {build_type.upper()} version increment"
        
        new_version = format_version(new_major, new_minor, new_patch, new_letter)
        
        print(f"Current version: {old_version}")
        print(f"New version: {new_version}")
        print(f"Build type: {build_type.upper()}")
        print(f"Description: {description}")
        
        if build_type == 'auto' and new_letter:
            print(f"Note: Letter suffix '{new_letter}' added for automatic build - no distribution files will be created")
        elif build_type == 'user' and not new_letter:
            print("Note: Letter suffix removed for user build - distribution files will be created")
        
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