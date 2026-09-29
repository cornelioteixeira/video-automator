"""UI Gradio do video-automator: longos 16:9 + shorts 9:16 + canal + upload + galeria.

Uso:
    python app.py
    # abre em http://127.0.0.1:7860
"""
import glob
import json
import os
import traceback

import gradio as gr

from config import SETTINGS


# ---------- helpers ----------

def listar_videos():
    return sorted(glob.glob("output/*.mp4"))


def listar_metas():
    return sorted(glob.glob("work/*/meta_youtube.txt"))


def listar_works():
    ds = sorted([d for d in glob.glob("work/*") if os.path.isdir(d)])
    return ds


def ler_texto(path: str, limite: int = 8000) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            txt = f.read()
        return txt[:limite]
    except OSError as e:
        return f"(sem arquivo: {e})"


# ---------- config amigavel ----------

def voz_amigavel() -> str:
    return "Feminina" if "Francisca" in SETTINGS.tts_voice else "Masculina"


def velocidade_amigavel() -> str:
    return {"-10%": "mais devagar", "+10%": "mais rápido"}.get(SETTINGS.tts_rate, "normal")


def status_amigavel() -> str:
    def item(ok: bool, nome: str, detalhe: str) -> str:
        return f"{'✓' if ok else '✗'} **{nome}** — {detalhe}"
    return "\n\n".join([
        item(bool(SETTINGS.groq_api_key), "Roteiros automáticos",
             "funcionando" if SETTINGS.groq_api_key else "falta a chave (veja o passo a passo abaixo)"),
        item(bool(SETTINGS.pexels_api_key), "Banco de vídeos e imagens",
             "funcionando" if SETTINGS.pexels_api_key else "falta a chave (veja o passo a passo abaixo)"),
        item(True, "Narração", f"voz {voz_amigavel().lower()}, velocidade {velocidade_amigavel()}"),
        item(whisper_ok(), "Legendas automáticas",
             "disponíveis" if whisper_ok() else "indisponível aqui — sem problema: o YouTube cria sozinho depois"),
        item(True, "Montagem do vídeo", "funcionando"),
    ])


def salvar_config(groq_key, pexels_key, voz, velocidade):
    import re
    mapa_voz = {"Masculina": "pt-BR-AntonioNeural", "Feminina": "pt-BR-FranciscaNeural"}
    mapa_vel = {"Mais devagar": "-10%", "Normal": "+0%", "Mais rápido": "+10%"}
    novos = {}
    if (groq_key or "").strip():
        novos["GROQ_API_KEY"] = groq_key.strip()
    if (pexels_key or "").strip():
        novos["PEXELS_API_KEY"] = pexels_key.strip()
    novos["TTS_VOICE"] = mapa_voz.get(voz, SETTINGS.tts_voice)
    novos["TTS_RATE"] = mapa_vel.get(velocidade, SETTINGS.tts_rate)
    attr = {"GROQ_API_KEY": "groq_api_key", "PEXELS_API_KEY": "pexels_api_key",
            "TTS_VOICE": "tts_voice", "TTS_RATE": "tts_rate"}
    linhas = []
    nl = "\n"
    if os.path.exists(".env"):
        with open(".env", "rb") as f:
            raw = f.read().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        linhas = raw.splitlines()
    vistos = set()
    out = []
    for lin in linhas:
        m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", lin)
        if m and m.group(1) in novos:
            out.append(f"{m.group(1)}={novos[m.group(1)]}")
            vistos.add(m.group(1))
        else:
            out.append(lin)
    for k, v in novos.items():
        if k not in vistos:
            out.append(f"{k}={v}")
    with open(".env", "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(out) + nl)
    for k, v in novos.items():
        object.__setattr__(SETTINGS, attr[k], v)
    return "Salvo ✓ Já está valendo, sem precisar reiniciar.", status_amigavel(), "", ""


# ---------- longos ----------

def gerar_roteiro_longo(tema, segundos):
    from src.script_gen import gerar_roteiro
    segundos = int(max(SETTINGS.min_seconds, min(segundos, SETTINGS.max_seconds)))
    roteiro = gerar_roteiro(tema.strip(), segundos)
    os.makedirs("work/run_atual", exist_ok=True)
    with open("work/run_atual/roteiro.json", "w", encoding="utf-8") as f:
        json.dump(roteiro, f, ensure_ascii=False, indent=2)
    resumo = f"TITULO: {roteiro.get('titulo')}\n\nBLOCOS: {len(roteiro.get('blocos', []))}\n"
    resumo += f"OPINIAO: {roteiro.get('opiniao_central', '')}\n\n"
    for i, b in enumerate(roteiro.get("blocos", []), 1):
        resumo += f"[{i}] ({b.get('visual_query')}) {b.get('texto', '')[:160]}...\n\n"
    return resumo, json.dumps(roteiro, ensure_ascii=False, indent=2)


def gerar_longo(tema, segundos, skip_legendas, saida, work, progress=gr.Progress()):
    import traceback as _tb
    log = []
    def emit(msg):
        log.append(msg)
        return "\n".join(log)
    try:
        progress(0, desc="Roteiro Groq...")
        yield emit(f"[1/5] Groq roteiro ({segundos}s): {tema}"), None, "", ""
        from src.script_gen import gerar_roteiro
        segundos = int(max(SETTINGS.min_seconds, min(segundos, SETTINGS.max_seconds)))
        os.makedirs(work, exist_ok=True)
        os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)
        roteiro = gerar_roteiro(tema.strip(), segundos)
        with open(os.path.join(work, "roteiro.json"), "w", encoding="utf-8") as f:
            json.dump(roteiro, f, ensure_ascii=False, indent=2)
        yield emit(f"Titulo: {roteiro.get('titulo')}"), None, "", ""

        if not SETTINGS.pexels_api_key:
            yield emit("ERRO: PEXELS_API_KEY vazio. Pegue em https://www.pexels.com/api/ e ponha no .env"), None, "", ""
            return

        progress(0.25, desc="Baixando Pexels...")
        yield emit("[2/5] Pexels: 1 video landscape por bloco"), None, "", ""
        from src.pexels_provider import baixar_para_blocos
        clips = baixar_para_blocos(roteiro["blocos"], SETTINGS.pexels_api_key, os.path.join(work, "assets"))
        yield emit(f"[2/5] ok: {len(clips)} clips"), None, "", ""

        progress(0.5, desc="edge-tts...")
        yield emit("[3/5] edge-tts narracao"), None, "", ""
        from src.tts import sintetizar_blocos
        textos = [roteiro.get("intro_pessoal", "")] + [b["texto"] for b in roteiro["blocos"]] + [roteiro.get("outro_pessoal", "")]
        textos = [t for t in textos if t]
        audio = sintetizar_blocos(textos, os.path.join(work, "audio"))
        from src.utils import audio_duration_sec
        yield emit(f"audio {audio_duration_sec(audio):.1f}s"), None, "", ""

        srt = None
        if not skip_legendas:
            progress(0.7, desc="Whisper...")
            yield emit("[4/5] faster-whisper legendas (cpu int8)"), None, "", ""
            from src.subtitles import transcrever
            srt = transcrever(audio, os.path.join(work, "subs.srt"))
        else:
            yield emit("[4/5] legendas puladas"), None, "", ""

        progress(0.85, desc="ffmpeg...")
        yield emit("[5/5] ffmpeg 1080p24 ultrafast threads=2"), None, "", ""
        from src.composer import montar
        final = montar(clips, audio, srt, saida)

        meta_path = os.path.join(work, "meta_youtube.txt")
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"TITULO:\n{roteiro.get('titulo')}\n\nDESCRICAO:\n{roteiro.get('descricao')}\n\nTAGS:\n{','.join(roteiro.get('tags', []))}\n")
        progress(1, desc="Pronto")
        meta = ler_texto(meta_path)
        roteiro_txt = json.dumps(roteiro, ensure_ascii=False, indent=2)
        yield emit(f"PRONTO: {final}\nSuba em youtube.com/upload usando {meta_path}"), final, meta, roteiro_txt
    except Exception as e:
        yield emit(f"ERRO: {e}\n{_tb.format_exc()[-3000:]}"), None, "", ""


# ---------- shorts ----------

def gerar_shorts(tema, hook, saida, work, progress=gr.Progress()):
    import traceback as _tb
    log = []
    def emit(msg):
        log.append(msg)
        return "\n".join(log)
    try:
        progress(0, desc="Roteiro shorts...")
        yield emit(f"[1/5] Groq shorts: {tema}"), None, "", ""
        os.makedirs(work, exist_ok=True)
        os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)
        from src.script_gen import gerar_roteiro_shorts
        rot = gerar_roteiro_shorts(tema.strip(), (hook or "").strip(), SETTINGS.shorts_target)
        with open(os.path.join(work, "roteiro.json"), "w", encoding="utf-8") as f:
            json.dump(rot, f, ensure_ascii=False, indent=2)
        yield emit(f"Titulo: {rot.get('titulo')}"), None, "", ""

        progress(0.3, desc="Pexels portrait...")
        yield emit("[2/5] Pexels portrait por cena"), None, "", ""
        from src.pexels_provider import baixar_para_blocos, _carregar_usados, USADOS_DEFAULT
        blocos = [{"visual_query": r["visual_query"]} for r in rot["roteiro"]]
        usados_antes = _carregar_usados(USADOS_DEFAULT)
        import glob as _glob
        ids_proprios = set()
        for sc in sorted(_glob.glob(os.path.join(work, "assets", "*.pexels.json"))):
            try:
                _info = json.load(open(sc, encoding="utf-8"))
                if _info.get("id") is not None:
                    ids_proprios.add(_info.get("id"))
            except OSError:
                pass
        clips = baixar_para_blocos(blocos, SETTINGS.pexels_api_key, os.path.join(work, "assets"), orientation="portrait")

        progress(0.5, desc="QA...")
        yield emit("[3/5] QA"), None, "", ""
        infos = []
        for sc in sorted(_glob.glob(os.path.join(work, "assets", "*.pexels.json"))):
            try:
                infos.append(json.load(open(sc, encoding="utf-8")))
            except OSError:
                pass
        from src.qa import checar
        qa = checar(rot, infos, usados_antes - ids_proprios)
        if (not qa["aprovado"] and qa["falhas"] == ["SEM_PONTE: corpo não cita o vídeo longo relacionado"]
                or (len(qa["falhas"]) == 1 and qa["falhas"][0].startswith("SEM_PONTE"))):
            rot["roteiro"][3]["fala"] = rot["roteiro"][3]["fala"].rstrip() + " Veja o vídeo longo completo no canal."
            with open(os.path.join(work, "roteiro.json"), "w", encoding="utf-8") as f:
                json.dump(rot, f, ensure_ascii=False, indent=2)
            qa = checar(rot, infos, usados_antes - ids_proprios)
            qa["reparo_auto"] = "ponte-para-longo injetada no corpo2"
        with open(os.path.join(work, "qa.json"), "w", encoding="utf-8") as f:
            json.dump(qa, f, ensure_ascii=False, indent=2)
        for fl in qa["falhas"]:
            yield emit(f"QA: {fl}"), None, "", ""
        if not qa["aprovado"]:
            yield emit("QA REPROVOU — arrume roteiro/queries e rode de novo."), None, json.dumps(qa, ensure_ascii=False, indent=2), ""
            return

        progress(0.7, desc="TTS + legenda viral...")
        yield emit("[4/5] edge-tts + legenda viral"), None, "", ""
        from src.tts import sintetizar_blocos
        textos = [r["fala"] for r in rot["roteiro"]]
        audio = sintetizar_blocos(textos, os.path.join(work, "audio"))
        from src.viral_subs import gerar_legenda_viral
        ass = gerar_legenda_viral(audio, os.path.join(work, "viral.ass"))

        progress(0.9, desc="ffmpeg 9:16...")
        yield emit("[5/5] ffmpeg 1080x1920"), None, "", ""
        from src.shorts_composer import montar_shorts
        final = montar_shorts(clips, audio, saida, ass_path=ass)
        desc = rot.get("descricao", "") + "\n\n#Shorts #brainrot"
        with open(os.path.join(work, "meta_youtube.txt"), "w", encoding="utf-8") as f:
            f.write(f"TITULO:\n{rot.get('titulo')}\n\nDESCRICAO:\n{desc}\n\nTAGS:\n{','.join(rot.get('tags', []))},shorts\n")
        progress(1, desc="Pronto")
        meta = ler_texto(os.path.join(work, "meta_youtube.txt"))
        roteiro_txt = json.dumps(rot, ensure_ascii=False, indent=2)
        yield emit(f"PRONTO: {final}"), final, meta, roteiro_txt
    except Exception as e:
        yield emit(f"ERRO: {e}\n{_tb.format_exc()[-3000:]}"), None, "", ""


# ---------- canal ----------

def canal_status():
    from src.strategy import carregar_estado
    from src.analytics import analisar_api
    estado = carregar_estado()
    try:
        diag = analisar_api().get("aviso")
    except Exception as e:
        diag = f"(API indisponivel: {e})"
    return (
        f"Publicados: {len(estado.get('publicados', []))}\n"
        f"Ultima analise: {estado.get('ultima_analise')}\n"
        f"Metas: 1000 subs + 4000h OU 1000 subs + 10M Shorts/90d\n"
        f"Diagnóstico API: {diag}\n\n"
        f"{json.dumps(estado.get('publicados', []), ensure_ascii=False, indent=2)}"
    )


def canal_planejar(csv_file):
    from src.analytics import analisar_csv
    from src.strategy import plano_semanal, carregar_estado, salvar_estado
    csv_path = csv_file.name if csv_file is not None else None
    analise = analisar_csv(csv_path) if csv_path else {"queda_0_3s": False, "ctr_baixo": False, "origem": "sem-csv"}
    plano = plano_semanal(analise)
    os.makedirs("work", exist_ok=True)
    with open("work/plano_semanal.json", "w", encoding="utf-8") as f:
        json.dump(plano, f, ensure_ascii=False, indent=2)
    estado = carregar_estado()
    estado["ultima_analise"] = analise.get("origem")
    salvar_estado(estado)
    resumo = f"Analise origem={analise.get('origem')} | {len(plano)} itens (14 shorts + 2 longos)\n\n"
    for i, p in enumerate(plano, 1):
        resumo += f"{i:02d}. [{p['tipo']}] {p.get('titulo') or p.get('hook')}\n"
    return resumo, json.dumps(plano, ensure_ascii=False, indent=2)


# ---------- upload ----------

def fazer_upload(arquivo, meta_path, privacidade):
    try:
        if not arquivo or not meta_path:
            return "Escolha o video e o meta_youtube.txt."
        from upload_youtube import autenticar, ler_meta, upload_um
        from googleapiclient.discovery import build
        creds = autenticar()
        youtube = build("youtube", "v3", credentials=creds)
        meta = ler_meta(meta_path)
        vid = upload_um(youtube, arquivo, meta, privacidade)
        return f"OK: https://youtu.be/{vid} -- {arquivo}"
    except Exception:
        return f"ERRO no upload:\n{traceback.format_exc()[-4000:]}"


# ---------- galeria ----------

def atualizar_galeria():
    vids = listar_videos()
    metas = listar_metas()
    works = listar_works()
    tabela = "VIDEOS:\n" + ("\n".join(f" - {v} ({os.path.getsize(v)/1e6:.1f} MB)" for v in vids) if vids else " (nenhum)") + "\n\nMETAS:\n" + ("\n".join(f" - {m}" for m in metas) if metas else " (nenhum)")
    return tabela, gr.update(choices=vids, value=vids[0] if vids else None)


def inspecionar_video(arquivo):
    if not arquivo or not os.path.exists(arquivo):
        return None, "(video nao encontrado)", ""
    base = os.path.splitext(os.path.basename(arquivo))[0]
    candidatos = glob.glob(f"work/*{base}*/meta_youtube.txt") + glob.glob("work/*/meta_youtube.txt")
    meta_txt = "(meta nao encontrado — escolha na aba Upload)"
    roteiro_txt = ""
    # tenta achar work correspondente pelo nome
    for m in candidatos:
        if base.replace("output", "") in m or True:
            pass
    # heuristica simples: procura meta cujo work contenha parte do nome
    for m in sorted(glob.glob("work/*/meta_youtube.txt")):
        w = os.path.basename(os.path.dirname(m))
        if any(p in arquivo for p in [w]) or any(p in w for p in base.split("_") if len(p) > 3):
            meta_txt = ler_texto(m)
            rj = os.path.join(os.path.dirname(m), "roteiro.json")
            if os.path.exists(rj):
                roteiro_txt = ler_texto(rj)
            break
    else:
        if candidatos:
            meta_txt = ler_texto(sorted(candidatos)[0])
    return arquivo, meta_txt, roteiro_txt


# ---------- assistente guiado (V6: passo a passo + exemplos + garantias) ----------

EXEMPLOS_ASSUNTO = [
    "como o sono afeta a memoria",
    "historia do cafe no brasil",
    "como o celular rouba seu foco",
    "filhos e telas: guia sem briga",
]

DURACOES = {
    "Rapidinho (± 2 min)": 120,
    "Padrão (± 2 min 30) — mais usado": 150,
    "Aprofundado (± 5 min)": 300,
}

GARANTIA = (
    "✓ Você só escolhe o assunto. "
    "**A gente escreve o roteiro, busca as imagens, narra e monta o vídeo sozinho.**"
)


def passos_md(n: int) -> str:
    nomes = ["Assunto", "Detalhes", "Criar"]
    partes = []
    for i, nome in enumerate(nomes, 1):
        if i < n:
            partes.append(f"✓ {nome}")
        elif i == n:
            partes.append(f"**► {i}. {nome}**")
        else:
            partes.append(f"{i}. {nome}")
    return "  →  ".join(partes)


def whisper_ok() -> bool:
    try:
        import faster_whisper  # noqa: F401
        return True
    except ImportError:
        return False


def ir_passo2(formato, tema):
    if not (tema or "").strip():
        return (
            passos_md(1), gr.update(visible=True), gr.update(visible=False),
            gr.update(visible=True), gr.update(visible=False),
            "⚠️ Escreva o assunto ou toque num exemplo abaixo.",
        )
    longo = (formato == "Vídeo longo")
    return (
        passos_md(2), gr.update(visible=False), gr.update(visible=True),
        gr.update(visible=longo), gr.update(visible=not longo), "",
    )


def ir_passo3(formato, tema, duracao, hook):
    detalhe = f"Duração: {duracao}" if formato == "Vídeo longo" else f"Frase de abertura: {(hook or '').strip() or 'a gente cria uma'}"
    resumo = f"**Formato:** {formato}\n\n**Assunto:** {(tema or '').strip()}\n\n**{detalhe}**"
    return passos_md(3), gr.update(visible=False), gr.update(visible=True), resumo


def linha_amigavel(linha: str):
    l = linha.strip()
    if not l:
        return None
    if l.startswith("ERRO") or "Traceback" in l or l.startswith("QA:") \
            or "QA REPROVOU" in l or "SEM_PONTE" in l or "reparo" in l.lower():
        return l
    if "Groq shorts" in l:
        return "① Escrevendo o roteiro do Shorts…"
    if "Groq roteiro" in l:
        return "① Escrevendo o roteiro…"
    if l.startswith("Titulo:"):
        return "Roteiro pronto ✓"
    if "portrait" in l:
        return "② Buscando as imagens…"
    if "Pexels" in l:
        return "② Buscando as imagens do vídeo…"
    if "clips" in l:
        return "Imagens prontas ✓"
    if "legenda viral" in l:
        return "④ Gravando a narração e preparando as legendas…"
    if "edge-tts" in l:
        return "③ Gravando a narração…"
    if l.startswith("audio "):
        return "Narração pronta ✓"
    if "whisper" in l.lower():
        return "④ Criando as legendas…"
    if "legendas puladas" in l or "Legendas automáticas indisponíveis" in l:
        return "Sem legendas queimadas (o YouTube gera sozinho depois) →"
    if "Legenda viral pronta" in l:
        return "Legendas prontas ✓"
    if "QA" in l:
        return "③ Conferindo a qualidade…"
    if "ffmpeg" in l or "[5/5]" in l:
        return "⑤ Montando o vídeo final… (leva alguns minutos, pode esperar)"
    if l.startswith("PRONTO"):
        return "Pronto! Assista ao vídeo acima ✓"
    return None


def criar_assistente(formato, tema, duracao, hook, progress=gr.Progress()):
    import re
    from datetime import datetime
    amigaveis = ["Você escolheu o assunto — agora é com a gente…"]
    vistas = [0]

    def traduzir(log_acumulado):
        linhas = log_acumulado.split("\n")
        for lin in linhas[vistas[0]:]:
            a = linha_amigavel(lin)
            if a and (not amigaveis or amigaveis[-1] != a):
                amigaveis.append(a)
        vistas[0] = len(linhas)
        return "\n".join(amigaveis)

    try:
        tema = (tema or "").strip()
        if not tema:
            yield "⚠️ Volte ao passo 1 e escolha um assunto.", None, ""
            return
        slug = re.sub(r"[^a-z0-9]+", "_", tema.lower()).strip("_")[:30] or "video"
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if formato == "Vídeo longo":
            segundos = DURACOES.get(duracao, 150)
            saida, work = f"output/{slug}.mp4", f"work/{slug}_{stamp}"
            skip = not whisper_ok()
            if skip:
                amigaveis.append("Legendas automáticas indisponíveis aqui — gerando sem queimar legendas.")
            for log, video, meta, _rot in gerar_longo(tema, segundos, skip, saida, work, progress):
                yield traduzir(log), video, meta
        else:
            saida, work = f"output/{slug}_shorts.mp4", f"work/{slug}_{stamp}"
            for log, video, meta, _rot in gerar_shorts(tema, hook or "", saida, work, progress):
                yield traduzir(log), video, meta
    except Exception:
        amigaveis.append(f"Ops, algo deu errado:\n{traceback.format_exc()[-1500:]}")
        yield "\n".join(amigaveis), None, ""


# ---------- app ----------

with gr.Blocks(title="video-automator") as demo:
    gr.Markdown("# video-automator — Shorts 9:16 + Longos 16:9\nNovo por aqui? Comece pelo **Assistente guiado** ★. Quem já sabe o caminho usa as outras abas.")
    gr.Markdown("## Sua configuração")
    cfg_md = gr.Markdown(status_amigavel())
    with gr.Row():
        btn_cfg = gr.Button("Atualizar estado", size="sm")
    with gr.Accordion("Arrumar chaves e voz", open=not (SETTINGS.groq_api_key and SETTINGS.pexels_api_key)):
        gr.Markdown("**1. Chave dos roteiros** — pegue grátis em console.groq.com (crie a conta, copie a chave e cole aqui):")
        cfg_groq = gr.Textbox(label="Chave dos roteiros (só preencher para trocar)", type="password",
                              placeholder="Começa com gsk_… — vazio = mantém a atual")
        gr.Markdown("**2. Chave dos vídeos e imagens** — pegue grátis em pexels.com/api (copie a chave e cole aqui):")
        cfg_pexels = gr.Textbox(label="Chave dos vídeos e imagens (só preencher para trocar)", type="password",
                                placeholder="Vazio = mantém a atual")
        with gr.Row():
            cfg_voz = gr.Radio(["Masculina", "Feminina"], value=voz_amigavel(), label="Voz da narração")
            cfg_vel = gr.Radio(["Mais devagar", "Normal", "Mais rápido"], value="Normal"
                               if velocidade_amigavel() == "normal"
                               else velocidade_amigavel().capitalize(),
                               label="Velocidade da fala")
        cfg_save = gr.Button("Salvar", variant="primary")
        cfg_msg = gr.Markdown("")

    with gr.Tab("Assistente guiado ★"):
        w_steps = gr.Markdown(passos_md(1))
        with gr.Column(visible=True) as w_g1:
            w_formato = gr.Radio(["Vídeo longo", "Shorts"], value="Vídeo longo",
                                 label="O que você quer fazer?")
            w_tema = gr.Textbox(label="Sobre o que é o vídeo?",
                                placeholder="Ex.: como o sono afeta a memória", lines=2)
            w_aviso = gr.Markdown("")
            gr.Markdown("Sem ideia? Toque num exemplo:")
            with gr.Row():
                w_ex1 = gr.Button(EXEMPLOS_ASSUNTO[0], size="sm")
                w_ex2 = gr.Button(EXEMPLOS_ASSUNTO[1], size="sm")
                w_ex3 = gr.Button(EXEMPLOS_ASSUNTO[2], size="sm")
                w_ex4 = gr.Button(EXEMPLOS_ASSUNTO[3], size="sm")
            gr.Markdown(GARANTIA)
            w_next1 = gr.Button("Continuar →", variant="primary")
        with gr.Column(visible=False) as w_g2:
            w_dur = gr.Radio(list(DURACOES.keys()), value="Padrão (± 2 min 30) — mais usado",
                             label="Quanto tempo de vídeo?", visible=True)
            w_hook = gr.Textbox(label="Frase de abertura (opcional — se vazio, a gente cria)",
                                placeholder="Ex.: Seu cérebro está apodrecendo e você nem percebeu",
                                lines=2, visible=False)
            with gr.Row():
                w_back2 = gr.Button("← Voltar", variant="secondary")
                w_next2 = gr.Button("Continuar →", variant="primary")
        with gr.Column(visible=False) as w_g3:
            w_resumo = gr.Markdown("")
            gr.Markdown(GARANTIA)
            w_criar = gr.Button("Criar meu vídeo", variant="primary")
            w_back3 = gr.Button("← Voltar e ajustar", variant="secondary", size="sm")
            w_log = gr.Textbox(label="A gente faz o resto — acompanhe aqui", lines=10)
            w_video = gr.Video(label="Seu vídeo")
            w_meta = gr.Textbox(label="Título + descrição + tags (pronto p/ o YouTube)", lines=8)
        for _b, _ex in ((w_ex1, EXEMPLOS_ASSUNTO[0]), (w_ex2, EXEMPLOS_ASSUNTO[1]),
                        (w_ex3, EXEMPLOS_ASSUNTO[2]), (w_ex4, EXEMPLOS_ASSUNTO[3])):
            _b.click(lambda ex=_ex: ex, [], [w_tema])
        w_next1.click(ir_passo2, [w_formato, w_tema],
                      [w_steps, w_g1, w_g2, w_dur, w_hook, w_aviso])
        w_back2.click(lambda: (passos_md(1), gr.update(visible=True), gr.update(visible=False)),
                      [], [w_steps, w_g1, w_g2])
        w_next2.click(ir_passo3, [w_formato, w_tema, w_dur, w_hook],
                      [w_steps, w_g2, w_g3, w_resumo])
        w_back3.click(lambda: (passos_md(2), gr.update(visible=True), gr.update(visible=False)),
                      [], [w_steps, w_g2, w_g3])
        w_criar.click(criar_assistente, [w_formato, w_tema, w_dur, w_hook],
                      [w_log, w_video, w_meta])

    with gr.Tab("Longo 16:9"):
        with gr.Row():
            with gr.Column():
                t_tema = gr.Textbox(label="Tema", placeholder="como o sono afeta a memoria", lines=2)
                t_seg = gr.Slider(120, 480, value=150, step=10, label="Duracao alvo (s)")
                t_saida = gr.Textbox(label="Saida", value="output/final.mp4")
                t_work = gr.Textbox(label="Work dir", value="work/run_atual")
                t_skip = gr.Checkbox(label="Pular legendas (mais rapido)", value=False)
                with gr.Row():
                    b_rot = gr.Button("So gerar roteiro", variant="secondary")
                    b_full = gr.Button("Gerar video completo", variant="primary")
            with gr.Column():
                t_log = gr.Textbox(label="Log", lines=12)
                t_video = gr.Video(label="Video final")
                t_meta = gr.Textbox(label="meta_youtube.txt", lines=6)
                t_rot = gr.Textbox(label="roteiro.json", lines=12)
        b_rot.click(gerar_roteiro_longo, [t_tema, t_seg], [t_log, t_rot])
        b_full.click(gerar_longo, [t_tema, t_seg, t_skip, t_saida, t_work], [t_log, t_video, t_meta, t_rot])

    with gr.Tab("Shorts 9:16"):
        with gr.Row():
            with gr.Column():
                s_tema = gr.Textbox(label="Tema", placeholder="sinal de brain rot", lines=2)
                s_hook = gr.Textbox(label="Hook 0-3s (opcional)", placeholder="Seu cerebro esta apodrecendo e voce nem percebeu", lines=2)
                s_saida = gr.Textbox(label="Saida", value="output/shorts01.mp4")
                s_work = gr.Textbox(label="Work dir", value="work/shorts01")
                b_shorts = gr.Button("Gerar shorts", variant="primary")
            with gr.Column():
                s_log = gr.Textbox(label="Log", lines=12)
                s_video = gr.Video(label="Shorts final")
                s_meta = gr.Textbox(label="meta_youtube.txt", lines=6)
                s_rot = gr.Textbox(label="roteiro/qa", lines=12)
        b_shorts.click(gerar_shorts, [s_tema, s_hook, s_saida, s_work], [s_log, s_video, s_meta, s_rot])

    with gr.Tab("Canal"):
        with gr.Row():
            with gr.Column():
                b_status = gr.Button("Status")
                csv_in = gr.File(label="analytics.csv do Studio (opcional)", file_types=[".csv"])
                b_plan = gr.Button("Planejar semana (14 shorts + 2 longos)")
            with gr.Column():
                c_status = gr.Textbox(label="Status / plano resumo", lines=14)
                c_plano = gr.Textbox(label="plano_semanal.json", lines=14)
        b_status.click(canal_status, [], [c_status])
        b_plan.click(canal_planejar, [csv_in], [c_status, c_plano])

    with gr.Tab("Upload YouTube"):
        gr.Markdown("Requer `client_secrets.json` na raiz. Na primeira vez abre o navegador para login Google.")
        with gr.Row():
            with gr.Column():
                u_arq = gr.Dropdown(choices=listar_videos(), label="Video (output/*.mp4)")
                u_meta = gr.Dropdown(choices=listar_metas(), label="Meta (work/*/meta_youtube.txt)")
                u_priv = gr.Radio(["unlisted", "public", "private"], value="unlisted", label="Privacidade")
                with gr.Row():
                    u_refresh = gr.Button("Atualizar listas", size="sm")
                    b_up = gr.Button("Postar", variant="primary")
            u_log = gr.Textbox(label="Resultado", lines=8)
        u_refresh.click(lambda: (gr.update(choices=listar_videos()), gr.update(choices=listar_metas())),
                        [], [u_arq, u_meta])
        b_up.click(fazer_upload, [u_arq, u_meta, u_priv], [u_log])

    with gr.Tab("Galeria"):
        with gr.Row():
            with gr.Column():
                g_btn = gr.Button("Atualizar galeria")
                g_lista = gr.Textbox(label="Arquivos", lines=14)
                g_sel = gr.Dropdown(choices=listar_videos(), label="Escolher video")
            with gr.Column():
                g_video = gr.Video(label="Preview")
                g_meta = gr.Textbox(label="Meta / roteiro", lines=10)
                g_rot = gr.Textbox(label="Roteiro (work correspondente)", lines=10)
        g_btn.click(atualizar_galeria, [], [g_lista, g_sel])
        g_sel.change(inspecionar_video, [g_sel], [g_video, g_meta, g_rot])

    btn_cfg.click(lambda: status_amigavel(), [], [cfg_md])
    cfg_save.click(salvar_config, [cfg_groq, cfg_pexels, cfg_voz, cfg_vel],
                   [cfg_msg, cfg_md, cfg_groq, cfg_pexels])

if __name__ == "__main__":
    demo.queue().launch(server_name="127.0.0.1", server_port=7860)
