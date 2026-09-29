"""Resolve ffmpeg/ffprobe: sistema primeiro, fallback imageio-ffmpeg (sem instalar nada)."""
import shutil
import subprocess

def get_ffmpeg() -> str:
    sys_ff = shutil.which("ffmpeg")
    if sys_ff:
        return sys_ff
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:
        raise RuntimeError("ffmpeg nao encontrado. pip install imageio-ffmpeg") from e

def get_ffprobe() -> str | None:
    return shutil.which("ffprobe")

def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)

def audio_duration_sec(path: str) -> float:
    """Duracao sem ffprobe: mutagen -> fallback ffmpeg -i parse."""
    try:
        from mutagen.mp3 import MP3
        return float(MP3(path).info.length)
    except Exception:
        pass
    ff = get_ffmpeg()
    p = run([ff, "-i", path])
    # ffmpeg joga info no stderr
    import re
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", p.stderr)
    if not m:
        raise RuntimeError(f"nao foi possivel medir duracao de {path}")
    h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return h * 3600 + mi * 60 + s
