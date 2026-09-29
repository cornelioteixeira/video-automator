"""Legendas com faster-whisper cpu int8 (base ~500MB)."""
import os
from config import SETTINGS

def _fmt(s: float) -> str:
    ms = int(s * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    sec, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

def transcrever(audio_path: str, dest_srt: str, language: str = "pt") -> str:
    from faster_whisper import WhisperModel
    model = WhisperModel(SETTINGS.whisper_model,
                         device=SETTINGS.whisper_device,
                         compute_type=SETTINGS.whisper_compute)
    segments, _ = model.transcribe(audio_path, language=language,
                                   word_timestamps=False, vad_filter=True)
    os.makedirs(os.path.dirname(dest_srt) or ".", exist_ok=True)
    with open(dest_srt, "w", encoding="utf-8") as f:
        for i, s in enumerate(segments, 1):
            f.write(f"{i}\n{_fmt(s.start)} --> {_fmt(s.end)}\n{s.text.strip()}\n\n")
    return dest_srt
