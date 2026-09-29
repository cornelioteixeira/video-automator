"""Config central. Longos 16:9 2-8min + Shorts 9:16 20-35s. Pexels como banco de video."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    pexels_api_key: str = os.getenv("PEXELS_API_KEY", "")
    tts_voice: str = os.getenv("TTS_VOICE", "pt-BR-AntonioNeural")
    tts_rate: str = os.getenv("TTS_RATE", "+0%")
    whisper_model: str = os.getenv("WHISPER_MODEL", "base")
    whisper_device: str = os.getenv("WHISPER_DEVICE", "cpu")
    whisper_compute: str = os.getenv("WHISPER_COMPUTE", "int8")
    # Upload: manual em youtube.com/upload (sem YouTube Data API por decisao do usuario)

    # Travas de formato: longos 16:9 + shorts 9:16
    width: int = 1920
    height: int = 1080
    fps: int = 24
    min_seconds: int = 120
    max_seconds: int = 480  # longos 2-8min (conversao 20% da estrategia)
    target_seconds: int = 150
    # Shorts: 1080x1920, 20-35s, loop >100% AVD
    shorts_width: int = 1080
    shorts_height: int = 1920
    shorts_min: int = 20
    shorts_max: int = 35
    shorts_target: int = 28
    threads_ffmpeg: int = 2  # limita CPU/RAM em maquina fraca

SETTINGS = Settings()
