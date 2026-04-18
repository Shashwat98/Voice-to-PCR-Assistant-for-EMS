"""Extraction endpoints — transcript to structured PCR fields."""

from fastapi import APIRouter, HTTPException

from app.dependencies import get_extraction_service, get_session_manager
from app.schemas.extraction import ExtractionRequest, ExtractionResponse

router = APIRouter(prefix="/sessions/{session_id}", tags=["extraction"])


@router.post("/extract", response_model=ExtractionResponse)
async def extract_pcr(session_id: str, request: ExtractionRequest):
    """Run extraction on a transcript using the fine-tuned model."""
    session_mgr = get_session_manager()
    session = await session_mgr.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    extractor = get_extraction_service()

    result = await extractor.extract(request.transcript)

    pcr_state = session.pcr_manager.apply_extraction(
        extracted=result.pcr,
        confidence_map=result.confidence_map,
        model_name=result.model_name,
    )

    return ExtractionResponse(
        extracted_pcr=result.pcr,
        confidence_map=result.confidence_map,
        model_used=result.model_name,
        latency_ms=result.latency_ms,
        pcr_state=pcr_state,
    )