#!/usr/bin/env python3
"""
Update test files to handle new tuple return from process_device_discovery
"""

import re
from pathlib import Path

def update_test_file(filepath):
    """Update a test file to handle tuple return"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern 1: result = db_manager.process_device_discovery(device_info)
    # Replace with: success, is_new = db_manager.process_device_discovery(device_info)
    content = re.sub(
        r'(\s+)result = db_manager\.process_device_discovery\(device_info\)',
        r'\1success, is_new = db_manager.process_device_discovery(device_info)',
        content
    )
    
    # Pattern 2: assert result is True
    # Replace with: assert success is True
    content = re.sub(
        r'assert result is True',
        r'assert success is True',
        content
    )
    
    # Pattern 3: result1 = db_manager.process_device_discovery
    # Replace with: success1, is_new1 = db_manager.process_device_discovery
    content = re.sub(
        r'(\s+)result1 = db_manager\.process_device_discovery\(device_info1\)',
        r'\1success1, is_new1 = db_manager.process_device_discovery(device_info1)',
        content
    )
    
    # Pattern 4: result2 = db_manager.process_device_discovery
    # Replace with: success2, is_new2 = db_manager.process_device_discovery
    content = re.sub(
        r'(\s+)result2 = db_manager\.process_device_discovery\(device_info2\)',
        r'\1success2, is_new2 = db_manager.process_device_discovery(device_info2)',
        content
    )
    
    # Pattern 5: assert result1 is True
    content = re.sub(
        r'assert result1 is True',
        r'assert success1 is True',
        content
    )
    
    # Pattern 6: assert result2 is True
    content = re.sub(
        r'assert result2 is True',
        r'assert success2 is True',
        content
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Updated: {filepath}")

# Update test files
test_files = [
    'tests/unit/test_database_primary_ip.py',
    'tests/property/test_database_primary_ip_properties.py',
    'tests/integration/test_database_connection_manager_integration.py'
]

for test_file in test_files:
    filepath = Path(test_file)
    if filepath.exists():
        update_test_file(filepath)
    else:
        print(f"Skipped (not found): {test_file}")

print("\nTest files updated successfully!")
