"""
Credential management with encryption support and interactive prompting
"""

import configparser
import hashlib
import logging
import os
import getpass
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Credentials:
    """Container for device credentials"""
    username: str
    password: str
    enable_password: Optional[str] = None


class CredentialManager:
    """Manages device credentials with encryption support and interactive prompting"""
    
    def __init__(self, credentials_file: str = "secret_creds.ini", cli_config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.credentials_file = self._find_credentials_file(credentials_file)
        self.cli_config = cli_config or {}
        self._credentials = {}
    
    def _find_credentials_file(self, filename: str) -> str:
        """
        Find credentials file in current directory or parent directory
        
        Search order:
        1. Current directory
        2. Parent directory (..\)
        
        Args:
            filename: Name of credentials file to find
            
        Returns:
            Path to credentials file (may not exist)
        """
        from pathlib import Path
        
        # Check current directory
        current_path = Path(filename)
        if current_path.exists():
            logging.info(f"Found {filename} in current directory")
            return str(current_path)
        
        # Check parent directory (..\)
        parent_path = Path("..") / filename
        if parent_path.exists():
            abs_path = parent_path.absolute()
            logging.info(f"Found {filename} in parent directory: {abs_path}")
            return str(abs_path)
        
        # Check grandparent directory (..\..\)
        grandparent_path = Path("..") / ".." / filename
        if grandparent_path.exists():
            abs_path = grandparent_path.absolute()
            logging.info(f"Found {filename} in grandparent directory: {abs_path}")
            return str(abs_path)
        
        # Return original filename (will be handled by exists check later)
        logging.debug(f"{filename} not found in current, parent, or grandparent directory")
        return filename
        
    def get_credentials(self) -> Optional[Credentials]:
        """
        Retrieve authentication credentials from multiple sources with fallback to interactive prompting
        
        Priority order:
        1. CLI arguments (--username, --password)
        2. Environment variables (NETWALKER_USERNAME, NETWALKER_PASSWORD)
        3. Configuration file (secret_creds.ini)
        4. Interactive prompting
        
        Returns:
            Credentials object or None if no credentials available
        """
        username = None
        password = None
        enable_password = None
        
        # 1. Check CLI arguments first (highest priority)
        if self.cli_config.get('username') and self.cli_config.get('password'):
            username = self.cli_config['username']
            password = self.cli_config['password']
            enable_password = self.cli_config.get('enable_password')
            self.logger.info("Using credentials from CLI arguments")
        
        # 2. Check environment variables
        elif os.getenv('NETWALKER_USERNAME') and os.getenv('NETWALKER_PASSWORD'):
            username = os.getenv('NETWALKER_USERNAME')
            password = os.getenv('NETWALKER_PASSWORD')
            enable_password = os.getenv('NETWALKER_ENABLE_PASSWORD')
            self.logger.info("Using credentials from environment variables")
        
        # 3. Check configuration file
        elif os.path.exists(self.credentials_file):
            file_creds = self._load_credentials_from_file()
            if file_creds:
                username = file_creds.username
                password = file_creds.password
                enable_password = file_creds.enable_password
                self.logger.info("Using credentials from configuration file")
        
        # 4. Interactive prompting (fallback)
        if not username or not password:
            self.logger.info("No credentials found in CLI, environment, or config file - prompting user")
            username, password, enable_password = self._prompt_for_credentials()
        
        if not username or not password:
            self.logger.error("No valid credentials available")
            return None
        
        return Credentials(
            username=username,
            password=password,
            enable_password=enable_password
        )
    
    def _load_credentials_from_file(self) -> Optional[Credentials]:
        """
        Load credentials from configuration file
        
        Returns:
            Credentials object or None if file not found or invalid
        """
        if not os.path.exists(self.credentials_file):
            self.logger.debug(f"Credentials file {self.credentials_file} not found")
            return None
            
        config = configparser.ConfigParser(interpolation=None)
        config.read(self.credentials_file)
        
        if not config.has_section('credentials'):
            self.logger.warning("No credentials section found in credentials file")
            return None
            
        # Check if credentials need encryption
        self._encrypt_plain_text_credentials(config)
        
        # Load credentials
        username = config.get('credentials', 'username', fallback=None)
        password = config.get('credentials', 'password', fallback=None)
        enable_password = config.get('credentials', 'enable_password', fallback=None)
        
        if not username or not password:
            self.logger.debug("Username or password not found in credentials file")
            return None
            
        # Check if password is encrypted (MD5 hash format)
        if self._is_encrypted(password):
            self.logger.debug("Decrypting password from file")
            password = self._decrypt_password(password)
        
        if enable_password and self._is_encrypted(enable_password):
            enable_password = self._decrypt_password(enable_password)
            
        return Credentials(
            username=username,
            password=password,
            enable_password=enable_password
        )
    
    def _prompt_for_credentials(self) -> tuple[str, str, Optional[str]]:
        """
        Interactively prompt user for credentials
        
        Returns:
            Tuple of (username, password, enable_password)
        """
        print("\n" + "="*50)
        print("NetWalker Credential Setup")
        print("="*50)
        print("No credentials found. Please provide device authentication details:")
        print()
        
        try:
            # Prompt for username
            username = input("Username: ").strip()
            if not username:
                print("Username cannot be empty")
                return "", "", None
            
            # Prompt for password (hidden input)
            password = getpass.getpass("Password: ")
            if not password:
                print("Password cannot be empty")
                return "", "", None
            
            # Check if enable password prompt is enabled
            prompt_enable = self.cli_config.get('enable_password', False)
            
            # Prompt for enable password only if enabled
            enable_password = None
            if prompt_enable:
                enable_prompt = getpass.getpass("Enable password (optional, press Enter to skip): ")
                enable_password = enable_prompt if enable_prompt else None
            
            print()
            print("Credentials entered successfully!")
            print("="*50)
            print()
            
            return username, password, enable_password
            
        except (KeyboardInterrupt, EOFError):
            print("\nCredential entry cancelled by user")
            return "", "", None
        except Exception as e:
            self.logger.error(f"Error during credential prompting: {e}")
            return "", "", None
    
    def _encrypt_plain_text_credentials(self, config: configparser.ConfigParser):
        """
        Convert plain text credentials to MD5 encrypted format and remove plain text
        
        Args:
            config: ConfigParser object with credentials
        """
        if not config.has_section('credentials'):
            return
            
        password = config.get('credentials', 'password', fallback=None)
        enable_password = config.get('credentials', 'enable_password', fallback=None)
        
        modified = False
        
        # Encrypt password if it's plain text
        if password and not self._is_encrypted(password):
            encrypted_password = self._encrypt_password(password)
            config.set('credentials', 'password', encrypted_password)
            modified = True
            self.logger.info("Encrypted plain text password")
            
        # Encrypt enable password if it's plain text
        if enable_password and not self._is_encrypted(enable_password):
            encrypted_enable = self._encrypt_password(enable_password)
            config.set('credentials', 'enable_password', encrypted_enable)
            modified = True
            self.logger.info("Encrypted plain text enable password")
            
        # Write back to file if modifications were made
        if modified:
            with open(self.credentials_file, 'w') as f:
                config.write(f)
            self.logger.info("Updated credentials file with encrypted passwords")
    
    def _encrypt_password(self, password: str) -> str:
        """
        Encrypt password using base64 encoding (simple reversible encoding)
        
        Args:
            password: Plain text password
            
        Returns:
            Base64 encoded password with prefix
        """
        import base64
        encoded = base64.b64encode(password.encode()).decode()
        return f"ENC:{encoded}"
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """
        Decrypt password from base64 encoding
        
        Args:
            encrypted_password: Base64 encoded password with ENC: prefix
            
        Returns:
            Decrypted password
        """
        import base64
        try:
            if encrypted_password.startswith("ENC:"):
                encoded_part = encrypted_password[4:]  # Remove "ENC:" prefix
                return base64.b64decode(encoded_part.encode()).decode()
            else:
                # Assume it's already plain text
                return encrypted_password
        except Exception as e:
            self.logger.error(f"Failed to decrypt password: {str(e)}")
            return encrypted_password
    
    def _is_encrypted(self, password: str) -> bool:
        """
        Check if password is in encrypted format
        
        Args:
            password: Password string to check
            
        Returns:
            True if password appears to be encrypted
        """
        return password.startswith("ENC:")
    
    def create_sample_credentials_file(self, username: str = "admin", password: str = "password"):
        """
        Create a sample credentials file for testing
        
        Args:
            username: Default username
            password: Default password
        """
        config_content = f"""# NetWalker Credentials File
# This file contains sensitive authentication information
# Keep this file secure and do not include in version control

[credentials]
username = {username}
password = {password}
# enable_password = enable_secret
"""
        
        with open(self.credentials_file, 'w') as f:
            f.write(config_content)
            
        self.logger.info(f"Sample credentials file created: {self.credentials_file}")
        self.logger.warning("Remember to update with actual credentials and keep file secure")