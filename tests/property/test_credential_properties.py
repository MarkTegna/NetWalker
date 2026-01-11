"""
Property-based tests for credential management
Feature: network-topology-discovery, Property 23: Automatic Credential Encryption
"""

import os
import tempfile
import configparser
from hypothesis import given, strategies as st
import pytest
from netwalker.config import CredentialManager


@given(
    username=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
    password=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
)
def test_automatic_credential_encryption(username, password):
    """
    Feature: network-topology-discovery, Property 23: Automatic Credential Encryption
    For any plain text credentials in configuration files, the system should encrypt them using MD5 and remove plain text versions
    **Validates: Requirements 8.2**
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False, encoding='utf-8') as f:
        # Create credentials file with plain text password
        f.write(f"""[credentials]
username = {username}
password = {password}
""")
        temp_creds = f.name
    
    try:
        # Load credentials - this should trigger encryption
        cred_manager = CredentialManager(temp_creds)
        credentials = cred_manager.get_credentials()
        
        # Verify credentials were loaded
        assert credentials is not None, "Credentials should be loaded successfully"
        assert credentials.username == username, f"Username should match: expected {username}, got {credentials.username}"
        
        # Read the file back to verify encryption occurred
        config = configparser.ConfigParser()
        config.read(temp_creds)
        
        stored_password = config.get('credentials', 'password')
        
        # Password should now be encrypted (32 character MD5 hash)
        assert len(stored_password) == 32, f"Password should be 32-character MD5 hash, got {len(stored_password)} characters"
        assert all(c in '0123456789abcdef' for c in stored_password.lower()), "Password should be hexadecimal MD5 hash"
        assert stored_password != password, "Stored password should not be plain text"
        
    finally:
        os.unlink(temp_creds)


def test_credential_exposure_prevention():
    """
    Feature: network-topology-discovery, Property 24: Credential Exposure Prevention
    For any system output (logs, documentation, CLI), credentials should never be exposed in plain text
    **Validates: Requirements 8.3, 8.4**
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        # Create credentials file
        f.write("""[credentials]
username = testuser
password = secretpassword123
""")
        temp_creds = f.name
    
    try:
        cred_manager = CredentialManager(temp_creds)
        credentials = cred_manager.get_credentials()
        
        # Verify credentials object doesn't expose password in string representation
        cred_str = str(credentials)
        assert "secretpassword123" not in cred_str, "Plain text password should not appear in string representation"
        
        # Verify credentials object doesn't expose password in repr
        cred_repr = repr(credentials)
        assert "secretpassword123" not in cred_repr, "Plain text password should not appear in repr"
        
    finally:
        os.unlink(temp_creds)


@given(st.text(min_size=32, max_size=32, alphabet='0123456789abcdef'))
def test_encrypted_credential_detection(encrypted_password):
    """
    Property test: For any 32-character hexadecimal string, it should be detected as encrypted
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write(f"""[credentials]
username = testuser
password = {encrypted_password}
""")
        temp_creds = f.name
    
    try:
        cred_manager = CredentialManager(temp_creds)
        
        # Should detect as encrypted and not modify
        config_before = configparser.ConfigParser()
        config_before.read(temp_creds)
        password_before = config_before.get('credentials', 'password')
        
        # Load credentials
        credentials = cred_manager.get_credentials()
        
        # Read config after
        config_after = configparser.ConfigParser()
        config_after.read(temp_creds)
        password_after = config_after.get('credentials', 'password')
        
        # Password should remain unchanged (already encrypted)
        assert password_before == password_after, "Already encrypted password should not be modified"
        assert password_after == encrypted_password, "Encrypted password should remain as provided"
        
    finally:
        os.unlink(temp_creds)


def test_missing_credentials_file_handling():
    """
    Test graceful handling of missing credentials file
    """
    non_existent_file = "non_existent_credentials.ini"
    
    # Ensure file doesn't exist
    if os.path.exists(non_existent_file):
        os.unlink(non_existent_file)
    
    cred_manager = CredentialManager(non_existent_file)
    credentials = cred_manager.get_credentials()
    
    # Should return None for missing file
    assert credentials is None, "Should return None for missing credentials file"


def test_credential_format_support():
    """
    Feature: network-topology-discovery, Property 22: Credential Format Support
    For any credential configuration (encrypted or plain text), the system should correctly process and use the credentials
    **Validates: Requirements 7.5**
    """
    # Test plain text format
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write("""[credentials]
username = plainuser
password = plainpass
""")
        plain_creds = f.name
    
    # Test encrypted format (MD5 of "encryptedpass")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write("""[credentials]
username = encrypteduser
password = 5d41402abc4b2a76b9719d911017c592
""")
        encrypted_creds = f.name
    
    try:
        # Test plain text credentials
        plain_manager = CredentialManager(plain_creds)
        plain_credentials = plain_manager.get_credentials()
        assert plain_credentials is not None, "Plain text credentials should be loaded"
        assert plain_credentials.username == "plainuser", "Plain text username should match"
        
        # Test encrypted credentials
        encrypted_manager = CredentialManager(encrypted_creds)
        encrypted_credentials = encrypted_manager.get_credentials()
        assert encrypted_credentials is not None, "Encrypted credentials should be loaded"
        assert encrypted_credentials.username == "encrypteduser", "Encrypted username should match"
        
    finally:
        os.unlink(plain_creds)
        os.unlink(encrypted_creds)