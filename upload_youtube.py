"""Upload YouTube Data API v3 — lote brainrot conscientização.
Uso:
  python upload_youtube.py --todos --privacidade unlisted
  python upload_youtube.py --arquivo output/video01_sinais.mp4 --meta work/video01_sinais/meta_youtube.txt --privacidade unlisted

Requer: client_secrets.json (OAuth Desktop) na raiz. Na primeira vez abre o navegador para login Google.
Guarda token em token_youtube.pickle para próximos uploads.
"""
import argparse
import os
import pickle
import re

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
SECRETS = "client_secrets.json"
TOKEN = "token_youtube.pickle"

LOTE = [
    ("output/video01_sinais.mp4", "work/video01_sinais/meta_youtube.txt"),
    ("output/video02_dopamina.mp4", "work/video02_dopamina/meta_youtube.txt"),
    ("output/video03_criancas.mp4", "work/video03_criancas/meta_youtube.txt"),
    ("output/video04_desafio.mp4", "work/video04_desafio/meta_youtube.txt"),
    ("output/video05_pais.mp4", "work/video05_pais/meta_youtube.txt"),
]


def ler_meta(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    def bloco(nome: str) -> str:
        m = re.search(rf"{nome}:\s*\n(.*?)(?=\n[A-Z_]+:\s*\n|\Z)", txt, re.S)
        return (m.group(1).strip() if m else "")
    titulo = bloco("TITULO")[:100]
    descricao = bloco("DESCRICAO")
    tags_raw = bloco("TAGS")
    tags = [t.strip() for t in re.split(r",|\n", tags_raw) if t.strip()][:15]
    return {"titulo": titulo, "descricao": descricao, "tags": tags}


def autenticar():
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    creds = None
    if os.path.exists(TOKEN):
        with open(TOKEN, "rb") as f:
            creds = pickle.load(f)
    # Se o token antigo só tem upload, força re-auth para incluir readonly/analytics
    if creds and creds.valid:
        granted = set(getattr(creds, "scopes", []) or [])
        if set(SCOPES).issubset(granted):
            return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN, "wb") as f:
            pickle.dump(creds, f)
        return creds
    if not os.path.exists(SECRETS):
        raise SystemExit(
            f"FALTA {SECRETS} na raiz.\n"
            "1. console.cloud.google.com → criar projeto → ativar YouTube Data API v3\n"
            "2. APIs e serviços → Tela de consentimento OAuth (Externo) → preencher\n"
            "3. Credenciais → Criar credencial → ID do cliente OAuth → Tipo Desktop → Baixar JSON\n"
            f"4. Renomeie para {SECRETS} e coloque em {os.path.abspath('.')}\n"
            "5. Rode de novo: python upload_youtube.py --todos --privacidade unlisted"
        )
    flow = InstalledAppFlow.from_client_secrets_file(SECRETS, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN, "wb") as f:
        pickle.dump(creds, f)
    return creds


def upload_um(youtube, arquivo: str, meta: dict, privacidade: str = "unlisted") -> str:
    from googleapiclient.http import MediaFileUpload
    body = {
        "snippet": {
            "title": meta["titulo"],
            "description": meta["descricao"],
            "tags": meta["tags"],
            "categoryId": "27",  # Educação
            "defaultLanguage": "pt-BR",
        },
        "status": {
            "privacyStatus": privacidade,  # unlisted | public | private
            "selfDeclaredMadeForKids": False,
            "madeForKids": False,
        },
    }
    media = MediaFileUpload(arquivo, chunksize=8 * 1024 * 1024, resumable=True)
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"  {arquivo}: {int(status.progress() * 100)}%")
    vid = resp["id"]
    print(f"OK: https://youtu.be/{vid} -- {arquivo}")
    # registra ID para auditoria (evita re-upload duplicado)
    with open("work/upload_ids.txt", "a", encoding="utf-8") as fh:
        fh.write(f"{arquivo} -> https://youtu.be/{vid}\n")
    return vid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arquivo", default=None)
    ap.add_argument("--meta", default=None)
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--privacidade", default="unlisted", choices=["unlisted", "public", "private"])
    args = ap.parse_args()

    from googleapiclient.discovery import build
    creds = autenticar()
    youtube = build("youtube", "v3", credentials=creds)

    alvos = LOTE if args.todos else [(args.arquivo, args.meta)]
    for arq, mt in alvos:
        if not arq or not mt:
            raise SystemExit("Use --todos ou --arquivo + --meta")
        if not os.path.exists(arq):
            print(f"PULA (sem arquivo): {arq}")
            continue
        meta = ler_meta(mt)
        print(f"Subindo: {meta['titulo']}")
        upload_um(youtube, arq, meta, args.privacidade)


if __name__ == "__main__":
    main()
