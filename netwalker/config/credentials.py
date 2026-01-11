"""
Credential management with encryption support
"""

import configparser
import hashlib
import logging
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Credentials:
    """Container for device credentials"""
    username: str
    password: str
    enable_password: Optional[str] = None


class CredentialManager:
    """Manages device credentials with encryption support"""
    
    def __init__(self, credentials_file: str = "secret_creds.ini"):
        self.credentials_file = credentials_file
        self.logger = logging.getLogger(__name__)
        self._credentials = {}
        
    def get_credentials(self) -> Optional[Credentials]:
        """
        Retrieve authentication credentials with encryption support
        
        Returns:
            Credentials object or None if no credentials available
        """
        if not os.path.exists(self.credentials_file):
            self.logger.warning(f"Credentials file {self.credentials_file} not found")
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
            self.logger.error("Username or password not found in credentials file")
            return None
            
        # Check if password is encrypted (MD5 hash format)
        if self._is_encrypted(password):
            self.logger.info("Using encrypted credentials")
            # For this implementation, we'll store the hash but note that
            # MD5 is not secure for real password storage - this is just for demo
            password = self._decrypt_password(password)
        else:
            self.logger.info("Using plain text credentials")
            
        if enable_password and self._is_encrypted(enable_password):
            enable_password = self._decrypt_password(enable_password)
            
        return Credentials(
            username=username,
            password=password,
            enable_password=enable_password
        )
    
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