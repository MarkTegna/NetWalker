"""
DNS Validator for NetWalker

Provides DNS validation, address resolution, and RFC1918 conflict detection.
Implements public IP detection, forward/reverse DNS testing, and Excel reporting.
"""

import logging
import socket
import subprocess
import ipaddress
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import concurrent.futures
import threading

logger = logging.getLogger(__name__)


@dataclass
class DNSValidationResult:
    """Result of DNS validation for a single device"""
    hostname: str
    ip_address: str
    forward_dns_success: bool
    forward_dns_resolved_ip: Optional[str]
    reverse_dns_success: bool
    reverse_dns_resolved_hostname: Optional[str]
    reverse_dns_hostname_mismatch: bool  # True if reverse DNS hostname doesn't match expected
    is_public_ip: bool
    ping_resolved_ip: Optional[str]
    ping_success: bool
    rfc1918_conflict: bool
    resolved_private_ip: Optional[str]
    validation_timestamp: datetime
    error_details: Optional[str]


class DNSValidator:
    """
    DNS Validator for network topology discovery.
    
    Features:
    - Public IP address detection and resolution
    - Forward and reverse DNS testing
    - RFC1918 conflict detection and resolution
    - DNS Excel report generation
    - Concurrent DNS validation processing
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize DNS Validator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.timeout = config.get('dns_timeout_seconds', 5)
        self.max_concurrent_dns = config.get('max_concurrent_dns', 10)
        self.enable_ping_resolution = config.get('enable_ping_resolution', True)
        
        # RFC1918 private address ranges
        self.rfc1918_networks = [
            ipaddress.IPv4Network('10.0.0.0/8'),
            ipaddress.IPv4Network('172.16.0.0/12'),
            ipaddress.IPv4Network('192.168.0.0/16')
        ]
        
        # Thread safety
        self._lock = threading.Lock()
        self._validation_results: Dict[str, DNSValidationResult] = {}
        
        logger.info(f"DNSValidator initialized with timeout={self.timeout}s, max_concurrent={self.max_concurrent_dns}")
    
    def validate_device_dns(self, hostname: str, ip_address: str) -> DNSValidationResult:
        """
        Validate DNS for a single device.
        
        Args:
            hostname: Device hostname
            ip_address: Device IP address
            
        Returns:
            DNS validation result
        """
        logger.debug(f"Validating DNS for {hostname}:{ip_address}")
        
        try:
            # Initialize result
            result = DNSValidationResult(
                hostname=hostname,
                ip_address=ip_address,
                forward_dns_success=False,
                forward_dns_resolved_ip=None,
                reverse_dns_success=False,
                reverse_dns_resolved_hostname=None,
                reverse_dns_hostname_mismatch=False,
                is_public_ip=False,
                ping_resolved_ip=None,
                ping_success=False,
                rfc1918_conflict=False,
                resolved_private_ip=None,
                validation_timestamp=datetime.now(),
                error_details=None
            )
            
            # Check if IP is public
            result.is_public_ip = self._is_public_ip(ip_address)
            
            # Perform forward DNS lookup
            result.forward_dns_success, result.forward_dns_resolved_ip = self._forward_dns_lookup(hostname)
            
            # Perform reverse DNS lookup
            result.reverse_dns_success, result.reverse_dns_resolved_hostname = self._reverse_dns_lookup(ip_address)
            
            # Validate reverse DNS hostname matches expected hostname
            if result.reverse_dns_success and result.reverse_dns_resolved_hostname:
                hostname_match = self._validate_hostname_match(hostname, result.reverse_dns_resolved_hostname)
                if not hostname_match:
                    result.reverse_dns_hostname_mismatch = True
                    # Log mismatch but don't fail the validation
                    logger.info(
                        f"Reverse DNS hostname mismatch for {hostname}: "
                        f"Expected '{hostname}', got '{result.reverse_dns_resolved_hostname}'"
                    )
            
            # If public IP, try ping resolution
            if result.is_public_ip and self.enable_ping_resolution:
                result.ping_success, result.ping_resolved_ip = self._ping_resolve_hostname(hostname)
                
                # Check for RFC1918 conflict
                if result.ping_resolved_ip and self._is_private_ip(result.ping_resolved_ip):
                    result.rfc1918_conflict = True
                    result.resolved_private_ip = result.ping_resolved_ip
            
            # Detect RFC1918 conflicts in forward DNS
            if (result.forward_dns_resolved_ip and 
                result.is_public_ip and 
                self._is_private_ip(result.forward_dns_resolved_ip)):
                result.rfc1918_conflict = True
                result.resolved_private_ip = result.forward_dns_resolved_ip
            
            logger.debug(f"DNS validation completed for {hostname}: "
                        f"forward={result.forward_dns_success}, reverse={result.reverse_dns_success}, "
                        f"public={result.is_public_ip}, conflict={result.rfc1918_conflict}")
            
            return result
            
        except Exception as e:
            logger.error(f"DNS validation failed for {hostname}:{ip_address}: {e}")
            result.error_details = str(e)
            return result
    
    def validate_devices_concurrent(self, devices: List[Tuple[str, str]]) -> Dict[str, DNSValidationResult]:
        """
        Validate DNS for multiple devices concurrently.
        
        Args:
            devices: List of (hostname, ip_address) tuples
            
        Returns:
            Dictionary of device_key -> DNSValidationResult
        """
        logger.info(f"Starting concurrent DNS validation for {len(devices)} devices")
        
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_dns) as executor:
            # Submit all validation tasks
            future_to_device = {
                executor.submit(self.validate_device_dns, hostname, ip_address): f"{hostname}:{ip_address}"
                for hostname, ip_address in devices
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_device):
                device_key = future_to_device[future]
                try:
                    result = future.result()
                    results[device_key] = result
                except Exception as e:
                    logger.error(f"DNS validation failed for {device_key}: {e}")
                    # Create error result
                    hostname, ip_address = device_key.split(':', 1)
                    results[device_key] = DNSValidationResult(
                        hostname=hostname,
                        ip_address=ip_address,
                        forward_dns_success=False,
                        forward_dns_resolved_ip=None,
                        reverse_dns_success=False,
                        reverse_dns_resolved_hostname=None,
                        reverse_dns_hostname_mismatch=False,
                        is_public_ip=False,
                        ping_resolved_ip=None,
                        ping_success=False,
                        rfc1918_conflict=False,
                        resolved_private_ip=None,
                        validation_timestamp=datetime.now(),
                        error_details=str(e)
                    )
        
        # Store results thread-safely
        with self._lock:
            self._validation_results.update(results)
        
        logger.info(f"Completed DNS validation for {len(results)} devices")
        return results
    
    def get_validation_results(self) -> Dict[str, DNSValidationResult]:
        """Get all DNS validation results"""
        with self._lock:
            return self._validation_results.copy()
    
    def get_rfc1918_conflicts(self) -> Dict[str, DNSValidationResult]:
        """Get devices with RFC1918 conflicts"""
        with self._lock:
            return {k: v for k, v in self._validation_results.items() if v.rfc1918_conflict}
    
    def get_resolved_private_addresses(self) -> Dict[str, str]:
        """
        Get mapping of device keys to resolved private IP addresses.
        
        Returns:
            Dictionary of device_key -> resolved_private_ip
        """
        resolved_addresses = {}
        with self._lock:
            for device_key, result in self._validation_results.items():
                if result.resolved_private_ip:
                    resolved_addresses[device_key] = result.resolved_private_ip
        return resolved_addresses
    
    def _is_public_ip(self, ip_address: str) -> bool:
        """Check if IP address is public (not RFC1918 private)"""
        try:
            ip = ipaddress.IPv4Address(ip_address)
            return not any(ip in network for network in self.rfc1918_networks)
        except (ipaddress.AddressValueError, ValueError):
            return False
    
    def _is_private_ip(self, ip_address: str) -> bool:
        """Check if IP address is RFC1918 private"""
        try:
            ip = ipaddress.IPv4Address(ip_address)
            return any(ip in network for network in self.rfc1918_networks)
        except (ipaddress.AddressValueError, ValueError):
            return False
    
    def _forward_dns_lookup(self, hostname: str) -> Tuple[bool, Optional[str]]:
        """
        Perform forward DNS lookup.
        
        Args:
            hostname: Hostname to resolve
            
        Returns:
            Tuple of (success, resolved_ip)
        """
        try:
            resolved_ip = socket.gethostbyname(hostname)
            return True, resolved_ip
        except (socket.gaierror, socket.herror, OSError) as e:
            logger.debug(f"Forward DNS lookup failed for {hostname}: {e}")
            return False, None
    
    def _reverse_dns_lookup(self, ip_address: str) -> Tuple[bool, Optional[str]]:
        """
        Perform reverse DNS lookup and validate hostname match.
        
        Args:
            ip_address: IP address to resolve
            
        Returns:
            Tuple of (success, resolved_hostname)
        """
        try:
            resolved_hostname = socket.gethostbyaddr(ip_address)[0]
            return True, resolved_hostname
        except (socket.gaierror, socket.herror, OSError) as e:
            logger.debug(f"Reverse DNS lookup failed for {ip_address}: {e}")
            return False, None
    
    def _validate_hostname_match(self, expected_hostname: str, dns_hostname: str) -> bool:
        """
        Validate that DNS hostname matches expected hostname.
        Compares the hostname before the first dot.
        
        Args:
            expected_hostname: Expected hostname from device
            dns_hostname: Hostname returned from DNS
            
        Returns:
            True if hostnames match, False otherwise
        """
        # Extract hostname before first dot
        expected_short = expected_hostname.split('.')[0].lower()
        dns_short = dns_hostname.split('.')[0].lower()
        
        match = expected_short == dns_short
        
        if not match:
            logger.warning(
                f"DNS hostname mismatch: Expected '{expected_hostname}' (short: '{expected_short}'), "
                f"but DNS returned '{dns_hostname}' (short: '{dns_short}')"
            )
        
        return match
    
    def _ping_resolve_hostname(self, hostname: str) -> Tuple[bool, Optional[str]]:
        """
        Ping hostname to resolve IP address (Windows compatible).
        
        Args:
            hostname: Hostname to ping
            
        Returns:
            Tuple of (success, resolved_ip)
        """
        try:
            # Use ping command to resolve hostname
            result = subprocess.run(
                ['ping', '-n', '1', hostname],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                # Parse ping output to extract IP address
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if 'Pinging' in line and '[' in line and ']' in line:
                        # Extract IP from "Pinging hostname [ip_address]"
                        start = line.find('[') + 1
                        end = line.find(']')
                        if start > 0 and end > start:
                            resolved_ip = line[start:end]
                            return True, resolved_ip
                
                # Alternative parsing for different ping output formats
                for line in output_lines:
                    if 'Reply from' in line:
                        # Extract IP from "Reply from ip_address:"
                        parts = line.split()
                        for part in parts:
                            if part.startswith('Reply') and len(parts) > 2:
                                ip_part = parts[2].rstrip(':')
                                try:
                                    ipaddress.IPv4Address(ip_part)
                                    return True, ip_part
                                except ipaddress.AddressValueError:
                                    continue
            
            return False, None
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as e:
            logger.debug(f"Ping resolution failed for {hostname}: {e}")
            return False, None
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of DNS validation results.
        
        Returns:
            Dictionary with validation statistics
        """
        with self._lock:
            total_devices = len(self._validation_results)
            if total_devices == 0:
                return {
                    'total_devices': 0,
                    'forward_dns_success': 0,
                    'reverse_dns_success': 0,
                    'public_ip_devices': 0,
                    'rfc1918_conflicts': 0,
                    'ping_resolutions': 0,
                    'validation_errors': 0
                }
            
            forward_success = sum(1 for r in self._validation_results.values() if r.forward_dns_success)
            reverse_success = sum(1 for r in self._validation_results.values() if r.reverse_dns_success)
            public_ips = sum(1 for r in self._validation_results.values() if r.is_public_ip)
            conflicts = sum(1 for r in self._validation_results.values() if r.rfc1918_conflict)
            ping_success = sum(1 for r in self._validation_results.values() if r.ping_success)
            errors = sum(1 for r in self._validation_results.values() if r.error_details)
            
            return {
                'total_devices': total_devices,
                'forward_dns_success': forward_success,
                'reverse_dns_success': reverse_success,
                'public_ip_devices': public_ips,
                'rfc1918_conflicts': conflicts,
                'ping_resolutions': ping_success,
                'validation_errors': errors,
                'forward_dns_success_rate': forward_success / total_devices * 100,
                'reverse_dns_success_rate': reverse_success / total_devices * 100
            }