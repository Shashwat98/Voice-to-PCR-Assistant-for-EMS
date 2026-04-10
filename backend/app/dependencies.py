"""FastAPI dependency providers — singleton service instances."""

from app.config import settings
from app.core.gap_detector import GapDetector
from app.core.session_manager import SessionManager
from app.services.asr.base import ASRService
from app.services.asr.whisper_local import WhisperLocalService
from app.services.extraction.base import ExtractionService
from app.services.llm.ollama_client import OllamaClient
from app.utils.logging import logger


_session_manager: SessionManager | None = None
_gap_detector: GapDetector | None = None
_ollama_client: OllamaClient | None = None
_asr_service: ASRService | None = None
_finetuned_extractor: ExtractionService | None = None


def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def get_gap_detector() -> GapDetector:
    global _gap_detector
    if _gap_detector is None:
        _gap_detector = GapDetector()
    return _gap_detector


def get_ollama_client() -> OllamaClient:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


def get_asr_service() -> ASRService:
    global _asr_service
    if _asr_service is None:
        _asr_service = WhisperLocalService(
            model_size=settings.whisper_model_size,
        )
    return _asr_service


def get_extraction_service() -> ExtractionService:
    global _finetuned_extractor
    if _finetuned_extractor is None:
        from app.services.extraction.finetuned_extractor import FineTunedExtractor
        _finetuned_extractor = FineTunedExtractor(
            model_path=settings.finetuned_model_path,
            device=settings.finetuned_model_device,
        )
    return _finetuned_extractor