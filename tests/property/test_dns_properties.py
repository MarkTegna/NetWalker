"""
Property-based tests for DNS validation functionality.

Tests DNS validation, address resolution, and RFC1918 conflict detection
using property-based testing with real network devices from prodtest_files.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import ip_addresses
import ipaddress
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import os

from netwalker.validation.dns_validator import DNSValidator, DNSValidationResult


class TestDNSValidationProperties:
    """Property-based tests for DNS validation functionality using real test data"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = {
            'dns_timeout_seconds': 5,
            'max_concurrent_dns': 5,
            'enable_ping_resolution': True
        }
        self.dns_validator = DNSValidator(self.config)
        
        # Load real test devices from prodtest_files
        self.test_devices = self._load_test_devices()
    
    def _load_test_devices(self):
        """Load real test devices from prodtest_files/seed_file.csv"""
        test_devices = []
        seed_file_path = "prodtest_files/seed_file.csv"
        
        if os.path.exists(seed_file_path):
            with open(seed_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Use hostname as both hostname and IP for DNS resolution testing
                        test_devices.append((line, line))
        
        # If no test devices available, use some safe public DNS servers
        if not test_devices:
            test_devices = [
                ("google-public-dns-a.google.com", "8.8.8.8"),
                ("google-public-dns-b.google.com", "8.8.4.4"),
                ("cloudflare-dns.com", "1.1.1.1")
            ]
        
        return test_devices
    
    @given(ip_addresses(v=4))
    def test_public_ip_detection_property(self, ip_address):
        """
        **Feature: dns-validation, Property 25: Public IP Address Resolution**
        
        For any IPv4 address, public IP detection should correctly identify
        whether the address is in RFC1918 private ranges or not.
        **Validates: Requirements 9.1**
        """
        ip_str = str(ip_address)
        
        # Define RFC1918 ranges
        rfc1918_networks = [
            ipaddress.IPv4Network('10.0.0.0/8'),
            ipaddress.IPv4Network('172.16.0.0/12'),
            ipaddress.IPv4Network('192.168.0.0/16')
        ]
        
        # Check if IP is in any RFC1918 range
        is_private_expected = any(ip_address in network for network in rfc1918_networks)
        is_public_expected = not is_private_expected
        
        # Test public IP detection
        is_public_actual = self.dns_validator._is_public_ip(ip_str)
        is_private_actual = self.dns_validator._is_private_ip(ip_str)
        
        # Verify results
        assert is_public_actual == is_public_expected, f"Public IP detection failed for {ip_str}"
        assert is_private_actual == is_private_expected, f"Private IP detection failed for {ip_str}"
        assert is_public_actual != is_private_actual, f"IP cannot be both public and private: {ip_str}"
    
    def test_dns_validation_result_structure_property(self):
        """
        **Feature: dns-validation, Property 25: Public IP Address Resolution**
        
        For any real hostname, DNS validation should return a properly structured
        DNSValidationResult with all required fields populated.
        **Validates: Requirements 9.1, 9.2**
        """
        # Use first test device
        if not self.test_devices:
            pytest.skip("No test devices available")
        
        hostname, ip_address = self.test_devices[0]
        
        # Perform real DNS validation
        result = self.dns_validator.validate_device_dns(hostname, ip_address)
        
        # Verify result structure
        assert isinstance(result, DNSValidationResult)
        assert result.hostname == hostname
        assert result.ip_address == ip_address
        assert isinstance(result.forward_dns_success, bool)
        assert isinstance(result.reverse_dns_success, bool)
        assert isinstance(result.is_public_ip, bool)
        assert isinstance(result.ping_success, bool)
        assert isinstance(result.rfc1918_conflict, bool)
        assert isinstance(result.validation_timestamp, datetime)
    
    def test_concurrent_validation_completeness_property(self):
        """
        **Feature: dns-validation, Property 26: DNS Validation Completeness**
        
        For any list of real devices, concurrent DNS validation should return
        results for all input devices without loss or duplication.
        **Validates: Requirements 9.2**
        """
        if not self.test_devices:
            pytest.skip("No test devices available")
        
        # Use all available test devices
        valid_devices = self.test_devices[:3]  # Limit to first 3 for faster testing
        
        # Perform concurrent validation with real DNS
        results = self.dns_validator.validate_devices_concurrent(valid_devices)
        
        # Verify completeness
        assert len(results) == len(valid_devices), "Result count should match input count"
        
        # Verify all devices have results
        input_keys = {f"{hostname}:{ip_str}" for hostname, ip_str in valid_devices}
        result_keys = set(results.keys())
        assert input_keys == result_keys, "All input devices should have results"
        
        # Verify no duplicate results
        assert len(result_keys) == len(results), "No duplicate results should exist"
        
        # Verify all results are properly structured
        for device_key, result in results.items():
            assert isinstance(result, DNSValidationResult)
            assert result.hostname is not None
            assert result.ip_address is not None
            assert isinstance(result.validation_timestamp, datetime)
    
    def test_rfc1918_conflict_detection_property(self):
        """
        **Feature: dns-validation, Property 25: Public IP Address Resolution**
        
        For any public IP address that resolves to a private IP address,
        RFC1918 conflict detection should correctly identify the conflict.
        **Validates: Requirements 9.4**
        """
        # Create a test case with known public IP that might resolve to private
        public_ip_str = "8.8.8.8"  # Google DNS - definitely public
        hostname = "test-device"
        
        # Mock only the forward DNS to simulate conflict
        with patch('socket.gethostbyname') as mock_forward:
            # Simulate public hostname resolving to private IP (conflict scenario)
            mock_forward.return_value = "192.168.1.100"  # Private IP
            
            # Perform validation
            result = self.dns_validator.validate_device_dns(hostname, public_ip_str)
            
            # Verify RFC1918 conflict detection
            assert result.is_public_ip == True, "Should detect public IP"
            assert result.rfc1918_conflict == True, "Should detect RFC1918 conflict"
            assert result.resolved_private_ip == "192.168.1.100", "Should capture resolved private IP"
    
    def test_dns_validation_error_handling_property(self):
        """
        **Feature: dns-validation, Property 26: DNS Validation Completeness**
        
        For any DNS validation that encounters errors, the system should
        handle errors gracefully and return appropriate error information.
        **Validates: Requirements 9.2**
        """
        # Use invalid hostname that should fail DNS resolution
        hostname = "invalid-nonexistent-hostname-12345.invalid"
        ip_address = "192.168.1.1"
        
        # Perform validation with invalid hostname
        result = self.dns_validator.validate_device_dns(hostname, ip_address)
        
        # Verify error handling
        assert isinstance(result, DNSValidationResult)
        assert result.hostname == hostname
        assert result.ip_address == ip_address
        # DNS resolution should fail for invalid hostname
        assert result.forward_dns_success == False, "Should fail forward DNS for invalid hostname"
    
    def test_validation_summary_accuracy_property(self):
        """
        **Feature: dns-validation, Property 26: DNS Validation Completeness**
        
        For any set of real DNS validation results, the validation summary
        should accurately reflect the statistics of all results.
        **Validates: Requirements 9.2**
        """
        if not self.test_devices:
            pytest.skip("No test devices available")
        
        # Use available test devices
        valid_devices = self.test_devices[:2]  # Limit for faster testing
        
        # Perform validation with real DNS
        results = self.dns_validator.validate_devices_concurrent(valid_devices)
        summary = self.dns_validator.get_validation_summary()
        
        # Verify summary accuracy
        assert summary['total_devices'] == len(results)
        
        # Count actual results
        forward_success_count = sum(1 for r in results.values() if r.forward_dns_success)
        reverse_success_count = sum(1 for r in results.values() if r.reverse_dns_success)
        public_ip_count = sum(1 for r in results.values() if r.is_public_ip)
        conflict_count = sum(1 for r in results.values() if r.rfc1918_conflict)
        error_count = sum(1 for r in results.values() if r.error_details)
        
        # Verify summary matches actual counts
        assert summary['forward_dns_success'] == forward_success_count
        assert summary['reverse_dns_success'] == reverse_success_count
        assert summary['public_ip_devices'] == public_ip_count
        assert summary['rfc1918_conflicts'] == conflict_count
        assert summary['validation_errors'] == error_count
        
        # Verify percentages are calculated correctly
        if summary['total_devices'] > 0:
            expected_forward_rate = forward_success_count / summary['total_devices'] * 100
            expected_reverse_rate = reverse_success_count / summary['total_devices'] * 100
            
            assert abs(summary['forward_dns_success_rate'] - expected_forward_rate) < 0.1
            assert abs(summary['reverse_dns_success_rate'] - expected_reverse_rate) < 0.1
    
    def test_dns_validation_completeness_property(self):
        """
        **Feature: dns-validation, Property 26: DNS Validation Completeness**
        
        For any set of real devices, DNS validation should be complete and consistent:
        - All devices should have validation results
        - Results should contain all required fields
        - Validation should be deterministic for the same inputs
        - No data should be lost during concurrent processing
        **Validates: Requirements 9.2**
        """
        if not self.test_devices:
            pytest.skip("No test devices available")
        
        # Use available test devices (limit for performance)
        valid_devices = self.test_devices[:2]
        
        # Perform validation twice to test consistency
        results1 = self.dns_validator.validate_devices_concurrent(valid_devices)
        results2 = self.dns_validator.validate_devices_concurrent(valid_devices)
        
        # Test completeness
        assert len(results1) == len(valid_devices), "First validation should cover all devices"
        assert len(results2) == len(valid_devices), "Second validation should cover all devices"
        
        # Test all required fields are present
        for device_key, result in results1.items():
            assert isinstance(result.hostname, str), f"Hostname should be string for {device_key}"
            assert isinstance(result.ip_address, str), f"IP address should be string for {device_key}"
            assert isinstance(result.forward_dns_success, bool), f"Forward DNS success should be bool for {device_key}"
            assert isinstance(result.reverse_dns_success, bool), f"Reverse DNS success should be bool for {device_key}"
            assert isinstance(result.is_public_ip, bool), f"Is public IP should be bool for {device_key}"
            assert isinstance(result.ping_success, bool), f"Ping success should be bool for {device_key}"
            assert isinstance(result.rfc1918_conflict, bool), f"RFC1918 conflict should be bool for {device_key}"
            assert isinstance(result.validation_timestamp, datetime), f"Timestamp should be datetime for {device_key}"
            
            # Test logical consistency
            if result.rfc1918_conflict:
                assert result.resolved_private_ip is not None, f"RFC1918 conflict should have resolved private IP for {device_key}"
            
            if result.forward_dns_success:
                assert result.forward_dns_resolved_ip is not None, f"Successful forward DNS should have resolved IP for {device_key}"
            
            if result.reverse_dns_success:
                assert result.reverse_dns_resolved_hostname is not None, f"Successful reverse DNS should have resolved hostname for {device_key}"
        
        # Test deterministic behavior (results should be consistent for same inputs)
        for device_key in results1.keys():
            result1 = results1[device_key]
            result2 = results2[device_key]
            
            # Core validation results should be identical for same inputs
            assert result1.hostname == result2.hostname, f"Hostname should be consistent for {device_key}"
            assert result1.ip_address == result2.ip_address, f"IP address should be consistent for {device_key}"
            assert result1.is_public_ip == result2.is_public_ip, f"Public IP detection should be consistent for {device_key}"
        
        # Test no data loss in concurrent processing
        input_device_keys = {f"{hostname}:{ip_str}" for hostname, ip_str in valid_devices}
        result_device_keys = set(results1.keys())
        
        assert input_device_keys == result_device_keys, "No devices should be lost during validation"
        
        # Test validation summary consistency
        summary1 = self.dns_validator.get_validation_summary()
        
        # Summary should reflect actual results
        actual_forward_success = sum(1 for r in results1.values() if r.forward_dns_success)
        actual_reverse_success = sum(1 for r in results1.values() if r.reverse_dns_success)
        actual_public_ips = sum(1 for r in results1.values() if r.is_public_ip)
        actual_conflicts = sum(1 for r in results1.values() if r.rfc1918_conflict)
        
        assert summary1['forward_dns_success'] == actual_forward_success, "Summary should match actual forward DNS successes"
        assert summary1['reverse_dns_success'] == actual_reverse_success, "Summary should match actual reverse DNS successes"
        assert summary1['public_ip_devices'] == actual_public_ips, "Summary should match actual public IP count"
        assert summary1['rfc1918_conflicts'] == actual_conflicts, "Summary should match actual RFC1918 conflicts"