"""TTS via edge-tts (nuvem, RAM ~zero). Um mp3 por bloco + concat."""
import os
from config import SETTINGS
from .utils import get_ffmpeg, run

async def _sintetizar(texto: str, saida: str):
    import edge_tts
    t = edge_tts.Communicate(texto, voice=SETTINGS.tts_voice, rate=SETTINGS.tts_rate)
    await t.save(saida)

def sintetizar_blocos(textos: list[str], dest_dir: str) -> str:
    """Retorna voice_full.mp3 concatenado."""
    import asyncio
    os.makedirs(dest_dir, exist_ok=True)
    partes = []
    for i, t in enumerate(textos):
        out = os.path.join(dest_dir, f"voice_{i:02d}.mp3")
        if not (os.path.exists(out) and os.path.getsize(out) > 1000):
            asyncio.run(_sintetizar(t, out))
        partes.append(out)
    full = os.path.join(dest_dir, "voice_full.mp3")
    # concat via ffmpeg (demuxer, sem re-encode)
    lst = os.path.join(dest_dir, "concat_audio.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in partes:
            f.write(f"file '{os.path.abspath(p)}'\n")
    ff = get_ffmpeg()
    r = run([ff, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", full])
    if r.returncode != 0:
        raise RuntimeError("falha concat audio: " + r.stderr[-2000:])
    return full
