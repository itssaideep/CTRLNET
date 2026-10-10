import logging
from typing import Dict, Any, Callable, Awaitable

from ctrlnet.config import PipelineStage, PredictionVerdict
from ctrlnet.scanner.evidence_extractor import EvidenceRecord
from ctrlnet.llm.llm_analyzer import LLMAnalyzer
from ctrlnet.llm.schemas import LLMPrediction
from ctrlnet.deterministic.verifier import Verifier
from ctrlnet.deterministic.cpe_matcher import generate_cpe_candidates

logger = logging.getLogger(__name__)

class HybridAnalyzer:
    """Orchestrates the full hybrid pipeline: Evidence -> LLM -> Verification"""

    def __init__(self, event_callback: Callable[[str, Dict[str, Any]], Awaitable[None]] = None):
        self.llm_analyzer = LLMAnalyzer()
        self.verifier = Verifier()
        self.event_callback = event_callback
        
    async def _emit(self, event_name: str, payload: Dict[str, Any]):
        if self.event_callback:
             try:
                 await self.event_callback(event_name, payload)
             except Exception as e:
                 logger.error(f"Error emitting event {event_name}: {e}")

    async def run_hybrid_pipeline(self, evidence: EvidenceRecord, model: str = None) -> Dict[str, Any]:
        """
        Execute the hybrid analysis pipeline for a single piece of evidence.
        """
        host = evidence.target_id
        port = evidence.port
        
        result = {
             "evidence": evidence.model_dump(),
             "llm_hypothesis": None,
             "deterministic_fallback": None,
             "verification": None,
             "final_status": PipelineStage.INSUFFICIENT.value
        }
        
        # 1. LLM Analysis
        await self._emit("llm_analysis_started", {"host": host, "port": port})
        prediction, raw_output, metrics = await self.llm_analyzer.analyze_evidence(evidence, model=model)
        
        if not prediction:
             await self._emit("failure_detected", {"host": host, "port": port, "reason": "LLM inference failed"})
             return result
             
        result["llm_hypothesis"] = {
             "prediction": prediction.model_dump(),
             "raw_output": raw_output,
             "metrics": metrics
        }
        
        await self._emit("llm_response", {
             "host": host, 
             "port": port, 
             "prediction": result["llm_hypothesis"]["prediction"]
        })
        
        # Check if LLM abstained
        if prediction.abstain or prediction.confidence < 0.3:
             result["final_status"] = PipelineStage.INSUFFICIENT.value
             await self._emit("service_complete", {"host": host, "port": port, "status": result["final_status"]})
             return result
             
        # 2. Verification
        await self._emit("verification_started", {"host": host, "port": port, "cpe": prediction.cpe})
        
        verification_results = await self.verifier.verify_cve_claims(
             predicted_cpe=prediction.cpe,
             predicted_cves=prediction.cves
        )
        
        result["verification"] = verification_results
        
        await self._emit("verification_done", {
             "host": host, 
             "port": port, 
             "results": verification_results
        })
        
        # 3. Final Verdict Determination
        # If CPE is valid and we have no hallucinations, we consider it verified.
        # If LLM claims CVEs that are hallucinations, we reject the hypothesis.
        # If no CVEs are claimed but CPE is valid, it's verified (just a secure version).
        
        hallucinated_count = verification_results["summary"][PredictionVerdict.HALLUCINATED.value]
        confirmed_count = verification_results["summary"][PredictionVerdict.CONFIRMED.value]
        
        if not verification_results["cpe_valid"]:
             result["final_status"] = PipelineStage.REJECTED.value
        elif hallucinated_count > 0:
             result["final_status"] = PipelineStage.REJECTED.value
        elif len(prediction.cves) > 0 and confirmed_count == 0:
             result["final_status"] = PipelineStage.REJECTED.value
        else:
             result["final_status"] = PipelineStage.VERIFIED.value
             
        await self._emit("service_complete", {"host": host, "port": port, "status": result["final_status"]})
        
        return result
