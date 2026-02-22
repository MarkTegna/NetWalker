"""
Test error handling and logging for stack members sheet creation.
"""
import pytest
from unittest.mock import Mock, patch
from openpyxl import Workbook
from netwalker.reports.excel_generator import ExcelReportGenerator
from netwalker.connection.data_models import StackMemberInfo


class TestStackMembersErrorHandlingLogging:
    """Test error handling and logging in stack members sheet creation."""
    
    @pytest.fixture
    def generator(self):
        """Create ExcelReportGenerator instance."""
        config = {
            'reports_directory': './test_reports',
            'output': {
                'site_boundary_pattern': '*-CORE-*'
            }
        }
        return ExcelReportGenerator(config)
    
    @pytest.fixture
    def workbook(self):
        """Create a test workbook."""
        return Workbook()
    
    def test_logging_for_stack_with_no_members(self, generator, workbook, caplog):
        """Test that debug logging occurs when device is marked as stack but has no members."""
        inventory = {
            'device1': {
                'hostname': 'switch1.example.com',
                'ip_address': '10.0.0.1',
                'platform': 'cisco_ios',
                'is_stack': True,
                'stack_members': []  # Empty list
            }
        }
        
        with caplog.at_level('DEBUG'):
            generator._create_stack_members_sheet(workbook, inventory)
        
        # Verify debug log message was generated
        assert any('is marked as stack but has no stack members' in record.message 
                  for record in caplog.records)
        assert any('switch1' in record.message for record in caplog.records)
    
    def test_logging_for_missing_required_fields(self, generator, workbook, caplog):
        """Test that warning logging occurs when stack member has missing required fields."""
        member = StackMemberInfo(
            switch_number=None,  # Missing required field
            role='Member',
            priority=1,
            hardware_model='WS-C3850-48P',
            serial_number='FCW1234A5B6',
            mac_address='00:1a:2b:3c:4d:5e',
            software_version='16.9.1',
            state='Ready'
        )
        
        inventory = {
            'device1': {
                'hostname': 'switch1.example.com',
                'ip_address': '10.0.0.1',
                'platform': 'cisco_ios',
                'is_stack': True,
                'stack_members': [member]
            }
        }
        
        with caplog.at_level('WARNING'):
            generator._create_stack_members_sheet(workbook, inventory)
        
        # Verify warning log message was generated
        assert any('Skipping stack member with missing required fields' in record.message 
                  for record in caplog.records)
        assert any('MISSING' in record.message for record in caplog.records)
    
    def test_logging_for_missing_optional_fields(self, generator, workbook, caplog):
        """Test that debug logging occurs when stack member has missing optional fields."""
        member = StackMemberInfo(
            switch_number=1,
            role='Member',
            priority=None,  # Missing optional field
            hardware_model='WS-C3850-48P',
            serial_number='FCW1234A5B6',
            mac_address=None,  # Missing optional field
            software_version=None,  # Missing optional field
            state='Ready'
        )
        
        inventory = {
            'device1': {
                'hostname': 'switch1.example.com',
                'ip_address': '10.0.0.1',
                'platform': 'cisco_ios',
                'is_stack': True,
                'stack_members': [member]
            }
        }
        
        with caplog.at_level('DEBUG'):
            generator._create_stack_members_sheet(workbook, inventory)
        
        # Verify debug log messages were generated
        assert any('Processing stack device' in record.message for record in caplog.records)
        assert any('Adding stack member to report' in record.message for record in caplog.records)
        assert any('has missing optional fields' in record.message for record in caplog.records)
        assert any('priority' in record.message for record in caplog.records)
        assert any('MAC address' in record.message for record in caplog.records)
        assert any('software version' in record.message for record in caplog.records)
    
    def test_logging_for_successful_processing(self, generator, workbook, caplog):
        """Test that debug logging occurs for successful stack member processing."""
        member = StackMemberInfo(
            switch_number=1,
            role='Master',
            priority=15,
            hardware_model='WS-C3850-48P',
            serial_number='FCW1234A5B6',
            mac_address='00:1a:2b:3c:4d:5e',
            software_version='16.9.1',
            state='Ready'
        )
        
        inventory = {
            'device1': {
                'hostname': 'switch1.example.com',
                'ip_address': '10.0.0.1',
                'platform': 'cisco_ios',
                'is_stack': True,
                'stack_members': [member]
            }
        }
        
        with caplog.at_level('DEBUG'):
            generator._create_stack_members_sheet(workbook, inventory)
        
        # Verify debug log messages were generated
        assert any('Processing stack device' in record.message and '1 members' in record.message
                  for record in caplog.records)
        assert any('Adding stack member to report' in record.message 
                  for record in caplog.records)
        assert any('Switch: 1' in record.message for record in caplog.records)
        assert any('Role: Master' in record.message for record in caplog.records)
