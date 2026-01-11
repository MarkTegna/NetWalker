"""
Property-based tests for OutputManager

Tests universal properties of output directory management functionality.
"""

import pytest
from hypothesis import given, strategies as st
import os
import tempfile
from pathlib import Path
from datetime import datetime

from netwalker.output.output_manager import OutputManager


class TestOutputManagerProperties:
    """Property-based tests for OutputManager functionality"""
    
    @given(
        reports_dir=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
        logs_dir=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))
    )
    def test_configurable_directory_usage_property(self, reports_dir, logs_dir):
        """
        Property 31: Configurable Output Directory Usage
        
        OutputManager should use configured directories when provided.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirectories within temp directory
            reports_path = os.path.join(temp_dir, reports_dir)
            logs_path = os.path.join(temp_dir, logs_dir)
            
            config = {
                'reports_directory': reports_path,
                'logs_directory': logs_path
            }
            
            output_manager = OutputManager(config)
            
            # Property: Should use configured directories
            assert output_manager.get_reports_directory() == str(Path(reports_path).resolve())
            assert output_manager.get_logs_directory() == str(Path(logs_path).resolve())
            
            # Property: Configured directories should be created
            assert os.path.exists(reports_path), "Reports directory should be created"
            assert os.path.exists(logs_path), "Logs directory should be created"
            assert os.path.isdir(reports_path), "Reports path should be a directory"
            assert os.path.isdir(logs_path), "Logs path should be a directory"
    
    def test_default_directory_behavior_property(self):
        """
        Property 32: Default Directory Behavior
        
        OutputManager should use default directories when not configured.
        """
        config = {}  # Empty config - should use defaults
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory to test relative paths
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                output_manager = OutputManager(config)
                
                # Property: Should use default directory names
                reports_dir = output_manager.get_reports_directory()
                logs_dir = output_manager.get_logs_directory()
                
                assert 'reports' in reports_dir, "Default reports directory should contain 'reports'"
                assert 'logs' in logs_dir, "Default logs directory should contain 'logs'"
                
                # Property: Default directories should be created
                assert os.path.exists(reports_dir), "Default reports directory should be created"
                assert os.path.exists(logs_dir), "Default logs directory should be created"
                
            finally:
                os.chdir(original_cwd)
    
    @given(
        directory_levels=st.integers(min_value=1, max_value=3),
        directory_names=st.lists(
            st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
            min_size=1, max_size=3
        )
    )
    def test_automatic_directory_creation_property(self, directory_levels, directory_names):
        """
        Property 33: Automatic Directory Creation
        
        OutputManager should create nested directories automatically.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested directory path
            nested_path = temp_dir
            for i in range(min(directory_levels, len(directory_names))):
                nested_path = os.path.join(nested_path, directory_names[i])
            
            reports_path = os.path.join(nested_path, 'reports')
            logs_path = os.path.join(nested_path, 'logs')
            
            # Property: Directories should not exist initially
            assert not os.path.exists(reports_path), "Reports directory should not exist initially"
            assert not os.path.exists(logs_path), "Logs directory should not exist initially"
            
            config = {
                'reports_directory': reports_path,
                'logs_directory': logs_path
            }
            
            # Create OutputManager (should create directories)
            output_manager = OutputManager(config)
            
            # Property: Nested directories should be created automatically
            assert os.path.exists(reports_path), "Nested reports directory should be created"
            assert os.path.exists(logs_path), "Nested logs directory should be created"
            assert os.path.isdir(reports_path), "Reports path should be a directory"
            assert os.path.isdir(logs_path), "Logs path should be a directory"
    
    @given(
        base_name=st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
        extension=st.sampled_from(['txt', 'log', 'xlsx', 'csv'])
    )
    def test_timestamped_filename_format_property(self, base_name, extension):
        """
        Property: Timestamped filenames should follow YYYYMMDD-HH-MM format
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {'reports_directory': temp_dir}
            output_manager = OutputManager(config)
            
            # Generate timestamped filename
            filename = output_manager.create_timestamped_filename(base_name, extension)
            
            # Property: Filename should contain base name
            assert base_name in filename, f"Filename should contain base name '{base_name}'"
            
            # Property: Filename should have correct extension
            assert filename.endswith(f".{extension}"), f"Filename should end with '.{extension}'"
            
            # Property: Filename should contain timestamp in correct format
            import re
            timestamp_pattern = r'\d{8}-\d{2}-\d{2}'
            assert re.search(timestamp_pattern, filename), "Filename should contain timestamp in YYYYMMDD-HH-MM format"
            
            # Property: Timestamp should be current (within reasonable range)
            current_time = datetime.now()
            current_timestamp = current_time.strftime("%Y%m%d-%H-%M")
            
            # Extract timestamp from filename
            match = re.search(timestamp_pattern, filename)
            if match:
                file_timestamp = match.group()
                # Should be same or very close (within 1 minute)
                assert file_timestamp == current_timestamp or abs(
                    int(file_timestamp.replace('-', '')) - int(current_timestamp.replace('-', ''))
                ) <= 1, "Timestamp should be current"
    
    @given(
        filenames=st.lists(
            st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
            min_size=1, max_size=5
        )
    )
    def test_file_path_generation_property(self, filenames):
        """
        Property: File path generation should be consistent and correct
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'reports_directory': os.path.join(temp_dir, 'reports'),
                'logs_directory': os.path.join(temp_dir, 'logs')
            }
            output_manager = OutputManager(config)
            
            for filename in filenames:
                # Test report file paths
                report_path = output_manager.get_report_filepath(filename)
                
                # Property: Report path should be in reports directory
                assert config['reports_directory'] in report_path, "Report path should be in reports directory"
                assert filename in report_path, f"Report path should contain filename '{filename}'"
                
                # Test log file paths
                log_path = output_manager.get_log_filepath(filename)
                
                # Property: Log path should be in logs directory
                assert config['logs_directory'] in log_path, "Log path should be in logs directory"
                assert filename in log_path, f"Log path should contain filename '{filename}'"
                
                # Property: Paths should be different for different directories
                assert report_path != log_path, "Report and log paths should be different"
    
    def test_directory_validation_property(self):
        """
        Property: Directory validation should correctly identify valid/invalid configurations
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Valid configuration
            valid_config = {
                'reports_directory': os.path.join(temp_dir, 'reports'),
                'logs_directory': os.path.join(temp_dir, 'logs')
            }
            
            valid_manager = OutputManager(valid_config)
            
            # Property: Valid configuration should pass validation
            assert valid_manager.validate_configuration(), "Valid configuration should pass validation"
            
            # Property: Directory info should be accurate
            dir_info = valid_manager.get_directory_info()
            
            assert 'reports' in dir_info, "Directory info should include reports"
            assert 'logs' in dir_info, "Directory info should include logs"
            
            for dir_name, info in dir_info.items():
                assert info['exists'], f"{dir_name} directory should exist"
                assert info['is_directory'], f"{dir_name} should be a directory"
                assert 'file_count' in info, f"{dir_name} info should include file count"
    
    @given(
        max_age_hours=st.integers(min_value=1, max_value=48)
    )
    def test_temp_file_cleanup_property(self, max_age_hours):
        """
        Property: Temp file cleanup should respect age limits
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {'temp_directory': temp_dir}
            output_manager = OutputManager(config)
            
            # Create some test files
            test_files = []
            for i in range(3):
                test_file = os.path.join(temp_dir, f"test_file_{i}.tmp")
                with open(test_file, 'w') as f:
                    f.write(f"Test content {i}")
                test_files.append(test_file)
            
            # Property: Files should exist before cleanup
            for test_file in test_files:
                assert os.path.exists(test_file), "Test file should exist before cleanup"
            
            # Run cleanup (with very high age limit, should not delete recent files)
            output_manager.cleanup_temp_files(max_age_hours=max_age_hours)
            
            # Property: Recent files should still exist (they're just created)
            for test_file in test_files:
                assert os.path.exists(test_file), "Recent test files should not be deleted"
    
    def test_path_normalization_property(self):
        """
        Property: Path normalization should handle various path formats consistently
        """
        test_paths = [
            './reports',
            '.\\reports',  # Windows style
            'reports',
            'reports/',
            'reports\\',
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)  # Change to temp directory for relative path testing
            
            normalized_paths = set()
            
            for path in test_paths:
                config = {'reports_directory': path}
                output_manager = OutputManager(config)
                normalized_path = output_manager.get_reports_directory()
                normalized_paths.add(normalized_path)
            
            # Property: All variations should normalize to the same path
            assert len(normalized_paths) == 1, f"All path variations should normalize to same path, got: {normalized_paths}"