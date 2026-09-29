"""Legenda viral estilo TikTok — APENAS Shorts.
Regras: 1 linha só, 3 palavras por vez, apenas palavras sendo ditas,
palavra ativa AMARELA, resto branca. Queimada no vídeo via ASS."""
import os
import re
from config import SETTINGS

ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Viral,Arial Black,92,&H00FFFFFF,&H000019FF,&H80000000,&H99000000,-1,0,0,0,100,100,0,0,1,4,0,2,60,60,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

YELLOW = r"{\c&H00D4FF&}"
WHITE = r"{\c&H00FFFFFF&}"


def _ass_ts(s: float) -> str:
    s = max(0.0, s)
    cs = int(round(s * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    sec, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{sec:02d}.{cs:02d}"


def _limpa(w: str) -> str:
    w = re.sub(r"\s+", " ", w).strip()
    return w.replace("{", "").replace("}", "")


def palavras_do_audio(audio_path: str, language: str = "pt") -> list[dict]:
    """Transcreve com word_timestamps=True. Retorna [{word, start, end}]."""
    from faster_whisper import WhisperModel
    model = WhisperModel(SETTINGS.whisper_model,
                         device=SETTINGS.whisper_device,
                         compute_type=SETTINGS.whisper_compute)
    segments, _ = model.transcribe(audio_path, language=language,
                                   word_timestamps=True, vad_filter=True)
    out = []
    for seg in segments:
        for w in (seg.words or []):
            txt = _limpa(w.word)
            if not txt:
                continue
            out.append({"word": txt, "start": float(w.start), "end": float(w.end)})
    return out


def build_ass_viral(palavras: list[dict], ass_path: str) -> str:
    """Janela deslizante de 3 palavras: evento por palavra ativa.
    Mostra [ativa(amarela) + prox 2(brancas)], 1 linha, só o que está sendo dito."""
    os.makedirs(os.path.dirname(ass_path) or ".", exist_ok=True)
    with open(ass_path, "w", encoding="utf-8") as fh:
        fh.write(ASS_HEAD)
        n = len(palavras)
        for i, p in enumerate(palavras):
            w0 = _limpa(p["word"])
            w1 = _limpa(palavras[i + 1]["word"]) if i + 1 < n else ""
            w2 = _limpa(palavras[i + 2]["word"]) if i + 2 < n else ""
            ini = p["start"]
            fim = palavras[i + 1]["start"] if i + 1 < n else p["end"] + 0.15
            fim = max(fim, ini + 0.12)
            linha = f"{YELLOW}{w0}{WHITE}"
            if w1:
                linha += f" {w1}"
            if w2:
                linha += f" {w2}"
            fh.write(f"Dialogue: 0,{_ass_ts(ini)},{_ass_ts(fim)},Viral,,0,0,0,,{linha}\n")
    return ass_path


def gerar_legenda_viral(audio_path: str, ass_path: str) -> str:
    palavras = palavras_do_audio(audio_path)
    if not palavras:
        raise RuntimeError("Whisper não retornou palavras — áudio vazio?")
    return build_ass_viral(palavras, ass_path)
