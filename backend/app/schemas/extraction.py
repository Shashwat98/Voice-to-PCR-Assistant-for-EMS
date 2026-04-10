"""Extraction request/response models."""

from pydantic import BaseModel, Field

from app.schemas.pcr import PCRDocument, PCRStateEnvelope


class ExtractionRequest(BaseModel):
    transcript: str


class ExtractionResponse(BaseModel):
    """Result of a single extraction run."""

    extracted_pcr: PCRDocument
    confidence_map: dict[str, float] = Field(default_factory=dict)
    model_used: str
    latency_ms: float
    pcr_state: PCRStateEnvelope