"""
URL validation and SSRF prevention for AccessLens backend.
Implements allowlist-based URL validation, private network blocking,
redirect handling, and loop detection.
"""

import re
import os
from typing import NamedTuple, Optional
from urllib.parse import urlparse, ParseResult
import ipaddress
import logging

logger = logging.getLogger(__name__)


class ValidationResult(NamedTuple):
    """Result of URL validation."""
    is_valid: bool
    error_message: Optional[str] = None
    final_url: Optional[str] = None
    redirect_count: int = 0


class URLValidator:
    """Validates URLs for SSRF prevention and security."""
    
    # Private network ranges
    PRIVATE_NETWORKS = [
        ipaddress.ip_network('10.0.0.0/8'),        # 10.0.0.0 - 10.255.255.255
        ipaddress.ip_network('172.16.0.0/12'),     # 172.16.0.0 - 172.31.255.255
        ipaddress.ip_network('192.168.0.0/16'),    # 192.168.0.0 - 192.168.255.255
        ipaddress.ip_network('127.0.0.0/8'),       # 127.0.0.0 - 127.255.255.255 (localhost)
        ipaddress.ip_network('169.254.0.0/16'),    # 169.254.0.0 - 169.254.255.255 (link-local)
        ipaddress.ip_network('fc00::/7'),          # IPv6 Unique Local Addresses
        ipaddress.ip_network('fe80::/10'),         # IPv6 Link-Local Addresses
        ipaddress.ip_network('::1/128'),           # IPv6 Loopback
        ipaddress.ip_network('::ffff:127.0.0.0/104'),  # IPv6-mapped IPv4 loopback
    ]
    
    def __init__(self, allowed_domains: Optional[list[str]] = None, max_redirects: int = 5, redirect_timeout: float = 5.0):
        """
        Initialize URL validator.
        
        Args:
            allowed_domains: List of allowed domain patterns (e.g., ["example.com", "*.example.com"]).
                           If None or empty, uses SSRF blocklist mode instead.
            max_redirects: Maximum number of redirects to follow (default: 5)
            redirect_timeout: Timeout in seconds for each redirect request (default: 5.0)
        """
        self.allowed_domains = allowed_domains or []
        self.max_redirects = max_redirects
        self.redirect_timeout = redirect_timeout
        self.logger = logger
    
    def validate(self, url: str) -> ValidationResult:
        """
        Validate a URL for SSRF vulnerabilities and security issues.
        
        Args:
            url: The URL to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        if not url:
            return ValidationResult(False, "URL cannot be empty")
        
        if len(url) > 2048:
            return ValidationResult(False, "URL exceeds maximum length of 2048 characters")
        
        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            return ValidationResult(False, f"Invalid URL format: {str(e)}")
        
        # Validate scheme
        if not parsed.scheme:
            return ValidationResult(False, "URL must include a scheme (http or https)")
        
        if parsed.scheme not in ('http', 'https'):
            return ValidationResult(False, f"Unsupported scheme: {parsed.scheme}. Only http and https are allowed.")
        
        # Validate hostname
        if not parsed.netloc:
            return ValidationResult(False, "URL must include a hostname")
        
        # Check for SSRF vulnerabilities
        ssrf_check = self._check_ssrf(parsed)
        if not ssrf_check[0]:
            return ValidationResult(False, ssrf_check[1])
        
        # Check allowlist if configured
        if self.allowed_domains:
            allowlist_check = self._check_allowlist(parsed.netloc)
            if not allowlist_check:
                return ValidationResult(False, f"Domain '{parsed.netloc}' is not in the allowed list")
        
        # Validate the URL can be reached (will attempt redirect following)
        final_url = url
        redirect_count = 0
        visited_urls = set()
        
        try:
            import requests
            
            # Follow redirects manually to detect loops and count them
            current_url = url
            for attempt in range(self.max_redirects + 1):
                if current_url in visited_urls:
                    return ValidationResult(False, f"Redirect loop detected after {redirect_count} redirects")
                visited_urls.add(current_url)
                
                try:
                    # HEAD request to avoid downloading content
                    response = requests.head(
                        current_url,
                        allow_redirects=False,
                        timeout=self.redirect_timeout,
                        verify=True
                    )
                    
                    # Check for redirect status codes
                    if response.status_code in (301, 302, 303, 307, 308):
                        if attempt >= self.max_redirects:
                            return ValidationResult(False, f"Too many redirects (max {self.max_redirects})")
                        
                        location = response.headers.get('Location')
                        if not location:
                            return ValidationResult(False, "Redirect without Location header")
                        
                        # Handle relative redirects
                        if location.startswith('/'):
                            parsed_current = urlparse(current_url)
                            current_url = f"{parsed_current.scheme}://{parsed_current.netloc}{location}"
                        elif not location.startswith(('http://', 'https://')):
                            parsed_current = urlparse(current_url)
                            current_url = f"{parsed_current.scheme}://{parsed_current.netloc}/{location}"
                        else:
                            current_url = location
                        
                        # Validate redirected URL doesn't go to private network
                        try:
                            parsed_redirect = urlparse(current_url)
                            ssrf_check = self._check_ssrf(parsed_redirect)
                            if not ssrf_check[0]:
                                return ValidationResult(False, f"Redirect to blocked URL: {ssrf_check[1]}")
                        except Exception as e:
                            return ValidationResult(False, f"Invalid redirect URL: {str(e)}")
                        
                        redirect_count += 1
                        final_url = current_url
                    else:
                        # Not a redirect, validation successful
                        final_url = current_url
                        break
                
                except requests.exceptions.Timeout:
                    return ValidationResult(False, f"URL request timed out after {self.redirect_timeout} seconds")
                except requests.exceptions.ConnectionError:
                    # Connection error is not necessarily a validation failure
                    # (domain might be valid but temporarily unreachable)
                    self.logger.info(f"Connection error validating URL (may be unreachable): {current_url}")
                    final_url = current_url
                    break
                except requests.exceptions.RequestException as e:
                    self.logger.warning(f"Error validating URL: {current_url}: {str(e)}")
                    final_url = current_url
                    break
        
        except ImportError:
            # If requests is not available, skip redirect validation
            self.logger.warning("requests library not available; skipping redirect validation")
            pass
        
        return ValidationResult(True, final_url=final_url, redirect_count=redirect_count)
    
    def _check_ssrf(self, parsed: ParseResult) -> tuple[bool, Optional[str]]:
        """
        Check for SSRF vulnerabilities in parsed URL.
        
        Returns:
            (is_safe, error_message) tuple
        """
        hostname = parsed.hostname
        
        if not hostname:
            return False, "URL has no hostname"
        
        # Try to parse as IP address
        try:
            ip = ipaddress.ip_address(hostname)
            if self._is_private_ip(ip):
                return False, f"Private IP address not allowed: {hostname}"
        except ValueError:
            # Not an IP, check as domain name
            # Block localhost by name
            if hostname.lower() in ('localhost', 'localhost.localdomain'):
                return False, "localhost is not allowed"
            
            # Block metadata endpoints
            if hostname in ('169.254.169.254', 'metadata.google.internal', 'metadata'):
                return False, f"Metadata endpoint not allowed: {hostname}"
        
        return True, None
    
    def _is_private_ip(self, ip: ipaddress.ip_address) -> bool:
        """Check if IP address is private or reserved."""
        for network in self.PRIVATE_NETWORKS:
            if ip in network:
                return True
        return False
    
    def _check_allowlist(self, netloc: str) -> bool:
        """
        Check if netloc (host:port) is in the allowlist.
        
        Supports wildcard domains (*.example.com).
        """
        # Extract hostname and port
        if ':' in netloc and not netloc.startswith('['):
            # IPv4 with port
            hostname = netloc.split(':')[0]
        elif netloc.startswith('['):
            # IPv6 - extract address without brackets
            if ']:' in netloc:
                hostname = netloc.split(']:')[0][1:]
            else:
                hostname = netloc.split(']')[0][1:]
        else:
            hostname = netloc
        
        # Check exact matches and wildcards
        for allowed in self.allowed_domains:
            if allowed == hostname:
                return True
            
            # Handle wildcard domains (*.example.com)
            if allowed.startswith('*.'):
                domain_suffix = allowed[2:]  # Remove "*."
                if hostname.endswith('.' + domain_suffix) or hostname == domain_suffix:
                    return True
        
        return False


# Convenience function for quick validation
def validate_url(url: str, allowed_domains: Optional[list[str]] = None) -> ValidationResult:
    """
    Quick URL validation using default settings.
    
    Args:
        url: The URL to validate
        allowed_domains: Optional list of allowed domains
        
    Returns:
        ValidationResult
    """
    validator = URLValidator(allowed_domains=allowed_domains)
    return validator.validate(url)
