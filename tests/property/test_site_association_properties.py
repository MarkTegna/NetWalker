"""
Property-based tests for Site Association Validation

Tests universal properties of site association and validation functionality.
"""

import pytest
from hypothesis import given, strategies as st, assume
from unittest.mock import Mock
from datetime import datetime

from netwalker.discovery.site_association_validator import SiteAssociationValidator


class TestSiteAssociationValidatorProperties:
    """Property-based tests for SiteAssociationValidator functionality"""
    
    @given(
        site_boundary_pattern=st.sampled_from(['*-CORE-*', '*-RTR-*', '*-SW-*', '*-MDF-*']),
        hostnames=st.lists(
            st.text(min_size=3, max_size=20, alphabet=st.characters(min_codepoint=65, max_codepoint=90)),  # A-Z only
            min_size=1, max_size=15, unique=True
        )
    )
    def test_site_boundary_pattern_consistency_property(self, site_boundary_pattern, hostnames):
        """
        Property 10: Site Boundary Pattern Consistency
        
        For any configured site boundary pattern, devices matching the pattern should be 
        consistently identified and associated with the correct site across multiple calls.
        
        **Feature: site-specific-device-collection-reporting, Property 10: Site Boundary Pattern Consistency**
        **Validates: Requirements 6.1, 10.1**
        """
        validator = SiteAssociationValidator(site_boundary_pattern)
        
        # Create test hostnames that match the pattern
        pattern_keyword = site_boundary_pattern.replace('*', '').replace('-', '')  # Extract CORE, RTR, etc.
        matching_hostnames = []
        non_matching_hostnames = []
        
        for hostname in hostnames:
            # Create matching hostname by inserting pattern keyword
            if len(hostname) >= 4:
                site_part = hostname[:4].upper()
                matching_hostname = f"{site_part}-{pattern_keyword}-01"
                matching_hostnames.append(matching_hostname)
                
                # Create non-matching hostname
                non_matching_hostname = f"{site_part}-OTHER-01"
                non_matching_hostnames.append(non_matching_hostname)
        
        assume(len(matching_hostnames) > 0)
        
        # Test consistency for matching hostnames
        for hostname in matching_hostnames:
            # Call site determination multiple times
            site1 = validator.determine_device_site(hostname, "192.168.1.1")
            site2 = validator.determine_device_site(hostname, "192.168.1.1")
            site3 = validator.determine_device_site(hostname, "192.168.1.1")
            
            # Property: Same inputs should produce same results
            assert site1 == site2 == site3, \
                f"Inconsistent site determination for {hostname}: {site1}, {site2}, {site3}"
            
            # Property: Matching hostnames should not be assigned to GLOBAL
            assert site1 != 'GLOBAL', \
                f"Hostname {hostname} matching pattern {site_boundary_pattern} should not be assigned to GLOBAL"
        
        # Test consistency for non-matching hostnames
        for hostname in non_matching_hostnames:
            site1 = validator.determine_device_site(hostname, "192.168.1.2")
            site2 = validator.determine_device_site(hostname, "192.168.1.2")
            
            # Property: Same inputs should produce same results
            assert site1 == site2, \
                f"Inconsistent site determination for non-matching {hostname}: {site1}, {site2}"
    
    @given(
        site_names=st.lists(
            st.text(min_size=2, max_size=8, alphabet=st.characters(min_codepoint=65, max_codepoint=90)),  # A-Z only
            min_size=2, max_size=5, unique=True
        ),
        device_types=st.sampled_from(['CORE', 'SW', 'RTR', 'MDF', 'IDF'])
    )
    def test_site_association_determinism_property(self, site_names, device_types):
        """
        Property: Site Association Determinism
        
        For any device hostname and site boundary pattern, the site association 
        should be deterministic and consistent across multiple calls.
        
        **Feature: site-specific-device-collection-reporting, Property: Site Association Determinism**
        **Validates: Requirements 6.1, 6.2**
        """
        validator = SiteAssociationValidator(f'*-{device_types}-*')
        
        # Create devices for each site
        test_devices = []
        for site_name in site_names:
            hostname = f"{site_name.upper()}-{device_types}-01"
            ip_address = f"192.168.{len(test_devices) + 1}.1"
            test_devices.append((hostname, ip_address, site_name.upper()))
        
        # Test determinism
        for hostname, ip_address, expected_site in test_devices:
            results = []
            
            # Call site determination multiple times
            for _ in range(5):
                site = validator.determine_device_site(hostname, ip_address)
                results.append(site)
            
            # Property: All results should be identical
            assert all(r == results[0] for r in results), \
                f"Non-deterministic site determination for {hostname}: {results}"
            
            # Property: Result should match expected site
            assert results[0] == expected_site, \
                f"Site determination mismatch for {hostname}: expected {expected_site}, got {results[0]}"
    
    @given(
        site_boundary_pattern=st.sampled_from(['*-CORE-*', '*-RTR-*', '*-SW-*']),
        site_count=st.integers(min_value=2, max_value=5),
        devices_per_site=st.integers(min_value=2, max_value=8)
    )
    def test_multi_site_isolation_property(self, site_boundary_pattern, site_count, devices_per_site):
        """
        Property: Multi-Site Isolation
        
        For any set of devices belonging to different sites, each device should be 
        consistently associated with exactly one site.
        
        **Feature: site-specific-device-collection-reporting, Property: Multi-Site Isolation**
        **Validates: Requirements 6.2, 6.3**
        """
        validator = SiteAssociationValidator(site_boundary_pattern)
        
        # Extract device type from pattern
        device_type = site_boundary_pattern.replace('*', '').replace('-', '')
        
        # Create devices for multiple sites
        all_devices = []
        site_device_mapping = {}
        
        for site_idx in range(site_count):
            site_name = f"SITE{site_idx + 1}"
            site_devices = []
            
            for device_idx in range(devices_per_site):
                hostname = f"{site_name}-{device_type}-{device_idx + 1:02d}"
                ip_address = f"192.168.{site_idx + 1}.{device_idx + 1}"
                device_info = {
                    'hostname': hostname,
                    'ip_address': ip_address
                }
                
                all_devices.append((hostname, ip_address, site_name))
                site_devices.append(device_info)
            
            site_device_mapping[site_name] = site_devices
        
        # Test site isolation
        for hostname, ip_address, expected_site in all_devices:
            determined_site = validator.determine_device_site(hostname, ip_address)
            
            # Property: Device should be assigned to expected site
            assert determined_site == expected_site, \
                f"Device {hostname} assigned to {determined_site}, expected {expected_site}"
            
            # Property: Device should validate as member of its site
            device_info = {'hostname': hostname, 'ip_address': ip_address}
            assert validator.validate_site_membership(device_info, expected_site), \
                f"Device {hostname} should validate as member of site {expected_site}"
            
            # Property: Device should NOT validate as member of other sites
            for other_site in site_device_mapping.keys():
                if other_site != expected_site:
                    assert not validator.validate_site_membership(device_info, other_site), \
                        f"Device {hostname} should NOT validate as member of site {other_site}"
    
    @given(
        hostnames_with_serials=st.lists(
            st.tuples(
                st.text(min_size=4, max_size=12, alphabet=st.characters(min_codepoint=65, max_codepoint=90)),  # A-Z only
                st.text(min_size=6, max_size=12, alphabet=st.characters(min_codepoint=48, max_codepoint=90))  # 0-9, A-Z
            ),
            min_size=1, max_size=10, unique=True
        )
    )
    def test_hostname_cleaning_consistency_property(self, hostnames_with_serials):
        """
        Property: Hostname Cleaning Consistency
        
        For any hostname with serial numbers or special characters, the cleaning 
        process should be consistent and preserve the core hostname for site matching.
        
        **Feature: site-specific-device-collection-reporting, Property: Hostname Cleaning Consistency**
        **Validates: Requirements 6.1, 6.4**
        """
        validator = SiteAssociationValidator('*-CORE-*')
        
        for base_hostname, serial in hostnames_with_serials:
            # Create various formats of the same hostname
            hostname_variants = [
                f"{base_hostname}-CORE-01",  # Clean format
                f"{base_hostname}-CORE-01({serial})",  # With serial in parentheses
                f"{base_hostname.lower()}-core-01",  # Lowercase
                f"{base_hostname}-CORE-01.domain.com",  # FQDN
                f"  {base_hostname}-CORE-01  ",  # With whitespace
            ]
            
            # Test consistency across variants
            sites = []
            for variant in hostname_variants:
                site = validator.determine_device_site(variant, "192.168.1.1")
                sites.append(site)
            
            # Property: All variants should produce the same site assignment
            assert all(s == sites[0] for s in sites), \
                f"Inconsistent site assignment for hostname variants of {base_hostname}: {list(zip(hostname_variants, sites))}"
            
            # Property: Site should be based on the base hostname
            expected_site = base_hostname.upper()
            assert sites[0] == expected_site, \
                f"Site assignment {sites[0]} should match base hostname {expected_site}"
    
    @given(
        device_info=st.fixed_dictionaries({
            'hostname': st.text(min_size=5, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
            'ip_address': st.ip_addresses(v=4).map(str)
        }),
        candidate_sites=st.lists(
            st.text(min_size=2, max_size=8, alphabet=st.characters(min_codepoint=65, max_codepoint=90)),  # A-Z only
            min_size=2, max_size=5, unique=True
        )
    )
    def test_conflict_resolution_consistency_property(self, device_info, candidate_sites):
        """
        Property: Conflict Resolution Consistency
        
        For any device with multiple potential site associations, the conflict 
        resolution should be deterministic and consistent.
        
        **Feature: site-specific-device-collection-reporting, Property: Conflict Resolution Consistency**
        **Validates: Requirements 6.3, 6.4**
        """
        validator = SiteAssociationValidator('*-CORE-*')
        
        # Test conflict resolution multiple times
        results = []
        for _ in range(5):
            resolved_site = validator.resolve_multi_site_conflicts(device_info, candidate_sites)
            results.append(resolved_site)
        
        # Property: Conflict resolution should be deterministic
        assert all(r == results[0] for r in results), \
            f"Non-deterministic conflict resolution for {device_info['hostname']}: {results}"
        
        # Property: Resolved site should be from candidate list or GLOBAL
        assert results[0] in candidate_sites or results[0] == 'GLOBAL', \
            f"Resolved site {results[0]} should be from candidates {candidate_sites} or GLOBAL"
        
        # Property: If only one candidate, it should be selected
        if len(candidate_sites) == 1:
            assert results[0] == candidate_sites[0], \
                f"Single candidate {candidate_sites[0]} should be selected, got {results[0]}"
    
    @given(
        inventory_size=st.integers(min_value=5, max_value=20),
        site_count=st.integers(min_value=2, max_value=4)
    )
    def test_site_device_filtering_completeness_property(self, inventory_size, site_count):
        """
        Property: Site Device Filtering Completeness
        
        For any inventory and site filtering operation, the sum of devices across 
        all sites plus global devices should equal the total inventory.
        
        **Feature: site-specific-device-collection-reporting, Property: Site Device Filtering Completeness**
        **Validates: Requirements 6.2, 6.4**
        """
        validator = SiteAssociationValidator('*-CORE-*')
        
        # Create test inventory with devices from multiple sites
        inventory = {}
        expected_sites = set()
        
        device_counter = 0
        for site_idx in range(site_count):
            site_name = f"SITE{site_idx + 1}"
            expected_sites.add(site_name)
            
            # Add site boundary device
            hostname = f"{site_name}-CORE-01"
            device_key = f"{hostname}:192.168.{site_idx + 1}.1"
            inventory[device_key] = {
                'hostname': hostname,
                'ip_address': f"192.168.{site_idx + 1}.1"
            }
            device_counter += 1
            
            # Add regular site devices
            devices_in_site = min(3, (inventory_size - device_counter) // (site_count - site_idx))
            for dev_idx in range(devices_in_site):
                hostname = f"{site_name}-SW-{dev_idx + 1:02d}"
                device_key = f"{hostname}:192.168.{site_idx + 1}.{dev_idx + 2}"
                inventory[device_key] = {
                    'hostname': hostname,
                    'ip_address': f"192.168.{site_idx + 1}.{dev_idx + 2}"
                }
                device_counter += 1
        
        # Add some global devices
        while device_counter < inventory_size:
            hostname = f"GLOBAL-DEV-{device_counter:02d}"
            device_key = f"{hostname}:10.0.0.{device_counter}"
            inventory[device_key] = {
                'hostname': hostname,
                'ip_address': f"10.0.0.{device_counter}"
            }
            device_counter += 1
        
        # Get all sites from inventory
        discovered_sites = validator.get_all_sites(inventory)
        
        # Property: Discovered sites should include expected sites
        for expected_site in expected_sites:
            assert expected_site in discovered_sites, \
                f"Expected site {expected_site} not found in discovered sites {discovered_sites}"
        
        # Get devices for each site and count totals
        total_site_devices = 0
        for site_name in discovered_sites:
            site_devices = validator.get_site_devices(inventory, site_name)
            total_site_devices += len(site_devices)
            
            # Property: All devices in site should validate as members
            for device_key, device_info in site_devices.items():
                assert validator.validate_site_membership(device_info, site_name), \
                    f"Device {device_key} in site {site_name} should validate as member"
        
        # Count global devices
        global_devices = 0
        for device_key, device_info in inventory.items():
            site = validator.determine_device_site(
                device_info.get('hostname', ''), 
                device_info.get('ip_address', '')
            )
            if site == 'GLOBAL':
                global_devices += 1
        
        # Property: Total devices should equal inventory size
        total_accounted = total_site_devices + global_devices
        assert total_accounted == len(inventory), \
            f"Device count mismatch: {total_site_devices} site + {global_devices} global = {total_accounted}, expected {len(inventory)}"
    
    @given(
        site_boundary_pattern=st.sampled_from(['*-CORE-*', '*-RTR-*', '*-MDF-*']),
        cache_operations=st.integers(min_value=10, max_value=50)
    )
    def test_cache_consistency_property(self, site_boundary_pattern, cache_operations):
        """
        Property: Cache Consistency
        
        For any sequence of site determination operations, caching should not 
        affect the correctness of results.
        
        **Feature: site-specific-device-collection-reporting, Property: Cache Consistency**
        **Validates: Requirements 6.1, 6.2**
        """
        validator = SiteAssociationValidator(site_boundary_pattern)
        
        # Extract device type from pattern
        device_type = site_boundary_pattern.replace('*', '').replace('-', '')
        
        # Create test devices
        test_devices = []
        for i in range(cache_operations):
            site_name = f"SITE{(i % 3) + 1}"
            hostname = f"{site_name}-{device_type}-{i + 1:02d}"
            ip_address = f"192.168.{(i % 3) + 1}.{i + 1}"
            test_devices.append((hostname, ip_address))
        
        # First pass: determine sites without cache
        validator.clear_cache()
        first_results = []
        for hostname, ip_address in test_devices:
            site = validator.determine_device_site(hostname, ip_address)
            first_results.append(site)
        
        # Second pass: determine sites with cache populated
        second_results = []
        for hostname, ip_address in test_devices:
            site = validator.determine_device_site(hostname, ip_address)
            second_results.append(site)
        
        # Property: Results should be identical regardless of cache state
        assert first_results == second_results, \
            f"Cache affected results: first_pass={first_results}, second_pass={second_results}"
        
        # Third pass: clear cache and test again
        validator.clear_cache()
        third_results = []
        for hostname, ip_address in test_devices:
            site = validator.determine_device_site(hostname, ip_address)
            third_results.append(site)
        
        # Property: Results should remain consistent after cache clear
        assert first_results == third_results, \
            f"Results changed after cache clear: original={first_results}, after_clear={third_results}"