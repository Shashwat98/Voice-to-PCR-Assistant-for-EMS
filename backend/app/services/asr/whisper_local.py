"""Local Whisper ASR — no API calls, no PHI leaves the device."""

import tempfile
from typing import Optional

import torch
import whisper

from app.schemas.transcription import TranscriptionResponse, TranscriptionSegment
from app.services.asr.base import ASRService


class WhisperLocalService(ASRService):
    """On-device Whisper speech recognition."""

    def __init__(
        self,
        model_size: str = "medium",
        device: Optional[str] = None,
    ):
        if device is None:
            device = "cpu"

        self.device = device
        self.model = whisper.load_model(model_size, device=device)

    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
        language: str = "en",
    ) -> TranscriptionResponse:
        """Transcribe audio locally."""
        with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=True) as tmp:
            tmp.write(audio_data)
            tmp.flush()

            result = self.model.transcribe(
                tmp.name,
                language=language,
                verbose=False,
            )

        segments = [
            TranscriptionSegment(
                text=seg["text"],
                start=seg["start"],
                end=seg["end"],
            )
            for seg in result.get("segments", [])
        ]

        duration = segments[-1].end if segments else None

        return TranscriptionResponse(
            transcript_text=result["text"].strip(),
            segments=segments,
            language=language,
            duration_sec=duration,
            model_used=f"whisper-local-{self.model.dims.n_mels}",
        )