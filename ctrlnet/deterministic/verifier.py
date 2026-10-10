from typing import Dict, List, Any
import re

from ctrlnet.config import PredictionVerdict
from ctrlnet.deterministic.nvd_client import NVDClient
from ctrlnet.llm.schemas import CVEPrediction

class Verifier:
    """Verifies LLM predictions against deterministic data (NVD)."""

    def __init__(self, nvd_client: NVDClient = None):
        self.nvd_client = nvd_client or NVDClient()

    async def verify_cve_claims(self, predicted_cpe: str, predicted_cves: List[CVEPrediction]) -> Dict[str, Any]:
        """
        Verify a list of predicted CVEs against a predicted CPE.
        Returns a dictionary with verdicts for each CVE and overall verification stats.
        """
        results = {
            "cpe_valid": False,
            "cve_verdicts": {},
            "summary": {
                PredictionVerdict.CONFIRMED.value: 0,
                PredictionVerdict.UNVERIFIED_REAL.value: 0,
                PredictionVerdict.HALLUCINATED.value: 0,
                PredictionVerdict.MALFORMED.value: 0
            }
        }
        
        # 1. Validate CPE Format
        if not predicted_cpe or not predicted_cpe.startswith("cpe:2.3:"):
            # If CPE is completely malformed or missing, we can't confirm anything via CPE match.
            # We must verify each CVE individually to see if it even exists.
            pass
        else:
             results["cpe_valid"] = True

        # Fetch known CVEs for the CPE if valid
        known_cves = []
        if results["cpe_valid"]:
            known_cves_data = await self.nvd_client.search_cve(predicted_cpe)
            known_cves = [cve["id"] for cve in known_cves_data]

        # 2. Verify each predicted CVE
        for cve_pred in predicted_cves:
            cve_id = cve_pred.id.upper()
            verdict = PredictionVerdict.MALFORMED
            
            # Format check
            if not re.match(r'^CVE-\d{4}-\d{4,}$', cve_id):
                 verdict = PredictionVerdict.MALFORMED
            elif cve_id in known_cves:
                 verdict = PredictionVerdict.CONFIRMED
            else:
                 # It's not in the CPE's list. Does it exist at all?
                 exists = await self.nvd_client.verify_cve(cve_id)
                 if exists:
                     verdict = PredictionVerdict.UNVERIFIED_REAL
                 else:
                     verdict = PredictionVerdict.HALLUCINATED
                     
            results["cve_verdicts"][cve_id] = verdict.value
            results["summary"][verdict.value] += 1
            
        return results
