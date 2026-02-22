#!/usr/bin/env python3
"""
Update test mocks for upsert_device to return tuples
"""

import re
from pathlib import Path

def update_test_file(filepath):
    """Update a test file to have upsert_device mocks return tuples"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern: db_manager.upsert_device = Mock(return_value=1)
    # Replace with: db_manager.upsert_device = Mock(return_value=(1, True))
    content = re.sub(
        r'db_manager\.upsert_device = Mock\(return_value=1\)',
        r'db_manager.upsert_device = Mock(return_value=(1, True))',
        content
    )
    
    # Pattern: db_manager.upsert_device = Mock(return_value=device_id)
    # Replace with: db_manager.upsert_device = Mock(return_value=(device_id, True))
    content = re.sub(
        r'db_manager\.upsert_device = Mock\(return_value=device_id\)',
        r'db_manager.upsert_device = Mock(return_value=(device_id, True))',
        content
    )
    
    # Pattern: db_manager.upsert_device = Mock(return_value=42)
    # Replace with: db_manager.upsert_device = Mock(return_value=(42, True))
    content = re.sub(
        r'db_manager\.upsert_device = Mock\(return_value=42\)',
        r'db_manager.upsert_device = Mock(return_value=(42, True))',
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

print("\nMock updates completed successfully!")
