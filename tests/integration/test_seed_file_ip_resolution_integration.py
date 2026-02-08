"""
Integration tests for seed file IP resolution feature
Feature: database-ip-lookup-for-seed-devices
Tasks: 5.3, 5.4, 5.5, 5.6

These tests validate end-to-end scenarios using real components (not mocks where possible)
to ensure the complete feature works correctly.

Requirements tested:
- 2.2, 3.1, 4.1, 7.1 (database-resolved IPs)
- 3.2, 4.2, 7.1 (DNS fallback)
- 5.3, 7.3 (mixed seed file)
- 3.3, 4.3 (complete resolution failure)
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from netwalker.netwalker_app import NetWalkerApp


class TestSeedFileIPResolutionIntegration:
    """Integration tests for seed file IP resolution end-to-end scenarios"""

    def create_temp_seed_file(self, content):
        """Helper to create a temporary seed file with given content"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_file.write(content)
        temp_file.close()
        return temp_file.name

    def test_database_resolved_ips_integration(self):
        """
        Integration test for database-resolved IPs
        Task: 5.3
        Requirements: 2.2, 3.1, 4.1, 7.1
        
        Scenario:
        - Create seed file with hostname-only entries
        - Pre-populate database with primary IPs for those hostnames
        - Verify devices are added to discovery queue with database IPs
        - Verify logs show "database" as resolution source
        """
        # Create seed file with hostname-only entries
        seed_content = """hostname,ip,status
ROUTER-DB-01,,pending
ROUTER-DB-02,,pending
ROUTER-DB-03,,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            
            # Mock database manager with pre-populated IPs
            app.db_manager = MagicMock()
            app.db_manager.enabled = True
            
            # Database returns IPs for all hostnames
            def mock_get_ip(hostname):
                ip_map = {
                    'ROUTER-DB-01': '192.168.1.101',
                    'ROUTER-DB-02': '192.168.1.102',
                    'ROUTER-DB-03': '192.168.1.103'
                }
                return ip_map.get(hostname)
            
            app.db_manager.get_primary_ip_by_hostname.side_effect = mock_get_ip
            
            # Parse seed file and capture logs
            with patch('netwalker.netwalker_app.logger') as mock_logger:
                result = app._parse_seed_file(seed_file)
                
                # Verify all devices were added to discovery queue with database IPs
                assert len(result) == 3, "Should have 3 devices in discovery queue"
                assert 'ROUTER-DB-01:192.168.1.101' in result
                assert 'ROUTER-DB-02:192.168.1.102' in result
                assert 'ROUTER-DB-03:192.168.1.103' in result
                
                # Verify database was called for each hostname
                assert app.db_manager.get_primary_ip_by_hostname.call_count == 3
                app.db_manager.get_primary_ip_by_hostname.assert_any_call('ROUTER-DB-01')
                app.db_manager.get_primary_ip_by_hostname.assert_any_call('ROUTER-DB-02')
                app.db_manager.get_primary_ip_by_hostname.assert_any_call('ROUTER-DB-03')
                
                # Verify logs show "database" as resolution source
                info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                
                # Check for database resolution logs
                db_logs = [msg for msg in info_calls if 'database' in msg.lower()]
                assert len(db_logs) == 3, "Should have 3 database resolution log messages"
                
                # Verify each hostname appears in logs
                assert any('ROUTER-DB-01' in msg for msg in db_logs)
                assert any('ROUTER-DB-02' in msg for msg in db_logs)
                assert any('ROUTER-DB-03' in msg for msg in db_logs)
                
                # Verify resolved IPs appear in logs
                assert any('192.168.1.101' in msg for msg in db_logs)
                assert any('192.168.1.102' in msg for msg in db_logs)
                assert any('192.168.1.103' in msg for msg in db_logs)
                
        finally:
            os.unlink(seed_file)

    def test_dns_fallback_integration(self):
        """
        Integration test for DNS fallback
        Task: 5.4
        Requirements: 3.2, 4.2, 7.1
        
        Scenario:
        - Create seed file with hostname-only entries
        - Ensure hostnames are NOT in database
        - Mock DNS to return IPs
        - Verify devices are added to discovery queue with DNS IPs
        - Verify logs show "DNS" as resolution source
        """
        # Create seed file with hostname-only entries
        seed_content = """hostname,ip,status
ROUTER-DNS-01,,pending
ROUTER-DNS-02,,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            
            # Mock database manager to return None (not in database)
            app.db_manager = MagicMock()
            app.db_manager.enabled = True
            app.db_manager.get_primary_ip_by_hostname.return_value = None
            
            # Mock DNS to return IPs
            def mock_dns(hostname):
                dns_map = {
                    'ROUTER-DNS-01': '10.0.0.201',
                    'ROUTER-DNS-02': '10.0.0.202'
                }
                return dns_map.get(hostname, '10.0.0.1')
            
            with patch('socket.gethostbyname', side_effect=mock_dns):
                with patch('netwalker.netwalker_app.logger') as mock_logger:
                    result = app._parse_seed_file(seed_file)
                    
                    # Verify all devices were added with DNS IPs
                    assert len(result) == 2, "Should have 2 devices in discovery queue"
                    assert 'ROUTER-DNS-01:10.0.0.201' in result
                    assert 'ROUTER-DNS-02:10.0.0.202' in result
                    
                    # Verify database was tried first (and returned None)
                    assert app.db_manager.get_primary_ip_by_hostname.call_count == 2
                    
                    # Verify logs show "DNS" as resolution source
                    info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                    
                    # Check for DNS resolution logs (look for "from DNS" specifically)
                    dns_logs = [msg for msg in info_calls if 'from DNS' in msg]
                    assert len(dns_logs) == 2, "Should have 2 DNS resolution log messages"
                    
                    # Verify hostnames appear in logs
                    assert any('ROUTER-DNS-01' in msg for msg in dns_logs)
                    assert any('ROUTER-DNS-02' in msg for msg in dns_logs)
                    
                    # Verify resolved IPs appear in logs
                    assert any('10.0.0.201' in msg for msg in dns_logs)
                    assert any('10.0.0.202' in msg for msg in dns_logs)
                    
        finally:
            os.unlink(seed_file)

    def test_mixed_seed_file_integration(self):
        """
        Integration test for mixed seed file
        Task: 5.5
        Requirements: 5.3, 7.3
        
        Scenario:
        - Create seed file with explicit IPs, database IPs, and DNS IPs
        - Verify all devices are processed correctly
        - Verify explicit IPs bypass resolution
        - Verify resolution methods are logged correctly
        """
        # Create seed file with mixed entries
        seed_content = """hostname,ip,status
ROUTER-EXPLICIT-01,192.168.100.1,pending
ROUTER-DB-MIXED,,pending
ROUTER-EXPLICIT-02,192.168.100.2,pending
ROUTER-DNS-MIXED,,pending
ROUTER-EXPLICIT-03,192.168.100.3,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            
            # Mock database manager
            app.db_manager = MagicMock()
            app.db_manager.enabled = True
            
            # Database returns IP for ROUTER-DB-MIXED, None for ROUTER-DNS-MIXED
            def mock_get_ip(hostname):
                if hostname == 'ROUTER-DB-MIXED':
                    return '192.168.1.200'
                return None
            
            app.db_manager.get_primary_ip_by_hostname.side_effect = mock_get_ip
            
            # Mock DNS to return IP for ROUTER-DNS-MIXED
            def mock_dns(hostname):
                if hostname == 'ROUTER-DNS-MIXED':
                    return '10.0.0.200'
                raise Exception("DNS failed")
            
            with patch('socket.gethostbyname', side_effect=mock_dns):
                with patch('netwalker.netwalker_app.logger') as mock_logger:
                    result = app._parse_seed_file(seed_file)
                    
                    # Verify all devices were processed correctly
                    assert len(result) == 5, "Should have 5 devices in discovery queue"
                    
                    # Verify explicit IPs are preserved
                    assert 'ROUTER-EXPLICIT-01:192.168.100.1' in result
                    assert 'ROUTER-EXPLICIT-02:192.168.100.2' in result
                    assert 'ROUTER-EXPLICIT-03:192.168.100.3' in result
                    
                    # Verify database-resolved IP
                    assert 'ROUTER-DB-MIXED:192.168.1.200' in result
                    
                    # Verify DNS-resolved IP
                    assert 'ROUTER-DNS-MIXED:10.0.0.200' in result
                    
                    # Verify entry order is preserved
                    assert result[0] == 'ROUTER-EXPLICIT-01:192.168.100.1'
                    assert result[1] == 'ROUTER-DB-MIXED:192.168.1.200'
                    assert result[2] == 'ROUTER-EXPLICIT-02:192.168.100.2'
                    assert result[3] == 'ROUTER-DNS-MIXED:10.0.0.200'
                    assert result[4] == 'ROUTER-EXPLICIT-03:192.168.100.3'
                    
                    # Verify database was only called for blank IPs
                    assert app.db_manager.get_primary_ip_by_hostname.call_count == 2
                    app.db_manager.get_primary_ip_by_hostname.assert_any_call('ROUTER-DB-MIXED')
                    app.db_manager.get_primary_ip_by_hostname.assert_any_call('ROUTER-DNS-MIXED')
                    
                    # Verify logs show correct resolution sources
                    info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                    
                    # Check for database resolution log
                    db_logs = [msg for msg in info_calls if 'database' in msg.lower()]
                    assert len(db_logs) == 1, "Should have 1 database resolution log"
                    assert any('ROUTER-DB-MIXED' in msg for msg in db_logs)
                    
                    # Check for DNS resolution log (look for "from DNS" specifically)
                    dns_logs = [msg for msg in info_calls if 'from DNS' in msg]
                    assert len(dns_logs) == 1, "Should have 1 DNS resolution log"
                    assert any('ROUTER-DNS-MIXED' in msg for msg in dns_logs)
                    
                    # Verify no resolution logs for explicit IPs
                    assert not any('ROUTER-EXPLICIT-01' in msg and 'Resolved' in msg 
                                  for msg in info_calls)
                    assert not any('ROUTER-EXPLICIT-02' in msg and 'Resolved' in msg 
                                  for msg in info_calls)
                    assert not any('ROUTER-EXPLICIT-03' in msg and 'Resolved' in msg 
                                  for msg in info_calls)
                    
        finally:
            os.unlink(seed_file)

    def test_complete_resolution_failure_integration(self):
        """
        Integration test for complete resolution failure
        Task: 5.6
        Requirements: 3.3, 4.3
        
        Scenario:
        - Create seed file with unresolvable hostname
        - Ensure hostname is NOT in database
        - Mock DNS to fail
        - Verify device is skipped
        - Verify warning is logged
        """
        # Create seed file with unresolvable hostname
        seed_content = """hostname,ip,status
ROUTER-GOOD,192.168.1.1,pending
ROUTER-UNRESOLVABLE,,pending
ROUTER-ALSO-GOOD,192.168.1.2,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            
            # Mock database manager to return None
            app.db_manager = MagicMock()
            app.db_manager.enabled = True
            app.db_manager.get_primary_ip_by_hostname.return_value = None
            
            # Mock DNS to fail
            import socket
            with patch('socket.gethostbyname', side_effect=socket.gaierror("Name resolution failed")):
                with patch('netwalker.netwalker_app.logger') as mock_logger:
                    result = app._parse_seed_file(seed_file)
                    
                    # Verify only devices with explicit IPs were added
                    assert len(result) == 2, "Should have 2 devices (unresolvable skipped)"
                    assert 'ROUTER-GOOD:192.168.1.1' in result
                    assert 'ROUTER-ALSO-GOOD:192.168.1.2' in result
                    
                    # Verify unresolvable device is NOT in result
                    assert not any('ROUTER-UNRESOLVABLE' in device for device in result)
                    
                    # Verify database was tried
                    app.db_manager.get_primary_ip_by_hostname.assert_called_once_with(
                        'ROUTER-UNRESOLVABLE'
                    )
                    
                    # Verify warning was logged for resolution failure
                    warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
                    
                    # Check for resolution failure warning
                    failure_warnings = [msg for msg in warning_calls 
                                       if 'ROUTER-UNRESOLVABLE' in msg]
                    assert len(failure_warnings) >= 1, \
                        "Should have warning for resolution failure"
                    
                    # Verify the warning mentions the failure
                    assert any('Failed to resolve' in msg or 'could not resolve' in msg 
                              for msg in failure_warnings)
                    
                    # Verify skipping warning
                    skip_warnings = [msg for msg in warning_calls 
                                    if 'Skipping' in msg and 'ROUTER-UNRESOLVABLE' in msg]
                    assert len(skip_warnings) >= 1, \
                        "Should have warning about skipping device"
                    
        finally:
            os.unlink(seed_file)


    def test_database_error_fallback_to_dns_integration(self):
        """
        Integration test for database error fallback to DNS
        Requirements: 6.3
        
        Scenario:
        - Create seed file with hostname-only entry
        - Database query returns None (simulating internal error handling)
        - DNS successfully resolves the hostname
        - Verify device is added with DNS IP
        - Verify DNS resolution is logged
        """
        # Create seed file
        seed_content = """hostname,ip,status
ROUTER-DB-ERROR,,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            
            # Mock database manager to return None (simulating error handled internally)
            app.db_manager = MagicMock()
            app.db_manager.enabled = True
            app.db_manager.get_primary_ip_by_hostname.return_value = None
            
            # Mock DNS to succeed
            with patch('socket.gethostbyname', return_value='10.0.0.100'):
                with patch('netwalker.netwalker_app.logger') as mock_logger:
                    result = app._parse_seed_file(seed_file)
                    
                    # Verify device was added with DNS IP (fallback worked)
                    assert len(result) == 1, "Should have 1 device"
                    assert 'ROUTER-DB-ERROR:10.0.0.100' in result
                    
                    # Verify DNS resolution was logged
                    info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                    dns_logs = [msg for msg in info_calls if 'from DNS' in msg]
                    assert len(dns_logs) == 1, "Should have DNS resolution log"
                    assert any('ROUTER-DB-ERROR' in msg for msg in dns_logs)
                    
        finally:
            os.unlink(seed_file)

    def test_large_seed_file_performance(self):
        """
        Integration test for large seed file processing
        
        Scenario:
        - Create seed file with many entries (mix of explicit and blank IPs)
        - Verify all entries are processed correctly
        - Verify performance is acceptable
        """
        # Create seed file with 50 entries
        lines = ["hostname,ip,status"]
        for i in range(1, 51):
            if i % 3 == 0:
                # Every third entry has blank IP
                lines.append(f"ROUTER-{i:03d},,pending")
            else:
                # Others have explicit IP
                lines.append(f"ROUTER-{i:03d},192.168.{i//256}.{i%256},pending")
        
        seed_content = "\n".join(lines) + "\n"
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            
            # Mock database manager
            app.db_manager = MagicMock()
            app.db_manager.enabled = True
            
            # Database returns IPs for blank entries
            def mock_get_ip(hostname):
                # Extract number from hostname
                num = int(hostname.split('-')[1])
                return f"10.0.{num//256}.{num%256}"
            
            app.db_manager.get_primary_ip_by_hostname.side_effect = mock_get_ip
            
            # Parse seed file
            import time
            start_time = time.time()
            result = app._parse_seed_file(seed_file)
            elapsed_time = time.time() - start_time
            
            # Verify all devices were processed
            assert len(result) == 50, "Should have 50 devices"
            
            # Verify explicit IPs are preserved
            assert 'ROUTER-001:192.168.0.1' in result
            assert 'ROUTER-002:192.168.0.2' in result
            
            # Verify resolved IPs
            assert 'ROUTER-003:10.0.0.3' in result  # Every third has blank IP
            assert 'ROUTER-006:10.0.0.6' in result
            
            # Verify performance (should complete in reasonable time)
            assert elapsed_time < 5.0, \
                f"Processing 50 entries took {elapsed_time:.2f}s, should be < 5s"
            
            # Verify database was called correct number of times (17 blank IPs)
            blank_ip_count = len([i for i in range(1, 51) if i % 3 == 0])
            assert app.db_manager.get_primary_ip_by_hostname.call_count == blank_ip_count
            
        finally:
            os.unlink(seed_file)

    def test_format_consistency_integration(self):
        """
        Integration test for format consistency
        Requirements: 7.3
        
        Scenario:
        - Create seed file with explicit and resolved IPs
        - Verify all devices have consistent format in discovery queue
        - Verify format is "hostname:ip_address"
        """
        # Create seed file
        seed_content = """hostname,ip,status
ROUTER-EXPLICIT,192.168.1.1,pending
ROUTER-RESOLVED,,pending
"""
        seed_file = self.create_temp_seed_file(seed_content)

        try:
            # Create NetWalker app
            app = NetWalkerApp()
            
            # Mock database manager
            app.db_manager = MagicMock()
            app.db_manager.enabled = True
            app.db_manager.get_primary_ip_by_hostname.return_value = '10.0.0.1'
            
            # Parse seed file
            result = app._parse_seed_file(seed_file)
            
            # Verify both devices have consistent format
            assert len(result) == 2
            
            # Check format: "hostname:ip_address"
            for device in result:
                assert ':' in device, "Device should have colon separator"
                parts = device.split(':')
                assert len(parts) == 2, "Device should have exactly 2 parts"
                hostname, ip = parts
                assert hostname, "Hostname should not be empty"
                assert ip, "IP should not be empty"
                assert '.' in ip, "IP should contain dots"
            
            # Verify specific formats
            assert result[0] == 'ROUTER-EXPLICIT:192.168.1.1'
            assert result[1] == 'ROUTER-RESOLVED:10.0.0.1'
            
        finally:
            os.unlink(seed_file)


if __name__ == "__main__":
    # Run integration tests
    test_instance = TestSeedFileIPResolutionIntegration()
    
    print("Running integration tests for seed file IP resolution...")
    
    print("\n[TEST 5.3] Database-resolved IPs integration...")
    test_instance.test_database_resolved_ips_integration()
    print("[OK] test_database_resolved_ips_integration")
    
    print("\n[TEST 5.4] DNS fallback integration...")
    test_instance.test_dns_fallback_integration()
    print("[OK] test_dns_fallback_integration")
    
    print("\n[TEST 5.5] Mixed seed file integration...")
    test_instance.test_mixed_seed_file_integration()
    print("[OK] test_mixed_seed_file_integration")
    
    print("\n[TEST 5.6] Complete resolution failure integration...")
    test_instance.test_complete_resolution_failure_integration()
    print("[OK] test_complete_resolution_failure_integration")
    
    print("\n[EXTRA] Database error fallback to DNS integration...")
    test_instance.test_database_error_fallback_to_dns_integration()
    print("[OK] test_database_error_fallback_to_dns_integration")
    
    print("\n[EXTRA] Large seed file performance...")
    test_instance.test_large_seed_file_performance()
    print("[OK] test_large_seed_file_performance")
    
    print("\n[EXTRA] Format consistency integration...")
    test_instance.test_format_consistency_integration()
    print("[OK] test_format_consistency_integration")
    
    print("\n" + "="*70)
    print("All integration tests passed!")
    print("="*70)
