"""Gap completion request/response models."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class GapCompletionRequest(BaseModel):
    transcript: Optional[str] = None


class FieldSuggestion(BaseModel):
    field: str
    value: Any
    confidence: str = "low"  # "high", "medium", "low"
    reason: str = ""


class GapCompletionResponse(BaseModel):
    suggestions: list[FieldSuggestion] = Field(default_factory=list)
    message: str = ""