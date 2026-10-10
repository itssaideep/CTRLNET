import logging
from typing import Tuple, Dict, Any, Optional

from ctrlnet.config import config
from ctrlnet.scanner.evidence_extractor import EvidenceRecord
from ctrlnet.llm.ollama_client import OllamaClient
from ctrlnet.llm.prompts.service_analysis import build_prompt_v1
from ctrlnet.llm.schemas import LLMPrediction
from ctrlnet.llm.parser import LLMParser

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """Orchestrates LLM inference for service analysis."""

    def __init__(self, ollama_client: OllamaClient = None):
        self.client = ollama_client or OllamaClient()
        self.parser = LLMParser()

    async def analyze_evidence(self, evidence: EvidenceRecord, model: str = None, prompt_version: str = "v1") -> Tuple[Optional[LLMPrediction], str, Dict[str, Any]]:
        """
        Analyze network evidence using the LLM.
        Returns (parsed_prediction, raw_json_string, metrics).
        """
        model = model or config.ollama_model
        
        # Select prompt version
        if prompt_version == "v1":
             prompt = build_prompt_v1(evidence)
        else:
             raise ValueError(f"Unknown prompt version: {prompt_version}")
             
        try:
             parsed_dict, raw_content, metrics = await self.client.generate_structured(
                 model=model,
                 prompt=prompt,
                 schema=LLMPrediction
             )
             
             prediction = self.parser.parse_prediction(parsed_dict)
             
             # Convert ollama duration to ms for easier reading
             latency_ms = (metrics.get('eval_duration', 0) + metrics.get('load_duration', 0)) / 1_000_000
             metrics['total_latency_ms'] = latency_ms
             
             return prediction, raw_content, metrics
             
        except Exception as e:
             logger.error(f"LLM analysis failed for target {evidence.target_id}:{evidence.port} : {e}")
             return None, str(e), {}
