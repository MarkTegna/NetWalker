"""
Property-based tests for ExcelReportGenerator

Tests universal properties of Excel report generation functionality.
"""

import pytest
from hypothesis import given, strategies as st, assume
import os
import tempfile
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook
from netwalker.reports.excel_generator import ExcelReportGenerator


class TestExcelReportGeneratorProperties:
    """Property-based tests for ExcelReportGenerator functionality"""
    
    def create_test_config(self, temp_dir: str) -> dict:
        """Create test configuration with temporary directory"""
        return {
            'reports_directory': temp_dir
        }
    
    def create_test_inventory(self, devices: list) -> dict:
        """Create test device inventory"""
        inventory = {}
        for i, (hostname, ip_address, platform) in enumerate(devices):
            device_key = f"{hostname}:{ip_address}"
            inventory[device_key] = {
                'hostname': hostname,
                'ip_address': ip_address,
                'platform': platform,
                'software_version': f"Version {i+1}.0",
                'serial_number': f"SN{i+1:06d}",
                'hardware_model': f"Model-{platform}",
                'uptime': f"{i+1} days",
                'discovery_depth': i % 3,
                'discovery_method': 'cdp' if i % 2 == 0 else 'lldp',
                'parent_device': None if i == 0 else f"parent{i}:192.168.1.{i}",
                'discovery_timestamp': datetime.now().isoformat(),
                'connection_method': 'ssh' if i % 2 == 0 else 'telnet',
                'status': 'connected',
                'neighbors': [
                    {
                        'hostname': f"neighbor{i}_1",
                        'ip_address': f"192.168.{i+10}.1",
                        'protocol': 'cdp',
                        'local_interface': f"Gi0/{i}",
                        'remote_interface': f"Gi0/{i+1}",
                        'platform': 'IOS'
                    }
                ] if i < 3 else []  # Only first few devices have neighbors
            }
        return inventory
    
    @given(
        devices=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
                st.ip_addresses(v=4).map(str),
                st.sampled_from(['IOS', 'IOS-XE', 'NX-OS'])
            ),
            min_size=1, max_size=5,
            unique_by=lambda x: f"{x[0]}:{x[1]}"
        )
    )
    def test_excel_report_completeness_property(self, devices):
        """
        Property 14: Excel Report Completeness
        
        Generated Excel reports should contain all required sheets and data.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.create_test_config(temp_dir)
            generator = ExcelReportGenerator(config)
            
            # Create test data
            inventory = self.create_test_inventory(devices)
            discovery_results = {
                'discovery_time_seconds': 120.5,
                'total_devices': len(devices),
                'successful_connections': len(devices),
                'failed_connections': 0,
                'filtered_devices': 0,
                'boundary_devices': 0,
                'max_depth_reached': 2
            }
            seed_devices = [f"{devices[0][0]}:{devices[0][1]}"] if devices else []
            
            # Generate report
            filepath = generator.generate_discovery_report(inventory, discovery_results, seed_devices)
            
            # Property: File should be created
            assert os.path.exists(filepath), "Excel file should be created"
            
            # Property: File should be a valid Excel workbook
            workbook = load_workbook(filepath)
            
            # Property: Required sheets should exist
            sheet_names = workbook.sheetnames
            required_sheets = ["Discovery Summary", "Device Inventory", "Network Connections"]
            
            for required_sheet in required_sheets:
                assert required_sheet in sheet_names, f"Sheet '{required_sheet}' should exist"
            
            # Property: Device Inventory sheet should contain all devices
            device_sheet = workbook["Device Inventory"]
            
            # Count data rows (excluding header)
            data_rows = 0
            for row in device_sheet.iter_rows(min_row=2):
                if row[0].value:  # If first column has value
                    data_rows += 1
            
            assert data_rows == len(devices), f"Should have {len(devices)} device rows, found {data_rows}"
            
            workbook.close()
    
    @given(
        base_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
        extension=st.sampled_from(['xlsx', 'csv', 'txt'])
    )
    def test_timestamp_file_naming_property(self, base_name, extension):
        """
        Property 16: Timestamp-Based File Naming
        
        Generated filenames should include timestamps in YYYYMMDD-HH-MM format.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.create_test_config(temp_dir)
            generator = ExcelReportGenerator(config)
            
            # Generate filename
            filename = generator.get_timestamp_filename(base_name, extension)
            
            # Property: Filename should contain base name
            assert base_name in filename, f"Filename should contain base name '{base_name}'"
            
            # Property: Filename should contain extension
            assert filename.endswith(f".{extension}"), f"Filename should end with '.{extension}'"
            
            # Property: Filename should contain timestamp pattern
            # Format: base_name_YYYYMMDD-HH-MM.extension
            import re
            timestamp_pattern = r'\d{8}-\d{2}-\d{2}'
            assert re.search(timestamp_pattern, filename), "Filename should contain timestamp in YYYYMMDD-HH-MM format"
    
    @given(
        devices=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
                st.ip_addresses(v=4).map(str),
                st.sampled_from(['IOS', 'NX-OS'])
            ),
            min_size=1, max_size=3,
            unique_by=lambda x: f"{x[0]}:{x[1]}"
        )
    )
    def test_excel_formatting_standards_property(self, devices):
        """
        Property 15: Excel Formatting Standards
        
        Excel reports should have consistent professional formatting.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.create_test_config(temp_dir)
            generator = ExcelReportGenerator(config)
            
            # Create test data
            inventory = self.create_test_inventory(devices)
            discovery_results = {
                'discovery_time_seconds': 60.0,
                'total_devices': len(devices),
                'successful_connections': len(devices),
                'failed_connections': 0,
                'filtered_devices': 0,
                'boundary_devices': 0,
                'max_depth_reached': 1
            }
            seed_devices = [f"{devices[0][0]}:{devices[0][1]}"] if devices else []
            
            # Generate report
            filepath = generator.generate_discovery_report(inventory, discovery_results, seed_devices)
            
            # Load and check formatting
            workbook = load_workbook(filepath)
            
            # Check Device Inventory sheet formatting
            device_sheet = workbook["Device Inventory"]
            
            # Property: Headers should be in row 1
            header_row = list(device_sheet.iter_rows(min_row=1, max_row=1))[0]
            
            for cell in header_row:
                if cell.value:  # If cell has content
                    # Property: Header cells should have bold font
                    assert cell.font.bold, f"Header cell {cell.coordinate} should be bold"
                    
                    # Property: Header cells should have fill color
                    assert cell.fill.start_color.rgb, f"Header cell {cell.coordinate} should have background color"
            
            # Property: Columns should be auto-sized (width > 0)
            for column_letter in ['A', 'B', 'C', 'D']:
                width = device_sheet.column_dimensions[column_letter].width
                assert width > 0, f"Column {column_letter} should have width > 0"
            
            workbook.close()
    
    def test_master_inventory_generation_property(self):
        """
        Property: Master inventory should consolidate devices from multiple seeds
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.create_test_config(temp_dir)
            generator = ExcelReportGenerator(config)
            
            # Create inventories for multiple seeds
            devices1 = [("device1", "192.168.1.1", "IOS"), ("device2", "192.168.1.2", "IOS")]
            devices2 = [("device2", "192.168.1.2", "IOS"), ("device3", "192.168.1.3", "NX-OS")]
            
            inventory1 = self.create_test_inventory(devices1)
            inventory2 = self.create_test_inventory(devices2)
            
            all_inventories = {
                "seed1": inventory1,
                "seed2": inventory2
            }
            seed_devices = ["seed1", "seed2"]
            
            # Generate master inventory
            filepath = generator.generate_master_inventory(all_inventories, seed_devices)
            
            # Property: File should be created
            assert os.path.exists(filepath), "Master inventory file should be created"
            
            # Load and verify content
            workbook = load_workbook(filepath)
            
            # Property: Master inventory sheet should exist
            assert "Master Device Inventory" in workbook.sheetnames
            
            master_sheet = workbook["Master Device Inventory"]
            
            # Count unique devices (device2 appears in both inventories)
            unique_devices = set()
            for row in master_sheet.iter_rows(min_row=2):
                if row[0].value:  # Device key column
                    unique_devices.add(row[0].value)
            
            # Property: Should have 3 unique devices (device1, device2, device3)
            assert len(unique_devices) == 3, f"Should have 3 unique devices, found {len(unique_devices)}"
            
            workbook.close()
    
    def test_output_directory_creation_property(self):
        """
        Property: Output directory should be created if it doesn't exist
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use a subdirectory that doesn't exist yet
            reports_dir = os.path.join(temp_dir, "reports", "subdirectory")
            config = {'reports_directory': reports_dir}
            
            # Property: Directory should not exist initially
            assert not os.path.exists(reports_dir)
            
            # Create generator (should create directory)
            generator = ExcelReportGenerator(config)
            
            # Property: Directory should be created
            assert os.path.exists(reports_dir), "Reports directory should be created"
            assert os.path.isdir(reports_dir), "Reports path should be a directory"
    
    @given(
        num_devices=st.integers(min_value=0, max_value=3)
    )
    def test_empty_inventory_handling_property(self, num_devices):
        """
        Property: Generator should handle empty or minimal inventories gracefully
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.create_test_config(temp_dir)
            generator = ExcelReportGenerator(config)
            
            # Create minimal inventory
            devices = [(f"device{i}", f"192.168.1.{i+1}", "IOS") for i in range(num_devices)]
            inventory = self.create_test_inventory(devices)
            
            discovery_results = {
                'discovery_time_seconds': 10.0,
                'total_devices': num_devices,
                'successful_connections': num_devices,
                'failed_connections': 0,
                'filtered_devices': 0,
                'boundary_devices': 0,
                'max_depth_reached': 0
            }
            seed_devices = []
            
            # Property: Should not raise exception even with empty data
            try:
                filepath = generator.generate_discovery_report(inventory, discovery_results, seed_devices)
                
                # Property: File should still be created
                assert os.path.exists(filepath), "Excel file should be created even with minimal data"
                
                # Property: File should be valid Excel
                workbook = load_workbook(filepath)
                assert len(workbook.sheetnames) > 0, "Workbook should have at least one sheet"
                workbook.close()
                
            except Exception as e:
                pytest.fail(f"Generator should handle empty inventory gracefully, but raised: {e}")