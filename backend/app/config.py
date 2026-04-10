"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PCR_", env_file=".env")

    # Server
    app_name: str = "Voice-to-PCR Assistant"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]

    # Local Whisper ASR
    whisper_model_size: str = "medium"

    # Local LLM (Ollama)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Fine-tuned model
    finetuned_model_path: str = "../models"
    finetuned_model_device: str = "cpu"

    # PCR State
    confidence_threshold: float = 0.5
    numeric_tolerance: int = 2

    # Audio
    max_audio_duration_sec: int = 300
    audio_buffer_interval_sec: float = 5.0

    # Evaluation
    eval_dataset_path: str = "data/medic-synthetic/test.json"


settings = Settings()