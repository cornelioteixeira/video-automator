"""Gestor do canal até monetização: analisar -> planejar -> gerar -> postar.
Uso:
  python manage_channel.py status
  python manage_channel.py planejar --csv work/analytics.csv
  python manage_channel.py gerar-shorts --tema "..." --hook "..." --saida output/shorts01.mp4 --work work/shorts01
  python manage_channel.py postar --arquivo output/shorts01.mp4 --meta work/shorts01/meta_youtube.txt --privacidade public
"""
import argparse
import json
import os

from config import SETTINGS


def cmd_status():
    from src.strategy import carregar_estado
    from src.analytics import analisar_api
    estado = carregar_estado()
    print(f"Publicados: {len(estado.get('publicados', []))}")
    print(f"Ultima analise: {estado.get('ultima_analise')}")
    print("Metas: 1000 subs + 4000h OU 1000 subs + 10M Shorts/90d")
    print("Diagnóstico API:", analisar_api().get("aviso"))


def cmd_planejar(csv: str | None):
    from src.analytics import analisar_csv
    from src.strategy import plano_semanal
    from src.strategy import carregar_estado, salvar_estado
    analise = analisar_csv(csv) if csv else {"queda_0_3s": False, "ctr_baixo": False}
    print(f"Analise origem={analise.get('origem')} flops={analise.get('flops', '?')}")
    plano = plano_semanal(analise)
    with open("work/plano_semanal.json", "w", encoding="utf-8") as f:
        json.dump(plano, f, ensure_ascii=False, indent=2)
    print(f"Plano: {len(plano)} itens -> work/plano_semanal.json (14 shorts + 2 longos)")
    estado = carregar_estado()
    estado["ultima_analise"] = analise.get("origem")
    salvar_estado(estado)


def cmd_gerar_shorts(tema: str, hook: str, saida: str, work: str):
    import json as _json
    os.makedirs(work, exist_ok=True)
    os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)
    from src.script_gen import gerar_roteiro_shorts
    print("[1/5] Groq shorts cena-a-cena: " + tema)
    rot = gerar_roteiro_shorts(tema, hook, SETTINGS.shorts_target)
    with open(os.path.join(work, "roteiro.json"), "w", encoding="utf-8") as f:
        _json.dump(rot, f, ensure_ascii=False, indent=2)
    print(" Titulo:", rot.get("titulo"))
    print("[2/5] Pexels portrait por cena (sem repetir)")
    from src.pexels_provider import baixar_para_blocos, _carregar_usados, USADOS_DEFAULT
    blocos = [{"visual_query": r["visual_query"]} for r in rot["roteiro"]]
    usados_antes = _carregar_usados(USADOS_DEFAULT)
    import glob as _glob
    # IDs que já eram deste work dir antes (retry após falha) — isentos do check global
    ids_proprios = set()
    for sc in sorted(_glob.glob(os.path.join(work, "assets", "*.pexels.json"))):
        try:
            _info = _json.load(open(sc, encoding="utf-8"))
            if _info.get("id") is not None:
                ids_proprios.add(_info.get("id"))
        except OSError:
            pass
    clips = baixar_para_blocos(blocos, SETTINGS.pexels_api_key,
                               os.path.join(work, "assets"), orientation="portrait")
    infos = []
    for sc in sorted(_glob.glob(os.path.join(work, "assets", "*.pexels.json"))):
        try:
            infos.append(_json.load(open(sc, encoding="utf-8")))
        except OSError:
            pass
    print("[3/5] QA (gancho, loop, repeticao, casamento, ponte p/ longo)")
    from src.qa import checar
    qa = checar(rot, infos, usados_antes - ids_proprios)
    # Auto-reparo honesto: se a ÚNICA falha for ponte p/ longo, injeta a frase
    # no corpo2 e revalida (registrado em qa.json como reparo).
    if (not qa["aprovado"] and qa["falhas"] == ["SEM_PONTE: corpo não cita o vídeo longo relacionado"]
            or (len(qa["falhas"]) == 1 and qa["falhas"][0].startswith("SEM_PONTE"))):
        rot["roteiro"][3]["fala"] = rot["roteiro"][3]["fala"].rstrip() + \
            " Veja o vídeo longo completo no canal."
        with open(os.path.join(work, "roteiro.json"), "w", encoding="utf-8") as f:
            _json.dump(rot, f, ensure_ascii=False, indent=2)
        qa = checar(rot, infos, usados_antes - ids_proprios)
        qa["reparo_auto"] = "ponte-para-longo injetada no corpo2"
    with open(os.path.join(work, "qa.json"), "w", encoding="utf-8") as f:
        _json.dump(qa, f, ensure_ascii=False, indent=2)
    for fl in qa["falhas"]:
        print("  QA:", fl)
    if not qa["aprovado"]:
        print("QA REPROVOU — arrume roteiro/queries e rode de novo. Interrompido antes do TTS.")
        raise SystemExit(1)
    print("[4/5] edge-tts + legenda viral (amarela ativa, 3 palavras, 1 linha)")
    from src.tts import sintetizar_blocos
    textos = [r["fala"] for r in rot["roteiro"]]
    audio = sintetizar_blocos(textos, os.path.join(work, "audio"))
    from src.viral_subs import gerar_legenda_viral
    ass = gerar_legenda_viral(audio, os.path.join(work, "viral.ass"))
    print("[5/5] ffmpeg 1080x1920 + legenda queimada")
    from src.shorts_composer import montar_shorts
    final = montar_shorts(clips, audio, saida, ass_path=ass)
    desc = rot.get("descricao", "") + "\n\n#Shorts #brainrot"
    with open(os.path.join(work, "meta_youtube.txt"), "w", encoding="utf-8") as f:
        f.write(f"TITULO:\n{rot.get('titulo')}\n\nDESCRICAO:\n{desc}\n\nTAGS:\n{','.join(rot.get('tags', []))},shorts\n")
    print("PRONTO:", final)


def cmd_postar(arquivo: str, meta: str, privacidade: str):
    import sys
    sys.argv = ["upload_youtube.py", "--arquivo", arquivo, "--meta", meta,
                "--privacidade", privacidade]
    from upload_youtube import main as up
    up()


def main():
    ap = argparse.ArgumentParser(description="Gestor do canal ate monetizacao")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    p = sub.add_parser("planejar")
    p.add_argument("--csv", default=None)
    g = sub.add_parser("gerar-shorts")
    g.add_argument("--tema", required=True)
    g.add_argument("--hook", default="")
    g.add_argument("--saida", default="output/shorts01.mp4")
    g.add_argument("--work", default="work/shorts01")
    u = sub.add_parser("postar")
    u.add_argument("--arquivo", required=True)
    u.add_argument("--meta", required=True)
    u.add_argument("--privacidade", default="public", choices=["unlisted", "public", "private"])
    args = ap.parse_args()
    if args.cmd == "status":
        cmd_status()
    elif args.cmd == "planejar":
        cmd_planejar(args.csv)
    elif args.cmd == "gerar-shorts":
        cmd_gerar_shorts(args.tema, args.hook, args.saida, args.work)
    elif args.cmd == "postar":
        cmd_postar(args.arquivo, args.meta, args.privacidade)


if __name__ == "__main__":
    main()
