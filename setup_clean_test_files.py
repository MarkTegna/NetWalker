#!/usr/bin/env python3
"""
Setup Clean Test Files

Copies clean test files from prodtest_files directory to working directory
for each test run. This ensures we start with clean, real data for all tests.

Author: Mark Oldham
"""

import os
import shutil
from pathlib import Path


def setup_clean_test_files():
    """Copy clean test files from prodtest_files to working directory"""
    
    # Define source and destination files
    files_to_copy = [
        ('prodtest_files/secret_test_creds.ini', 'secret_creds.ini'),
        ('prodtest_files/seed_file.csv', 'seed_file.csv')
    ]
    
    print("Setting up clean test files...")
    print("-" * 40)
    
    for source, destination in files_to_copy:
        source_path = Path(source)
        dest_path = Path(destination)
        
        if source_path.exists():
            # Copy the file
            shutil.copy2(source_path, dest_path)
            print(f"✅ Copied: {source} -> {destination}")
            
            # Show file size
            file_size = dest_path.stat().st_size
            print(f"   Size: {file_size} bytes")
            
        else:
            print(f"❌ Source file not found: {source}")
    
    print("-" * 40)
    print("Clean test files setup completed!")
    
    # Verify the files
    print("\nVerifying copied files:")
    for _, destination in files_to_copy:
        dest_path = Path(destination)
        if dest_path.exists():
            print(f"✅ {destination} - Ready for testing")
        else:
            print(f"❌ {destination} - Missing!")


def show_file_contents():
    """Show contents of the clean test files for verification"""
    
    print("\n" + "="*60)
    print("CLEAN TEST FILE CONTENTS")
    print("="*60)
    
    # Show secret_creds.ini (mask password)
    creds_path = Path('secret_creds.ini')
    if creds_path.exists():
        print("\n📄 secret_creds.ini:")
        print("-" * 30)
        with open(creds_path, 'r') as f:
            content = f.read()
            # Mask the password for security
            lines = content.split('\n')
            for line in lines:
                if line.startswith('password ='):
                    print('password = ********** (masked)')
                else:
                    print(line)
    
    # Show seed_file.csv
    seed_path = Path('seed_file.csv')
    if seed_path.exists():
        print("\n📄 seed_file.csv:")
        print("-" * 30)
        with open(seed_path, 'r') as f:
            content = f.read().strip()
            if content:
                print(content)
            else:
                print("(empty file)")
    
    print("\n" + "="*60)


def main():
    """Main function"""
    print("NetWalker Clean Test Files Setup")
    print("Author: Mark Oldham")
    print("="*60)
    
    # Setup clean test files
    setup_clean_test_files()
    
    # Show file contents for verification
    show_file_contents()
    
    print("\n🎉 Ready for testing with clean, real data!")
    print("\nUsage:")
    print("  python setup_clean_test_files.py  # Run this before each test")
    print("  netwalker.exe --verbose           # Test with file-based seed devices")
    print("  netwalker.exe --seed-devices \"DEVICE:IP\" --verbose  # Test with CLI override")


if __name__ == "__main__":
    main()