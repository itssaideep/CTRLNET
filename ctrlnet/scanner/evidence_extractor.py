from typing import Optional, Dict, Any
from pydantic import BaseModel

from ctrlnet.config import EvidenceLevel

class EvidenceRecord(BaseModel):
    """Structured representation of network evidence."""
    target_id: str
    service: str
    port: int
    raw_banner: Optional[str]
    extracted_product: Optional[str]
    extracted_version: Optional[str]
    os_hint: Optional[str]
    level: EvidenceLevel

def extract_evidence(nmap_service_data: Dict[str, Any], port: int, target_id: str, os_hint: str = None) -> EvidenceRecord:
    """
    Extract structured evidence from Nmap service scan data and assign an evidence level.
    """
    service_name = nmap_service_data.get('name', 'unknown')
    product = nmap_service_data.get('product', '')
    version = nmap_service_data.get('version', '')
    extrainfo = nmap_service_data.get('extrainfo', '')
    
    # Nmap sometimes puts the banner in 'extrainfo' or we might have grabbed it differently
    # Let's construct a synthetic 'raw_banner' based on what Nmap found if we don't have a real one
    raw_banner = f"{product} {version} {extrainfo}".strip()
    
    # Determine Evidence Level (E0-E4)
    level = EvidenceLevel.E0_INSUFFICIENT
    
    if product and version:
        level = EvidenceLevel.E4_EXACT
    elif product:
        level = EvidenceLevel.E3_MOSTLY_COMPLETE
    elif raw_banner:
        level = EvidenceLevel.E2_PARTIAL
    elif service_name != 'unknown':
         level = EvidenceLevel.E1_AMBIGUOUS
         
    return EvidenceRecord(
        target_id=target_id,
        service=service_name,
        port=port,
        raw_banner=raw_banner if raw_banner else None,
        extracted_product=product if product else None,
        extracted_version=version if version else None,
        os_hint=os_hint,
        level=level
    )
