"""
Output Manager for NetWalker

Manages output directories and file organization for reports and logs.
Provides configurable directory structure with automatic creation.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OutputManager:
    """
    Manages output directories and file organization.
    
    Features:
    - Configurable output directories for reports and logs
    - Default directory behavior (./reports, ./logs)
    - Automatic directory creation
    - Path validation and normalization
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OutputManager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Get configured directories or use defaults
        self.reports_directory = self._normalize_path(
            config.get('reports_directory', './reports')
        )
        self.logs_directory = self._normalize_path(
            config.get('logs_directory', './logs')
        )
        
        # Create directories
        self._create_directories()
        
        logger.info(f"OutputManager initialized:")
        logger.info(f"  Reports: {self.reports_directory}")
        logger.info(f"  Logs: {self.logs_directory}")
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize and resolve path.
        
        Args:
            path: Input path string
            
        Returns:
            Normalized absolute path
        """
        # Convert to Path object for cross-platform handling
        path_obj = Path(path)
        
        # Resolve to absolute path
        resolved_path = path_obj.resolve()
        
        return str(resolved_path)
    
    def _create_directories(self):
        """Create all configured directories if they don't exist"""
        directories = [
            ('reports', self.reports_directory),
            ('logs', self.logs_directory)
        ]
        
        for dir_type, dir_path in directories:
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created {dir_type} directory: {dir_path}")
            except Exception as e:
                logger.error(f"Failed to create {dir_type} directory {dir_path}: {e}")
                raise
    
    def get_reports_directory(self) -> str:
        """Get the reports directory path"""
        return self.reports_directory
    
    def get_logs_directory(self) -> str:
        """Get the logs directory path"""
        return self.logs_directory
    
    def get_report_filepath(self, filename: str) -> str:
        """
        Get full path for a report file.
        
        Args:
            filename: Report filename
            
        Returns:
            Full path to report file
        """
        return os.path.join(self.reports_directory, filename)
    
    def get_log_filepath(self, filename: str) -> str:
        """
        Get full path for a log file.
        
        Args:
            filename: Log filename
            
        Returns:
            Full path to log file
        """
        return os.path.join(self.logs_directory, filename)
    
    def create_timestamped_filename(self, base_name: str, extension: str = "txt") -> str:
        """
        Create filename with timestamp in YYYYMMDD-HH-MM format.
        
        Args:
            base_name: Base name for the file
            extension: File extension (without dot)
            
        Returns:
            Timestamped filename
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H-%M")
        return f"{base_name}_{timestamp}.{extension}"
    
    def create_timestamped_report_path(self, base_name: str, extension: str = "xlsx") -> str:
        """
        Create full path for timestamped report file.
        
        Args:
            base_name: Base name for the report
            extension: File extension (without dot)
            
        Returns:
            Full path to timestamped report file
        """
        filename = self.create_timestamped_filename(base_name, extension)
        return self.get_report_filepath(filename)
    
    def create_timestamped_log_path(self, base_name: str, extension: str = "log") -> str:
        """
        Create full path for timestamped log file.
        
        Args:
            base_name: Base name for the log
            extension: File extension (without dot)
            
        Returns:
            Full path to timestamped log file
        """
        filename = self.create_timestamped_filename(base_name, extension)
        return self.get_log_filepath(filename)
    
    def ensure_directory_exists(self, directory_path: str):
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory_path: Path to directory
        """
        try:
            Path(directory_path).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory_path}: {e}")
            raise
    
    def get_directory_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all managed directories.
        
        Returns:
            Dictionary with directory information
        """
        directories = {
            'reports': self.reports_directory,
            'logs': self.logs_directory
        }
        
        info = {}
        for name, path in directories.items():
            path_obj = Path(path)
            info[name] = {
                'path': path,
                'exists': path_obj.exists(),
                'is_directory': path_obj.is_dir() if path_obj.exists() else False,
                'file_count': len(list(path_obj.iterdir())) if path_obj.exists() and path_obj.is_dir() else 0
            }
        
        return info
    
    def validate_configuration(self) -> bool:
        """
        Validate output manager configuration.
        
        Returns:
            True if configuration is valid
        """
        try:
            # Check if all directories can be created/accessed
            for directory in [self.reports_directory, self.logs_directory]:
                path_obj = Path(directory)
                
                # Try to create if it doesn't exist
                if not path_obj.exists():
                    path_obj.mkdir(parents=True, exist_ok=True)
                
                # Check if it's writable
                if not os.access(directory, os.W_OK):
                    logger.error(f"Directory not writable: {directory}")
                    return False
            
            logger.info("Output manager configuration validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Output manager configuration validation failed: {e}")
            return False