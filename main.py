"""CLI: python main.py --tema "..." [--segundos 150] [--dry-run] [--skip-legendas] (upload manual no YouTube)"""
import argparse
import json
import os
import sys

from config import SETTINGS

def main():
    ap = argparse.ArgumentParser(description="Video-automator YouTube 16:9 2-3min | Pexels")
    ap.add_argument("--tema", required=True, help="Tema do video ex: 'como o sono afeta a memoria'")
    ap.add_argument("--segundos", type=int, default=150, help="Duracao alvo 120-200")
    ap.add_argument("--saida", default="output/final.mp4")
    ap.add_argument("--work", default="work/run_atual")
    ap.add_argument("--dry-run", action="store_true", help="So gera roteiro, sem baixar/sintetizar")
    ap.add_argument("--skip-legendas", action="store_true")
    ap.add_argument("--opcional-tts-offline", action="store_true",
                    help="Apenas informativo: use Kokoro-82M GGUF se quiser 100%% offline")
    args = ap.parse_args()

    segundos = max(SETTINGS.min_seconds, min(args.segundos, SETTINGS.max_seconds))
    os.makedirs(args.work, exist_ok=True)
    os.makedirs(os.path.dirname(args.saida) or ".", exist_ok=True)

    print(f"[1/5] Groq roteiro ({segundos}s): {args.tema}")
    from src.script_gen import gerar_roteiro
    roteiro = gerar_roteiro(args.tema, segundos)
    with open(os.path.join(args.work, "roteiro.json"), "w", encoding="utf-8") as f:
        json.dump(roteiro, f, ensure_ascii=False, indent=2)
    print(" Titulo:", roteiro.get("titulo"))

    if args.dry_run:
        print("dry-run ok ->", os.path.join(args.work, "roteiro.json"))
        return

    if not SETTINGS.pexels_api_key:
        sys.exit("ERRO: PEXELS_API_KEY vazio. Pegue em https://www.pexels.com/api/ e ponha no .env")

    print("[2/5] Pexels: 1 video landscape por bloco")
    from src.pexels_provider import baixar_para_blocos
    clips = baixar_para_blocos(roteiro["blocos"], SETTINGS.pexels_api_key,
                               os.path.join(args.work, "assets"))

    print("[3/5] edge-tts narracao")
    from src.tts import sintetizar_blocos
    textos = [roteiro.get("intro_pessoal", "")] + \
             [b["texto"] for b in roteiro["blocos"]] + \
             [roteiro.get("outro_pessoal", "")]
    textos = [t for t in textos if t]
    audio = sintetizar_blocos(textos, os.path.join(args.work, "audio"))
    from src.utils import audio_duration_sec
    print(f" audio {audio_duration_sec(audio):.1f}s")

    srt = None
    if not args.skip_legendas:
        print("[4/5] faster-whisper legendas (cpu int8)")
        from src.subtitles import transcrever
        srt = transcrever(audio, os.path.join(args.work, "subs.srt"))
    else:
        print("[4/5] legendas puladas")

    print("[5/5] ffmpeg 1080p24 ultrafast threads=2")
    from src.composer import montar
    final = montar(clips, audio, srt, args.saida)
    print("PRONTO:", final)

    with open(os.path.join(args.work, "meta_youtube.txt"), "w", encoding="utf-8") as f:
        f.write(f"TITULO:\n{roteiro.get('titulo')}\n\nDESCRICAO:\n{roteiro.get('descricao')}\n\nTAGS:\n{','.join(roteiro.get('tags',[]))}\n")
    print(f"Upload manual: suba {final} em youtube.com/upload e use {os.path.join(args.work, 'meta_youtube.txt')}")

if __name__ == "__main__":
    main()
