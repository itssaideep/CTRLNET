"""
Prompt templates for service analysis.
"""

from ctrlnet.scanner.evidence_extractor import EvidenceRecord

SYSTEM_PROMPT_V1 = """You are an expert cybersecurity network analyst system called CTRLNET.
Your task is to analyze network reconnaissance data and identify the underlying software product, version, CPE, and potential vulnerabilities (CVEs).

You must adhere strictly to the requested JSON format.

Guidelines:
1. Reason carefully based ONLY on the provided evidence.
2. If evidence is missing, state it.
3. If there is not enough evidence to confidently identify the product, you MUST set "abstain" to true.
4. Do not hallucinate CVEs. Only list CVEs you know are associated with this specific product and version.
5. Provide a confidence score between 0.0 (complete guess) and 1.0 (absolute certainty).
"""

USER_PROMPT_V1 = """
Analyze the following network evidence:

Target ID: {target_id}
Port: {port}
Service Protocol: {service}
OS Hint: {os_hint}
Raw Banner / Data: {raw_banner}
Extracted Product: {extracted_product}
Extracted Version: {extracted_version}

Based on this evidence, determine:
1. The specific software product and vendor.
2. The exact version (if possible).
3. The correct CPE 2.3 string.
4. Any highly relevant known CVEs for this specific version.

Return your analysis as a structured JSON object.
"""

def build_prompt_v1(evidence: EvidenceRecord) -> str:
    """Build the complete v1 prompt for a given evidence record."""
    user_content = USER_PROMPT_V1.format(
        target_id=evidence.target_id,
        port=evidence.port,
        service=evidence.service,
        os_hint=evidence.os_hint or "Unknown",
        raw_banner=evidence.raw_banner or "None",
        extracted_product=evidence.extracted_product or "None",
        extracted_version=evidence.extracted_version or "None"
    )
    
    # We combine system and user prompt for models that might not strongly respect system prompts,
    # or pass them as a single user message if using the basic generate/chat api.
    return f"{SYSTEM_PROMPT_V1}\n{user_content}"
