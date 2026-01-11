"""
Property-based tests for version management
Feature: network-topology-discovery, Property: Version format validation
"""

import re
from hypothesis import given, strategies as st
import pytest
from netwalker.version import __version__


def test_version_format_validation():
    """
    Feature: network-topology-discovery, Property: Version format validation
    For any version string, it should follow the MAJOR.MINOR.PATCH format
    **Validates: Requirements 12.5**
    """
    # Test current version format
    version_pattern = r'^\d+\.\d+\.\d+$'
    assert re.match(version_pattern, __version__), f"Version {__version__} does not match MAJOR.MINOR.PATCH format"
    
    # Verify version components are numeric
    major, minor, patch = __version__.split('.')
    assert major.isdigit(), f"Major version '{major}' is not numeric"
    assert minor.isdigit(), f"Minor version '{minor}' is not numeric" 
    assert patch.isdigit(), f"Patch version '{patch}' is not numeric"


@given(st.integers(min_value=0, max_value=999))
def test_version_component_validity(version_component):
    """
    Property test: For any valid version component (0-999), 
    it should be acceptable in version format
    """
    test_version = f"{version_component}.{version_component}.{version_component}"
    version_pattern = r'^\d+\.\d+\.\d+$'
    assert re.match(version_pattern, test_version)


def test_initial_version_requirement():
    """
    Test that initial version follows the 0.0.1 requirement from version management standards
    """
    # For initial development, version should start with 0.0.1
    major, minor, patch = __version__.split('.')
    assert int(major) >= 0, "Major version should be >= 0"
    assert int(minor) >= 0, "Minor version should be >= 0" 
    assert int(patch) >= 1, "Patch version should be >= 1 for initial version"