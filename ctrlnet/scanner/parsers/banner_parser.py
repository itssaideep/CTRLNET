import re
from typing import Dict, Optional, Tuple

def parse_ssh_banner(banner: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse an SSH banner (e.g., 'SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.11')"""
    # Look for OpenSSH specifically
    match = re.search(r'OpenSSH[_-]?([\d\.]+[p\d]*)', banner, re.IGNORECASE)
    if match:
        return "OpenSSH", match.group(1)
        
    # Generic SSH-2.0-Software_Version
    match = re.search(r'SSH-\d\.\d-([A-Za-z0-9_-]+)_([\d\.]+)', banner)
    if match:
        return match.group(1), match.group(2)
        
    return None, None

def parse_http_server_header(header: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse an HTTP Server header (e.g., 'Apache/2.4.41 (Ubuntu)', 'nginx/1.18.0')"""
    # Apache
    match = re.search(r'Apache/([\d\.]+)', header, re.IGNORECASE)
    if match:
        return "Apache", match.group(1)
        
    # Nginx
    match = re.search(r'nginx/([\d\.]+)', header, re.IGNORECASE)
    if match:
        return "nginx", match.group(1)
        
    # Generic Server/Version
    match = re.search(r'^([A-Za-z0-9_-]+)/([\d\.]+)', header)
    if match:
        return match.group(1), match.group(2)
        
    # Just the product name
    match = re.search(r'^([A-Za-z0-9_-]+)', header)
    if match:
        return match.group(1), None
        
    return None, None

def parse_generic_banner(banner: str, service: str) -> Tuple[Optional[str], Optional[str]]:
    """Attempt generic parsing if protocol-specific parsing isn't available."""
    # Look for common version patterns (e.g., v1.2.3, version 4.5)
    version_match = re.search(r'(?:v|version)?\s*([\d]+(?:\.[\d]+)+)', banner, re.IGNORECASE)
    version = version_match.group(1) if version_match else None
    
    # Very naive product extraction (first word) - usually not great, rely on Nmap for product
    product_match = re.search(r'^([A-Za-z0-9]+)', banner)
    product = product_match.group(1) if product_match else None
    
    return product, version
