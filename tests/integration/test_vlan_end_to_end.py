"""
Integration tests for end-to-end VLAN collection and reporting workflow

Feature: vlan-inventory-collection
Task: 14.3
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from netwalker.vlan.vlan_collector import VLANCollector
from netwalker.reports.excel_generator import ExcelReportGenerator
from netwalker.discovery.device_collector import DeviceCollector
from netwalker.connection.data_models import DeviceInfo
from netwalker.connection.data_models import VLANInfo


class TestVLANEndToEndIntegration:
    """Integration tests for complete VLAN workflow"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'vlan_collection': {
                'enabled': True,
                'timeout': 30,
                'commands': {
                    'ios': ['show vlan brief'],
                    'nxos': ['show vlan'],
                    'iosxe': ['show vlan brief']
                }
            },
            'reports_directory': self.temp_dir,
            'output': {
                'site_boundary_pattern': '*-CORE-*'
            }
        }
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_complete_vlan_collection_and_reporting_workflow(self):
        """
        Test complete VLAN collection and reporting workflow
        
        Validates: Requirements 1.1, 4.1, 5.1, 10.1
        """
        # Create test devices with VLAN data
        test_devices = [
            {
                'hostname': 'SW01-CORE-01',
                'ip': '192.168.1.10',
                'platform': 'ios',
                'vlan_output': """VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/1, Fa0/2, Fa0/3, Fa0/4
10   VLAN0010                         active    Fa0/5, Fa0/6, Po1
20   VLAN0020                         active    Fa0/7, Fa0/8
100  Management                       active    Fa0/9"""
            },
            {
                'hostname': 'SW02-CORE-01',
                'ip': '192.168.1.11',
                'platform': 'nxos',
                'vlan_output': """VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Eth1/1, Eth1/2, Eth1/3
10   VLAN0010                         active    Eth1/4, Eth1/5, Po10
30   VLAN0030                         active    Eth1/6, Eth1/7, Eth1/8"""
            }
        ]
        
        # Mock connection manager and device connections
        mock_connections = {}
        for device in test_devices:
            mock_conn = Mock()
            mock_conn.send_command.return_value = device['vlan_output']
            mock_connections[f"{device['hostname']}_{device['ip']}"] = mock_conn
        
        # Create device collector with mocked connections
        device_collector = DeviceCollector(self.config)
        
        # Create VLAN collector
        vlan_collector = VLANCollector(self.config)
        
        # Create Excel generator
        excel_generator = ExcelReportGenerator(self.config)
        
        # Simulate device discovery with VLAN collection
        inventory = {}
        
        for device in test_devices:
            device_key = f"{device['hostname']}_{device['ip']}"
            
            # Create device info
            device_info = DeviceInfo(
                hostname=device['hostname'],
                ip_address=device['ip'],
                platform=device['platform'],
                connection_status='success'
            )
            
            # Mock connection for VLAN collection
            mock_connection = mock_connections[device_key]
            
            # Collect VLAN information
            with patch.object(vlan_collector, '_get_device_connection', return_value=mock_connection):
                vlan_result = vlan_collector.collect_vlan_information(device_info)
            
            # Verify VLAN collection succeeded
            assert vlan_result.success, f"VLAN collection should succeed for {device['hostname']}"
            assert len(vlan_result.vlans) > 0, f"Should collect VLANs for {device['hostname']}"
            
            # Add to inventory
            inventory[device_key] = {
                'hostname': device['hostname'],
                'ip_address': device['ip'],
                'platform': device['platform'],
                'connection_status': 'success',
                'vlans': vlan_result.vlans,
                'neighbors': []
            }
        
        # Generate discovery report with VLAN data
        discovery_results = {
            'total_devices': len(test_devices),
            'successful_connections': len(test_devices),
            'failed_connections': 0,
            'start_time': '2024-01-01 10:00:00',
            'end_time': '2024-01-01 11:00:00',
            'duration': '1:00:00'
        }
        
        seed_devices = [f"{device['hostname']}:{device['ip']}" for device in test_devices]
        
        # Generate reports
        with patch('openpyxl.Workbook.save'), \
             patch('openpyxl.Workbook.close'):
            
            report_files = excel_generator.generate_discovery_report(
                inventory, discovery_results, seed_devices
            )
        
        # Verify reports were generated
        assert len(report_files) > 0, "Should generate at least one report file"
        
        # Verify VLAN data is properly structured
        for device_key, device_data in inventory.items():
            vlans = device_data.get('vlans', [])
            for vlan in vlans:
                assert isinstance(vlan, VLANInfo), "VLAN data should be VLANInfo objects"
                assert 1 <= vlan.vlan_id <= 4094, "VLAN ID should be in valid range"
                assert vlan.vlan_name, "VLAN should have a name"
                assert vlan.port_count >= 0, "Port count should be non-negative"
                assert vlan.portchannel_count >= 0, "PortChannel count should be non-negative"
    
    def test_graceful_partial_failure_handling(self):
        """
        Test graceful handling of partial failures in VLAN collection
        
        Validates: Requirements 5.4
        """
        # Create test scenario with mixed success/failure
        test_devices = [
            {
                'hostname': 'SW01-SUCCESS',
                'ip': '192.168.1.10',
                'platform': 'ios',
                'should_succeed': True,
                'vlan_output': """VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/1, Fa0/2
10   VLAN0010                         active    Fa0/3, Fa0/4"""
            },
            {
                'hostname': 'SW02-FAILURE',
                'ip': '192.168.1.11',
                'platform': 'ios',
                'should_succeed': False,
                'error': 'Connection timeout'
            },
            {
                'hostname': 'SW03-PARTIAL',
                'ip': '192.168.1.12',
                'platform': 'ios',
                'should_succeed': True,
                'vlan_output': 'Invalid output format'  # Will cause parsing error
            }
        ]
        
        # Create VLAN collector
        vlan_collector = VLANCollector(self.config)
        
        # Create Excel generator
        excel_generator = ExcelReportGenerator(self.config)
        
        inventory = {}
        successful_collections = 0
        failed_collections = 0
        
        for device in test_devices:
            device_key = f"{device['hostname']}_{device['ip']}"
            
            device_info = DeviceInfo(
                hostname=device['hostname'],
                ip_address=device['ip'],
                platform=device['platform'],
                connection_status='success'
            )
            
            if device['should_succeed'] and 'VLAN' in device.get('vlan_output', ''):
                # Mock successful connection
                mock_connection = Mock()
                mock_connection.send_command.return_value = device['vlan_output']
                
                with patch.object(vlan_collector, '_get_device_connection', return_value=mock_connection):
                    vlan_result = vlan_collector.collect_vlan_information(device_info)
                
                if vlan_result.success:
                    successful_collections += 1
                else:
                    failed_collections += 1
                
                inventory[device_key] = {
                    'hostname': device['hostname'],
                    'ip_address': device['ip'],
                    'platform': device['platform'],
                    'connection_status': 'success',
                    'vlans': vlan_result.vlans,
                    'vlan_collection_status': 'success' if vlan_result.success else 'failed'
                }
            
            elif device['should_succeed']:
                # Mock parsing failure
                mock_connection = Mock()
                mock_connection.send_command.return_value = device['vlan_output']
                
                with patch.object(vlan_collector, '_get_device_connection', return_value=mock_connection):
                    vlan_result = vlan_collector.collect_vlan_information(device_info)
                
                failed_collections += 1
                
                inventory[device_key] = {
                    'hostname': device['hostname'],
                    'ip_address': device['ip'],
                    'platform': device['platform'],
                    'connection_status': 'success',
                    'vlans': [],
                    'vlan_collection_status': 'failed'
                }
            
            else:
                # Mock connection failure
                with patch.object(vlan_collector, '_get_device_connection', side_effect=Exception(device['error'])):
                    vlan_result = vlan_collector.collect_vlan_information(device_info)
                
                failed_collections += 1
                
                inventory[device_key] = {
                    'hostname': device['hostname'],
                    'ip_address': device['ip'],
                    'platform': device['platform'],
                    'connection_status': 'success',
                    'vlans': [],
                    'vlan_collection_status': 'failed'
                }
        
        # Verify mixed results
        assert successful_collections > 0, "Should have some successful VLAN collections"
        assert failed_collections > 0, "Should have some failed VLAN collections"
        
        # Generate report despite partial failures
        discovery_results = {
            'total_devices': len(test_devices),
            'successful_connections': len(test_devices),
            'failed_connections': 0
        }
        
        seed_devices = [f"{device['hostname']}:{device['ip']}" for device in test_devices]
        
        # Should still generate reports successfully
        with patch('openpyxl.Workbook.save'), \
             patch('openpyxl.Workbook.close'):
            
            report_files = excel_generator.generate_discovery_report(
                inventory, discovery_results, seed_devices
            )
        
        # Verify reports were generated despite failures
        assert len(report_files) > 0, "Should generate reports even with partial failures"
        
        # Verify inventory contains both successful and failed devices
        success_count = sum(1 for device_data in inventory.values() 
                          if device_data.get('vlan_collection_status') == 'success')
        failure_count = sum(1 for device_data in inventory.values() 
                          if device_data.get('vlan_collection_status') == 'failed')
        
        assert success_count > 0, "Should have successful VLAN collections in inventory"
        assert failure_count > 0, "Should have failed VLAN collections in inventory"
    
    def test_configuration_options_integration(self):
        """
        Test that VLAN collection configuration options work correctly
        """
        # Test with VLAN collection disabled
        disabled_config = self.config.copy()
        disabled_config['vlan_collection']['enabled'] = False
        
        device_info = DeviceInfo(
            hostname='TEST-DEVICE',
            ip_address='192.168.1.100',
            platform='ios',
            connection_status='success'
        )
        
        vlan_collector = VLANCollector(disabled_config)
        
        # Should skip VLAN collection when disabled
        result = vlan_collector.collect_vlan_information(device_info)
        
        # Verify collection was skipped
        assert not result.success, "VLAN collection should be skipped when disabled"
        assert len(result.vlans) == 0, "No VLANs should be collected when disabled"
        assert "disabled" in result.error_message.lower(), "Error message should indicate collection is disabled"