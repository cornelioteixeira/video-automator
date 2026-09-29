"""Composer 16:9 1080p24, baixo consumo: sem xfade, concat demuxer, ultrafast, threads=2."""
import os
from config import SETTINGS
from .utils import get_ffmpeg, run, audio_duration_sec

VF_NORM = (
    "scale=1920:1080:force_original_aspect_ratio=increase,"
    "crop=1920:1080,setsar=1,fps=24,format=yuv420p"
)

def _norm(ff: str, src: str, dst: str):
    r = run([ff, "-y", "-i", src,
             "-vf", VF_NORM,
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
             "-an", "-threads", str(SETTINGS.threads_ffmpeg), dst])
    if r.returncode != 0:
        raise RuntimeError("normalize falhou: " + r.stderr[-3000:])

def montar(clips: list[str], audio_mp3: str, srt: str | None, saida: str) -> str:
    ff = get_ffmpeg()
    os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)
    # Pasta isolada por video: evita reutilizar n_*.mp4 de outro video (bug que
    # fazia video01 e video02 parecerem identicos por causa do cache compartilhado).
    base = os.path.splitext(os.path.basename(saida))[0]
    work = os.path.join(os.path.dirname(saida) or ".", f"_norm_{base}")
    os.makedirs(work, exist_ok=True)

    # 1. normaliza cada clip Pexels (720p/1080p -> 1080p24 leve)
    # Sempre re-normaliza: garante que o mp4 final use os clips deste video,
    # nunca cache de outro video.
    normed = []
    for i, c in enumerate(clips):
        d = os.path.join(work, f"n_{i:02d}.mp4")
        _norm(ff, c, d)
        normed.append(d)

    # 2. concat demuxer (sem re-encode aqui, rapido e barato)
    lst = os.path.join(work, "video_list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in normed:
            f.write(f"file '{os.path.abspath(p)}'\n")
    joined = os.path.join(work, "joined.mp4")
    r = run([ff, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
    if r.returncode != 0:
        raise RuntimeError("concat video falhou: " + r.stderr[-3000:])

    # 3. ajusta ao audio: duracao total = narracao + 1.0s respiro
    dur = audio_duration_sec(audio_mp3) + 1.0
    # trava 2-3min (sem Shorts): se passar, corta; se faltar, loop do joined
    dur = max(SETTINGS.min_seconds, min(dur, SETTINGS.max_seconds))

    # 4. mux final + fade in/out simples + legendas queimadas
    # -stream_loop para estender se joined < dur; -shortest/-t para cortar se maior
    # fade: in 0.5s, out 0.5s (filtros baratos, sem xfade entre clips)
    vf = f"{VF_NORM},fade=t=in:st=0:d=0.5,fade=t=out:st={dur-0.5:.2f}:d=0.5"
    if srt and os.path.exists(srt):
        srt_esc = os.path.abspath(srt).replace("\\", "/").replace(":", "\\:")
        vf += f",subtitles='{srt_esc}':force_style='FontName=Arial,FontSize=22,PrimaryColour=&HFFFFFF,Outline=2,Shadow=0,MarginV=60'"

    cmd = [ff, "-y",
           "-stream_loop", "3", "-i", joined,
           "-i", audio_mp3,
           "-vf", vf,
           "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
           "-crf", "23", "-threads", str(SETTINGS.threads_ffmpeg),
           "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
           "-t", f"{dur:.2f}",
           "-movflags", "+faststart", "-shortest",
           saida]
    r = run(cmd)
    if r.returncode != 0:
        raise RuntimeError("mux final falhou: " + r.stderr[-4000:])
    return saida
