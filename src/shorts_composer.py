"""Composer Shorts 9:16 1080x1920, baixo consumo: ultrafast threads=2, sem xfade."""
import os
from config import SETTINGS
from .utils import get_ffmpeg, run, audio_duration_sec

VF_NORM_SHORTS = (
    "scale=1080:1920:force_original_aspect_ratio=increase,"
    "crop=1080:1920,setsar=1,fps=30,format=yuv420p"
)


def montar_shorts(clips: list[str], audio_mp3: str, saida: str,
                  ass_path: str | None = None) -> str:
    from .composer import _norm as _norm_h  # reuso do runner, com vf próprio abaixo
    ff = get_ffmpeg()
    os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)
    base = os.path.splitext(os.path.basename(saida))[0]
    work = os.path.join(os.path.dirname(saida) or ".", f"_norm_{base}")
    os.makedirs(work, exist_ok=True)

    normed = []
    for i, c in enumerate(clips):
        d = os.path.join(work, f"s_{i:02d}.mp4")
        r = run([ff, "-y", "-i", c, "-vf", VF_NORM_SHORTS,
                 "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                 "-an", "-threads", str(SETTINGS.threads_ffmpeg), d])
        if r.returncode != 0:
            raise RuntimeError("normalize shorts falhou: " + r.stderr[-3000:])
        normed.append(d)

    lst = os.path.join(work, "video_list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in normed:
            f.write(f"file '{os.path.abspath(p)}'\n")
    joined = os.path.join(work, "joined.mp4")
    r = run([ff, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
    if r.returncode != 0:
        raise RuntimeError("concat shorts falhou: " + r.stderr[-3000:])

    dur = audio_duration_sec(audio_mp3) + 0.5
    dur = max(SETTINGS.shorts_min, min(dur, SETTINGS.shorts_max))
    vf = f"{VF_NORM_SHORTS},fade=t=in:st=0:d=0.3,fade=t=out:st={dur-0.3:.2f}:d=0.3"
    if ass_path and os.path.exists(ass_path):
        ass_esc = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:")
        vf += f",subtitles='{ass_esc}'"
    cmd = [ff, "-y", "-stream_loop", "3", "-i", joined, "-i", audio_mp3,
           "-vf", vf, "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
           "-crf", "23", "-threads", str(SETTINGS.threads_ffmpeg),
           "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
           "-t", f"{dur:.2f}", "-movflags", "+faststart", "-shortest", saida]
    r = run(cmd)
    if r.returncode != 0:
        raise RuntimeError("mux shorts falhou: " + r.stderr[-4000:])
    return saida
