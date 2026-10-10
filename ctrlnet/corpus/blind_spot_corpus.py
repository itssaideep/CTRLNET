import json
from pathlib import Path
from typing import Dict, List, Any

from ctrlnet.config import EvidenceLevel
from ctrlnet.scanner.evidence_extractor import EvidenceRecord

class BlindSpotCorpus:
    """Generates degraded evidence variants for controlled testing."""

    def __init__(self):
        self.targets_dir = Path(__file__).parent / "targets"

    def load_target(self, target_id: str) -> Dict[str, Any]:
        """Load ground truth data for a specific target."""
        target_path = self.targets_dir / f"{target_id}.json"
        if not target_path.exists():
            raise FileNotFoundError(f"Target {target_id} not found in {self.targets_dir}")
            
        with open(target_path, 'r') as f:
            return json.load(f)
            
    def load_all_targets(self) -> List[Dict[str, Any]]:
        """Load all ground truth targets."""
        targets = []
        if not self.targets_dir.exists():
            return targets
            
        for file_path in self.targets_dir.glob("*.json"):
            with open(file_path, 'r') as f:
                targets.append(json.load(f))
        return targets

    def generate_variants(self, gt: Dict[str, Any]) -> Dict[str, EvidenceRecord]:
        """
        Generate degraded evidence variants (E4 to E0) for a given target.
        """
        
        base_kwargs = {
            "target_id": gt["target_id"],
            "service": gt["service"],
            "port": gt["port"],
            "os_hint": gt.get("os_hint")
        }
        
        product = gt["product"]
        version = gt["version"]
        base_banner = gt.get("base_banner") or gt.get("banner", "")
        
        variants = {}
        
        # E4 - Exact (Complete banner, extracted product and version)
        variants[EvidenceLevel.E4_EXACT.value] = EvidenceRecord(
            **base_kwargs,
            raw_banner=base_banner,
            extracted_product=product,
            extracted_version=version,
            level=EvidenceLevel.E4_EXACT
        )
        
        # E3 - Mostly Complete (Banner has no version, product identified but no version)
        # e.g., SSH-2.0-OpenSSH
        if gt["service"] == "ssh":
             e3_banner = "SSH-2.0-OpenSSH"
        elif gt["service"] == "http":
             e3_banner = f"{product} (Ubuntu)"
        else:
             e3_banner = product
             
        variants[EvidenceLevel.E3_MOSTLY_COMPLETE.value] = EvidenceRecord(
            **base_kwargs,
            raw_banner=e3_banner,
            extracted_product=product,
            extracted_version=None,
            level=EvidenceLevel.E3_MOSTLY_COMPLETE
        )
        
        # E2 - Partial (Generic banner, no Nmap extraction)
        # e.g., SSH-2.0-unknown
        if gt["service"] == "ssh":
             e2_banner = "SSH-2.0-unknown"
        elif gt["service"] == "http":
             e2_banner = "Server: WebServer"
        else:
             e2_banner = "Generic Service v2"
             
        variants[EvidenceLevel.E2_PARTIAL.value] = EvidenceRecord(
            **base_kwargs,
            raw_banner=e2_banner,
            extracted_product=None,
            extracted_version=None,
            level=EvidenceLevel.E2_PARTIAL
        )
        
        # E1 - Ambiguous (Misleading or conflicting)
        e1_banner = "Service-v1.0 (Embedded)"
        variants[EvidenceLevel.E1_AMBIGUOUS.value] = EvidenceRecord(
            **base_kwargs,
            raw_banner=e1_banner,
            extracted_product=None,
            extracted_version=None,
            level=EvidenceLevel.E1_AMBIGUOUS
        )
        
        # E0 - Insufficient
        variants[EvidenceLevel.E0_INSUFFICIENT.value] = EvidenceRecord(
            **base_kwargs,
            raw_banner=None,
            extracted_product=None,
            extracted_version=None,
            level=EvidenceLevel.E0_INSUFFICIENT
        )
        
        return variants
