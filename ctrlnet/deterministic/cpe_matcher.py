from typing import List, Tuple, Optional

def generate_cpe_candidates(product: str, vendor: Optional[str] = None, version: Optional[str] = None) -> List[str]:
    """
    Generates candidate CPE 2.3 strings based on available product and version info.
    Format: cpe:2.3:a:<vendor>:<product>:<version>:*:*:*:*:*:*:*
    """
    candidates = []
    
    # Normalize product name (lowercase, replace spaces with underscores)
    norm_product = product.lower().replace(" ", "_").replace("-", "_")
    norm_vendor = vendor.lower().replace(" ", "_").replace("-", "_") if vendor else norm_product
    norm_version = version.lower() if version else "*"
    
    # Primary candidate
    cpe_base = f"cpe:2.3:a:{norm_vendor}:{norm_product}:{norm_version}:*:*:*:*:*:*:*"
    candidates.append(cpe_base)
    
    # If vendor wasn't explicitly provided, sometimes vendor is different from product
    # Add common variations
    if not vendor:
        common_vendors = {
            "openssh": "openbsd",
            "nginx": "f5",
            "httpd": "apache",
            "apache": "apache",
            "mysql": "oracle",
            "redis": "redis",
            "vsftpd": "vsftpd",
            "proftpd": "proftpd",
            "tomcat": "apache"
        }
        
        if norm_product in common_vendors:
            cpe_var = f"cpe:2.3:a:{common_vendors[norm_product]}:{norm_product}:{norm_version}:*:*:*:*:*:*:*"
            candidates.append(cpe_var)
            
        # Also try 'o' (OS) for some things
        cpe_os = f"cpe:2.3:o:{norm_product}:{norm_product}:{norm_version}:*:*:*:*:*:*:*"
        candidates.append(cpe_os)

    return list(set(candidates)) # Return unique candidates

def fuzzy_match_cpe(target_cpe: str, cpe_list: List[str]) -> Tuple[Optional[str], float]:
    """
    Find the closest matching CPE from a list of known valid CPEs.
    Returns (best_match_cpe, confidence_score)
    (Simplified placeholder for more advanced fuzzy matching)
    """
    if target_cpe in cpe_list:
        return target_cpe, 1.0
        
    # Split components
    target_parts = target_cpe.split(':')
    
    best_match = None
    best_score = 0.0
    
    for known_cpe in cpe_list:
        known_parts = known_cpe.split(':')
        
        # Check if product matches
        if len(target_parts) > 4 and len(known_parts) > 4:
            if target_parts[4] == known_parts[4]: # Product part
                score = 0.5
                if target_parts[3] == known_parts[3]: # Vendor
                    score += 0.2
                if len(target_parts) > 5 and len(known_parts) > 5 and target_parts[5] == known_parts[5]: # Version
                    score += 0.3
                    
                if score > best_score:
                    best_score = score
                    best_match = known_cpe
                    
    return best_match, best_score
