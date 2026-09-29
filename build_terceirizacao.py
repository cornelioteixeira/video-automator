"""Build customizado: "A Crise da Terceirizacao do Cerebro" (6 cenas, ~2min30).
Pipeline: Pexels (1 clip/cena) + edge-tts por cena + SRT por cena (sem Whisper)
+ ffmpeg 1080p24 com narracao legendada + "legendas grandes" via drawtext.
Upload: manual em youtube.com/upload.
Uso: python build_terceirizacao.py
"""
import os
import re

from config import SETTINGS

WORK = "work/crise"
ASSETS = os.path.join(WORK, "assets")
AUDIO = os.path.join(WORK, "audio")
SAIDA = "output/terceirizacao.mp4"

SCENES = [
    {
        "narracao": "Você acabou de escrever um texto. Alguns segundos depois, você lembra do que escreveu?",
        "query": "tired woman laptop screen glow",
        "overlay": "83% dos usuários de IA não lembram do que acabaram de escrever.",
    },
    {
        "narracao": (
            "Um estudo do MIT acompanhou três grupos de pessoas escrevendo. "
            "O grupo que usou ChatGPT teve atividade cerebral 55% menor do que quem pensou sozinho. "
            "Dias depois, 83% deles não conseguiam repetir nenhuma frase do próprio texto. "
            "Já o grupo que escreveu apenas com o próprio cérebro manteve várias regiões cerebrais altamente ativas."
        ),
        "query": "neural network connections",
        "overlay": 'Atividade cerebral caiu 55% | "Descarga cognitiva" em ação.',
    },
    {
        "narracao": (
            "O neurocientista Adam Green, da Universidade de Georgetown, disse uma frase que dói: "
            "é como ir à academia e deixar um robô levantar o peso por você. Você não ganha nada. "
            "O cérebro segue a mesma lógica do músculo: se um tipo de pensamento é terceirizado repetidamente, "
            "os circuitos neurais responsáveis por ele enfraquecem. "
            "O GPS nos fez perder o senso de direção. Os mecanismos de busca criaram o efeito Google. "
            "A IA é a ferramenta de terceirização cognitiva mais poderosa da história."
        ),
        "query": "person lifting weights gym",
        "overlay": '"Use ou perca" não é metáfora. É neurociência.',
    },
    {
        "narracao": (
            "O problema não é só ficar preguiçoso. "
            "A professora de neuropsicologia clínica Barbara Sahakian, da Universidade de Cambridge, "
            "alerta que o uso generalizado da IA tem alta probabilidade de aumentar os casos de demência. "
            "Não porque a IA seja tóxica, mas porque, quando o cérebro pula a fase do esforço de codificação, "
            "a confusão, a luta, o erro, a finalmente sacada, a reserva cognitiva vai embora. "
            "Para adolescentes, habilidades críticas de pensamento estão sendo substituídas bem na fase de desenvolvimento. "
            "Para idosos, que já perdem cognição naturalmente após a aposentadoria, "
            "preencher todo o esforço mental com IA aumenta ainda mais o risco."
        ),
        "query": "teenager burnout laptop dark room",
        "overlay": 'Reserva cognitiva: o "seguro anti-envelhecimento" do seu cérebro está sendo pulado.',
    },
    {
        "narracao": (
            "A boa notícia é que o problema não está na ferramenta, mas em como usamos. "
            "A recomendação dos especialistas é simples: não deixe a IA fazer a parte de entender por você. "
            "Use a IA para economizar tempo em tarefas repetitivas e depois invista esse tempo aprendendo algo mais difícil. "
            "Terminou de escrever um texto? Pergunte-se: consigo repetir sem olhar para a tela? "
            "Se não conseguir, o problema não é a IA. É o seu cérebro avisando que precisa de exercício."
        ),
        "query": "handwriting pen paper close up",
        "overlay": "Entregue o repetitivo à IA. Guarde o pensamento para você.",
    },
    {
        "narracao": (
            "Da próxima vez que você abrir o chat de IA, pare um segundo. "
            "Pergunte: esse passo era para eu dar sozinho? "
            "Porque o seu cérebro está observando cada escolha que você faz."
        ),
        "query": "person typing computer dark room",
        "overlay": "O processo de pensar é o que mantém o cérebro vivo.",
    },
]

META = {
    "titulo": "A Crise da Terceirização do Cérebro: a IA Está Atrofiando Seu Pensamento?",
    "descricao": (
        "Estudo do MIT mostrou atividade cerebral 55% menor em quem escreveu com ChatGPT — "
        "e 83% não lembravam do próprio texto dias depois. Entenda a 'descarga cognitiva', "
        "o alerta sobre reserva cognitiva e como usar a IA sem terceirizar o pensamento.\n\n"
        "E você: consegue repetir sem olhar para a tela o último texto que a IA escreveu por você? Comente.\n\n"
        "Se inscreva no canal para mais vídeos sobre mente, IA e foco."
    ),
    "tags": "cérebro,ia,inteligência artificial,neurociência,chatgpt,pensamento crítico,memória,foco,produtividade",
}

# CTA final (locução + overlay central). Sem narração legendada: só amarelos pontuais + CTA.
CTA_AUDIO = "Se você chegou até aqui, se inscreva no canal e ative o sininho. Seu cérebro agradece."
CTA_OVERLAY = "Se inscreva no canal\\Ne ative o sininho!"


def _fmt(s: float) -> str:
    ms = int(s * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    sec, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def build_srt(durs: list[float], srt_path: str):
    """Legenda COMPLETA da narracao por frases (arquivo p/ upload no YouTube Studio; nao queimada)."""
    entries = []
    t = 0.5  # respiro inicial
    textos = [s["narracao"] for s in SCENES] + [CTA_AUDIO]
    for texto, d in zip(textos, durs):
        frases = [f.strip() for f in re.split(r"(?<=[.!?…])\s+", texto.strip()) if f.strip()]
        total_chars = sum(len(f) for f in frases) or 1
        cur = t
        for f in frases:
            share = len(f) / total_chars * (d - 0.15)
            entries.append((cur, cur + share, f))
            cur += share + 0.15 / max(len(frases), 1)
        t += d
    with open(srt_path, "w", encoding="utf-8") as fh:
        for i, (a, b, txt) in enumerate(entries, 1):
            fh.write(f"{i}\n{_fmt(a)} --> {_fmt(b)}\n{txt}\n\n")
    return srt_path


def esc_path(p: str) -> str:
    return os.path.abspath(p).replace("\\", "/").replace(":", "\\:")


def _ass_ts(s: float) -> str:
    cs = int(round(s * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    sec, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{sec:02d}.{cs:02d}"


def build_ass_overlays(spans: list[tuple[str, float, float, str]], ass_path: str):
    """Legendas grandes amarelas (estilo ASS). spans=(texto,inicio,fim,estilo)."""
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Big,Arial,44,&H0000D4FF,&H000019FF,&H80000000,&H99000000,-1,0,0,0,100,100,0,0,1,2,0,2,60,60,300,1
Style: CTA,Arial,64,&H0000D4FF,&H000019FF,&H80000000,&H99000000,-1,0,0,0,100,100,0,0,1,3,0,5,60,60,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(ass_path, "w", encoding="utf-8") as fh:
        fh.write(head)
        for txt, a, b, style in spans:
            fh.write(f"Dialogue: 0,{_ass_ts(a)},{_ass_ts(b)},{style},,0,0,0,,{txt}\n")
    return ass_path


def main():
    import glob
    from src.tts import sintetizar_blocos
    from src.pexels_provider import baixar_para_blocos
    from src.utils import get_ffmpeg, run, audio_duration_sec

    if not SETTINGS.pexels_api_key:
        raise SystemExit("ERRO: PEXELS_API_KEY vazio no .env")
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(os.path.dirname(SAIDA) or ".", exist_ok=True)

    print("[1/4] edge-tts: 6 cenas + CTA")
    textos = [s["narracao"] for s in SCENES] + [CTA_AUDIO]
    audio_full = sintetizar_blocos(textos, AUDIO)
    part_files = sorted(glob.glob(os.path.join(AUDIO, "voice_0*.mp3")))
    durs = [audio_duration_sec(p) for p in part_files[: len(textos)]]
    scene_durs = durs[: len(SCENES)]
    print(f"  partes={[round(d,1) for d in durs]} total={sum(durs):.1f}s")

    print("[2/4] Pexels: 1 clip por cena")
    blocos = [{"visual_query": s["query"]} for s in SCENES]
    clips = baixar_para_blocos(blocos, SETTINGS.pexels_api_key, ASSETS)

    print("[3/4] SRT completo p/ upload + ASS amarelos (pontuais + CTA)")
    srt = build_srt(durs, os.path.join(WORK, "subs.srt"))

    print("[4/4] ffmpeg 1080p24 + legendas")
    ff = get_ffmpeg()
    vf_norm = "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,fps=24,format=yuv420p"
    norm_dir = os.path.join(WORK, "_norm")
    os.makedirs(norm_dir, exist_ok=True)
    normed = []
    for i, c in enumerate(clips):
        d = os.path.join(norm_dir, f"n_{i:02d}.mp4")
        if not (os.path.exists(d) and os.path.getsize(d) > 100_000):
            r = run([ff, "-y", "-i", c, "-vf", vf_norm, "-c:v", "libx264",
                     "-preset", "ultrafast", "-crf", "23", "-an",
                     "-threads", str(SETTINGS.threads_ffmpeg), d])
            if r.returncode != 0:
                raise RuntimeError("normalize falhou: " + r.stderr[-3000:])
        normed.append(d)
    lst = os.path.join(norm_dir, "video_list.txt")
    with open(lst, "w", encoding="utf-8") as fh:
        for p in normed:
            fh.write(f"file '{os.path.abspath(p)}'\n")
    joined = os.path.join(norm_dir, "joined.mp4")
    r = run([ff, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
    if r.returncode != 0:
        raise RuntimeError("concat falhou: " + r.stderr[-3000:])

    total = sum(durs)
    dur = min(max(total + 1.0, 120.0), 230.0)

    # amarelos pontuais (estilo Big) + CTA final centralizado (estilo CTA)
    spans = []
    t = 0.5
    for s, d in zip(SCENES, scene_durs):
        show = min(7.0, max(d * 0.6, 3.0))
        spans.append((s["overlay"], t + 0.3, t + 0.3 + show, "Big"))
        t += d
    cta_dur = durs[len(SCENES)] if len(durs) > len(SCENES) else 6.0
    spans.append((CTA_OVERLAY, t + 0.2, min(t + cta_dur + 0.8, dur - 0.3), "CTA"))
    ass = build_ass_overlays(spans, os.path.join(WORK, "overlays.ass"))

    # sem legenda branca queimada: so os amarelos (ASS). subs.srt fica p/ upload no Studio.
    vf = f"{vf_norm},fade=t=in:st=0:d=0.5,fade=t=out:st={dur-0.5:.2f}:d=0.5"
    vf += f",subtitles='{esc_path(ass)}'"

    cmd = [ff, "-y", "-stream_loop", "3", "-i", joined, "-i", audio_full,
           "-vf", vf, "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
           "-crf", "23", "-threads", str(SETTINGS.threads_ffmpeg),
           "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
           "-t", f"{dur:.2f}", "-movflags", "+faststart", "-shortest", SAIDA]
    r = run(cmd)
    if r.returncode != 0:
        raise RuntimeError("mux final falhou: " + r.stderr[-4000:])
    print("PRONTO:", SAIDA, f"({dur:.0f}s)")

    with open(os.path.join(WORK, "meta_youtube.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"TITULO:\n{META['titulo']}\n\nDESCRICAO:\n{META['descricao']}\n\nTAGS:\n{META['tags']}\n")
    print(f"Upload manual: suba {SAIDA} em youtube.com/upload usando {WORK}/meta_youtube.txt")
    print(f"Legendas p/ o Studio (opcional): {WORK}/subs.srt")


if __name__ == "__main__":
    main()
