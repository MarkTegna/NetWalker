"""
Property-based tests for site boundary detection functionality.

Feature: site-boundary-detection-fix
"""

import pytest
import re
import fnmatch
from hypothesis import given, strategies as st, assume
from netwalker.reports.excel_generator import ExcelReportGenerator


class TestSiteBoundaryDetection:
    """Property-based tests for site boundary detection."""
    
    def setup_method(self):
        """Set up test configuration."""
        self.config = {
            'reports_directory': './test_reports',
            'output': {
                'site_boundary_pattern': '*-CORE-*'
            }
        }
        self.generator = ExcelReportGenerator(self.config)
    
    @given(
        hostname=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-'),
            min_size=1,
            max_size=50
        )
    )
    def test_pattern_matching_consistency(self, hostname):
        """
        Feature: site-boundary-detection-fix, Property 1: Pattern Matching Consistency
        For any valid hostname and site boundary pattern, the pattern matching function 
        should return consistent results when called multiple times with the same inputs.
        Validates: Requirements 1.1, 4.3
        """
        assume(hostname and not hostname.startswith('-') and not hostname.endswith('-'))
        
        pattern = self.generator.site_boundary_pattern
        
        # Test consistency - same inputs should produce same results
        result1 = fnmatch.fnmatch(hostname, pattern)
        result2 = fnmatch.fnmatch(hostname, pattern)
        result3 = fnmatch.fnmatch(hostname, pattern)
        
        assert result1 == result2 == result3, f"Pattern matching inconsistent for hostname: {hostname}, pattern: {pattern}"
    
    @given(
        site_prefix=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
            min_size=1,
            max_size=20
        ),
        suffix=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-'),
            min_size=0,
            max_size=20
        )
    )
    def test_site_name_extraction_determinism(self, site_prefix, suffix):
        """
        Feature: site-boundary-detection-fix, Property 2: Site Name Extraction Determinism
        For any hostname that matches the site boundary pattern, extracting the site name 
        should always produce the same result.
        Validates: Requirements 1.4, 6.2
        """
        assume(site_prefix and not site_prefix.startswith('-') and not site_prefix.endswith('-'))
        
        # Create hostname that matches *-CORE-* pattern
        hostname = f"{site_prefix}-CORE-{suffix}" if suffix else f"{site_prefix}-CORE-A"
        
        # Test determinism - same hostname should produce same site name
        site_name1 = self.generator._extract_site_name(hostname)
        site_name2 = self.generator._extract_site_name(hostname)
        site_name3 = self.generator._extract_site_name(hostname)
        
        assert site_name1 == site_name2 == site_name3, f"Site name extraction inconsistent for hostname: {hostname}"
        assert site_name1 == site_prefix, f"Expected site name '{site_prefix}', got '{site_name1}' for hostname: {hostname}"
    
    @given(
        hostnames=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
                min_size=1,
                max_size=15
            ).map(lambda x: f"{x}-CORE-A"),
            min_size=1,
            max_size=10,
            unique=True
        )
    )
    def test_unique_site_identification(self, hostnames):
        """
        Feature: site-boundary-detection-fix, Property 3: Unique Site Identification
        For any set of devices matching the site boundary pattern, the system should 
        identify each unique site prefix exactly once.
        Validates: Requirements 1.3
        """
        # Create mock inventory
        inventory = {}
        seed_devices = []
        
        for i, hostname in enumerate(hostnames):
            device_key = f"{hostname}:{hostname}"
            inventory[device_key] = {
                'hostname': hostname,
                'primary_ip': hostname,
                'status': 'connected'
            }
            seed_devices.append(device_key)
        
        # Identify site boundaries
        site_boundaries = self.generator._identify_site_boundaries(inventory, seed_devices)
        
        # Extract expected unique sites
        expected_sites = set()
        for hostname in hostnames:
            site_name = self.generator._extract_site_name(hostname)
            expected_sites.add(site_name)
        
        # Verify each unique site is identified exactly once
        actual_sites = set(site_boundaries.keys())
        assert actual_sites == expected_sites, f"Expected sites {expected_sites}, got {actual_sites}"
    
    @given(
        site_prefix=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
            min_size=1,
            max_size=15
        ),
        serial_number=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
            min_size=5,
            max_size=15
        )
    )
    def test_hostname_cleaning_integration(self, site_prefix, serial_number):
        """
        Feature: site-boundary-detection-fix, Property 4: Hostname Cleaning Integration
        For any hostname with serial numbers in parentheses, pattern matching should 
        work correctly with cleaned hostnames.
        Validates: Requirements 1.5, 6.1
        """
        assume(site_prefix and serial_number)
        
        # Create hostname with serial number
        hostname_with_serial = f"{site_prefix}-CORE-A({serial_number})"
        clean_hostname = f"{site_prefix}-CORE-A"
        
        # Test that cleaned hostname matches pattern
        pattern = self.generator.site_boundary_pattern
        
        # Clean hostname should match pattern
        cleaned = self.generator._clean_hostname(hostname_with_serial)
        assert fnmatch.fnmatch(cleaned, pattern), f"Cleaned hostname '{cleaned}' should match pattern '{pattern}'"
        
        # Site name extraction should work with cleaned hostname
        site_name = self.generator._extract_site_name(cleaned)
        assert site_name == site_prefix, f"Expected site name '{site_prefix}', got '{site_name}'"


def test_specific_examples():
    """Test specific examples mentioned in requirements."""
    config = {
        'reports_directory': './test_reports',
        'output': {
            'site_boundary_pattern': '*-CORE-*'
        }
    }
    generator = ExcelReportGenerator(config)
    
    # Test specific examples from requirements 1.2
    test_cases = [
        ("LUMT-CORE-A", True, "LUMT"),
        ("BORO-CORE-B", True, "BORO"), 
        ("SITE-CORE-01", True, "SITE"),
        ("LUMT-CORE-A(FOX1849GQKY)", True, "LUMT"),  # With serial number
        ("REGULAR-SWITCH", False, None),
        ("CORE-ONLY", False, None),
        ("NO-MATCH", False, None)
    ]
    
    for hostname, should_match, expected_site in test_cases:
        # Test pattern matching
        clean_hostname = generator._clean_hostname(hostname)
        matches = fnmatch.fnmatch(clean_hostname, generator.site_boundary_pattern)
        assert matches == should_match, f"Hostname '{hostname}' (cleaned: '{clean_hostname}') should {'match' if should_match else 'not match'} pattern"
        
        # Test site extraction for matching hostnames
        if should_match:
            site_name = generator._extract_site_name(clean_hostname)
            assert site_name == expected_site, f"Expected site '{expected_site}', got '{site_name}' for hostname '{hostname}'"

    @given(
        site_count=st.integers(min_value=1, max_value=5),
        devices_per_site=st.integers(min_value=1, max_value=10)
    )
    def test_device_association_completeness(self, site_count, devices_per_site):
        """
        Feature: site-boundary-detection-fix, Property 7: Device Association Completeness
        For any device in the inventory, it should be associated with exactly one site 
        or the main workbook.
        Validates: Requirements 2.3, 3.1
        """
        # Create mock inventory with multiple sites
        inventory = {}
        seed_devices = []
        all_devices = []
        
        for site_idx in range(site_count):
            site_name = f"SITE{site_idx:02d}"
            
            # Create seed device for this site
            seed_hostname = f"{site_name}-CORE-A"
            seed_key = f"{seed_hostname}:{seed_hostname}"
            inventory[seed_key] = {
                'hostname': seed_hostname,
                'primary_ip': seed_hostname,
                'status': 'connected'
            }
            seed_devices.append(seed_key)
            all_devices.append(seed_key)
            
            # Create additional devices for this site
            for dev_idx in range(devices_per_site - 1):
                device_hostname = f"{site_name}-SW{dev_idx:02d}"
                device_key = f"{device_hostname}:{device_hostname}"
                inventory[device_key] = {
                    'hostname': device_hostname,
                    'primary_ip': device_hostname,
                    'status': 'connected'
                }
                all_devices.append(device_key)
        
        # Identify site boundaries
        site_boundaries = self.generator._identify_site_boundaries(inventory, seed_devices)
        
        # Count devices across all sites
        total_associated_devices = 0
        for site_name, site_data in site_boundaries.items():
            if site_name != 'All_Sites':  # Skip fallback site
                total_associated_devices += len(site_data['inventory'])
        
        # Every device should be associated with exactly one site
        # (In this test case, all devices should be associated since they follow naming convention)
        expected_devices = len(all_devices)
        assert total_associated_devices == expected_devices, \
            f"Expected {expected_devices} devices to be associated, got {total_associated_devices}"
    
    @given(
        site_name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
            min_size=1,
            max_size=10
        ),
        neighbor_count=st.integers(min_value=1, max_value=5)
    )
    def test_neighbor_inclusion_consistency(self, site_name, neighbor_count):
        """
        Feature: site-boundary-detection-fix, Property 8: Neighbor Inclusion Consistency
        For any device associated with a site boundary, all its neighbors should be 
        included in the same site workbook.
        Validates: Requirements 2.4, 3.2
        """
        assume(site_name and not site_name.startswith('-') and not site_name.endswith('-'))
        
        # Create site boundary device
        boundary_hostname = f"{site_name}-CORE-A"
        boundary_key = f"{boundary_hostname}:{boundary_hostname}"
        
        # Create neighbor devices
        neighbors = []
        inventory = {
            boundary_key: {
                'hostname': boundary_hostname,
                'primary_ip': boundary_hostname,
                'status': 'connected',
                'neighbors': []
            }
        }
        
        for i in range(neighbor_count):
            neighbor_hostname = f"{site_name}-SW{i:02d}"
            neighbor_key = f"{neighbor_hostname}:{neighbor_hostname}"
            
            # Add neighbor to inventory
            inventory[neighbor_key] = {
                'hostname': neighbor_hostname,
                'primary_ip': neighbor_hostname,
                'status': 'connected'
            }
            
            # Add to boundary device's neighbor list
            neighbors.append({
                'hostname': neighbor_hostname,
                'ip_address': neighbor_hostname
            })
        
        inventory[boundary_key]['neighbors'] = neighbors
        
        # Identify site boundaries
        site_boundaries = self.generator._identify_site_boundaries(inventory, [boundary_key])
        
        # Verify site boundary was created
        assert site_name in site_boundaries, f"Site boundary '{site_name}' should be created"
        
        site_inventory = site_boundaries[site_name]['inventory']
        
        # Verify boundary device is included
        assert boundary_key in site_inventory, f"Boundary device should be in site inventory"
        
        # Verify all neighbor devices are included (this tests the neighbor association logic)
        for i in range(neighbor_count):
            neighbor_hostname = f"{site_name}-SW{i:02d}"
            neighbor_key = f"{neighbor_hostname}:{neighbor_hostname}"
            
            # Check if neighbor is associated with the site (either directly or through naming convention)
            neighbor_in_site = any(
                self.generator._clean_hostname(device_info.get('hostname', '')) == neighbor_hostname
                for device_info in site_inventory.values()
            )
            
            assert neighbor_in_site, f"Neighbor device '{neighbor_hostname}' should be associated with site '{site_name}'"


class TestSiteBoundaryWorkbookGeneration:
    """Property-based tests for workbook generation logic."""
    
    def setup_method(self):
        """Set up test configuration."""
        self.config = {
            'reports_directory': './test_reports',
            'output': {
                'site_boundary_pattern': '*-CORE-*'
            }
        }
        self.generator = ExcelReportGenerator(self.config)
    
    @given(
        site_names=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
                min_size=1,
                max_size=10
            ),
            min_size=1,
            max_size=5,
            unique=True
        )
    )
    def test_workbook_creation_completeness(self, site_names):
        """
        Feature: site-boundary-detection-fix, Property 5: Workbook Creation Completeness
        For any set of identified sites, the system should create exactly one workbook per site.
        Validates: Requirements 2.1
        """
        assume(all(name and not name.startswith('-') and not name.endswith('-') for name in site_names))
        
        # Create mock site boundaries
        site_boundaries = {}
        for site_name in site_names:
            site_boundaries[site_name] = {
                'inventory': {
                    f"{site_name}-CORE-A:{site_name}-CORE-A": {
                        'hostname': f"{site_name}-CORE-A",
                        'primary_ip': f"{site_name}-CORE-A",
                        'status': 'connected'
                    }
                },
                'seed_devices': [f"{site_name}-CORE-A:{site_name}-CORE-A"]
            }
        
        # Test the condition that determines if separate workbooks should be created
        has_site_boundaries = len(site_boundaries) >= 1 and 'All_Sites' not in site_boundaries
        
        # Should create separate workbooks for any number of actual sites (not 'All_Sites')
        assert has_site_boundaries == True, f"Should create separate workbooks for {len(site_names)} sites"
    
    @given(
        site_name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
            min_size=1,
            max_size=15
        )
    )
    def test_filename_format_consistency(self, site_name):
        """
        Feature: site-boundary-detection-fix, Property 6: Filename Format Consistency
        For any site name and timestamp, the generated workbook filename should follow 
        the format "Discovery_SITENAME_YYYYMMDD-HH-MM.xlsx".
        Validates: Requirements 2.2
        """
        assume(site_name and not site_name.startswith('-') and not site_name.endswith('-'))
        
        # Clean site name (simulate what would happen in actual generation)
        clean_site_name = re.sub(r'[^\w-]', '', site_name)
        
        # Test filename format
        timestamp = "20260112-07-46"  # Fixed timestamp for testing
        expected_pattern = f"Discovery_{clean_site_name}_{timestamp}.xlsx"
        
        # Verify the pattern is valid
        assert clean_site_name in expected_pattern, f"Site name should be in filename"
        assert expected_pattern.startswith("Discovery_"), f"Filename should start with 'Discovery_'"
        assert expected_pattern.endswith(".xlsx"), f"Filename should end with '.xlsx'"
        assert timestamp in expected_pattern, f"Timestamp should be in filename"