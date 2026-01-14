"""
Property-based tests for VLAN report integration

Feature: vlan-inventory-collection
Tasks: 12.1, 12.2, 12.3, 12.4
"""

import pytest
from hypothesis import given, strategies as st, assume
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path

from netwalker.reports.excel_generator import ExcelReportGenerator
from netwalker.connection.data_models import VLANInfo


class TestVLANReportIntegrationProperties:
    """Property-based tests for VLAN report integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = {
            'reports_directory': tempfile.mkdtemp(),
            'output': {
                'site_boundary_pattern': '*-CORE-*'
            }
        }
        self.generator = ExcelReportGenerator(self.config)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.config['reports_directory']):
            shutil.rmtree(self.config['reports_directory'])
    
    @given(
        devices=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),  # hostname
                st.ip_addresses(v=4).map(str),  # ip
                st.sampled_from(['ios', 'nxos', 'iosxe']),  # platform
                st.lists(
                    st.tuples(
                        st.integers(min_value=1, max_value=4094),  # vlan_id
                        st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))  # vlan_name
                    ),
                    min_size=0, max_size=5
                )  # vlans
            ),
            min_size=1, max_size=3
        ),
        seed_devices=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=2)
    )
    def test_main_report_vlan_sheet_inclusion(self, devices, seed_devices):
        """
        Property 36: Main Report VLAN Sheet Inclusion
        
        For any main discovery report generation, the VLAN inventory sheet
        must be included in the workbook with proper structure and data.
        
        Validates: Requirements 10.1
        """
        # Create test inventory with VLAN data
        inventory = {}
        discovery_results = {
            'total_devices': len(devices),
            'successful_connections': len(devices),
            'failed_connections': 0,
            'start_time': '2024-01-01 10:00:00',
            'end_time': '2024-01-01 11:00:00',
            'duration': '1:00:00'
        }
        
        for hostname, ip, platform, vlans in devices:
            device_key = f"{hostname}_{ip}"
            vlan_info_list = []
            
            for vlan_id, vlan_name in vlans:
                vlan_info = VLANInfo(
                    vlan_id=vlan_id,
                    vlan_name=vlan_name,
                    port_count=2,
                    portchannel_count=1,
                    device_hostname=hostname,
                    device_ip=ip
                )
                vlan_info_list.append(vlan_info)
            
            inventory[device_key] = {
                'hostname': hostname,
                'ip_address': ip,
                'platform': platform,
                'vlans': vlan_info_list,
                'connection_status': 'success'
            }
        
        # Mock file operations to avoid actual file creation
        with patch('openpyxl.Workbook') as mock_workbook_class:
            mock_workbook = Mock()
            mock_workbook_class.return_value = mock_workbook
            mock_workbook.active = Mock()
            mock_workbook.sheetnames = []
            
            # Mock sheet creation
            mock_sheet = Mock()
            mock_workbook.create_sheet.return_value = mock_sheet
            
            # Generate main discovery report
            with patch.object(self.generator, '_create_summary_sheet'), \
                 patch.object(self.generator, '_create_device_inventory_sheet'), \
                 patch.object(self.generator, '_create_connections_sheet'), \
                 patch.object(self.generator, '_create_vlan_inventory_sheet') as mock_vlan_sheet:
                
                # Call the method
                result = self.generator._generate_main_discovery_report(
                    inventory, discovery_results, seed_devices
                )
                
                # Verify VLAN inventory sheet was created
                mock_vlan_sheet.assert_called_once_with(mock_workbook, inventory)
                
                # Verify result is a file path
                assert isinstance(result, str)
                assert result.endswith('.xlsx')
                assert 'Discovery_' in result
    
    @given(
        site_devices=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),  # hostname
                st.ip_addresses(v=4).map(str),  # ip
                st.sampled_from(['ios', 'nxos', 'iosxe']),  # platform
                st.lists(
                    st.tuples(
                        st.integers(min_value=1, max_value=4094),  # vlan_id
                        st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))  # vlan_name
                    ),
                    min_size=0, max_size=3
                )  # vlans
            ),
            min_size=1, max_size=3
        ),
        site_name=st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
    )
    def test_site_specific_vlan_data_inclusion(self, site_devices, site_name):
        """
        Property 37: Site-Specific VLAN Data Inclusion
        
        For any site-specific report generation, VLAN data must be included
        and properly filtered to only show devices from that site.
        
        Validates: Requirements 10.2
        """
        # Create site-specific inventory
        site_inventory = {}
        discovery_results = {
            'total_devices': len(site_devices),
            'successful_connections': len(site_devices),
            'failed_connections': 0
        }
        seed_devices = []
        
        for hostname, ip, platform, vlans in site_devices:
            device_key = f"{hostname}_{ip}"
            vlan_info_list = []
            
            for vlan_id, vlan_name in vlans:
                vlan_info = VLANInfo(
                    vlan_id=vlan_id,
                    vlan_name=vlan_name,
                    port_count=1,
                    portchannel_count=0,
                    device_hostname=hostname,
                    device_ip=ip
                )
                vlan_info_list.append(vlan_info)
            
            site_inventory[device_key] = {
                'hostname': hostname,
                'ip_address': ip,
                'platform': platform,
                'vlans': vlan_info_list,
                'connection_status': 'success'
            }
            seed_devices.append(f"{hostname}:{ip}")
        
        # Mock file operations
        with patch('openpyxl.Workbook') as mock_workbook_class:
            mock_workbook = Mock()
            mock_workbook_class.return_value = mock_workbook
            mock_workbook.active = Mock()
            
            mock_sheet = Mock()
            mock_workbook.create_sheet.return_value = mock_sheet
            
            # Generate site-specific report
            with patch.object(self.generator, '_create_site_summary_sheet'), \
                 patch.object(self.generator, '_create_device_inventory_sheet'), \
                 patch.object(self.generator, '_create_connections_sheet'), \
                 patch.object(self.generator, '_create_vlan_inventory_sheet') as mock_vlan_sheet:
                
                result = self.generator._generate_site_discovery_report(
                    site_inventory, discovery_results, seed_devices, site_name
                )
                
                # Verify VLAN inventory sheet was created with site-specific data
                mock_vlan_sheet.assert_called_once_with(mock_workbook, site_inventory)
                
                # Verify result contains site name
                assert isinstance(result, str)
                assert site_name in result
                assert result.endswith('.xlsx')
    
    @given(
        seed_devices=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),  # hostname
                st.ip_addresses(v=4).map(str),  # ip
                st.lists(
                    st.tuples(
                        st.integers(min_value=1, max_value=4094),  # vlan_id
                        st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))  # vlan_name
                    ),
                    min_size=0, max_size=2
                )  # vlans
            ),
            min_size=1, max_size=2
        )
    )
    def test_per_seed_vlan_data_inclusion(self, seed_devices):
        """
        Property 38: Per-Seed VLAN Data Inclusion
        
        For any per-seed report generation, VLAN data must be included
        for devices discovered by that specific seed.
        
        Validates: Requirements 10.3
        """
        # Create inventory with seed-specific devices
        inventory = {}
        seed_device_list = []
        
        for hostname, ip, vlans in seed_devices:
            device_key = f"{hostname}_{ip}"
            seed_device_list.append(f"{hostname}:{ip}")
            
            vlan_info_list = []
            for vlan_id, vlan_name in vlans:
                vlan_info = VLANInfo(
                    vlan_id=vlan_id,
                    vlan_name=vlan_name,
                    port_count=1,
                    portchannel_count=0,
                    device_hostname=hostname,
                    device_ip=ip
                )
                vlan_info_list.append(vlan_info)
            
            inventory[device_key] = {
                'hostname': hostname,
                'ip_address': ip,
                'platform': 'ios',
                'vlans': vlan_info_list,
                'connection_status': 'success',
                'neighbors': []
            }
        
        # Mock file operations
        with patch('openpyxl.Workbook') as mock_workbook_class:
            mock_workbook = Mock()
            mock_workbook_class.return_value = mock_workbook
            mock_workbook.active = Mock()
            
            mock_sheet = Mock()
            mock_workbook.create_sheet.return_value = mock_sheet
            
            # Generate per-seed reports
            with patch.object(self.generator, '_create_seed_summary_sheet'), \
                 patch.object(self.generator, '_create_device_inventory_sheet'), \
                 patch.object(self.generator, '_create_vlan_inventory_sheet') as mock_vlan_sheet, \
                 patch.object(self.generator, '_create_neighbor_detail_sheets'):
                
                results = self.generator._generate_per_seed_reports(inventory, seed_device_list)
                
                # Verify VLAN sheets were created for each seed
                assert mock_vlan_sheet.call_count == len(seed_device_list)
                
                # Verify results
                assert len(results) == len(seed_device_list)
                for result in results:
                    assert isinstance(result, str)
                    assert result.endswith('.xlsx')
    
    @given(
        all_inventories=st.dictionaries(
            keys=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
            values=st.dictionaries(
                keys=st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
                values=st.fixed_dictionaries({
                    'hostname': st.text(min_size=1, max_size=15),
                    'ip_address': st.ip_addresses(v=4).map(str),
                    'platform': st.sampled_from(['ios', 'nxos', 'iosxe']),
                    'vlans': st.lists(
                        st.builds(
                            VLANInfo,
                            vlan_id=st.integers(min_value=1, max_value=4094),
                            vlan_name=st.text(min_size=1, max_size=10),
                            port_count=st.integers(min_value=0, max_value=5),
                            portchannel_count=st.integers(min_value=0, max_value=2),
                            device_hostname=st.text(min_size=1, max_size=15),
                            device_ip=st.ip_addresses(v=4).map(str)
                        ),
                        min_size=0, max_size=3
                    )
                }),
                min_size=1, max_size=2
            ),
            min_size=1, max_size=2
        )
    )
    def test_master_inventory_vlan_consolidation(self, all_inventories):
        """
        Property 39: Master Inventory VLAN Consolidation
        
        For master inventory generation, VLAN data from all seed discoveries
        must be consolidated and properly attributed to their source seeds.
        
        Validates: Requirements 10.4
        """
        assume(len(all_inventories) > 0)
        
        seed_devices = list(all_inventories.keys())
        
        # Mock file operations
        with patch('openpyxl.Workbook') as mock_workbook_class:
            mock_workbook = Mock()
            mock_workbook_class.return_value = mock_workbook
            mock_workbook.active = Mock()
            
            mock_sheet = Mock()
            mock_workbook.create_sheet.return_value = mock_sheet
            
            # Generate master inventory
            with patch.object(self.generator, '_create_master_inventory_sheet'), \
                 patch.object(self.generator, '_create_master_vlan_inventory_sheet') as mock_master_vlan_sheet:
                
                result = self.generator.generate_master_inventory(all_inventories, seed_devices)
                
                # Verify master VLAN inventory sheet was created
                mock_master_vlan_sheet.assert_called_once()
                
                # Get the consolidated inventory argument
                call_args = mock_master_vlan_sheet.call_args[0]
                consolidated_inventory = call_args[1]
                
                # Verify consolidation occurred
                assert isinstance(consolidated_inventory, dict)
                
                # Verify result
                assert isinstance(result, str)
                assert result.endswith('.xlsx')
                assert 'Master_Inventory_' in result

class TestVLANIntegrationProperties:
    """Property-based tests for VLAN integration completeness"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = {
            'reports_directory': tempfile.mkdtemp(),
            'vlan_collection': {
                'enabled': True,
                'timeout': 30
            },
            'output': {
                'site_boundary_pattern': '*-CORE-*'
            }
        }
        self.generator = ExcelReportGenerator(self.config)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.config['reports_directory']):
            shutil.rmtree(self.config['reports_directory'])
    
    @given(
        devices_with_mixed_success=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),  # hostname
                st.ip_addresses(v=4).map(str),  # ip
                st.sampled_from(['ios', 'nxos', 'iosxe']),  # platform
                st.booleans(),  # vlan_success
                st.lists(
                    st.tuples(
                        st.integers(min_value=1, max_value=4094),  # vlan_id
                        st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))  # vlan_name
                    ),
                    min_size=0, max_size=3
                )  # vlans (only if success)
            ),
            min_size=2, max_size=5
        )
    )
    def test_report_integration_completeness(self, devices_with_mixed_success):
        """
        Property 17: Report Integration Completeness
        
        All report types must include VLAN inventory sheets with proper
        structure and data, regardless of the mix of successful/failed
        VLAN collections.
        
        Validates: Requirements 5.3
        """
        # Create inventory with mixed VLAN collection results
        inventory = {}
        successful_vlan_devices = 0
        failed_vlan_devices = 0
        
        for hostname, ip, platform, vlan_success, vlans in devices_with_mixed_success:
            device_key = f"{hostname}_{ip}"
            
            if vlan_success and vlans:
                # Successful VLAN collection
                vlan_info_list = []
                for vlan_id, vlan_name in vlans:
                    vlan_info = VLANInfo(
                        vlan_id=vlan_id,
                        vlan_name=vlan_name,
                        port_count=2,
                        portchannel_count=1,
                        device_hostname=hostname,
                        device_ip=ip
                    )
                    vlan_info_list.append(vlan_info)
                
                inventory[device_key] = {
                    'hostname': hostname,
                    'ip_address': ip,
                    'platform': platform,
                    'vlans': vlan_info_list,
                    'vlan_collection_status': 'success',
                    'connection_status': 'success'
                }
                successful_vlan_devices += 1
            else:
                # Failed VLAN collection
                inventory[device_key] = {
                    'hostname': hostname,
                    'ip_address': ip,
                    'platform': platform,
                    'vlans': [],
                    'vlan_collection_status': 'failed',
                    'connection_status': 'success'
                }
                failed_vlan_devices += 1
        
        # Ensure we have mixed results
        assume(successful_vlan_devices > 0 or failed_vlan_devices > 0)
        
        discovery_results = {
            'total_devices': len(devices_with_mixed_success),
            'successful_connections': len(devices_with_mixed_success),
            'failed_connections': 0
        }
        
        seed_devices = [f"{hostname}:{ip}" for hostname, ip, _, _, _ in devices_with_mixed_success]
        
        # Mock file operations
        with patch('openpyxl.Workbook') as mock_workbook_class:
            mock_workbook = Mock()
            mock_workbook_class.return_value = mock_workbook
            mock_workbook.active = Mock()
            mock_workbook.sheetnames = []
            
            mock_sheet = Mock()
            mock_workbook.create_sheet.return_value = mock_sheet
            
            # Test main discovery report
            with patch.object(self.generator, '_create_summary_sheet'), \
                 patch.object(self.generator, '_create_device_inventory_sheet'), \
                 patch.object(self.generator, '_create_connections_sheet'), \
                 patch.object(self.generator, '_create_vlan_inventory_sheet') as mock_vlan_sheet:
                
                main_report = self.generator._generate_main_discovery_report(
                    inventory, discovery_results, seed_devices
                )
                
                # Verify VLAN sheet was created for main report
                mock_vlan_sheet.assert_called_with(mock_workbook, inventory)
            
            # Test inventory report
            with patch.object(self.generator, '_create_device_inventory_sheet'), \
                 patch.object(self.generator, '_create_vlan_inventory_sheet') as mock_vlan_sheet:
                
                inventory_report = self.generator.generate_inventory_report(inventory)
                
                # Verify VLAN sheet was created for inventory report
                mock_vlan_sheet.assert_called_with(mock_workbook, inventory)
            
            # Verify both reports were generated successfully
            assert isinstance(main_report, str) and main_report.endswith('.xlsx')
            assert isinstance(inventory_report, str) and inventory_report.endswith('.xlsx')
    
    @given(
        devices_with_failures=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),  # hostname
                st.ip_addresses(v=4).map(str),  # ip
                st.sampled_from(['connection_failed', 'vlan_failed', 'success']),  # failure_type
                st.lists(
                    st.tuples(
                        st.integers(min_value=1, max_value=4094),  # vlan_id
                        st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))  # vlan_name
                    ),
                    min_size=0, max_size=2
                )  # vlans
            ),
            min_size=2, max_size=4
        )
    )
    def test_graceful_partial_failure_handling(self, devices_with_failures):
        """
        Property 18: Graceful Partial Failure Handling
        
        The system must handle partial failures gracefully, continuing
        to generate reports and include available data while properly
        documenting failures.
        
        Validates: Requirements 5.4
        """
        # Create inventory with various failure scenarios
        inventory = {}
        connection_failures = 0
        vlan_failures = 0
        successes = 0
        
        for hostname, ip, failure_type, vlans in devices_with_failures:
            device_key = f"{hostname}_{ip}"
            
            if failure_type == 'connection_failed':
                # Device connection failed - no device in inventory
                connection_failures += 1
                continue
            
            elif failure_type == 'vlan_failed':
                # Device connected but VLAN collection failed
                inventory[device_key] = {
                    'hostname': hostname,
                    'ip_address': ip,
                    'platform': 'ios',
                    'vlans': [],
                    'vlan_collection_status': 'failed',
                    'connection_status': 'success'
                }
                vlan_failures += 1
            
            else:  # success
                # Successful device and VLAN collection
                vlan_info_list = []
                for vlan_id, vlan_name in vlans:
                    vlan_info = VLANInfo(
                        vlan_id=vlan_id,
                        vlan_name=vlan_name,
                        port_count=1,
                        portchannel_count=0,
                        device_hostname=hostname,
                        device_ip=ip
                    )
                    vlan_info_list.append(vlan_info)
                
                inventory[device_key] = {
                    'hostname': hostname,
                    'ip_address': ip,
                    'platform': 'ios',
                    'vlans': vlan_info_list,
                    'vlan_collection_status': 'success',
                    'connection_status': 'success'
                }
                successes += 1
        
        # Ensure we have some failures to test graceful handling
        assume(connection_failures > 0 or vlan_failures > 0)
        assume(len(inventory) > 0)  # At least some devices succeeded
        
        discovery_results = {
            'total_devices': len(devices_with_failures),
            'successful_connections': len(inventory),
            'failed_connections': connection_failures
        }
        
        seed_devices = [f"{hostname}:{ip}" for hostname, ip, failure_type, _ in devices_with_failures 
                       if failure_type != 'connection_failed']
        
        # Mock file operations
        with patch('openpyxl.Workbook') as mock_workbook_class:
            mock_workbook = Mock()
            mock_workbook_class.return_value = mock_workbook
            mock_workbook.active = Mock()
            
            mock_sheet = Mock()
            mock_workbook.create_sheet.return_value = mock_sheet
            
            # Generate reports despite failures
            with patch.object(self.generator, '_create_summary_sheet'), \
                 patch.object(self.generator, '_create_device_inventory_sheet'), \
                 patch.object(self.generator, '_create_connections_sheet'), \
                 patch.object(self.generator, '_create_vlan_inventory_sheet') as mock_vlan_sheet:
                
                # Should not raise exceptions despite failures
                try:
                    report_files = self.generator.generate_discovery_report(
                        inventory, discovery_results, seed_devices
                    )
                    
                    # Verify reports were generated
                    assert len(report_files) > 0, "Should generate reports despite partial failures"
                    
                    # Verify VLAN sheet creation was attempted
                    assert mock_vlan_sheet.call_count > 0, "VLAN sheets should be created despite failures"
                    
                except Exception as e:
                    pytest.fail(f"Report generation should not fail due to partial failures: {e}")