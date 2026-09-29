"""Publica o SEO otimizado (work/seo_longos.json) nos 5 vídeos longos via YouTube Data API.

Uso:
  python seo_publish.py

Na primeira vez abre o navegador para login Google (precisa do escopo
youtube.force-ssl, que o token atual não tem). Depois de logar, aplica
título + descrição + tags + capítulos nos 5 vídeos de uma vez.
"""
import json
import pickle

from upload_youtube import SECRETS, TOKEN, SCOPES

# videos.update exige escopo com escrita total (youtube.upload sozinho dá 403)
SCOPES_PUBLISH = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def autenticar_full():
    import os
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    creds = None
    if os.path.exists(TOKEN):
        with open(TOKEN, "rb") as f:
            creds = pickle.load(f)
    granted = set(getattr(creds, "scopes", []) or [])
    if creds and creds.valid and set(SCOPES_PUBLISH).issubset(granted):
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            creds = None
        if creds and creds.valid and set(SCOPES_PUBLISH).issubset(set(getattr(creds, "scopes", []) or [])):
            with open(TOKEN, "wb") as f:
                pickle.dump(creds, f)
            return creds
    print("Abrindo o navegador para login Google (escopo youtube.force-ssl)...")
    flow = InstalledAppFlow.from_client_secrets_file(SECRETS, SCOPES_PUBLISH)
    creds = flow.run_local_server(port=0)
    with open(TOKEN, "wb") as f:
        pickle.dump(creds, f)
    return creds


def main():
    from googleapiclient.discovery import build
    creds = autenticar_full()
    yt = build("youtube", "v3", credentials=creds)
    with open("work/seo_longos.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    for v in data["videos"]:
        body = {
            "id": v["id"],
            "snippet": {
                "title": v["titulo"],
                "description": v["descricao"],
                "tags": v["tags"],
                "categoryId": "27",
                "defaultLanguage": "pt-BR",
            },
        }
        r = yt.videos().update(part="snippet", body=body).execute()
        print(f"OK https://youtu.be/{r['id']} | {r['snippet']['title']}")
    print("SEO publicado nos 5 longos.")


if __name__ == "__main__":
    main()
