from typing import List, Optional
from pydantic import BaseModel, Field

class CVEPrediction(BaseModel):
    id: str = Field(..., description="The CVE ID (e.g., CVE-2020-15778)")
    reason: str = Field(..., description="Reasoning for why this CVE applies to the target based on the evidence")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0 that this CVE applies")
    evidence: List[str] = Field(..., description="Specific pieces of evidence from the input used to make this determination")

class LLMPrediction(BaseModel):
    service: str = Field(..., description="The identified service type (e.g., ssh, http, ftp)")
    product: Optional[str] = Field(..., description="The identified software product name (e.g., OpenSSH, nginx)")
    version: Optional[str] = Field(..., description="The identified software version (e.g., 8.2)")
    cpe: Optional[str] = Field(..., description="The inferred CPE 2.3 string (e.g., cpe:2.3:a:openbsd:openssh:8.2:*:*:*:*:*:*:*)")
    cves: List[CVEPrediction] = Field(default_factory=list, description="List of predicted CVEs applicable to the product/version")
    confidence: float = Field(..., description="Overall confidence score for the prediction between 0.0 and 1.0")
    missing_evidence: List[str] = Field(default_factory=list, description="Information missing from the input that would increase confidence")
    abstain: bool = Field(..., description="True if there is insufficient evidence to make a reliable identification")
    reasoning: str = Field(..., description="Explanation of the overall reasoning process")
